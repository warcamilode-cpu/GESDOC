"""
routers/comments.py — CRUD de comentarios con hilos (threading)
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends

import database as db
from backend.models import CommentCreate, CommentUpdate, CommentRead
from backend.auth import get_current_user

router = APIRouter()


def _enriquecer_con_respuestas(comentario: dict) -> dict:
    respuestas = db.get_replies(comentario["id"])
    return {**comentario, "replies": [_enriquecer_con_respuestas(r) for r in respuestas]}


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/")
def listar_comentarios(
    document_id: int = Query(...),
    category: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    con_respuestas: bool = Query(True),
):
    raiz = db.get_root_comments(
        doc_id=document_id,
        category=category,
        priority=priority,
        status=status,
        search=search,
    )
    if con_respuestas:
        return [_enriquecer_con_respuestas(c) for c in raiz]
    return raiz


@router.post("/", status_code=201)
def crear_comentario(data: CommentCreate, current_user: dict = Depends(get_current_user)):
    # El autor se toma del usuario logueado — no se puede falsificar
    autor = current_user.get("nombre") or current_user.get("username", "")
    comment_id = db.add_comment(
        doc_id=data.document_id,
        content=data.content,
        category=data.category,
        priority=data.priority,
        status=data.status,
        location_info=data.location_info,
        highlighted_text=data.highlighted_text,
        author=autor,
        parent_id=data.parent_id,
    )
    if comment_id is None:
        raise HTTPException(500, "No se pudo crear el comentario")

    conn = __import__("database").get_connection()
    row = conn.execute("SELECT * FROM comments WHERE id=?", (comment_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(500, "Comentario creado pero no encontrado")
    return {**dict(row), "replies": []}


@router.put("/{comment_id}")
def actualizar_comentario(comment_id: int, data: CommentUpdate):
    conn = __import__("database").get_connection()
    row = conn.execute("SELECT id FROM comments WHERE id=?", (comment_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Comentario no encontrado")

    db.update_comment(comment_id, **data.model_dump(exclude_none=True))

    conn = __import__("database").get_connection()
    row = conn.execute("SELECT * FROM comments WHERE id=?", (comment_id,)).fetchone()
    conn.close()
    respuestas = db.get_replies(comment_id)
    return {**dict(row), "replies": respuestas}


@router.delete("/{comment_id}", status_code=204)
def eliminar_comentario(comment_id: int):
    conn = __import__("database").get_connection()
    row = conn.execute("SELECT id FROM comments WHERE id=?", (comment_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Comentario no encontrado")
    db.delete_comment(comment_id)


@router.get("/{comment_id}/replies")
def obtener_respuestas(comment_id: int):
    return db.get_replies(comment_id)
