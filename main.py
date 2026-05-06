"""
main.py — GESDOC v3 con FastAPI + Sistema de Usuarios
Ejecutar: uvicorn main:app --reload --host 0.0.0.0 --port 8001
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.responses import FileResponse

import database as db
from backend.auth import get_current_user, hash_password
from backend.routers import documents, folders, comments, search, export, relations
from backend.routers import auth as auth_router
from backend.routers import users as users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Tablas base
    db.init_db()
    db.init_folders()
    # Migraciones de comentarios
    db.add_author_column()
    db.add_parent_id_column()
    # Migraciones normativas
    db.add_metadatos_normativos()
    db.init_relations()
    # Migraciones de usuarios
    db.init_users()
    db.add_campos_usuario_documento()
    # Repositorio físico
    db.ensure_vault()
    # Crear admin inicial si no hay usuarios
    pwd = os.environ.get("GESDOC_ADMIN_PASSWORD", "admin123")
    db.seed_admin(hash_password(pwd))
    yield


app = FastAPI(
    title="GESDOC",
    description="Sistema de gestión documental con árbol normativo y usuarios",
    version="3.0.0",
    lifespan=lifespan,
)

# ── Rutas públicas (sin autenticación) ───────────────────────────────────────
app.include_router(auth_router.router, prefix="/api/auth", tags=["autenticacion"])

# ── Rutas protegidas (requieren token JWT) ────────────────────────────────────
_auth = [Depends(get_current_user)]

app.include_router(documents.router,    prefix="/api/documents",  tags=["documentos"],    dependencies=_auth)
app.include_router(folders.router,      prefix="/api/folders",    tags=["carpetas"],      dependencies=_auth)
app.include_router(comments.router,     prefix="/api/comments",   tags=["comentarios"],   dependencies=_auth)
app.include_router(search.router,       prefix="/api/search",     tags=["busqueda"],      dependencies=_auth)
app.include_router(export.router,       prefix="/api/export",     tags=["exportar"],      dependencies=_auth)
app.include_router(relations.router,    prefix="/api/relations",  tags=["relaciones"],    dependencies=_auth)
app.include_router(users_router.router, prefix="/api/users",      tags=["usuarios"],      dependencies=_auth)


@app.get("/", include_in_schema=False)
def index():
    return FileResponse("frontend/index.html")
