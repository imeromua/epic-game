import hashlib
import hmac
import json
from urllib.parse import unquote
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from api.core.config import settings

bearer_scheme = HTTPBearer()


# ==========================================
# Telegram initData валідація
# https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
# ==========================================

def validate_telegram_init_data(init_data: str) -> dict:
    """
    Перевіряє підпис Telegram WebApp initData.
    Повертає словник з даними гравця або кидає HTTPException.
    """
    # Розбираємо init_data на параметри
    parsed: dict[str, str] = {}
    for part in init_data.split("&"):
        if "=" in part:
            key, value = part.split("=", 1)
            parsed[unquote(key)] = unquote(value)

    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Відсутній hash в initData",
        )

    # Формуємо data-check-string
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(parsed.items())
    )

    # HMAC-SHA256 з ключем WebAppData
    secret_key = hmac.new(
        b"WebAppData",
        settings.BOT_TOKEN.encode(),
        hashlib.sha256,
    ).digest()

    expected_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_hash, received_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалідний підпис Telegram",
        )

    # Парсимо user JSON
    user_data = {}
    if "user" in parsed:
        user_data = json.loads(parsed["user"])

    return user_data


# ==========================================
# JWT
# ==========================================

def create_access_token(player_id: int, tg_id: int, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {
        "sub": str(player_id),
        "tg_id": tg_id,
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалідний або прострочений токен",
        )


# ==========================================
# FastAPI Depends — поточний гравець
# ==========================================

def get_current_player(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """Dependency — повертає payload JWT"""
    return decode_token(credentials.credentials)


def require_admin(
    current: dict = Depends(get_current_player),
) -> dict:
    """Dependency — тільки для admin"""
    if current.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ заборонено",
        )
    return current
