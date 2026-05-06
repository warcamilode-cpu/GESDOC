"""
routers/users.py — Gestión de usuarios (solo Admin)
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

import database as db
from backend.auth import require_admin, hash_password, get_current_user

router = APIRouter()


class UserCreate(BaseModel):
    username: str
    password: str
    nombre:   str = ""
    email:    str = ""
    role:     str = "lector"


class UserUpdate(BaseModel):
    nombre:   Optional[str] = None
    email:    Optional[str] = None
    role:     Optional[str] = None
    activo:   Optional[int] = None
    password: Optional[str] = None


@router.get("/")
def listar_usuarios(_: dict = Depends(require_admin)):
    return db.get_all_users()


@router.post("/", status_code=201)
def crear_usuario(data: UserCreate, _: dict = Depends(require_admin)):
    if data.role not in db.ROLES:
        raise HTTPException(400, f"Rol inválido. Opciones: {db.ROLES}")
    if db.get_user_by_username(data.username):
        raise HTTPException(409, "El nombre de usuario ya existe")
    uid = db.add_user(
        data.username, hash_password(data.password),
        nombre=data.nombre, email=data.email, role=data.role,
    )
    if not uid:
        raise HTTPException(500, "Error al crear usuario")
    user = db.get_user_by_id(uid)
    return {k: v for k, v in user.items() if k != "password"}


@router.put("/{user_id}")
def actualizar_usuario(
    user_id: int,
    data: UserUpdate,
    admin: dict = Depends(require_admin),
):
    if not db.get_user_by_id(user_id):
        raise HTTPException(404, "Usuario no encontrado")
    cambios = data.model_dump(exclude_none=True)
    if "password" in cambios:
        if len(cambios["password"]) < 6:
            raise HTTPException(400, "La contraseña debe tener al menos 6 caracteres")
        cambios["password"] = hash_password(cambios["password"])
    if "role" in cambios and cambios["role"] not in db.ROLES:
        raise HTTPException(400, f"Rol inválido. Opciones: {db.ROLES}")
    db.update_user(user_id, **cambios)
    user = db.get_user_by_id(user_id)
    return {k: v for k, v in user.items() if k != "password"}


@router.delete("/{user_id}", status_code=204)
def eliminar_usuario(user_id: int, admin: dict = Depends(require_admin)):
    if not db.get_user_by_id(user_id):
        raise HTTPException(404, "Usuario no encontrado")
    if user_id == admin["id"]:
        raise HTTPException(400, "No puedes eliminar tu propio usuario")
    db.delete_user(user_id)
