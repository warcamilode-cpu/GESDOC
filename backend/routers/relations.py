"""
routers/relations.py — Relaciones normativas entre documentos
"""

from typing import List
from fastapi import APIRouter, HTTPException

import database as db
from backend.models import RelacionCreate, RelacionRead

router = APIRouter()

TIPOS_VALIDOS = set(db.TIPOS_RELACION)


@router.get("/document/{doc_id}", response_model=List[RelacionRead])
def relaciones_del_documento(doc_id: int):
    if not db.get_document(doc_id):
        raise HTTPException(404, "Documento no encontrado")
    return db.get_relations(doc_id)


@router.post("/", status_code=201, response_model=RelacionRead)
def crear_relacion(data: RelacionCreate):
    if data.tipo_relacion not in TIPOS_VALIDOS:
        raise HTTPException(400, f"tipo_relacion inválido. Opciones: {list(TIPOS_VALIDOS)}")
    if not db.get_document(data.doc_origen_id):
        raise HTTPException(404, "Documento origen no encontrado")
    if not db.get_document(data.doc_destino_id):
        raise HTTPException(404, "Documento destino no encontrado")
    if data.doc_origen_id == data.doc_destino_id:
        raise HTTPException(400, "Un documento no puede relacionarse consigo mismo")

    rel_id = db.add_relation(
        data.doc_origen_id, data.doc_destino_id,
        data.tipo_relacion, data.descripcion,
    )
    rels = db.get_relations(data.doc_origen_id)
    rel = next((r for r in rels if r["id"] == rel_id), None)
    if not rel:
        raise HTTPException(500, "Relación creada pero no encontrada")
    return rel


@router.delete("/{rel_id}", status_code=204)
def eliminar_relacion(rel_id: int):
    conn = db.get_connection()
    row = conn.execute("SELECT id FROM document_relations WHERE id=?", (rel_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Relación no encontrada")
    db.delete_relation(rel_id)


@router.get("/tipos")
def listar_tipos():
    return db.TIPOS_RELACION


@router.get("/constantes")
def constantes_normativas():
    return {
        "tipos_norma":    db.TIPOS_NORMA,
        "vigencia_estados": db.VIGENCIA_ESTADOS,
        "tipos_relacion": db.TIPOS_RELACION,
    }
