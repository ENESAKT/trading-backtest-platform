"""
storage_layer_guard.py — ClickHouse / MySQL / Redis katman ayrımı politikası.

Bu modül, hangi verinin hangi depolama katmanına yazılabileceğini tanımlar ve
yanlış kullanımı derleme zamanı (tip uyarısı) ile çalışma zamanı (exception)
seviyesinde engeller.

Politika özeti:
  ClickHouse → OHLCV bar, tick, büyük zaman serisi, kalite olayları
  MySQL      → Sembol metadata, kullanıcı, plan, alarm, envanter, lisans
  Redis      → Sıcak cache, pub/sub, kısa ömürlü snapshot (kalıcı kayıt yasak)

Kullanım:
    from backend.data.storage_layer_guard import StorageLayerGuard

    # Çalışma zamanı kontrolü
    StorageLayerGuard.assert_clickhouse("timeseries_write", "market_bars")
    StorageLayerGuard.assert_mysql("metadata_write", "users")
    StorageLayerGuard.assert_redis("cache_write", "hot_candles")

    # İzin sorgusu
    if not StorageLayerGuard.is_allowed("redis", "timeseries_write"):
        raise StorageLayerViolation(...)
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import FrozenSet

_logger = logging.getLogger(__name__)

# ─── Sabitler ────────────────────────────────────────────────────────────────


class StorageKind(str, Enum):
    CLICKHOUSE = "clickhouse"
    MYSQL      = "mysql"
    REDIS      = "redis"


# Veri kategorileri — storage türüne göre izin matrisi
# key: kategori etiketi   value: izin verilen storage kind kümesi

_ALLOWED: dict[str, FrozenSet[StorageKind]] = {
    # ── Zaman serisi / piyasa verisi (sadece ClickHouse) ─────────────────────
    "timeseries_write":  frozenset({StorageKind.CLICKHOUSE}),
    "timeseries_read":   frozenset({StorageKind.CLICKHOUSE, StorageKind.REDIS}),  # Redis: cache oku
    "ohlcv_write":       frozenset({StorageKind.CLICKHOUSE}),
    "tick_write":        frozenset({StorageKind.CLICKHOUSE}),
    "quality_event":     frozenset({StorageKind.CLICKHOUSE}),
    "derived_bar_write": frozenset({StorageKind.CLICKHOUSE}),

    # ── Metadata (sadece MySQL) ───────────────────────────────────────────────
    "user_write":        frozenset({StorageKind.MYSQL}),
    "user_read":         frozenset({StorageKind.MYSQL}),
    "plan_write":        frozenset({StorageKind.MYSQL}),
    "plan_read":         frozenset({StorageKind.MYSQL}),
    "alarm_write":       frozenset({StorageKind.MYSQL}),
    "alarm_read":        frozenset({StorageKind.MYSQL}),
    "symbol_meta_write": frozenset({StorageKind.MYSQL}),
    "symbol_meta_read":  frozenset({StorageKind.MYSQL}),
    "inventory_write":   frozenset({StorageKind.MYSQL}),
    "inventory_read":    frozenset({StorageKind.MYSQL}),
    "license_write":     frozenset({StorageKind.MYSQL}),
    "provider_contract": frozenset({StorageKind.MYSQL}),

    # ── Hot cache / pub-sub (sadece Redis, kalıcı kayıt yasak) ───────────────
    "hot_cache_write":   frozenset({StorageKind.REDIS}),
    "hot_cache_read":    frozenset({StorageKind.REDIS}),
    "pubsub_publish":    frozenset({StorageKind.REDIS}),
    "pubsub_subscribe":  frozenset({StorageKind.REDIS}),
    "distributed_lock":  frozenset({StorageKind.REDIS}),
    "snapshot_write":    frozenset({StorageKind.REDIS}),   # kısa ömürlü, TTL zorunlu

    # ── Yasaklılar: hiçbir katmanda yapılmamalı ───────────────────────────────
    "permanent_redis_write": frozenset(),          # Redis'i kalıcı truth source gibi kullanma
    "user_in_clickhouse":    frozenset(),          # Kullanıcı/plan verisi ClickHouse'a gitmemeli
    "timeseries_in_mysql":   frozenset(),          # Zaman serisi MySQL'e yazılmamalı
}


class StorageLayerViolation(RuntimeError):
    """Yanlış depolama katmanı kullanıldığında fırlatılır."""


# ─── Guard sınıfı ────────────────────────────────────────────────────────────


class StorageLayerGuard:
    """
    Depolama katmanı ayrımı politika kontrolörü.

    Tüm metodlar statiktir; instantiation gerekmez.
    """

    @staticmethod
    def is_allowed(storage: str | StorageKind, category: str) -> bool:
        """Verilen kategori için bu storage izinli mi?"""
        kind = StorageKind(storage) if isinstance(storage, str) else storage
        allowed = _ALLOWED.get(category)
        if allowed is None:
            # Tanımsız kategoriler uyarı üretir ama engellenmez
            _logger.warning(
                "[StorageLayerGuard] Bilinmeyen kategori '%s' — politika tanımlanmamış", category
            )
            return True
        return kind in allowed

    @staticmethod
    def assert_allowed(storage: str | StorageKind, category: str, context: str = "") -> None:
        """
        Verilen kategori için storage izinli değilse StorageLayerViolation fırlatır.

        Args:
            storage:  Kullanılan depolama türü (clickhouse / mysql / redis)
            category: Veri kategorisi (örn. 'timeseries_write', 'user_write')
            context:  Hata mesajına eklenecek serbest metin (fonksiyon adı, endpoint vb.)
        """
        if not StorageLayerGuard.is_allowed(storage, category):
            allowed = _ALLOWED.get(category, frozenset())
            allowed_names = ", ".join(k.value for k in allowed) or "hiçbiri"
            msg = (
                f"[StorageLayerGuard] Katman ihlali! "
                f"Kategori='{category}' için '{storage}' kullanılamaz. "
                f"İzinliler: [{allowed_names}]. "
                f"Bağlam: {context or '—'}"
            )
            _logger.error(msg)
            raise StorageLayerViolation(msg)

    # ── Kısayol metodlar ─────────────────────────────────────────────────────

    @staticmethod
    def assert_clickhouse(category: str, context: str = "") -> None:
        """Bu kategori ClickHouse'a yazılabilir mi?"""
        StorageLayerGuard.assert_allowed(StorageKind.CLICKHOUSE, category, context)

    @staticmethod
    def assert_mysql(category: str, context: str = "") -> None:
        """Bu kategori MySQL'e yazılabilir mi?"""
        StorageLayerGuard.assert_allowed(StorageKind.MYSQL, category, context)

    @staticmethod
    def assert_redis(category: str, context: str = "") -> None:
        """Bu kategori Redis'e yazılabilir mi?"""
        StorageLayerGuard.assert_allowed(StorageKind.REDIS, category, context)

    @staticmethod
    def assert_no_timeseries_in_mysql(context: str = "") -> None:
        """Zaman serisi MySQL'e yazılıyorsa ihlal fırlat."""
        StorageLayerGuard.assert_allowed(StorageKind.MYSQL, "timeseries_in_mysql", context)

    @staticmethod
    def assert_no_user_in_clickhouse(context: str = "") -> None:
        """Kullanıcı/plan verisi ClickHouse'a yazılıyorsa ihlal fırlat."""
        StorageLayerGuard.assert_allowed(StorageKind.CLICKHOUSE, "user_in_clickhouse", context)

    @staticmethod
    def assert_no_permanent_redis(context: str = "") -> None:
        """Redis kalıcı truth source olarak kullanılıyorsa ihlal fırlat."""
        StorageLayerGuard.assert_allowed(StorageKind.REDIS, "permanent_redis_write", context)

    @staticmethod
    def policy_summary() -> dict[str, list[str]]:
        """Tüm politikayı okunabilir dict olarak döner (dokümantasyon/debug amaçlı)."""
        return {
            cat: [k.value for k in allowed]
            for cat, allowed in _ALLOWED.items()
        }
