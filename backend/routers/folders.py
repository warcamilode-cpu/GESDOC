"""
routers/folders.py — CRUD de carpetas con soporte de árbol jerárquico y biblioteca
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends

import database as db
from backend.models import FolderCreate, FolderUpdate, FolderRead, DocumentRead
from backend.auth import get_current_user

router = APIRouter()


def _build_tree(folders: list, parent_id=None) -> list:
    nodos = []
    for f in folders:
        if f["parent_id"] == parent_id:
            hijos = _build_tree(folders, parent_id=f["id"])
            nodos.append({**f, "children": hijos})
    return nodos


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[FolderRead])
def listar_carpetas(
    biblioteca:   str  = Query("general"),
    current_user: dict = Depends(get_current_user),
):
    uid = int(current_user.get("id", 0))
    rol = current_user.get("role", "lector")
    return db.get_folders_for_user(uid, rol, biblioteca)


@router.get("/tree")
def arbol_carpetas(
    biblioteca:   str  = Query("general"),
    current_user: dict = Depends(get_current_user),
):
    uid = int(current_user.get("id", 0))
    rol = current_user.get("role", "lector")
    carpetas = db.get_folders_for_user(uid, rol, biblioteca)
    return _build_tree(carpetas, parent_id=None)


@router.post("/", status_code=201)
def crear_carpeta(
    data:         FolderCreate,
    current_user: dict = Depends(get_current_user),
):
    uid = int(current_user.get("id", 0))
    # La biblioteca de la carpeta viene en el request body
    biblioteca = getattr(data, "biblioteca", "general")
    owner_id   = uid if biblioteca == "personal" else None

    folder_id = db.add_folder(
        name=data.name,
        icon=data.icon,
        color=data.color,
        parent_id=data.parent_id,
        biblioteca=biblioteca,
        owner_id=owner_id,
    )
    if folder_id is None:
        raise HTTPException(500, "No se pudo crear la carpeta")
    carpeta = next((f for f in db.get_all_folders() if f["id"] == folder_id), None)
    if not carpeta:
        raise HTTPException(500, "Carpeta creada pero no encontrada")
    return {**carpeta, "children": []}


@router.put("/{folder_id}")
def actualizar_carpeta(folder_id: int, data: FolderUpdate):
    if not any(f["id"] == folder_id for f in db.get_all_folders()):
        raise HTTPException(404, "Carpeta no encontrada")
    db.update_folder(folder_id, **data.model_dump(exclude_none=True))
    carpeta = next((f for f in db.get_all_folders() if f["id"] == folder_id), None)
    return {**carpeta, "children": []}


@router.delete("/{folder_id}", status_code=204)
def eliminar_carpeta(folder_id: int):
    if not any(f["id"] == folder_id for f in db.get_all_folders()):
        raise HTTPException(404, "Carpeta no encontrada")
    db.delete_folder(folder_id)


@router.get("/{folder_id}/documents", response_model=List[DocumentRead])
def documentos_en_carpeta(folder_id: int):
    return db.get_documents_in_folder(folder_id)


@router.post("/{folder_id}/documents/{doc_id}", status_code=204)
def asignar_documento(folder_id: int, doc_id: int):
    db.assign_document_to_folder(doc_id, folder_id)


@router.delete("/{folder_id}/documents/{doc_id}", status_code=204)
def quitar_documento(folder_id: int, doc_id: int):
    db.remove_document_from_folder(doc_id, folder_id)
