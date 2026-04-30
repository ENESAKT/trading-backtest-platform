"""Worker sağlık izleyici — çöken worker'lar için Telegram uyarısı gönderir.

Bu modül periyodik olarak WorkerSupervisor.health() çağırır ve
önceki duruma göre değişen (çalışan→çökmüş) worker'lar için
Telegram bildirimi gönderir.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

_logger = logging.getLogger(__name__)

# Aynı worker için ardışık uyarı aralığı (saniye)
_ALERT_COOLDOWN = 300  # 5 dakika
_CHECK_INTERVAL = 30   # 30 saniyede bir kontrol


class WorkerHealthMonitor:
    """Worker sağlık durumunu izler, çöküşlerde Telegram uyarısı gönderir."""

    def __init__(self, supervisor: Any) -> None:
        self._supervisor = supervisor
        self._prev_states: dict[str, bool] = {}
        self._last_alert: dict[str, float] = {}
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        """İzleme döngüsünü başlat."""
        self._task = asyncio.create_task(self._monitor_loop())
        _logger.info("[worker-monitor] Worker sağlık izleyici başlatıldı")

    async def stop(self) -> None:
        """İzleme döngüsünü durdur."""
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        _logger.info("[worker-monitor] Worker sağlık izleyici durduruldu")

    async def _monitor_loop(self) -> None:
        """Periyodik sağlık kontrolü."""
        import time
        try:
            while True:
                await asyncio.sleep(_CHECK_INTERVAL)
                await self._check_health(time.time())
        except asyncio.CancelledError:
            pass

    async def _check_health(self, now: float) -> None:
        """Worker durumlarını kontrol et, çöküş varsa uyar."""
        try:
            health = self._supervisor.health()
        except Exception as exc:
            _logger.warning("[worker-monitor] Sağlık bilgisi alınamadı: %s", exc)
            return

        for w in health:
            name = w.get("name", "unknown")
            running = bool(w.get("running"))
            prev_running = self._prev_states.get(name)

            # Durum değişimi: çalışıyor → çökmüş
            if prev_running is True and running is False:
                last_alert = self._last_alert.get(name, 0)
                if now - last_alert >= _ALERT_COOLDOWN:
                    await self._send_crash_alert(name, w)
                    self._last_alert[name] = now

            self._prev_states[name] = running

    async def _send_crash_alert(self, name: str, worker_info: dict[str, Any]) -> None:
        """Telegram üzerinden çöküş uyarısı gönder."""
        last_error = worker_info.get("last_error", "bilinmiyor")
        iterations = worker_info.get("iterations", 0)

        message = (
            f"⚠️ Worker Çöktü: {name}\n"
            f"Son hata: {last_error}\n"
            f"Toplam iterasyon: {iterations}\n"
            f"Durum: otomatik yeniden başlatma denenecek"
        )
        _logger.warning("[worker-monitor] %s çöktü! Son hata: %s", name, last_error)

        try:
            from backend.config import getenv
            token = getenv("TELEGRAM_BOT_TOKEN")
            chat_id = getenv("TELEGRAM_CHAT_ID")
            if not token or not chat_id:
                return

            import urllib.request
            import json

            payload = json.dumps({"chat_id": chat_id, "text": message}).encode()
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            req = urllib.request.Request(
                url, data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=10)
            _logger.info("[worker-monitor] Telegram çöküş uyarısı gönderildi: %s", name)
        except Exception as exc:
            _logger.warning("[worker-monitor] Telegram uyarısı gönderilemedi: %s", exc)
