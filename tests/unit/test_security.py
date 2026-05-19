"""API key middleware ve env validator testleri."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from backend.env_validator import EnvValidationError, validate_env


class TestEnvValidator:
    def test_validate_env_returns_missing_optional(self) -> None:
        """Opsiyonel değişkenler eksikse missing_optional listesi döner."""
        with patch.dict(os.environ, {}, clear=False):
            result = validate_env(strict=False)
            assert isinstance(result["missing_optional"], list)
            assert isinstance(result["missing_required"], list)

    def test_strict_mode_no_required_vars(self) -> None:
        """Zorunlu değişken listesi boşsa strict modda hata fırlatmaz."""
        result = validate_env(strict=True)
        assert result["missing_required"] == []

    def test_strict_env_var(self) -> None:
        """STRICT_ENV_VALIDATION=1 iken varsayılan strict değeri okunur."""
        with patch.dict(os.environ, {"STRICT_ENV_VALIDATION": "1"}, clear=False):
            # Şu an REQUIRED_VARS boş olduğu için hata fırlatmaz
            result = validate_env(strict=None)
            assert result["missing_required"] == []

    def test_production_requires_api_key(self) -> None:
        """Production modunda API_KEY yoksa servis açıkça kırılır."""
        env = {
            k: v
            for k, v in os.environ.items()
            if k not in {"API_KEY", "APP_ENV"}
        }
        env["APP_ENV"] = "production"
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(EnvValidationError, match="API_KEY"):
                validate_env(strict=False)

    def test_production_strict_requires_data_urls(self) -> None:
        """Production strict modda veri platformu URL'leri zorunludur."""
        env = {
            k: v
            for k, v in os.environ.items()
            if k
            not in {
                "APP_ENV",
                "API_KEY",
                "CORS_ORIGINS",
                "DATABASE_URL",
                "CLICKHOUSE_URL",
                "REDIS_URL",
            }
        }
        env["APP_ENV"] = "production"
        env["API_KEY"] = "test-key-12345"
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(EnvValidationError, match="CORS_ORIGINS"):
                validate_env(strict=True)


class TestAPIKeyMiddleware:
    def test_no_key_allows_all(self) -> None:
        """API_KEY tanımlı değilken tüm istekler geçer."""
        env = {k: v for k, v in os.environ.items() if k != "API_KEY"}
        env["PIYASAPILOT_DISABLE_WORKERS"] = "1"
        with patch.dict(os.environ, env, clear=True):
            from backend.api.main import create_app
            app = create_app()
            from starlette.testclient import TestClient
            client = TestClient(app, raise_server_exceptions=False)
            resp = client.get("/api/health")
            assert resp.status_code == 200

    def test_with_key_allows_browser_api_without_header(self) -> None:
        """API_KEY tanımlıyken browser-facing /api yolları header istemez."""
        env = dict(os.environ)
        env["PIYASAPILOT_DISABLE_WORKERS"] = "1"
        env["API_KEY"] = "test-key-12345"
        with patch.dict(os.environ, env, clear=True):
            from backend.api.main import create_app
            app = create_app()
            from starlette.testclient import TestClient
            client = TestClient(app, raise_server_exceptions=False)
            resp = client.get("/api/backtest/strategies")
            body = resp.json()
            assert "Geçersiz veya eksik API anahtarı" not in str(body.get("detail", ""))

    def test_with_key_allows_health(self) -> None:
        """API_KEY tanımlıyken /api/health muaf."""
        env = dict(os.environ)
        env["PIYASAPILOT_DISABLE_WORKERS"] = "1"
        env["API_KEY"] = "test-key-12345"
        with patch.dict(os.environ, env, clear=True):
            from backend.api.main import create_app
            app = create_app()
            from starlette.testclient import TestClient
            client = TestClient(app, raise_server_exceptions=False)
            resp = client.get("/api/health")
            assert resp.status_code == 200

    def test_with_key_blocks_protected_ops_path_without_header(self) -> None:
        """API_KEY tanımlıyken /metrics gibi ops yolları header ister."""
        env = dict(os.environ)
        env["PIYASAPILOT_DISABLE_WORKERS"] = "1"
        env["API_KEY"] = "test-key-12345"
        with patch.dict(os.environ, env, clear=True):
            from backend.api.main import create_app
            app = create_app()
            from starlette.testclient import TestClient
            client = TestClient(app, raise_server_exceptions=False)
            resp = client.get("/metrics")
            assert resp.status_code == 401

    def test_with_key_allows_correct_header_on_protected_ops_path(self) -> None:
        """Doğru X-API-Key header ile ops endpoint'i middleware'den geçer."""
        env = dict(os.environ)
        env["PIYASAPILOT_DISABLE_WORKERS"] = "1"
        env["API_KEY"] = "test-key-12345"
        with patch.dict(os.environ, env, clear=True):
            from backend.api.main import create_app
            app = create_app()
            from starlette.testclient import TestClient
            client = TestClient(app, raise_server_exceptions=False)
            resp = client.get(
                "/metrics",
                headers={"X-API-Key": "test-key-12345"},
            )
            assert resp.status_code == 200

    def test_with_key_rejects_wrong_header_on_protected_ops_path(self) -> None:
        """Yanlış X-API-Key header ile korumalı ops yolu 401 döner."""
        env = dict(os.environ)
        env["PIYASAPILOT_DISABLE_WORKERS"] = "1"
        env["API_KEY"] = "test-key-12345"
        with patch.dict(os.environ, env, clear=True):
            from backend.api.main import create_app
            app = create_app()
            from starlette.testclient import TestClient
            client = TestClient(app, raise_server_exceptions=False)
            resp = client.get(
                "/metrics",
                headers={"X-API-Key": "wrong-key"},
            )
            assert resp.status_code == 401

    def test_websocket_allows_without_query_token_by_default(self) -> None:
        """Browser WS bağlantısı varsayılan olarak API_KEY query token istemez."""
        env = dict(os.environ)
        env["PIYASAPILOT_DISABLE_WORKERS"] = "1"
        env["API_KEY"] = "test-key-12345"
        with patch.dict(os.environ, env, clear=True):
            from backend.api.main import create_app
            from starlette.testclient import TestClient

            app = create_app()
            client = TestClient(app, raise_server_exceptions=False)
            with client.websocket_connect("/ws/quotes") as ws:
                ready = ws.receive_json()
                assert ready["type"] == "ready"

    def test_websocket_requires_query_token_when_enabled(self) -> None:
        """REQUIRE_WS_API_KEY=1 ise WebSocket bağlantısı token olmadan kapanır."""
        env = dict(os.environ)
        env["PIYASAPILOT_DISABLE_WORKERS"] = "1"
        env["API_KEY"] = "test-key-12345"
        env["REQUIRE_WS_API_KEY"] = "1"
        with patch.dict(os.environ, env, clear=True):
            from backend.api.main import create_app
            from starlette.testclient import TestClient
            from starlette.websockets import WebSocketDisconnect

            app = create_app()
            client = TestClient(app, raise_server_exceptions=False)
            with pytest.raises(WebSocketDisconnect) as exc:
                with client.websocket_connect("/ws/quotes"):
                    pass
            assert exc.value.code == 1008

    def test_websocket_allows_query_token_when_api_key_set(self) -> None:
        """Doğru query token ile WebSocket ready mesajına ulaşır."""
        env = dict(os.environ)
        env["PIYASAPILOT_DISABLE_WORKERS"] = "1"
        env["API_KEY"] = "test-key-12345"
        env["REQUIRE_WS_API_KEY"] = "1"
        with patch.dict(os.environ, env, clear=True):
            from backend.api.main import create_app
            from starlette.testclient import TestClient

            app = create_app()
            client = TestClient(app, raise_server_exceptions=False)
            with client.websocket_connect("/ws/quotes?token=test-key-12345") as ws:
                ready = ws.receive_json()
                assert ready["type"] == "ready"
