"""
routers/documents.py — CRUD de documentos + upload + visor de contenido
"""

import os
import tempfile
import io
import html as html_lib
from typing import Optional, List

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query, Depends
from fastapi.responses import FileResponse, HTMLResponse

import database as db
from backend.models import DocumentRead, DocumentUpdate
from backend.auth import get_current_user, require_editor

router = APIRouter()

FORMATOS_VALIDOS = {"pdf", "docx", "doc", "md", "txt", "markdown"}


def _ext(path: str) -> str:
    return os.path.splitext(path)[1].lstrip(".").lower()


def _docx_a_html(path: str) -> str:
    from docx import Document
    from docx.shared import RGBColor

    doc = Document(path)
    partes = []
    for para in doc.paragraphs:
        texto = para.text.strip()
        if not texto:
            partes.append("<br>")
            continue
        style = para.style.name.lower()
        if "heading 1" in style:
            partes.append(f"<h1>{html_lib.escape(texto)}</h1>")
        elif "heading 2" in style:
            partes.append(f"<h2>{html_lib.escape(texto)}</h2>")
        elif "heading 3" in style:
            partes.append(f"<h3>{html_lib.escape(texto)}</h3>")
        else:
            runs_html = []
            for run in para.runs:
                t = html_lib.escape(run.text)
                if run.bold:
                    t = f"<strong>{t}</strong>"
                if run.italic:
                    t = f"<em>{t}</em>"
                if run.underline:
                    t = f"<u>{t}</u>"
                runs_html.append(t)
            partes.append(f"<p>{''.join(runs_html)}</p>")
    return "\n".join(partes)


def _md_a_html(path: str) -> str:
    import markdown as md_lib
    with open(path, encoding="utf-8", errors="replace") as f:
        texto = f.read()
    return md_lib.markdown(texto, extensions=["tables", "fenced_code", "nl2br"])


def _txt_a_html(path: str) -> str:
    with open(path, encoding="utf-8", errors="replace") as f:
        texto = f.read()
    return f"<pre style='white-space:pre-wrap;word-break:break-word;'>{html_lib.escape(texto)}</pre>"


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[DocumentRead])
def listar_documentos(
    folder_id:       Optional[int] = Query(None),
    sin_carpeta:     bool          = Query(False),
    status:          Optional[str] = Query(None),
    vigencia_estado: Optional[str] = Query(None),
    tipo_norma:      Optional[str] = Query(None),
    entidad_emisora: Optional[str] = Query(None),
    biblioteca:      str           = Query("general"),   # general | personal
    current_user:    dict          = Depends(get_current_user),
):
    # Filtrado por biblioteca hecho directamente en SQL
    uid = int(current_user.get("id", 0))
    rol = current_user.get("role", "lector")

    if sin_carpeta:
        docs = db.get_unfoldered_documents_for_user(uid, rol, biblioteca)
    elif folder_id is not None:
        docs = db.get_documents_in_folder_for_user(folder_id, uid, rol, biblioteca)
    else:
        docs = db.get_all_documents_for_user(uid, rol, biblioteca)

    if status:
        docs = [d for d in docs if d["status"] == status]
    if vigencia_estado:
        docs = [d for d in docs if d.get("vigencia_estado") == vigencia_estado]
    if tipo_norma:
        docs = [d for d in docs if d.get("tipo_norma") == tipo_norma]
    if entidad_emisora:
        q = entidad_emisora.lower()
        docs = [d for d in docs if q in (d.get("entidad_emisora") or "").lower()]
    return docs


@router.post("/", response_model=DocumentRead, status_code=201)
async def subir_documento(
    file:             UploadFile    = File(...),
    folder_id:        Optional[int] = Form(None),
    status:           str           = Form("Por revisar"),
    tags:             str           = Form(""),
    tipo_norma:       str           = Form(""),
    numero_norma:     str           = Form(""),
    entidad_emisora:  str           = Form(""),
    fecha_expedicion: str           = Form(""),
    fecha_vigencia:   str           = Form(""),
    vigencia_estado:  str           = Form("Por confirmar"),
    biblioteca:       str           = Form("general"),
    current_user:     dict          = Depends(require_editor),
):
    ext = (file.filename or "").rsplit(".", 1)[-1].lower()
    if ext not in FORMATOS_VALIDOS:
        raise HTTPException(400, f"Formato no soportado: {ext}")

    contenido = await file.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
        tmp.write(contenido)
        tmp_path = tmp.name

    try:
        nombre = file.filename or f"documento.{ext}"
        folder_name = None
        if folder_id:
            carpetas = db.get_all_folders()
            carpeta = next((f for f in carpetas if f["id"] == folder_id), None)
            if carpeta:
                folder_name = carpeta["name"]

        doc_id = db.add_document(
            nombre, tmp_path, ext,
            tags=tags, status=status, folder_name=folder_name,
            tipo_norma=tipo_norma, numero_norma=numero_norma,
            entidad_emisora=entidad_emisora, fecha_expedicion=fecha_expedicion,
            fecha_vigencia=fecha_vigencia, vigencia_estado=vigencia_estado,
            owner_id=current_user["id"], biblioteca=biblioteca,
        )
        if doc_id is None:
            raise HTTPException(500, "No se pudo guardar el documento")

        if folder_id and doc_id:
            db.assign_document_to_folder(doc_id, folder_id)

        doc = db.get_document(doc_id)
        if not doc:
            raise HTTPException(500, "Documento no encontrado tras guardar")
        return doc
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


@router.get("/{doc_id}", response_model=DocumentRead)
def obtener_documento(doc_id: int):
    doc = db.get_document(doc_id)
    if not doc:
        raise HTTPException(404, "Documento no encontrado")
    db.update_last_opened(doc_id)
    return doc


@router.put("/{doc_id}", response_model=DocumentRead)
def actualizar_documento(doc_id: int, data: DocumentUpdate):
    doc = db.get_document(doc_id)
    if not doc:
        raise HTTPException(404, "Documento no encontrado")

    cambios = data.model_dump(exclude_none=True)
    if "name" in cambios and cambios["name"] != doc["name"]:
        db.rename_document(doc_id, cambios.pop("name"))
    if cambios:
        db.update_document(doc_id, **cambios)

    return db.get_document(doc_id)


@router.delete("/{doc_id}", status_code=204)
def eliminar_documento(doc_id: int):
    doc = db.get_document(doc_id)
    if not doc:
        raise HTTPException(404, "Documento no encontrado")
    db.delete_document(doc_id)


@router.get("/{doc_id}/folders")
def carpetas_del_documento(doc_id: int):
    doc = db.get_document(doc_id)
    if not doc:
        raise HTTPException(404, "Documento no encontrado")
    return db.get_folders_for_document(doc_id)


@router.get("/{doc_id}/file")
def servir_archivo(doc_id: int, descarga: bool = False):
    doc = db.get_document(doc_id)
    if not doc:
        raise HTTPException(404, "Documento no encontrado")
    path = doc["path"]
    if not os.path.isfile(path):
        raise HTTPException(404, "Archivo físico no encontrado")
    nombre = os.path.basename(path)
    ext = _ext(path)
    media_types = {
        "pdf":  "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "doc":  "application/msword",
        "md":   "text/plain",
        "txt":  "text/plain",
    }
    media_type = media_types.get(ext, "application/octet-stream")
    disposition = "attachment" if descarga else "inline"
    return FileResponse(
        path,
        media_type=media_type,
        headers={"Content-Disposition": f'{disposition}; filename="{nombre}"'},
    )


@router.get("/{doc_id}/content", response_class=HTMLResponse)
def contenido_documento(doc_id: int):
    doc = db.get_document(doc_id)
    if not doc:
        raise HTTPException(404, "Documento no encontrado")
    path = doc["path"]
    if not os.path.isfile(path):
        raise HTTPException(404, "Archivo físico no encontrado")

    fmt = _ext(path)
    if fmt == "pdf":
        return HTMLResponse(
            '<p style="color:#a6adc8;text-align:center;padding:2rem;">'
            'Usa el visor PDF integrado.</p>'
        )
    elif fmt in ("docx", "doc"):
        cuerpo = _docx_a_html(path)
    elif fmt in ("md", "markdown"):
        cuerpo = _md_a_html(path)
    else:
        cuerpo = _txt_a_html(path)

    return HTMLResponse(f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{
    font-family: 'Times New Roman', serif;
    font-size: 11pt;
    color: #cdd6f4;
    background: #1e1e2e;
    padding: 2rem 3rem;
    line-height: 1.7;
    max-width: 800px;
    margin: 0 auto;
  }}
  h1,h2,h3 {{ color: #89b4fa; margin-top: 1.5rem; }}
  a {{ color: #cba6f7; }}
  code {{ background: #313244; padding: 2px 6px; border-radius: 4px; font-size: 10pt; }}
  pre {{ background: #313244; padding: 1rem; border-radius: 8px; overflow-x: auto; }}
  table {{ border-collapse: collapse; width: 100%; }}
  th,td {{ border: 1px solid #45475a; padding: 6px 12px; }}
  th {{ background: #313244; }}
  blockquote {{ border-left: 3px solid #89b4fa; margin-left: 0; padding-left: 1rem; color: #a6adc8; }}
</style>
</head>
<body>{cuerpo}</body>
</html>""")
