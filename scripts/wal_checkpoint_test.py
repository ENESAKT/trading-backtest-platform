#!/usr/bin/env python3
"""WAL checkpoint doğrulama testi — docker compose down sonrasını simüle eder.

Kullanım:
    python scripts/wal_checkpoint_test.py
"""

from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path


def test_wal_checkpoint() -> None:
    """PaperDB.checkpoint() çağrıldıktan sonra WAL dosyasının boş olduğunu doğrula."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from backend.paper.db import PaperDB

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_wal.sqlite3"
        db = PaperDB(db_path)
        db.ensure_tables()

        # WAL modunu aktif et
        conn = sqlite3.connect(str(db_path), timeout=10)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.close()

        # Bazı veriler yaz (WAL'a biriksin)
        db.get_or_create_wallet("test_strategy_1")
        db.get_or_create_wallet("test_strategy_2")
        db.record_trade(
            strategy_id="test_strategy_1",
            symbol="BTCUSDT",
            side="BUY",
            price=50000.0,
            quantity=0.1,
            commission=0.5,
            opened_at="2024-01-01T00:00:00",
            reason="Test trade",
        )

        # WAL dosyası var mı kontrol et
        wal_path = Path(str(db_path) + "-wal")

        # Checkpoint çalıştır
        db.checkpoint()

        # Checkpoint sonrası WAL dosyası boş veya çok küçük olmalı
        if wal_path.exists():
            wal_size = wal_path.stat().st_size
            print(f"✅ WAL checkpoint tamamlandı. WAL boyutu: {wal_size} byte")
            # Başarılı checkpoint sonrası WAL boyutu 0 olabilir veya header-only (32 byte)
            assert wal_size <= 4096, f"WAL dosyası beklenenden büyük: {wal_size} byte"
        else:
            print("✅ WAL dosyası yok — journal_mode=WAL olmamış olabilir ama checkpoint başarılı")

        # DB hala okunabilir olmalı
        db2 = PaperDB(db_path)
        wallets = db2.all_wallets()
        assert len(wallets) >= 2, f"Checkpoint sonrası veriler kaybolmuş! {len(wallets)} wallet"
        print(f"✅ Checkpoint sonrası {len(wallets)} cüzdan okunabilir")
        print("✅ WAL checkpoint doğrulaması başarılı!")


if __name__ == "__main__":
    test_wal_checkpoint()
