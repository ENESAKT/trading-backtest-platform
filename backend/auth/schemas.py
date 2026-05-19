"""
Auth Pydantic Şemaları — Request / Response modelleri.
"""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, field_validator

from .password import validate_password_strength

# ── Request modelleri ────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        errors = validate_password_strength(v)
        if errors:
            raise ValueError(" ".join(errors))
        return v

    @field_validator("display_name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Ad en az 2 karakter olmalı.")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    totp_code: str | None = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        errors = validate_password_strength(v)
        if errors:
            raise ValueError(" ".join(errors))
        return v


class VerifyEmailRequest(BaseModel):
    token: str


class UpdateSettingsRequest(BaseModel):
    default_symbol: str | None = None
    default_timeframe: str | None = None
    theme: str | None = None
    accent_color: str | None = None
    language: str | None = None
    onboarding_done: bool | None = None


class TotpVerifyRequest(BaseModel):
    code: str


class ApiKeyCreateRequest(BaseModel):
    name: str = "API Key"
    expires_at: str | None = None


# ── Response modelleri ───────────────────────────────────────────────────────

class PlanInfo(BaseModel):
    slug: str
    display_name: str
    api_calls_per_day: int
    backtest_runs_per_day: int
    backtest_pro: bool
    scanner: bool
    real_time_data: bool
    mali_analiz_scope: str
    multi_chart: bool
    api_access: bool


class QuotaInfo(BaseModel):
    api_calls: dict
    backtest_runs: dict
    signal_views: dict


class UserMeResponse(BaseModel):
    id: int
    email: str
    email_verified: bool
    display_name: str | None
    avatar_url: str | None
    role: str
    language: str
    plan: PlanInfo
    quotas: QuotaInfo | None = None
    settings: dict | None = None


class AuthResponse(BaseModel):
    ok: bool = True
    data: dict | None = None


class ErrorDetail(BaseModel):
    code: str
    tr: str
    en: str
    upgrade_url: str | None = None


class ErrorResponse(BaseModel):
    ok: bool = False
    error: ErrorDetail
