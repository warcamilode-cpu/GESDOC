"""
models.py — Modelos Pydantic para GESDOC API
"""

from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel


# ─────────────────────────────────────────────────────────────────────────────
# DOCUMENTOS
# ─────────────────────────────────────────────────────────────────────────────

class DocumentUpdate(BaseModel):
    name:             Optional[str] = None
    tags:             Optional[str] = None
    status:           Optional[str] = None
    # Metadatos normativos
    tipo_norma:       Optional[str] = None
    numero_norma:     Optional[str] = None
    entidad_emisora:  Optional[str] = None
    fecha_expedicion: Optional[str] = None
    fecha_vigencia:   Optional[str] = None
    fecha_derogacion: Optional[str] = None
    vigencia_estado:  Optional[str] = None


class DocumentRead(BaseModel):
    id:               int
    name:             str
    path:             str
    format:           str
    tags:             str
    status:           str
    added_at:         str
    last_opened:      Optional[str] = None
    # Metadatos normativos
    tipo_norma:       str = ""
    numero_norma:     str = ""
    entidad_emisora:  str = ""
    fecha_expedicion: str = ""
    fecha_vigencia:   str = ""
    fecha_derogacion: str = ""
    vigencia_estado:  str = "Por confirmar"
    # Campos de usuario
    owner_id:         Optional[int] = None
    biblioteca:       str = "general"


# ─────────────────────────────────────────────────────────────────────────────
# CARPETAS
# ─────────────────────────────────────────────────────────────────────────────

class FolderCreate(BaseModel):
    name:      str
    icon:      str = "📁"
    color:     str = "#89b4fa"
    parent_id: Optional[int] = None


class FolderUpdate(BaseModel):
    name:  Optional[str] = None
    icon:  Optional[str] = None
    color: Optional[str] = None


class FolderRead(BaseModel):
    id:         int
    name:       str
    icon:       str
    color:      str
    parent_id:  Optional[int] = None
    created_at: str
    children:   List[FolderRead] = []


FolderRead.model_rebuild()


# ─────────────────────────────────────────────────────────────────────────────
# COMENTARIOS
# ─────────────────────────────────────────────────────────────────────────────

class CommentCreate(BaseModel):
    document_id:      int
    content:          str
    category:         str = "General"
    priority:         str = "Media"
    status:           str = "Abierto"
    location_info:    str = ""
    highlighted_text: str = ""
    author:           str = ""
    parent_id:        Optional[int] = None


class CommentUpdate(BaseModel):
    content:          Optional[str] = None
    category:         Optional[str] = None
    priority:         Optional[str] = None
    status:           Optional[str] = None
    location_info:    Optional[str] = None
    author:           Optional[str] = None
    highlighted_text: Optional[str] = None


class CommentRead(BaseModel):
    id:               int
    document_id:      int
    content:          str
    category:         str
    priority:         str
    status:           str
    location_info:    str
    highlighted_text: str
    author:           str
    parent_id:        Optional[int] = None
    created_at:       str
    updated_at:       str
    replies:          List[CommentRead] = []


CommentRead.model_rebuild()


# ─────────────────────────────────────────────────────────────────────────────
# RELACIONES ENTRE DOCUMENTOS
# ─────────────────────────────────────────────────────────────────────────────

class RelacionCreate(BaseModel):
    doc_origen_id:  int
    doc_destino_id: int
    tipo_relacion:  str
    descripcion:    str = ""


class RelacionRead(BaseModel):
    id:                    int
    doc_origen_id:         int
    doc_destino_id:        int
    tipo_relacion:         str
    descripcion:           str
    created_at:            str
    doc_origen_nombre:     Optional[str] = None
    doc_origen_tipo:       Optional[str] = None
    doc_origen_numero:     Optional[str] = None
    doc_destino_nombre:    Optional[str] = None
    doc_destino_tipo:      Optional[str] = None
    doc_destino_numero:    Optional[str] = None
