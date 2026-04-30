"""API key middleware ve env validator testleri."""

from __future__ import annotations

import os
from unittest.mock import patch

from backend.env_validator import validate_env


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

    def test_with_key_blocks_without_header(self) -> None:
        """API_KEY tanımlıyken header olmadan 401 döner."""
        env = dict(os.environ)
        env["PIYASAPILOT_DISABLE_WORKERS"] = "1"
        env["API_KEY"] = "test-key-12345"
        with patch.dict(os.environ, env, clear=True):
            from backend.api.main import create_app
            app = create_app()
            from starlette.testclient import TestClient
            client = TestClient(app, raise_server_exceptions=False)
            resp = client.get("/api/backtest/strategies")
            assert resp.status_code == 401

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

    def test_with_key_allows_correct_header(self) -> None:
        """Doğru X-API-Key header ile istek geçer."""
        env = dict(os.environ)
        env["PIYASAPILOT_DISABLE_WORKERS"] = "1"
        env["API_KEY"] = "test-key-12345"
        with patch.dict(os.environ, env, clear=True):
            from backend.api.main import create_app
            app = create_app()
            from starlette.testclient import TestClient
            client = TestClient(app, raise_server_exceptions=False)
            resp = client.get(
                "/api/backtest/strategies",
                headers={"X-API-Key": "test-key-12345"},
            )
            assert resp.status_code == 200

    def test_with_key_rejects_wrong_header(self) -> None:
        """Yanlış X-API-Key header ile 401 döner."""
        env = dict(os.environ)
        env["PIYASAPILOT_DISABLE_WORKERS"] = "1"
        env["API_KEY"] = "test-key-12345"
        with patch.dict(os.environ, env, clear=True):
            from backend.api.main import create_app
            app = create_app()
            from starlette.testclient import TestClient
            client = TestClient(app, raise_server_exceptions=False)
            resp = client.get(
                "/api/backtest/strategies",
                headers={"X-API-Key": "wrong-key"},
            )
            assert resp.status_code == 401
