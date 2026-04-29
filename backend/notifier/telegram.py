"""Telegram bildirim modülü.

Tüm bildirimler .env dosyasındaki TELEGRAM_BOT_TOKEN ve TELEGRAM_CHAT_ID
değişkenlerinden okunur. Token hiçbir zaman kod içine yazılmaz.

Desteklenen olaylar:
  - Bot başlatıldı / durduruldu
  - Yeni sinyal
  - Alım / satım notu
  - Günlük zarar limiti aşıldı (cüzdan donduruldu)
  - Hata
  - Günlük özet
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
_API_BASE = f"https://api.telegram.org/bot{_TOKEN}"


def _configured() -> bool:
    if not _TOKEN or not _CHAT_ID:
        logger.warning(
            "telegram: TELEGRAM_BOT_TOKEN veya TELEGRAM_CHAT_ID .env dosyasında ayarlanmamış"
        )
        return False
    return True


async def send_telegram(text: str, parse_mode: str = "Markdown") -> bool:
    """Ham metin gönder. Diğer fonksiyonlar bunu çağırır."""
    if not _configured():
        return False
    try:
        import httpx

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{_API_BASE}/sendMessage",
                json={"chat_id": _CHAT_ID, "text": text, "parse_mode": parse_mode},
            )
        if resp.status_code == 200:
            return True
        logger.warning(
            "telegram: API hatası %d — %s", resp.status_code, resp.text[:200]
        )
        return False
    except Exception as exc:  # noqa: BLE001
        logger.warning("telegram: gönderim başarısız — %s", exc)
        return False


# ── Olay bildirimleri ────────────────────────────────────────────────────────

async def bildir_bot_basladi() -> bool:
    return await send_telegram(
        "🟢 *PiyasaPilot başlatıldı*\n"
        "Paper trading robotu çalışıyor. Sinyaller izleniyor."
    )


async def bildir_bot_durdu() -> bool:
    return await send_telegram(
        "🔴 *PiyasaPilot durduruldu*\n"
        "Robot kapatıldı. Açık pozisyonlar korunuyor."
    )


async def bildir_yeni_sinyal(signal: dict[str, Any]) -> bool:
    symbol = signal.get("symbol", "?")
    sig_type = signal.get("signal_type", "?")
    price = float(signal.get("price", 0))
    strategy = signal.get("strategy_id", "?")
    strength = int(signal.get("strength", 5))
    reason = signal.get("reason", "")
    stars = "⭐" * min(strength // 2, 5)
    emoji = "🟢" if "BUY" in sig_type else "🔴"
    return await send_telegram(
        f"{emoji} *Yeni Sinyal — {sig_type}*\n"
        f"📌 Sembol: `{symbol}`\n"
        f"💰 Fiyat: `{price:.4f}`\n"
        f"📊 Strateji: `{strategy}`\n"
        f"💪 Güç: {strength}/10 {stars}\n"
        f"📝 {reason}"
    )


async def bildir_alim(strategy_id: str, symbol: str, price: float,
                      quantity: float, tutar: float, reason: str) -> bool:
    return await send_telegram(
        f"🛒 *Alım Gerçekleşti*\n"
        f"📌 Sembol: `{symbol}`\n"
        f"💰 Fiyat: `{price:.4f}`\n"
        f"📦 Miktar: `{quantity:.4f}`\n"
        f"💵 Tutar: `{tutar:,.2f}₺`\n"
        f"📊 Strateji: `{strategy_id}`\n"
        f"📝 {reason}"
    )


async def bildir_satim(strategy_id: str, symbol: str, price: float,
                       quantity: float, pnl: float, reason: str) -> bool:
    emoji = "🟢" if pnl >= 0 else "🔴"
    isaret = "+" if pnl >= 0 else ""
    return await send_telegram(
        f"💸 *Satım Gerçekleşti*\n"
        f"📌 Sembol: `{symbol}`\n"
        f"💰 Fiyat: `{price:.4f}`\n"
        f"📦 Miktar: `{quantity:.4f}`\n"
        f"{emoji} Kâr/Zarar: `{isaret}{pnl:,.2f}₺`\n"
        f"📊 Strateji: `{strategy_id}`\n"
        f"📝 {reason}"
    )


async def bildir_cuzdан_donduruldu(strategy_id: str, daily_loss: float,
                                   initial_capital: float) -> bool:
    oran = abs(daily_loss) / initial_capital * 100
    return await send_telegram(
        f"⛔ *Cüzdan Donduruldu*\n"
        f"📊 Strateji: `{strategy_id}`\n"
        f"📉 Günlük zarar: `{daily_loss:,.2f}₺` (`{oran:.1f}%`)\n"
        f"ℹ️ Günlük zarar limiti aşıldı. Yeni işlem yapılmayacak."
    )


async def bildir_hata(hata: str, baglam: str = "") -> bool:
    mesaj = f"⚠️ *Hata Oluştu*\n`{hata}`"
    if baglam:
        mesaj += f"\n📍 Bağlam: {baglam}"
    return await send_telegram(mesaj)


async def bildir_gunluk_ozet(wallets: list[dict], trades: list[dict]) -> bool:
    satirlar = ["📊 *Günlük Paper Trading Özeti*\n"]
    for w in wallets:
        pnl = w["cash"] - w["initial_capital"]
        emoji = "🟢" if pnl >= 0 else "🔴"
        durum = "🔒 Donduruldu" if w["is_halted"] else "✅ Aktif"
        satirlar.append(
            f"*{w['strategy_id']}*: {durum}\n"
            f"  {emoji} Nakit: `{w['cash']:,.2f}₺` | PnL: `{pnl:+,.2f}₺`"
        )
    tamamlanan = [t for t in trades if t.get("closed_at")]
    kazananlar = [t for t in tamamlanan if (t.get("pnl") or 0) > 0]
    if tamamlanan:
        win_rate = len(kazananlar) / len(tamamlanan) * 100
        satirlar.append(
            f"\n📈 Kazanma Oranı: `{win_rate:.1f}%` "
            f"({len(kazananlar)}/{len(tamamlanan)} işlem)"
        )
    return await send_telegram("\n".join(satirlar))


async def test_baglantisi() -> bool:
    """Bağlantı testi — 'Telegram bağlantısı başarılı.' mesajı gönderir."""
    tamam = await send_telegram(
        "✅ *Telegram bağlantısı başarılı.*\n"
        "PiyasaPilot bildirim sistemi hazır."
    )
    if tamam:
        logger.info("telegram: bağlantı testi başarılı")
    else:
        logger.error("telegram: bağlantı testi başarısız — .env dosyasını kontrol et")
    return tamam
