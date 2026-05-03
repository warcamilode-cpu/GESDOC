"""
main.py — GESDOC v2 con FastAPI
Ejecutar: uvicorn main:app --reload --host 0.0.0.0 --port 8001
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import FileResponse

import database as db
from backend.routers import documents, folders, comments, search, export, relations


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    db.init_folders()
    db.add_author_column()
    db.add_parent_id_column()
    db.add_metadatos_normativos()
    db.init_relations()
    db.ensure_vault()
    yield


app = FastAPI(
    title="GESDOC",
    description="Sistema de gestión documental con árbol de consulta y anotaciones",
    version="2.1.0",
    lifespan=lifespan,
)

app.include_router(documents.router,  prefix="/api/documents",  tags=["documentos"])
app.include_router(folders.router,    prefix="/api/folders",    tags=["carpetas"])
app.include_router(comments.router,   prefix="/api/comments",   tags=["comentarios"])
app.include_router(search.router,     prefix="/api/search",     tags=["busqueda"])
app.include_router(export.router,     prefix="/api/export",     tags=["exportar"])
app.include_router(relations.router,  prefix="/api/relations",  tags=["relaciones"])


@app.get("/", include_in_schema=False)
def index():
    return FileResponse("frontend/index.html")
