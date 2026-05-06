"""
routers/search.py — Búsqueda full-text y por metadatos
"""

from typing import Optional
from fastapi import APIRouter, Query, Depends

import database as db
from backend.auth import get_current_user

router = APIRouter()


def _documentos_visibles(current_user: dict) -> list:
    """Devuelve todos los documentos que el usuario puede ver (general + su personal)."""
    uid = int(current_user.get("id", 0))
    rol = current_user.get("role", "lector")
    generales  = db.get_all_documents_for_user(uid, rol, "general")
    personales = db.get_all_documents_for_user(uid, rol, "personal")
    return generales + personales


@router.get("/")
def buscar(
    q:            str           = Query(..., min_length=1),
    status:       Optional[str] = Query(None),
    current_user: dict          = Depends(get_current_user),
):
    resultados_fts = db.search_documents_fts(q)
    ids_encontrados = {int(r["doc_id"]) for r in resultados_fts}

    # Solo buscar en documentos que el usuario puede ver
    docs_visibles = _documentos_visibles(current_user)
    enriquecidos  = []

    for doc in docs_visibles:
        coincide_fts    = doc["id"] in ids_encontrados
        coincide_nombre = q.lower() in doc["name"].lower()
        coincide_tags   = q.lower() in (doc.get("tags") or "").lower()

        if coincide_fts or coincide_nombre or coincide_tags:
            if status and doc["status"] != status:
                continue
            snippet = next(
                (r["snippet"] for r in resultados_fts if int(r["doc_id"]) == doc["id"]),
                None,
            )
            enriquecidos.append({**doc, "snippet": snippet})

    return enriquecidos


@router.get("/stats")
def estadisticas(current_user: dict = Depends(get_current_user)):
    # Estadísticas solo de documentos visibles para este usuario
    docs = _documentos_visibles(current_user)

    por_formato: dict = {}
    por_estado:  dict = {}
    for d in docs:
        por_formato[d["format"]] = por_formato.get(d["format"], 0) + 1
        por_estado[d["status"]]  = por_estado.get(d["status"], 0) + 1

    conn = db.get_connection()
    total_comentarios = conn.execute("SELECT COUNT(*) as n FROM comments").fetchone()["n"]
    total_carpetas    = conn.execute("SELECT COUNT(*) as n FROM folders").fetchone()["n"]
    conn.close()

    return {
        "total_documentos": len(docs),
        "total_comentarios": total_comentarios,
        "total_carpetas":    total_carpetas,
        "por_formato":       por_formato,
        "por_estado":        por_estado,
    }
