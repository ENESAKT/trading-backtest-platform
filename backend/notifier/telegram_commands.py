"""Telegram bot komut işleyicileri.

Her fonksiyon bir komuta karşılık gelir ve Telegram'a gönderilecek
Türkçe metin döner. Gizli bilgi (token, key) asla döndürülmez.
"""

from __future__ import annotations

import datetime as dt
import logging
import os
import re
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_API_URL = os.getenv("NOTIFY_API_URL", "http://localhost:8000")


# ── Yardımcılar ──────────────────────────────────────────────────────────────

async def _api_get(path: str, timeout: float = 8.0) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.get(f"{_API_URL}{path}")
            return r.json()
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}


def _mask_sensitive(text: str) -> str:
    """Token, API key ve şifre pattern'larını maskele."""
    text = re.sub(r"\d{8,}:[A-Za-z0-9_-]{30,}", "[TOKEN_GİZLİ]", text)
    text = re.sub(
        r"(?i)(token|key|password|secret|api_key)\s*[:=]\s*\S+",
        r"\1=[GİZLİ]",
        text,
    )
    return text


def _price_str(price: float) -> str:
    if price >= 100:
        return f"{price:,.2f}"
    elif price >= 1:
        return f"{price:.4f}"
    return f"{price:.6f}"


def _calc_rsi(closes: "pd.Series", period: int = 14) -> float:  # type: ignore[name-defined]
    if len(closes) < period + 1:
        return 50.0
    delta = closes.diff()
    avg_gain = delta.clip(lower=0).rolling(period, min_periods=period).mean().iloc[-1]
    avg_loss = (-delta.clip(upper=0)).rolling(period, min_periods=period).mean().iloc[-1]
    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0
    return 100.0 - (100.0 / (1.0 + avg_gain / avg_loss))


# ── Komut işleyicileri ────────────────────────────────────────────────────────

async def cmd_yardim(_args: str) -> str:
    return (
        "🤖 *PiyasaPilot Asistanı*\n\n"
        "Kullanılabilir komutlar:\n\n"
        "*/durum* — Sistem durumu\n"
        "*/fiyat* SEMBOL — Anlık fiyat\n"
        "  _Örn: /fiyat THYAO_\n"
        "*/sinyal* SEMBOL — Sinyal analizi\n"
        "  _Örn: /sinyal BTCUSDT_\n"
        "*/strateji* SEMBOL — Teknik detay\n"
        "*/ozet* — Günlük paper trading özeti\n"
        "*/son* — Son sinyaller\n"
        "*/hata* — Son hatalar\n"
        "*/kontrol* — Proje sağlık kontrolü\n"
        "*/gorev* [metin] — Görev analizi\n"
        "*/duzelt* [metin] — Güvenli düzeltme\n"
        "*/yardim* — Bu liste\n\n"
        "⚠️ _Yatırım tavsiyesi değildir._"
    )


async def cmd_durum(_args: str) -> str:
    health = await _api_get("/api/health")
    notifier = await _api_get("/api/notifier/status")

    if "error" in health:
        return f"⚠️ *Backend ulaşılamıyor*\n`{health['error'][:200]}`"

    status_icon = "🟢" if health.get("status") == "ok" else "🔴"
    version = health.get("version", "?")
    fetched = health.get("fetched_at", "?")

    # Worker satırları
    workers = health.get("workers", {})
    worker_lines: list[str] = []
    if isinstance(workers, dict):
        for name, w in workers.items():
            if isinstance(w, dict):
                icon = "🟢" if w.get("running") else "🔴"
                iters = w.get("iterations", 0)
                worker_lines.append(f"  {icon} `{name}` — {iters} iter")

    # Telegram durumu
    tg_ok = notifier.get("telegram_yapilandirildi", False)
    tg_icon = "🟢" if tg_ok else "🔴"
    tg_toplam = notifier.get("toplam_bildirim", 0)
    tg_son_raw = notifier.get("son_bildirim") or ""
    tg_son = "—"
    if tg_son_raw:
        try:
            tg_son = dt.datetime.fromisoformat(tg_son_raw).strftime("%H:%M")
        except Exception:  # noqa: BLE001
            tg_son = tg_son_raw[:16]

    # İstatistikler
    sig_bus = health.get("signal_bus", {})
    cache = health.get("cache", {})

    lines: list[str] = [
        f"{status_icon} *PiyasaPilot Durum Raporu*",
        f"📌 Versiyon: `{version}`",
        f"🕒 Sunucu: `{fetched}`",
        "",
        "*🔧 Veri Sağlayıcılar:*",
    ]
    if worker_lines:
        lines.extend(worker_lines)
    else:
        lines.append("  ⚠️ Worker bilgisi yok")
    lines.extend([
        "",
        "*📊 Sinyal:*",
        f"  📡 Yayınlanan: {sig_bus.get('published', 0)}",
        f"  💾 Cache: {cache.get('rows', 0):,} bar",
        "",
        "*📱 Telegram:*",
        f"  {tg_icon} Yapılandırıldı: {'Evet' if tg_ok else 'Hayır'}",
        f"  📬 Toplam bildirim: {tg_toplam}",
        f"  🕒 Son: {tg_son}",
    ])

    son_hata = notifier.get("son_hata")
    if son_hata:
        lines.append(f"\n⚠️ Son hata: `{_mask_sensitive(son_hata)[:150]}`")

    return "\n".join(lines)


async def cmd_fiyat(args: str) -> str:
    symbol = args.strip().upper()
    if not symbol:
        return "❌ Kullanım: `/fiyat SEMBOL`\nÖrn: `/fiyat THYAO`"

    data = await _api_get(
        f"/api/v2/candles?symbol={symbol}&interval=15m&limit=2",
        timeout=12,
    )

    if "error" in data:
        return f"❌ API hatası: `{data['error'][:150]}`"
    if data.get("status") == "error":
        msg = data.get("message") or data.get("detail") or "Bilinmeyen hata"
        return f"❌ `{symbol}` bulunamadı.\n{msg}"

    bars = data.get("bars", [])
    if not bars:
        return f"❌ `{symbol}` için veri bulunamadı."

    last = bars[-1]
    price = float(last.get("close", 0))
    ts = last.get("time", 0)
    time_str = "—"
    if ts:
        try:
            time_str = dt.datetime.fromtimestamp(float(ts)).strftime("%H:%M")
        except Exception:  # noqa: BLE001
            pass

    freshness = "🕒 Eski veri" if data.get("status") == "stale" else "🟢 Güncel"
    display = data.get("display_name", symbol)
    market = data.get("market", "")
    market_str = f" ({market})" if market else ""

    return (
        f"💰 *{display}{market_str}*\n"
        f"Fiyat: `{_price_str(price)}`\n"
        f"Saat: {time_str}\n"
        f"{freshness}"
    )


async def cmd_sinyal(args: str) -> str:
    symbol = args.strip().upper()
    if not symbol:
        return "❌ Kullanım: `/sinyal SEMBOL`\nÖrn: `/sinyal BTCUSDT`"

    data = await _api_get(
        f"/api/v2/candles?symbol={symbol}&interval=15m&limit=200",
        timeout=15,
    )

    if "error" in data or not data.get("bars"):
        return f"❌ `{symbol}` için veri bulunamadı."

    bars = data["bars"]
    if len(bars) < 20:
        return f"❌ `{symbol}` için yeterli veri yok ({len(bars)} bar < 20)."

    try:
        import pandas as pd

        closes = pd.Series([float(b["close"]) for b in bars])
        highs = pd.Series([float(b["high"]) for b in bars])
        lows = pd.Series([float(b["low"]) for b in bars])
        volumes = pd.Series([float(b.get("volume", 0)) for b in bars])
        price = float(closes.iloc[-1])

        rsi = _calc_rsi(closes)

        ema20 = float(closes.ewm(span=20, adjust=False).mean().iloc[-1])
        ema50 = (
            float(closes.ewm(span=50, adjust=False).mean().iloc[-1])
            if len(closes) >= 50
            else ema20
        )
        ema200 = (
            float(closes.ewm(span=200, adjust=False).mean().iloc[-1])
            if len(closes) >= 200
            else ema50
        )

        # EMA trend
        if ema20 > ema50 * 1.005:
            trend, trend_icon = "YÜKSELEN", "📈"
        elif ema20 < ema50 * 0.995:
            trend, trend_icon = "DÜŞEN", "📉"
        else:
            trend, trend_icon = "YATAY", "➡️"

        # Hacim oranı
        vol_avg = float(volumes.rolling(20).mean().iloc[-1]) if len(volumes) >= 20 else float(volumes.mean())
        vol_ratio = float(volumes.iloc[-1]) / vol_avg if vol_avg > 0 else 1.0

        # Skor hesapla
        reasons: list[str] = []
        score = 0

        if rsi < 30:
            score += 2
            reasons.append(f"RSI aşırı satım ({rsi:.1f}) — AL sinyali güçlü")
        elif rsi > 70:
            score -= 2
            reasons.append(f"RSI aşırı alım ({rsi:.1f}) — SAT sinyali güçlü")
        else:
            reasons.append(f"RSI nötr bölge ({rsi:.1f})")

        if trend == "YÜKSELEN":
            score += 1
            reasons.append("EMA20 > EMA50 yükselen trend")
        elif trend == "DÜŞEN":
            score -= 1
            reasons.append("EMA20 < EMA50 düşen trend")
        else:
            reasons.append("Yatay trend")

        if price > ema200:
            score += 1
            reasons.append("Fiyat EMA200 üzerinde (uzun vade pozitif)")
        else:
            score -= 1
            reasons.append("Fiyat EMA200 altında (uzun vade negatif)")

        if vol_ratio > 1.5:
            vol_dir = score > 0
            score += 1 if vol_dir else -1
            reasons.append(f"Hacim ortalamanın {vol_ratio:.1f}x üzerinde")

        # Karar
        if score >= 2:
            karar, karar_icon = "AL", "🟢"
            guc = min(score + 4, 10)
        elif score <= -2:
            karar, karar_icon = "SAT", "🔴"
            guc = min(abs(score) + 4, 10)
        else:
            karar, karar_icon = "BEKLE", "⏸"
            guc = 5

        stars = "⭐" * min(guc // 2, 5)
        reasons_text = "\n".join(f"  • {r}" for r in reasons)
        display = data.get("display_name", symbol)

        return (
            f"{karar_icon} *{display} — {karar}*\n"
            f"💰 Fiyat: `{_price_str(price)}`\n"
            f"💪 Güç: {guc}/10 {stars}\n"
            f"{trend_icon} Trend: {trend}\n\n"
            f"*Sebepler:*\n{reasons_text}\n\n"
            f"⚠️ _Bilgilendirme amaçlıdır. Yatırım tavsiyesi değildir._"
        )

    except Exception as exc:  # noqa: BLE001
        logger.warning("cmd_sinyal analiz hatası — %s: %s", symbol, exc)
        return f"❌ Analiz hatası: `{type(exc).__name__}: {exc}`"


async def cmd_strateji(args: str) -> str:
    symbol = args.strip().upper()
    if not symbol:
        return "❌ Kullanım: `/strateji SEMBOL`\nÖrn: `/strateji THYAO`"

    blueprints = await _api_get("/api/backtest/strategies")
    strategy_names = [
        s.get("id", s) if isinstance(s, dict) else str(s)
        for s in blueprints.get("strategies", [])[:6]
    ]

    data = await _api_get(
        f"/api/v2/candles?symbol={symbol}&interval=15m&limit=200",
        timeout=15,
    )
    if "error" in data or not data.get("bars"):
        return f"❌ `{symbol}` için veri bulunamadı."

    bars = data["bars"]
    if len(bars) < 20:
        return f"❌ `{symbol}` için yeterli veri yok."

    try:
        import pandas as pd

        closes = pd.Series([float(b["close"]) for b in bars])
        price = float(closes.iloc[-1])

        rsi = _calc_rsi(closes)
        ema20 = float(closes.ewm(span=20, adjust=False).mean().iloc[-1])
        ema50 = (
            float(closes.ewm(span=50, adjust=False).mean().iloc[-1])
            if len(closes) >= 50
            else ema20
        )

        destek = float(closes.rolling(20).min().iloc[-1])
        direnc = float(closes.rolling(20).max().iloc[-1])

        if ema20 > ema50 * 1.005:
            trend_str = "Yükselen 📈"
        elif ema20 < ema50 * 0.995:
            trend_str = "Düşen 📉"
        else:
            trend_str = "Yatay ➡️"

        rsi_yorum = (
            "Aşırı satım bölgesi" if rsi < 30
            else ("Aşırı alım bölgesi" if rsi > 70 else "Nötr bölge")
        )

        display = data.get("display_name", symbol)

        lines = [
            f"📊 *{display} Strateji Analizi*",
            f"💰 Fiyat: `{_price_str(price)}`",
            "",
            "*Teknik Göstergeler:*",
            f"  📊 RSI(14): `{rsi:.1f}` — {rsi_yorum}",
            f"  📈 EMA20: `{ema20:.2f}` | EMA50: `{ema50:.2f}`",
            f"  🔀 Trend: {trend_str}",
            f"  🛡 Destek(20p): `{_price_str(destek)}`",
            f"  🎯 Direnç(20p): `{_price_str(direnc)}`",
        ]

        if strategy_names:
            lines.append(f"\n*Kayıtlı Stratejiler ({len(strategy_names)}):*")
            for s in strategy_names:
                lines.append(f"  • `{s}`")

        lines.append("\n⚠️ _Yatırım tavsiyesi değildir._")
        return "\n".join(lines)

    except Exception as exc:  # noqa: BLE001
        logger.warning("cmd_strateji hatası — %s: %s", symbol, exc)
        return f"❌ Analiz hatası: `{type(exc).__name__}`"


async def cmd_ozet(_args: str) -> str:
    wallets = await _api_get("/api/paper/wallets")
    trades = await _api_get("/api/paper/trades?limit=20")
    health = await _api_get("/api/health")

    today = dt.date.today().strftime("%d.%m.%Y")
    lines = [f"📊 *Günlük Özet — {today}*\n"]

    wallet_list = wallets.get("wallets", [])
    if wallet_list:
        lines.append("*Paper Trading:*")
        for w in wallet_list[:5]:
            pnl = w.get("cash", 0) - w.get("initial_capital", 10_000)
            emoji = "🟢" if pnl >= 0 else "🔴"
            durum = "🔒" if w.get("is_halted") else "✅"
            lines.append(
                f"  {durum} `{w.get('strategy_id', '?')}`: "
                f"{emoji} `{pnl:+,.2f}₺`"
            )
    else:
        lines.append("*Paper Trading:* Henüz işlem yok.")

    sig_bus = health.get("signal_bus", {})
    lines.append(f"\n*Sinyal motoru:* 📡 {sig_bus.get('published', 0)} sinyal")

    trade_list = trades.get("trades", [])
    kapali = [t for t in trade_list if t.get("closed_at")]
    if kapali:
        kazananlar = [t for t in kapali if (t.get("pnl") or 0) > 0]
        wr = len(kazananlar) / len(kapali) * 100
        lines.append(
            f"\n*Son işlemler ({len(kapali)}):*\n"
            f"  🎯 Kazanma oranı: `{wr:.0f}%`"
        )

    return "\n".join(lines)


async def cmd_son(_args: str) -> str:
    try:
        from backend.notifier.main import get_notifier_status

        durum = get_notifier_status()
        recent: list[dict] = durum.get("son_sinyaller", [])
    except Exception:  # noqa: BLE001
        recent = []

    if not recent:
        return "📭 Henüz sinyal gelmedi.\nSinyal üretilince burada görünür."

    lines = [f"📡 *Son {len(recent)} Sinyal:*\n"]
    for sig in recent[:10]:
        sig_type = sig.get("signal_type", "?")
        symbol = sig.get("symbol", "?")
        price = float(sig.get("price", 0))
        ts_raw = sig.get("ts", "")
        ts_str = "—"
        if ts_raw:
            try:
                ts_str = dt.datetime.fromisoformat(ts_raw).strftime("%H:%M")
            except Exception:  # noqa: BLE001
                pass
        emoji = "🟢" if "BUY" in sig_type else "🔴"
        lines.append(f"{emoji} `{symbol}` {sig_type} @ `{_price_str(price)}` — {ts_str}")

    return "\n".join(lines)


async def cmd_hata(_args: str) -> str:
    health = await _api_get("/api/health")

    try:
        from backend.notifier.main import get_notifier_status

        durum = get_notifier_status()
    except Exception:  # noqa: BLE001
        durum = {}

    lines = ["⚠️ *Son Hatalar*\n"]

    # Notifier hatası
    son_hata = durum.get("son_hata")
    if son_hata:
        lines.append(f"*Notifier:* `{_mask_sensitive(son_hata)[:200]}`")
    else:
        lines.append("*Notifier:* Hata yok ✅")

    # Worker hataları
    workers = health.get("workers", {})
    worker_errors: list[str] = []
    if isinstance(workers, dict):
        for name, w in workers.items():
            if isinstance(w, dict) and w.get("last_error"):
                safe_err = _mask_sensitive(str(w["last_error"]))
                worker_errors.append(f"  • `{name}`: {safe_err[:100]}")
    if worker_errors:
        lines.append("\n*Worker hatalar:*")
        lines.extend(worker_errors)
    else:
        lines.append("*Worker hatalar:* Yok ✅")

    # Signal generator
    sg = health.get("signal_generator", {})
    if sg.get("last_error"):
        safe_err = _mask_sensitive(str(sg["last_error"]))
        lines.append(f"\n*Sinyal motoru:* `{safe_err[:100]}`")

    return "\n".join(lines)


async def cmd_kontrol(_args: str) -> str:
    from backend.assistant.project_assistant import project_health_report

    return await project_health_report()


async def cmd_gorev(args: str) -> str:
    if not args.strip():
        return (
            "❌ Kullanım: `/gorev [görev metni]`\n"
            "Örn: `/gorev Telegram durum çubuğu çalışmıyor`"
        )
    from backend.assistant.project_assistant import analyze_task

    return await analyze_task(args.strip())


async def cmd_duzelt(args: str) -> str:
    if not args.strip():
        return (
            "❌ Kullanım: `/duzelt [sorun metni]`\n"
            "Örn: `/duzelt SignalFeed Telegram alanı görünmüyor`"
        )
    from backend.assistant.project_assistant import fix_task

    return await fix_task(args.strip())


# ── Komut tablosu ─────────────────────────────────────────────────────────────

COMMANDS: dict[str, Any] = {
    "/yardim": cmd_yardim,
    "/durum": cmd_durum,
    "/fiyat": cmd_fiyat,
    "/sinyal": cmd_sinyal,
    "/strateji": cmd_strateji,
    "/ozet": cmd_ozet,
    "/son": cmd_son,
    "/hata": cmd_hata,
    "/kontrol": cmd_kontrol,
    "/gorev": cmd_gorev,
    "/duzelt": cmd_duzelt,
    # Kısaltmalar
    "/start": cmd_yardim,
    "/help": cmd_yardim,
}
