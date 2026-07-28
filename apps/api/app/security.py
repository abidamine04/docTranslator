import base64
import hashlib
import hmac

from cryptography.fernet import Fernet, InvalidToken
from fastapi import Header, HTTPException

from .config import get_settings


def _fernet() -> Fernet:
    raw = get_settings().provider_secret_encryption_key or get_settings().app_secret_key
    key = base64.urlsafe_b64encode(hashlib.sha256(raw.encode()).digest())
    return Fernet(key)


def encrypt_secret(value: str | None) -> str | None:
    return _fernet().encrypt(value.encode()).decode() if value else None


def decrypt_secret(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return _fernet().decrypt(value.encode()).decode()
    except InvalidToken as exc:
        raise RuntimeError("Provider secret cannot be decrypted; verify the encryption key") from exc


def admin_token_error(supplied: str) -> tuple[int, str] | None:
    expected = get_settings().admin_api_token
    if not expected:
        return 503, "ADMIN_API_TOKEN is not configured"
    if not hmac.compare_digest(supplied, expected):
        return 401, "A valid administrator token is required"
    return None


def require_admin(x_admin_token: str = Header(default="")) -> None:
    if error := admin_token_error(x_admin_token):
        raise HTTPException(status_code=error[0], detail=error[1])

