"""
ui/dialogs.py - Dialogs for DocManager
"""
import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QComboBox,
    QDialogButtonBox, QFrame, QSizePolicy, QFileDialog,
    QCheckBox, QGroupBox, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import database as db


class AddCommentDialog(QDialog):
    """Dialog for adding or editing a comment."""

    def __init__(self, parent=None, document=None, highlighted_text="",
                 location_info="", existing_comment=None):
        super().__init__(parent)
        self.document = document
        self.highlighted_text = highlighted_text
        self.location_info = location_info
        self.existing = existing_comment
        self.setWindowTitle("Editar comentario" if existing_comment else "Nuevo comentario")
        self.setMinimumWidth(500)
        self.setMinimumHeight(420)
        self.setModal(True)
        self._setup_ui()
        if existing_comment:
            self._populate(existing_comment)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        icon = "✏️" if self.existing else "💬"
        action = "Editar" if self.existing else "Nuevo"
        title = QLabel(f"{icon} {action} comentario")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        if self.document:
            doc_lbl = QLabel(f"📄 {self.document.get('name', '')}")
            doc_lbl.setObjectName("subtitle")
            layout.addWidget(doc_lbl)

        # Highlight preview
        if self.highlighted_text:
            hl_frame = QFrame()
            hl_frame.setObjectName("highlightBar")
            hl_layout = QVBoxLayout(hl_frame)
            hl_layout.setContentsMargins(8, 6, 8, 6)
            hl_lbl = QLabel(f'🖊 "{self.highlighted_text[:200]}{"..." if len(self.highlighted_text) > 200 else ""}"')
            hl_lbl.setWordWrap(True)
            hl_lbl.setObjectName("subtitle")
            hl_layout.addWidget(hl_lbl)
            layout.addWidget(hl_frame)
        elif self.location_info:
            loc_lbl = QLabel(f"📍 {self.location_info}")
            loc_lbl.setObjectName("subtitle")
            layout.addWidget(loc_lbl)

        # Form
        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        # Comment text
        self.txt_content = QTextEdit()
        self.txt_content.setPlaceholderText("Escribe tu comentario aquí...")
        self.txt_content.setMinimumHeight(100)
        form.addRow("Comentario:", self.txt_content)

        # Category
        self.cmb_category = QComboBox()
        from utils.theme import CATEGORY_ICONS
        for cat in db.COMMENT_CATEGORIES:
            icon_char = CATEGORY_ICONS.get(cat, "•")
            self.cmb_category.addItem(f"{icon_char} {cat}", cat)
        form.addRow("Categoría:", self.cmb_category)

        # Priority
        self.cmb_priority = QComboBox()
        priority_icons = {"Alta": "🔴", "Media": "🟡", "Baja": "🟢"}
        for p in db.COMMENT_PRIORITIES:
            self.cmb_priority.addItem(f"{priority_icons[p]} {p}", p)
        self.cmb_priority.setCurrentIndex(1)  # Media default
        form.addRow("Prioridad:", self.cmb_priority)

        # Status
        self.cmb_status = QComboBox()
        for s in db.COMMENT_STATUSES:
            self.cmb_status.addItem(s, s)
        form.addRow("Estado:", self.cmb_status)

        layout.addLayout(form)

        # Buttons
        btn_box = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        self.btn_save = QPushButton("💾 Guardar")
        self.btn_save.setObjectName("primaryBtn")
        self.btn_save.clicked.connect(self._save)
        btn_box.addStretch()
        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(self.btn_save)
        layout.addLayout(btn_box)

    def _populate(self, comment):
        self.txt_content.setPlainText(comment.get("content", ""))
        cat = comment.get("category", "General")
        for i in range(self.cmb_category.count()):
            if self.cmb_category.itemData(i) == cat:
                self.cmb_category.setCurrentIndex(i)
                break
        pri = comment.get("priority", "Media")
        for i in range(self.cmb_priority.count()):
            if self.cmb_priority.itemData(i) == pri:
                self.cmb_priority.setCurrentIndex(i)
                break
        sts = comment.get("status", "Abierto")
        for i in range(self.cmb_status.count()):
            if self.cmb_status.itemData(i) == sts:
                self.cmb_status.setCurrentIndex(i)
                break

    def _save(self):
        content = self.txt_content.toPlainText().strip()
        if not content:
            QMessageBox.warning(self, "Campo requerido", "Por favor escribe un comentario.")
            return
        self.accept()

    def get_data(self):
        return {
            "content": self.txt_content.toPlainText().strip(),
            "category": self.cmb_category.currentData(),
            "priority": self.cmb_priority.currentData(),
            "status": self.cmb_status.currentData(),
            "highlighted_text": self.highlighted_text,
            "location_info": self.location_info,
        }


class DocumentInfoDialog(QDialog):
    """Dialog to view/edit document metadata."""

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

        # Name (editable)
        self.txt_name = QLineEdit(self.document.get("name", ""))
        form.addRow("Nombre:", self.txt_name)

        # Path (readonly)
        path_lbl = QLabel(self.document.get("path", "—"))
        path_lbl.setWordWrap(True)
        path_lbl.setObjectName("subtitle")
        form.addRow("Ruta:", path_lbl)

        # Format
        fmt_lbl = QLabel(self.document.get("format", "—").upper())
        form.addRow("Formato:", fmt_lbl)

        # Status
        self.cmb_status = QComboBox()
        for s in db.DOCUMENT_STATUSES:
            self.cmb_status.addItem(s, s)
        cur = self.document.get("status", "Por revisar")
        idx = db.DOCUMENT_STATUSES.index(cur) if cur in db.DOCUMENT_STATUSES else 0
        self.cmb_status.setCurrentIndex(idx)
        form.addRow("Estado:", self.cmb_status)

        # Tags
        self.txt_tags = QLineEdit(self.document.get("tags", ""))
        self.txt_tags.setPlaceholderText("Ej: manual, python, revisión")
        form.addRow("Etiquetas:", self.txt_tags)

        # Added date
        added = self.document.get("added_at", "—")
        if added and len(added) > 10:
            added = added[:16].replace("T", " ")
        form.addRow("Añadido:", QLabel(added))

        # Last opened
        last = self.document.get("last_opened", "Nunca")
        if last and len(last) > 10:
            last = last[:16].replace("T", " ")
        form.addRow("Último acceso:", QLabel(last or "Nunca"))

        layout.addLayout(form)

        # Buttons
        btn_box = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("💾 Guardar cambios")
        btn_save.setObjectName("primaryBtn")
        btn_save.clicked.connect(self.accept)
        btn_box.addStretch()
        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_save)
        layout.addLayout(btn_box)

    def get_data(self):
        return {
            "name": self.txt_name.text().strip(),
            "status": self.cmb_status.currentData(),
            "tags": self.txt_tags.text().strip(),
        }


class ExportDialog(QDialog):
    """Export comments dialog."""

    def __init__(self, parent=None, documents=None):
        super().__init__(parent)
        self.documents = documents or []
        self.setWindowTitle("Exportar comentarios")
        self.setMinimumWidth(440)
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

        # Scope
        self.cmb_scope = QComboBox()
        self.cmb_scope.addItem("Todos los documentos", None)
        for doc in self.documents:
            self.cmb_scope.addItem(f"📄 {doc['name']}", doc["id"])
        form.addRow("Documentos:", self.cmb_scope)

        # Format
        self.cmb_format = QComboBox()
        self.cmb_format.addItem("📊 Excel (.xlsx)", "xlsx")
        self.cmb_format.addItem("📄 PDF (.pdf)", "pdf")
        form.addRow("Formato:", self.cmb_format)

        # Output path
        path_row = QHBoxLayout()
        self.txt_path = QLineEdit()
        self.txt_path.setPlaceholderText("Selecciona dónde guardar...")
        self.txt_path.setReadOnly(True)
        btn_browse = QPushButton("...")
        btn_browse.setFixedWidth(36)
        btn_browse.clicked.connect(self._browse)
        path_row.addWidget(self.txt_path)
        path_row.addWidget(btn_browse)
        form.addRow("Guardar en:", path_row)

        layout.addLayout(form)

        # Buttons
        btn_box = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        self.btn_export = QPushButton("📤 Exportar")
        self.btn_export.setObjectName("primaryBtn")
        self.btn_export.clicked.connect(self._validate_and_accept)
        btn_box.addStretch()
        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(self.btn_export)
        layout.addLayout(btn_box)

    def _browse(self):
        fmt = self.cmb_format.currentData()
        ext_filter = "Excel (*.xlsx)" if fmt == "xlsx" else "PDF (*.pdf)"
        default_ext = ".xlsx" if fmt == "xlsx" else ".pdf"
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar exportación", f"comentarios{default_ext}", ext_filter
        )
        if path:
            self.txt_path.setText(path)

    def _validate_and_accept(self):
        if not self.txt_path.text():
            QMessageBox.warning(self, "Ruta requerida", "Selecciona dónde guardar el archivo.")
            return
        self.accept()

    def get_data(self):
        return {
            "doc_id": self.cmb_scope.currentData(),
            "format": self.cmb_format.currentData(),
            "path": self.txt_path.text(),
        }
