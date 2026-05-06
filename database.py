"""
database.py — Capa de persistencia SQLite para DocManager (edición Streamlit)

Mejoras respecto a la versión PyQt5:
  • docs_vault  →  repositorio
  • Carpetas con parent_id para soporte de subcarpetas
  • copy_to_vault_with_folder() organiza archivos en subcarpetas por carpeta
  • rename_document() renombra nombre en BD Y el archivo físico en repositorio
  • add_comment() incluye author correctamente
"""

import sqlite3
import os
import shutil
import re
from datetime import datetime

DB_DIR   = os.path.join(os.path.expanduser("~"), ".docmanager")
DB_PATH  = os.path.join(DB_DIR, "docmanager.db")

# ── Renombrado de docs_vault → repositorio ────────────────────────────────────
VAULT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "repositorio")


# ─────────────────────────────────────────────────────────────────────────────
# Constantes
# ─────────────────────────────────────────────────────────────────────────────

DOCUMENT_STATUSES   = ["Por revisar", "En progreso", "Revisado", "Aprobado"]
COMMENT_CATEGORIES  = ["General", "Importante", "Pregunta", "Corrección", "Referencia", "Tarea"]
COMMENT_PRIORITIES  = ["Alta", "Media", "Baja"]
COMMENT_STATUSES    = ["Abierto", "Resuelto", "Pendiente"]

ROLES = ["admin", "editor", "lector"]

TIPOS_NORMA = [
    "Resolución", "Circular", "Oficio", "Memorando", "Decreto",
    "Acuerdo", "Especificación Técnica", "Ficha Técnica", "Contrato", "Otro",
]
VIGENCIA_ESTADOS = ["Por confirmar", "Vigente", "Modificado", "Derogado", "Suspendido", "Compilado"]
TIPOS_RELACION   = ["Deroga", "Modifica", "Desarrolla", "Concordante con", "Suspende", "Compila", "Referencia"]


# ─────────────────────────────────────────────────────────────────────────────
# Utilidades de repositorio
# ─────────────────────────────────────────────────────────────────────────────

def ensure_vault():
    os.makedirs(VAULT_DIR, exist_ok=True)


def _safe_name(name: str) -> str:
    """Convierte un nombre en uno seguro para el sistema de archivos."""
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name)
    name = name.strip('. ')
    return name or "carpeta"


def copy_to_vault_with_folder(src_path: str, folder_name: str = None) -> str:
    """
    Copia src_path al repositorio, opcionalmente dentro de una subcarpeta
    que lleva el nombre de la carpeta de la biblioteca.
    Devuelve la ruta destino en el repositorio.
    """
    ensure_vault()
    abs_src   = os.path.abspath(src_path)
    vault_abs = os.path.abspath(VAULT_DIR)

    # Ya está dentro del repositorio
    if abs_src.startswith(vault_abs + os.sep) or abs_src == vault_abs:
        return abs_src

    filename = os.path.basename(abs_src)

    if folder_name:
        dest_dir = os.path.join(VAULT_DIR, _safe_name(folder_name))
        os.makedirs(dest_dir, exist_ok=True)
    else:
        dest_dir = VAULT_DIR

    dest_path = os.path.join(dest_dir, filename)

    # Evitar colisión de nombres
    if os.path.exists(dest_path):
        try:
            if os.path.samefile(abs_src, dest_path):
                return dest_path
        except Exception:
            pass
        base, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(dest_path):
            dest_path = os.path.join(dest_dir, f"{base}_{counter}{ext}")
            counter += 1

    shutil.copy2(abs_src, dest_path)
    return dest_path


def copy_to_vault(src_path: str) -> str:
    """Compatibilidad: copia al raíz del repositorio."""
    return copy_to_vault_with_folder(src_path, folder_name=None)


# ─────────────────────────────────────────────────────────────────────────────
# Conexión BD
# ─────────────────────────────────────────────────────────────────────────────

def get_connection():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ─────────────────────────────────────────────────────────────────────────────
# Inicialización y migraciones
# ─────────────────────────────────────────────────────────────────────────────

def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            path        TEXT    NOT NULL UNIQUE,
            format      TEXT    NOT NULL,
            tags        TEXT    DEFAULT '',
            status      TEXT    DEFAULT 'Por revisar',
            added_at    TEXT    DEFAULT CURRENT_TIMESTAMP,
            last_opened TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id      INTEGER NOT NULL,
            content          TEXT    NOT NULL,
            category         TEXT    DEFAULT 'General',
            priority         TEXT    DEFAULT 'Media',
            status           TEXT    DEFAULT 'Abierto',
            location_info    TEXT    DEFAULT '',
            highlighted_text TEXT    DEFAULT '',
            author           TEXT    DEFAULT '',
            parent_id        INTEGER DEFAULT NULL,
            created_at       TEXT    DEFAULT CURRENT_TIMESTAMP,
            updated_at       TEXT    DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE,
            FOREIGN KEY(parent_id)   REFERENCES comments(id)  ON DELETE CASCADE
        )
    ''')

    c.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts
        USING fts5(doc_id UNINDEXED, name, content)
    ''')

    conn.commit()
    conn.close()


def init_folders():
    """Crea tablas de carpetas con soporte de subcarpetas (parent_id)."""
    conn = get_connection()

    conn.execute('''
        CREATE TABLE IF NOT EXISTS folders (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT    NOT NULL,
            parent_id  INTEGER DEFAULT NULL,
            icon       TEXT    DEFAULT '📁',
            color      TEXT    DEFAULT '#89b4fa',
            created_at TEXT    DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(parent_id) REFERENCES folders(id) ON DELETE CASCADE
        )
    ''')

    # Migración: añadir parent_id si no existe
    try:
        conn.execute("ALTER TABLE folders ADD COLUMN parent_id INTEGER DEFAULT NULL")
    except Exception:
        pass

    conn.execute('''
        CREATE TABLE IF NOT EXISTS document_folders (
            document_id INTEGER NOT NULL,
            folder_id   INTEGER NOT NULL,
            PRIMARY KEY (document_id, folder_id),
            FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE,
            FOREIGN KEY(folder_id)   REFERENCES folders(id)   ON DELETE CASCADE
        )
    ''')
    conn.commit()
    conn.close()


def add_author_column():
    """Migración: añade columna author a comments si no existe."""
    conn = get_connection()
    try:
        conn.execute("ALTER TABLE comments ADD COLUMN author TEXT DEFAULT ''")
        conn.commit()
    except Exception:
        pass
    conn.close()


def add_parent_id_column():
    """Migración: añade parent_id a comments si no existe."""
    conn = get_connection()
    try:
        conn.execute("ALTER TABLE comments ADD COLUMN parent_id INTEGER DEFAULT NULL")
        conn.commit()
    except Exception:
        pass
    conn.close()


def migrate_existing_to_vault():
    """Mueve documentos fuera del repositorio al repositorio."""
    ensure_vault()
    vault_abs = os.path.abspath(VAULT_DIR)
    conn = get_connection()
    docs = conn.execute("SELECT id, name, path FROM documents").fetchall()
    for doc in docs:
        abs_path = os.path.abspath(doc["path"])
        if abs_path.startswith(vault_abs + os.sep):
            continue
        if not os.path.isfile(abs_path):
            continue
        try:
            new_path = copy_to_vault(abs_path)
            conn.execute("UPDATE documents SET path=? WHERE id=?", (new_path, doc["id"]))
        except Exception:
            pass
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# DOCUMENTOS
# ─────────────────────────────────────────────────────────────────────────────

def add_document(name, path, fmt, tags="", status="Por revisar", folder_name=None,
                 tipo_norma="", numero_norma="", entidad_emisora="",
                 fecha_expedicion="", fecha_vigencia="", vigencia_estado="Por confirmar",
                 owner_id=None, biblioteca="general"):
    """
    Añade un documento al repositorio.
    Si se especifica folder_name, el archivo se copia a repositorio/[folder_name]/.
    """
    try:
        vault_path = copy_to_vault_with_folder(path, folder_name=folder_name)
    except Exception:
        vault_path = path

    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO documents (name, path, format, tags, status,"
            " tipo_norma, numero_norma, entidad_emisora,"
            " fecha_expedicion, fecha_vigencia, vigencia_estado,"
            " owner_id, biblioteca)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (name, vault_path, fmt, tags, status,
             tipo_norma, numero_norma, entidad_emisora,
             fecha_expedicion, fecha_vigencia, vigencia_estado,
             owner_id, biblioteca)
        )
        conn.commit()
        row = conn.execute("SELECT id FROM documents WHERE path=?", (vault_path,)).fetchone()
        return row["id"]
    except sqlite3.IntegrityError:
        for p in (vault_path, path):
            row = conn.execute("SELECT id FROM documents WHERE path=?", (p,)).fetchone()
            if row:
                return row["id"]
        return None
    finally:
        conn.close()


def rename_document(doc_id: int, new_name: str) -> bool:
    """
    Renombra el documento:
      1. Renombra el archivo físico dentro del repositorio.
      2. Actualiza la ruta y el nombre en la BD.
    """
    doc = get_document(doc_id)
    if not doc:
        return False

    old_path = doc["path"]
    safe_new  = _safe_name(new_name)

    if os.path.isfile(old_path):
        dir_   = os.path.dirname(old_path)
        _, ext = os.path.splitext(old_path)
        new_filename = safe_new + ext
        new_path = os.path.join(dir_, new_filename)

        # Evitar colisión si ya existe otro archivo con ese nombre
        counter = 1
        base_np = new_path
        while os.path.exists(new_path) and os.path.abspath(new_path) != os.path.abspath(old_path):
            base_ne, ext2 = os.path.splitext(base_np)
            new_path = f"{base_ne}_{counter}{ext2}"
            counter += 1

        try:
            os.rename(old_path, new_path)
            conn = get_connection()
            conn.execute(
                "UPDATE documents SET name=?, path=? WHERE id=?",
                (new_name, new_path, doc_id)
            )
            conn.commit()
            conn.close()
            return True
        except Exception:
            pass

    # Si no se pudo renombrar el archivo, al menos actualiza el nombre en BD
    conn = get_connection()
    conn.execute("UPDATE documents SET name=? WHERE id=?", (new_name, doc_id))
    conn.commit()
    conn.close()
    return True


def get_all_documents():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM documents ORDER BY added_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Consultas filtradas por biblioteca y usuario (nivel SQL) ─────────────────

def _where_biblioteca(biblioteca: str, user_id: int, role: str) -> tuple:
    """
    Devuelve (cláusula WHERE, parámetros) para filtrar documentos
    según biblioteca y permisos del usuario.
    """
    if biblioteca == "personal":
        if role == "admin":
            return "COALESCE(biblioteca,'general') = 'personal'", []
        else:
            return "COALESCE(biblioteca,'general') = 'personal' AND owner_id = ?", [user_id]
    else:
        # general: cualquier doc que NO sea personal
        return "COALESCE(biblioteca,'general') = 'general'", []


def get_all_documents_for_user(user_id: int, role: str, biblioteca: str = "general"):
    where, params = _where_biblioteca(biblioteca, user_id, role)
    conn = get_connection()
    rows = conn.execute(
        f"SELECT * FROM documents WHERE {where} ORDER BY added_at DESC", params
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_documents_in_folder_for_user(folder_id: int, user_id: int, role: str,
                                     biblioteca: str = "general"):
    where, params = _where_biblioteca(biblioteca, user_id, role)
    conn = get_connection()
    rows = conn.execute(
        f"SELECT d.* FROM documents d "
        f"JOIN document_folders df ON d.id = df.document_id "
        f"WHERE df.folder_id = ? AND {where} ORDER BY d.name",
        [folder_id] + params,
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_unfoldered_documents_for_user(user_id: int, role: str,
                                      biblioteca: str = "general"):
    where, params = _where_biblioteca(biblioteca, user_id, role)
    conn = get_connection()
    rows = conn.execute(
        f"SELECT * FROM documents "
        f"WHERE id NOT IN (SELECT DISTINCT document_id FROM document_folders) "
        f"AND {where} ORDER BY name",
        params,
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_document(doc_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM documents WHERE id=?", (doc_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_document(doc_id, **kwargs):
    allowed = {"name", "tags", "status", "tipo_norma", "numero_norma",
               "entidad_emisora", "fecha_expedicion", "fecha_vigencia",
               "fecha_derogacion", "vigencia_estado"}
    fields  = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return
    set_clause = ", ".join(f"{k}=?" for k in fields)
    vals = list(fields.values()) + [doc_id]
    conn = get_connection()
    conn.execute(f"UPDATE documents SET {set_clause} WHERE id=?", vals)
    conn.commit()
    conn.close()


def update_last_opened(doc_id):
    conn = get_connection()
    conn.execute(
        "UPDATE documents SET last_opened=? WHERE id=?",
        (datetime.now().isoformat(), doc_id)
    )
    conn.commit()
    conn.close()


def delete_document(doc_id):
    conn = get_connection()
    conn.execute("DELETE FROM documents WHERE id=?", (doc_id,))
    conn.commit()
    conn.close()


def update_document_fts(doc_id, name, content):
    conn = get_connection()
    conn.execute("DELETE FROM documents_fts WHERE doc_id=?", (str(doc_id),))
    conn.execute(
        "INSERT INTO documents_fts(doc_id, name, content) VALUES (?,?,?)",
        (str(doc_id), name, content[:500_000])
    )
    conn.commit()
    conn.close()


def search_documents_fts(query):
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT doc_id, snippet(documents_fts, 2, '<b>', '</b>', '...', 20) AS snippet "
            "FROM documents_fts WHERE documents_fts MATCH ? ORDER BY rank",
            (query,)
        ).fetchall()
        return [dict(r) for r in rows]
    except Exception:
        return []
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# COMENTARIOS
# ─────────────────────────────────────────────────────────────────────────────

def add_comment(doc_id, content, category="General", priority="Media",
                status="Abierto", location_info="", highlighted_text="", author="",
                parent_id=None):
    conn = get_connection()
    conn.execute(
        '''INSERT INTO comments
           (document_id, content, category, priority, status,
            location_info, highlighted_text, author, parent_id)
           VALUES (?,?,?,?,?,?,?,?,?)''',
        (doc_id, content, category, priority, status,
         location_info, highlighted_text, author, parent_id)
    )
    conn.commit()
    row = conn.execute("SELECT last_insert_rowid() AS id").fetchone()
    conn.close()
    return row["id"]


def get_comments(doc_id, category=None, priority=None, status=None, search=None):
    conn = get_connection()
    q      = "SELECT * FROM comments WHERE document_id=?"
    params = [doc_id]
    if category and category != "Todas":
        q += " AND category=?"; params.append(category)
    if priority and priority != "Todas":
        q += " AND priority=?"; params.append(priority)
    if status and status != "Todos":
        q += " AND status=?"; params.append(status)
    if search:
        q += " AND (content LIKE ? OR highlighted_text LIKE ? OR author LIKE ?)"
        params += [f"%{search}%", f"%{search}%", f"%{search}%"]
    q += " ORDER BY created_at DESC"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_comment(comment_id, **kwargs):
    allowed = {"content", "category", "priority", "status",
               "location_info", "author", "highlighted_text"}
    fields  = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return
    fields["updated_at"] = datetime.now().isoformat()
    set_clause = ", ".join(f"{k}=?" for k in fields)
    vals = list(fields.values()) + [comment_id]
    conn = get_connection()
    conn.execute(f"UPDATE comments SET {set_clause} WHERE id=?", vals)
    conn.commit()
    conn.close()


def delete_comment(comment_id):
    conn = get_connection()
    conn.execute("DELETE FROM comments WHERE id=?", (comment_id,))
    conn.commit()
    conn.close()


def get_all_comments_for_export(doc_id=None):
    conn = get_connection()
    if doc_id:
        q    = '''SELECT c.*, d.name as doc_name FROM comments c
                  JOIN documents d ON c.document_id=d.id
                  WHERE c.document_id=? ORDER BY c.created_at DESC'''
        rows = conn.execute(q, (doc_id,)).fetchall()
    else:
        q    = '''SELECT c.*, d.name as doc_name FROM comments c
                  JOIN documents d ON c.document_id=d.id
                  ORDER BY d.name, c.created_at DESC'''
        rows = conn.execute(q).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─────────────────────────────────────────────────────────────────────────────
# CARPETAS  (con soporte de subcarpetas via parent_id)
# ─────────────────────────────────────────────────────────────────────────────

def get_all_folders():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM folders ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_folder(name, icon="📁", color="#89b4fa", parent_id=None):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO folders (name, icon, color, parent_id) VALUES (?,?,?,?)",
            (name, icon, color, parent_id)
        )
        conn.commit()
        row = conn.execute(
            "SELECT id FROM folders WHERE name=? AND (parent_id IS ? OR parent_id=?)",
            (name, parent_id, parent_id)
        ).fetchone()
        return row["id"] if row else None
    except Exception:
        row = conn.execute("SELECT id FROM folders WHERE name=?", (name,)).fetchone()
        return row["id"] if row else None
    finally:
        conn.close()


def update_folder(folder_id, name=None, icon=None, color=None):
    fields = {}
    if name  is not None: fields["name"]  = name
    if icon  is not None: fields["icon"]  = icon
    if color is not None: fields["color"] = color
    if not fields:
        return
    set_clause = ", ".join(f"{k}=?" for k in fields)
    vals = list(fields.values()) + [folder_id]
    conn = get_connection()
    conn.execute(f"UPDATE folders SET {set_clause} WHERE id=?", vals)
    conn.commit()
    conn.close()


def delete_folder(folder_id):
    conn = get_connection()
    conn.execute("DELETE FROM folders WHERE id=?", (folder_id,))
    conn.commit()
    conn.close()


def assign_document_to_folder(doc_id, folder_id):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO document_folders (document_id, folder_id) VALUES (?,?)",
            (doc_id, folder_id)
        )
        conn.commit()
    finally:
        conn.close()


def remove_document_from_folder(doc_id, folder_id):
    conn = get_connection()
    conn.execute(
        "DELETE FROM document_folders WHERE document_id=? AND folder_id=?",
        (doc_id, folder_id)
    )
    conn.commit()
    conn.close()


def get_folders_for_document(doc_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT f.* FROM folders f "
        "JOIN document_folders df ON f.id=df.folder_id "
        "WHERE df.document_id=?", (doc_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_documents_in_folder(folder_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT d.* FROM documents d "
        "JOIN document_folders df ON d.id=df.document_id "
        "WHERE df.folder_id=? ORDER BY d.name", (folder_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_unfoldered_documents():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM documents WHERE id NOT IN "
        "(SELECT DISTINCT document_id FROM document_folders) ORDER BY name"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def auto_create_folders_from_tags():
    conn = get_connection()
    docs = conn.execute("SELECT id, tags FROM documents WHERE tags != ''").fetchall()
    conn.close()
    for doc in docs:
        for tag in [t.strip() for t in (doc["tags"] or "").split(",") if t.strip()]:
            folder_id = add_folder(tag)
            if folder_id:
                assign_document_to_folder(doc["id"], folder_id)

def get_root_comments(doc_id, category=None, priority=None, status=None, search=None):
    """Solo comentarios raíz (sin parent_id) para un documento."""
    conn = get_connection()
    q      = "SELECT * FROM comments WHERE document_id=? AND parent_id IS NULL"
    params = [doc_id]
    if category and category != "Todas":
        q += " AND category=?"; params.append(category)
    if priority and priority != "Todas":
        q += " AND priority=?"; params.append(priority)
    if status and status != "Todos":
        q += " AND status=?"; params.append(status)
    if search:
        q += " AND (content LIKE ? OR highlighted_text LIKE ? OR author LIKE ?)"
        params += [f"%{search}%", f"%{search}%", f"%{search}%"]
    q += " ORDER BY created_at ASC"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_replies(parent_id):
    """Obtiene todas las respuestas directas a un comentario padre."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM comments WHERE parent_id=? ORDER BY created_at ASC",
        (parent_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def count_replies(parent_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT COUNT(*) as n FROM comments WHERE parent_id=?", (parent_id,)
    ).fetchone()
    conn.close()
    return row["n"] if row else 0


# ─────────────────────────────────────────────────────────────────────────────
# METADATOS NORMATIVOS — migraciones
# ─────────────────────────────────────────────────────────────────────────────

def add_metadatos_normativos():
    """Migración: añade columnas de metadatos normativos a documents."""
    columnas = [
        ("tipo_norma",      "TEXT DEFAULT ''"),
        ("numero_norma",    "TEXT DEFAULT ''"),
        ("entidad_emisora", "TEXT DEFAULT ''"),
        ("fecha_expedicion","TEXT DEFAULT ''"),
        ("fecha_vigencia",  "TEXT DEFAULT ''"),
        ("fecha_derogacion","TEXT DEFAULT ''"),
        ("vigencia_estado", "TEXT DEFAULT 'Por confirmar'"),
    ]
    conn = get_connection()
    for col, defn in columnas:
        try:
            conn.execute(f"ALTER TABLE documents ADD COLUMN {col} {defn}")
        except Exception:
            pass
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# RELACIONES ENTRE DOCUMENTOS
# ─────────────────────────────────────────────────────────────────────────────

def init_relations():
    """Crea la tabla de relaciones entre documentos."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS document_relations (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_origen_id  INTEGER NOT NULL,
            doc_destino_id INTEGER NOT NULL,
            tipo_relacion  TEXT    NOT NULL,
            descripcion    TEXT    DEFAULT '',
            created_at     TEXT    DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(doc_origen_id)  REFERENCES documents(id) ON DELETE CASCADE,
            FOREIGN KEY(doc_destino_id) REFERENCES documents(id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()


def add_relation(doc_origen_id: int, doc_destino_id: int,
                 tipo_relacion: str, descripcion: str = "") -> int:
    conn = get_connection()
    conn.execute(
        "INSERT INTO document_relations (doc_origen_id, doc_destino_id, tipo_relacion, descripcion)"
        " VALUES (?,?,?,?)",
        (doc_origen_id, doc_destino_id, tipo_relacion, descripcion),
    )
    conn.commit()
    row = conn.execute("SELECT last_insert_rowid() as id").fetchone()
    conn.close()
    return row["id"]


def get_relations(doc_id: int) -> list:
    """Devuelve todas las relaciones donde el doc participa (origen o destino)."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT r.*,
               d1.name AS doc_origen_nombre,  d1.tipo_norma AS doc_origen_tipo,
               d1.numero_norma AS doc_origen_numero,
               d2.name AS doc_destino_nombre, d2.tipo_norma AS doc_destino_tipo,
               d2.numero_norma AS doc_destino_numero
        FROM document_relations r
        JOIN documents d1 ON r.doc_origen_id  = d1.id
        JOIN documents d2 ON r.doc_destino_id = d2.id
        WHERE r.doc_origen_id = ? OR r.doc_destino_id = ?
        ORDER BY r.tipo_relacion, r.created_at
    """, (doc_id, doc_id)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_relation(relation_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM document_relations WHERE id=?", (relation_id,))
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# USUARIOS
# ─────────────────────────────────────────────────────────────────────────────

def init_users():
    """Crea la tabla de usuarios."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT UNIQUE NOT NULL,
            password   TEXT NOT NULL,
            nombre     TEXT DEFAULT '',
            email      TEXT DEFAULT '',
            role       TEXT DEFAULT 'lector',
            activo     INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def add_campos_usuario_documento():
    """Migración: añade owner_id y biblioteca a la tabla documents."""
    conn = get_connection()
    for col, defn in [
        ("owner_id",   "INTEGER DEFAULT NULL"),
        ("biblioteca", "TEXT DEFAULT 'general'"),
    ]:
        try:
            conn.execute(f"ALTER TABLE documents ADD COLUMN {col} {defn}")
        except Exception:
            pass
    conn.commit()
    conn.close()


def seed_admin(hashed_password: str):
    """Crea el usuario admin inicial si no existe ningún usuario."""
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) as n FROM users").fetchone()["n"]
    conn.close()
    if count == 0:
        add_user("admin", hashed_password, nombre="Administrador", role="admin")
        print("ℹ️  Usuario admin creado. Usa la contraseña configurada en GESDOC_ADMIN_PASSWORD (defecto: admin123)")


def get_user_by_username(username: str):
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(user_id: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_users():
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, username, nombre, email, role, activo, created_at"
        " FROM users ORDER BY username"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_user(username: str, hashed_password: str,
             nombre: str = "", email: str = "", role: str = "lector") -> int | None:
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users (username, password, nombre, email, role) VALUES (?,?,?,?,?)",
            (username, hashed_password, nombre, email, role),
        )
        conn.commit()
        row = conn.execute("SELECT last_insert_rowid() as id").fetchone()
        return row["id"]
    except Exception:
        return None
    finally:
        conn.close()


def update_user(user_id: int, **kwargs):
    allowed = {"nombre", "email", "role", "activo", "password"}
    fields  = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return
    set_clause = ", ".join(f"{k}=?" for k in fields)
    vals = list(fields.values()) + [user_id]
    conn = get_connection()
    conn.execute(f"UPDATE users SET {set_clause} WHERE id=?", vals)
    conn.commit()
    conn.close()


def delete_user(user_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

