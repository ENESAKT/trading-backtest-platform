"""Telegram bağlantı testi.

Çalıştırma:
    python scripts/test_telegram.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

# Proje kökünü sys.path'e ekle
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# .env yükle
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv yoksa elle oku
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())


async def main() -> None:
    from backend.notifier.telegram import (
        test_baglantisi,
        bildir_yeni_sinyal,
        bildir_alim,
        bildir_satim,
        bildir_hata,
        bildir_gunluk_ozet,
    )

    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")

    if not token or not chat_id:
        print("❌ HATA: .env dosyasında TELEGRAM_BOT_TOKEN veya TELEGRAM_CHAT_ID eksik.")
        print("   .env.example dosyasını kopyalayıp değerleri doldurun.")
        sys.exit(1)

    print(f"📡 Token: ...{token[-8:]}")
    print(f"📡 Chat ID: {chat_id}")
    print()

    # 1. Bağlantı testi
    print("1️⃣  Bağlantı testi gönderiliyor...")
    tamam = await test_baglantisi()
    print(f"   {'✅ Başarılı' if tamam else '❌ Başarısız'}")

    if not tamam:
        print("\n❌ Telegram'a bağlanılamadı.")
        print("   Kontrol listesi:")
        print("   • .env dosyasındaki token doğru mu?")
        print("   • Bot'a bir mesaj attın mı? (@BotFather ile oluşturuldu mu?)")
        print("   • İnternet bağlantısı var mı?")
        sys.exit(1)

    await asyncio.sleep(1)

    # 2. Sinyal bildirimi
    print("2️⃣  Örnek sinyal bildirimi gönderiliyor...")
    await bildir_yeni_sinyal({
        "symbol": "THYAO.IS",
        "signal_type": "STRONG_BUY",
        "price": 328.50,
        "strategy_id": "ema_cross",
        "strength": 8,
        "reason": "EMA 50 üstü EMA 200 kesti, hacim artışı var",
    })
    print("   ✅ Gönderildi")
    await asyncio.sleep(1)

    # 3. Alım bildirimi
    print("3️⃣  Örnek alım bildirimi gönderiliyor...")
    await bildir_alim("ema_cross", "THYAO.IS", 328.50, 30.44, 10_000.0, "EMA kesişimi")
    print("   ✅ Gönderildi")
    await asyncio.sleep(1)

    # 4. Satım bildirimi
    print("4️⃣  Örnek satım bildirimi gönderiliyor...")
    await bildir_satim("ema_cross", "THYAO.IS", 341.20, 30.44, +385.50, "Hedef fiyata ulaşıldı")
    print("   ✅ Gönderildi")
    await asyncio.sleep(1)

    # 5. Hata bildirimi
    print("5️⃣  Örnek hata bildirimi gönderiliyor...")
    await bildir_hata("Veri sağlayıcıya bağlanılamadı", "BinanceKlineWorker")
    print("   ✅ Gönderildi")
    await asyncio.sleep(1)

    # 6. Günlük özet
    print("6️⃣  Örnek günlük özet gönderiliyor...")
    await bildir_gunluk_ozet(
        wallets=[
            {
                "strategy_id": "ema_cross",
                "cash": 10_385.50,
                "initial_capital": 10_000.0,
                "is_halted": False,
            }
        ],
        trades=[
            {"closed_at": "2026-04-29", "pnl": 385.50},
            {"closed_at": "2026-04-29", "pnl": -120.0},
            {"closed_at": "2026-04-29", "pnl": 210.0},
        ],
    )
    print("   ✅ Gönderildi")

    print()
    print("✅ Tüm testler tamamlandı. Telegram'ı kontrol et.")


if __name__ == "__main__":
    asyncio.run(main())
