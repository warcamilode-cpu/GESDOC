"""
auth.py — Utilidades JWT y dependencias de autenticación para GESDOC
"""

import os
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SECRET_KEY   = os.environ.get("GESDOC_SECRET", "gesdoc-cambia-esta-clave-en-produccion-2025")
ALGORITHM    = "HS256"
EXPIRE_HORAS = 8

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer  = HTTPBearer(auto_error=False)


# ─────────────────────────────────────────────────────────────────────────────
# Contraseñas
# ─────────────────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return pwd_ctx.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)


# ─────────────────────────────────────────────────────────────────────────────
# JWT
# ─────────────────────────────────────────────────────────────────────────────

def crear_token(user: dict) -> str:
    payload = {
        "sub":      str(user["id"]),
        "id":       user["id"],
        "username": user["username"],
        "nombre":   user.get("nombre") or user["username"],
        "role":     user["role"],
        "exp":      datetime.now(timezone.utc) + timedelta(hours=EXPIRE_HORAS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido o expirado")


# ─────────────────────────────────────────────────────────────────────────────
# Dependencias FastAPI
# ─────────────────────────────────────────────────────────────────────────────

async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
) -> dict:
    if not creds:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "No autenticado")
    return decode_token(creds.credentials)


async def require_editor(user: dict = Depends(get_current_user)) -> dict:
    """Solo Editor o Admin pueden llamar este endpoint."""
    if user.get("role") not in ("admin", "editor"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Se requiere rol Editor o Admin")
    return user


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """Solo Admin puede llamar este endpoint."""
    if user.get("role") != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Se requiere rol Admin")
    return user
