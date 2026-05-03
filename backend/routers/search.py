"""
routers/search.py — Búsqueda full-text y por metadatos
"""

from typing import Optional
from fastapi import APIRouter, Query

import database as db

router = APIRouter()


@router.get("/")
def buscar(
    q: str = Query(..., min_length=1),
    status: Optional[str] = Query(None),
):
    resultados_fts = db.search_documents_fts(q)
    ids_encontrados = {int(r["doc_id"]) for r in resultados_fts}

    todos = db.get_all_documents()
    enriquecidos = []

    for doc in todos:
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
def estadisticas():
    docs = db.get_all_documents()

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
