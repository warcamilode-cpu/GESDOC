"""
routers/auth.py — Login, perfil y cambio de contraseña
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

import database as db
from backend.auth import verify_password, crear_token, get_current_user, hash_password

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class CambiarPasswordRequest(BaseModel):
    password_actual: str
    password_nueva: str


@router.post("/login")
def login(data: LoginRequest):
    user = db.get_user_by_username(data.username)
    if not user or not user.get("activo"):
        raise HTTPException(401, "Usuario o contraseña incorrectos")
    if not verify_password(data.password, user["password"]):
        raise HTTPException(401, "Usuario o contraseña incorrectos")
    token = crear_token(user)
    return {
        "token": token,
        "user": {
            "id":       user["id"],
            "username": user["username"],
            "nombre":   user["nombre"] or user["username"],
            "role":     user["role"],
            "email":    user.get("email", ""),
        },
    }


@router.get("/me")
def me(current_user: dict = Depends(get_current_user)):
    user = db.get_user_by_id(current_user["id"])
    if not user:
        raise HTTPException(404, "Usuario no encontrado")
    return {
        "id":       user["id"],
        "username": user["username"],
        "nombre":   user["nombre"] or user["username"],
        "role":     user["role"],
        "email":    user.get("email", ""),
    }


@router.post("/cambiar-password")
def cambiar_password(
    data: CambiarPasswordRequest,
    current_user: dict = Depends(get_current_user),
):
    user = db.get_user_by_id(current_user["id"])
    if not user:
        raise HTTPException(404, "Usuario no encontrado")
    if not verify_password(data.password_actual, user["password"]):
        raise HTTPException(400, "Contraseña actual incorrecta")
    if len(data.password_nueva) < 6:
        raise HTTPException(400, "La contraseña debe tener al menos 6 caracteres")
    db.update_user(current_user["id"], password=hash_password(data.password_nueva))
    return {"message": "Contraseña actualizada correctamente"}
