# -*- coding: utf-8 -*-
"""ui/dialogs.py — Dialogs for DocManager"""
import os
import re
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QComboBox,
    QFrame, QSizePolicy, QFileDialog, QScrollArea,
    QWidget, QMessageBox, QCheckBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
import database as db


# ─────────────────────────────────────────────────────────────────────────────
# AddCommentDialog
# ─────────────────────────────────────────────────────────────────────────────

class AddCommentDialog(QDialog):
    """Dialog for adding or editing a comment."""

    def __init__(self, parent=None, document=None, highlighted_text="",
                 location_info="", existing_comment=None):
        super().__init__(parent)
        self.document          = document
        self.highlighted_text  = highlighted_text or ""
        self.location_info     = location_info or ""
        self.existing          = existing_comment

        self.setWindowTitle("Editar comentario" if existing_comment else "Nuevo comentario")
        self.setMinimumWidth(560)
        self.setMinimumHeight(560)
        self.setModal(True)
        self._setup_ui()
        if existing_comment:
            self._populate(existing_comment)

    # ─── UI ──────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        # ── Blue header bar ───────────────────────────────────────────────────
        hdr = QFrame()
        hdr.setStyleSheet("QFrame{background:#1e3a5f;}")
        hl = QVBoxLayout(hdr)
        hl.setContentsMargins(18, 12, 18, 12)
        hl.setSpacing(2)

        icon   = "✏️" if self.existing else "💬"
        action = "Editar" if self.existing else "Nuevo"
        lbl_t = QLabel(f"{icon}  {action} comentario")
        lbl_t.setStyleSheet(
            "color:white;font-size:15px;font-weight:bold;background:transparent;")
        hl.addWidget(lbl_t)

        if self.document:
            lbl_d = QLabel(f"📄  {self.document.get('name','')}")
            lbl_d.setStyleSheet("color:#89b4fa;font-size:11px;background:transparent;")
            hl.addWidget(lbl_d)

        root.addWidget(hdr)

        # ── Scrollable body ───────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")

        body = QWidget()
        body.setStyleSheet("background:transparent;")
        bl = QVBoxLayout(body)
        bl.setSpacing(14)
        bl.setContentsMargins(18, 16, 18, 16)

        # ── Form fields ───────────────────────────────────────────────────────
        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        # Author — plain QLineEdit, straightforward
        self.txt_author = QLineEdit()
        self.txt_author.setPlaceholderText("Nombre de quien hace el comentario")
        self.txt_author.setMinimumHeight(30)
        form.addRow("👤  Autor:", self.txt_author)

        # Page number
        page_box = QHBoxLayout()
        page_box.setSpacing(6)
        self.txt_page = QLineEdit()
        self.txt_page.setPlaceholderText("Ej: 5")
        self.txt_page.setFixedWidth(72)
        self.txt_page.setMinimumHeight(30)
        self.txt_page.setText(self._extract_page(self.location_info))
        hint = QLabel("número de página")
        hint.setStyleSheet("color:#888;font-size:11px;")
        page_box.addWidget(self.txt_page)
        page_box.addWidget(hint)
        page_box.addStretch()
        form.addRow("📄  Página:", page_box)

        # Category
        self.cmb_category = QComboBox()
        self.cmb_category.setMinimumHeight(30)
        from utils.theme import CATEGORY_ICONS
        for cat in db.COMMENT_CATEGORIES:
            self.cmb_category.addItem(f"{CATEGORY_ICONS.get(cat,'•')}  {cat}", cat)
        form.addRow("🏷  Categoría:", self.cmb_category)

        # Priority
        self.cmb_priority = QComboBox()
        self.cmb_priority.setMinimumHeight(30)
        for p, ico in [("Alta","🔴"), ("Media","🟡"), ("Baja","🟢")]:
            self.cmb_priority.addItem(f"{ico}  {p}", p)
        self.cmb_priority.setCurrentIndex(1)
        form.addRow("⚡  Prioridad:", self.cmb_priority)

        # Status
        self.cmb_status = QComboBox()
        self.cmb_status.setMinimumHeight(30)
        for s in db.COMMENT_STATUSES:
            self.cmb_status.addItem(s, s)
        form.addRow("◆  Estado:", self.cmb_status)

        bl.addLayout(form)

        # ── Highlighted text ──────────────────────────────────────────────────
        self._add_section_label(bl, "🖊  Texto resaltado")

        hl_hint = QLabel(
            "Escribe o pega aquí el fragmento del documento al que se refiere el comentario.\n"
            "En PDFs: usa el botón  📋 Copiar texto  en la barra del visor, luego pega aquí."
        )
        hl_hint.setStyleSheet("color:#888;font-size:11px;")
        hl_hint.setWordWrap(True)
        bl.addWidget(hl_hint)

        self.txt_highlight = QTextEdit()
        self.txt_highlight.setPlaceholderText(
            "Fragmento del texto al que aplica este comentario (opcional)..."
        )
        self.txt_highlight.setFixedHeight(72)
        self.txt_highlight.setPlainText(self.highlighted_text)
        bl.addWidget(self.txt_highlight)

        # ── Comment body ──────────────────────────────────────────────────────
        self._add_section_label(bl, "💬  Comentario  *")

        self.txt_content = QTextEdit()
        self.txt_content.setPlaceholderText("Escribe el comentario aquí...")
        self.txt_content.setMinimumHeight(110)
        bl.addWidget(self.txt_content)

        bl.addStretch()
        scroll.setWidget(body)
        root.addWidget(scroll)

        # ── Footer buttons ────────────────────────────────────────────────────
        ftr = QFrame()
        ftr.setStyleSheet("QFrame{border-top:1px solid #45475a;}")
        fl = QHBoxLayout(ftr)
        fl.setContentsMargins(18, 8, 18, 10)
        fl.setSpacing(8)

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setMinimumHeight(32)
        btn_cancel.clicked.connect(self.reject)

        self.btn_save = QPushButton("💾  Guardar")
        self.btn_save.setObjectName("primaryBtn")
        self.btn_save.setMinimumHeight(32)
        self.btn_save.setMinimumWidth(110)
        self.btn_save.clicked.connect(self._save)

        fl.addStretch()
        fl.addWidget(btn_cancel)
        fl.addWidget(self.btn_save)
        root.addWidget(ftr)

    def _add_section_label(self, layout, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("font-weight:bold;font-size:12px;margin-top:4px;")
        layout.addWidget(lbl)

    # ─── Helpers ─────────────────────────────────────────────────────────────

    def _extract_page(self, location_info):
        if not location_info:
            return ""
        # Match "Página 5", "Pag 5", "Pag. 5", etc.
        m = re.search(r'P[a\xe1]g(?:ina)?[\s.:]*(\d+)', location_info, re.IGNORECASE)
        if m:
            return m.group(1)
        # Fallback: first number
        m = re.search(r'(\d+)', location_info)
        return m.group(1) if m else ""

    def _populate(self, comment):
        """Fill form with existing comment data when editing."""
        self.txt_author.setText(comment.get("author", "") or "")
        self.txt_content.setPlainText(comment.get("content", "") or "")
        self.txt_highlight.setPlainText(comment.get("highlighted_text", "") or "")

        loc = comment.get("location_info", "") or ""
        self.txt_page.setText(self._extract_page(loc))

        for cmb, key, default in [
            (self.cmb_category, "category", "General"),
            (self.cmb_priority, "priority", "Media"),
            (self.cmb_status,   "status",   "Abierto"),
        ]:
            val = comment.get(key, default)
            for i in range(cmb.count()):
                if cmb.itemData(i) == val:
                    cmb.setCurrentIndex(i)
                    break

    def _save(self):
        if not self.txt_content.toPlainText().strip():
            QMessageBox.warning(self, "Campo requerido",
                                "El campo  Comentario  no puede estar vacío.")
            return
        self.accept()

    def get_data(self):
        page = self.txt_page.text().strip()
        if page:
            loc = f"Pagina {page}"   # ASCII-safe, _extract_page handles both spellings
        else:
            loc = self.location_info or ""

        return {
            "author":           self.txt_author.text().strip(),
            "content":          self.txt_content.toPlainText().strip(),
            "category":         self.cmb_category.currentData(),
            "priority":         self.cmb_priority.currentData(),
            "status":           self.cmb_status.currentData(),
            "highlighted_text": self.txt_highlight.toPlainText().strip(),
            "location_info":    loc,
            "page":             int(page) if page.isdigit() else None,
        }


# ─────────────────────────────────────────────────────────────────────────────
# ViewCommentDialog  —  read-only full view
# ─────────────────────────────────────────────────────────────────────────────

class ViewCommentDialog(QDialog):
    """Read-only, full-content view of a comment."""

    def __init__(self, comment, parent=None):
        super().__init__(parent)
        self.comment = comment
        self.setWindowTitle("Ver comentario")
        self.setMinimumWidth(500)
        self.setMaximumWidth(640)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        c = self.comment

        # ── Coloured header chips ─────────────────────────────────────────────
        hdr = QFrame()
        hdr.setStyleSheet("QFrame{background:#1e3a5f;}")
        hl = QVBoxLayout(hdr)
        hl.setContentsMargins(16, 12, 16, 12)
        hl.setSpacing(6)

        lbl_t = QLabel("👁  Ver comentario completo")
        lbl_t.setStyleSheet(
            "color:white;font-size:14px;font-weight:bold;background:transparent;")
        hl.addWidget(lbl_t)

        chip_row = QHBoxLayout()
        chip_row.setSpacing(6)
        chip_colors = {
            c.get("category",""): "#89b4fa",
            c.get("priority",""): "#fab387",
            c.get("status",""):   "#a6e3a1",
        }
        for text, color in chip_colors.items():
            if text:
                chip = QLabel(f"  {text}  ")
                chip.setStyleSheet(
                    f"background:{color};color:#1e1e2e;border-radius:10px;"
                    f"font-size:11px;font-weight:bold;padding:2px 0;")
                chip_row.addWidget(chip)
        chip_row.addStretch()
        hl.addLayout(chip_row)
        root.addWidget(hdr)

        # ── Scrollable body ───────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea{border:none;}")

        body = QWidget()
        bl = QVBoxLayout(body)
        bl.setSpacing(12)
        bl.setContentsMargins(18, 14, 18, 14)

        def field(label, value):
            if not value:
                return
            lbl = QLabel(f"<b>{label}</b>")
            lbl.setStyleSheet("font-size:11px;color:#888;margin-bottom:1px;")
            val = QLabel(str(value))
            val.setWordWrap(True)
            val.setStyleSheet("font-size:13px;")
            bl.addWidget(lbl)
            bl.addWidget(val)
            self._separator(bl)

        field("👤 Autor",      c.get("author"))
        field("📍 Página",     c.get("location_info"))
        field("📅 Fecha",      (c.get("created_at") or "")[:16])

        # Highlighted text in a coloured box
        hl_text = c.get("highlighted_text", "")
        if hl_text:
            lbl_h = QLabel("<b>🖊  Texto resaltado</b>")
            lbl_h.setStyleSheet("font-size:11px;color:#888;")
            bl.addWidget(lbl_h)
            hl_box = QLabel(hl_text)
            hl_box.setWordWrap(True)
            hl_box.setStyleSheet(
                "background:#2a2a3a;color:#a6e3a1;border-left:3px solid #89b4fa;"
                "padding:8px 10px;font-family:'Times New Roman';font-size:12px;"
                "font-style:italic;border-radius:0 4px 4px 0;"
            )
            bl.addWidget(hl_box)
            self._separator(bl)

        # Main comment text
        lbl_c = QLabel("<b>💬  Comentario</b>")
        lbl_c.setStyleSheet("font-size:11px;color:#888;")
        bl.addWidget(lbl_c)
        txt = QTextEdit()
        txt.setReadOnly(True)
        txt.setPlainText(c.get("content", ""))
        txt.setMinimumHeight(140)
        txt.setStyleSheet(
            "background:#181825;color:#cdd6f4;border:1px solid #313244;"
            "border-radius:4px;padding:6px;"
            "font-family:'Times New Roman';font-size:13px;"
        )
        bl.addWidget(txt)

        bl.addStretch()
        scroll.setWidget(body)
        root.addWidget(scroll)

        # ── Close button ──────────────────────────────────────────────────────
        ftr = QFrame()
        ftr.setStyleSheet("QFrame{border-top:1px solid #45475a;}")
        fl = QHBoxLayout(ftr)
        fl.setContentsMargins(16, 8, 16, 10)
        btn = QPushButton("Cerrar")
        btn.setMinimumHeight(30)
        btn.clicked.connect(self.accept)
        fl.addStretch()
        fl.addWidget(btn)
        root.addWidget(ftr)

    def _separator(self, layout):
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color:#313244;max-height:1px;background:#313244;")
        layout.addWidget(sep)


# ─────────────────────────────────────────────────────────────────────────────
# DocumentInfoDialog
# ─────────────────────────────────────────────────────────────────────────────

class DocumentInfoDialog(QDialog):

    def __init__(self, parent=None, document=None):
        super().__init__(parent)
        self.document = document or {}
        self.setWindowTitle("Información del documento")
        self.setMinimumWidth(460)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("📋 Información del documento")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.txt_name = QLineEdit(self.document.get("name", ""))
        form.addRow("Nombre:", self.txt_name)

        path_val = self.document.get("path", "")
        lbl_path = QLabel(path_val)
        lbl_path.setWordWrap(True)
        lbl_path.setObjectName("subtitle")
        form.addRow("Ruta:", lbl_path)

        fmt = self.document.get("format", "").upper()
        form.addRow("Formato:", QLabel(fmt))

        self.txt_tags = QLineEdit(self.document.get("tags", ""))
        self.txt_tags.setPlaceholderText("tag1, tag2, tag3")
        form.addRow("Etiquetas:", self.txt_tags)

        self.cmb_status = QComboBox()
        for s in db.DOCUMENT_STATUSES:
            self.cmb_status.addItem(s, s)
        cur = self.document.get("status", db.DOCUMENT_STATUSES[0])
        for i in range(self.cmb_status.count()):
            if self.cmb_status.itemData(i) == cur:
                self.cmb_status.setCurrentIndex(i)
                break
        form.addRow("Estado:", self.cmb_status)

        added = (self.document.get("added_at") or "")[:16]
        opened = (self.document.get("last_opened") or "")[:16]
        if added:
            form.addRow("Añadido:", QLabel(added))
        if opened:
            form.addRow("Último acceso:", QLabel(opened))

        layout.addLayout(form)

        btn_box = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("💾 Guardar")
        btn_save.setObjectName("primaryBtn")
        btn_save.clicked.connect(self.accept)
        btn_box.addStretch()
        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_save)
        layout.addLayout(btn_box)

    def get_data(self):
        return {
            "name":   self.txt_name.text().strip(),
            "tags":   self.txt_tags.text().strip(),
            "status": self.cmb_status.currentData(),
        }


# ─────────────────────────────────────────────────────────────────────────────
# ExportDialog
# ─────────────────────────────────────────────────────────────────────────────

class ExportDialog(QDialog):

    def __init__(self, parent=None, documents=None):
        super().__init__(parent)
        self.documents = documents or []
        self.setWindowTitle("Exportar comentarios")
        self.setMinimumWidth(420)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("📤 Exportar comentarios")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.cmb_doc = QComboBox()
        self.cmb_doc.addItem("Todos los documentos", None)
        for doc in self.documents:
            self.cmb_doc.addItem(doc.get("name", ""), doc.get("id"))
        form.addRow("Documento:", self.cmb_doc)

        self.cmb_format = QComboBox()
        self.cmb_format.addItem("Excel (.xlsx)", "xlsx")
        self.cmb_format.addItem("PDF (.pdf)",    "pdf")
        form.addRow("Formato:", self.cmb_format)

        layout.addLayout(form)

        path_row = QHBoxLayout()
        self.txt_path = QLineEdit()
        self.txt_path.setPlaceholderText("Selecciona dónde guardar el archivo...")
        btn_browse = QPushButton("📂 Examinar")
        btn_browse.clicked.connect(self._browse)
        path_row.addWidget(self.txt_path)
        path_row.addWidget(btn_browse)
        layout.addLayout(path_row)

        btn_box = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_export = QPushButton("📤 Exportar")
        btn_export.setObjectName("primaryBtn")
        btn_export.clicked.connect(self._do_export)
        btn_box.addStretch()
        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_export)
        layout.addLayout(btn_box)

    def _browse(self):
        fmt = self.cmb_format.currentData()
        ext = "Excel (*.xlsx)" if fmt == "xlsx" else "PDF (*.pdf)"
        path, _ = QFileDialog.getSaveFileName(self, "Guardar exportación", "", ext)
        if path:
            self.txt_path.setText(path)

    def _do_export(self):
        if not self.txt_path.text().strip():
            QMessageBox.warning(self, "Ruta requerida",
                                "Selecciona dónde guardar el archivo.")
            return
        self.accept()

    def get_data(self):
        return {
            "doc_id": self.cmb_doc.currentData(),
            "format": self.cmb_format.currentData(),
            "path":   self.txt_path.text().strip(),
        }
