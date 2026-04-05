"""
ui/library_panel.py - Left sidebar with collapsible folder tree + document list.

Structure:
  📁 Carpeta A          ← folder node (collapsible)
    📕 documento1.pdf
    📘 documento2.docx
  📁 Carpeta B
    📗 guia.md
  📂 Sin carpeta        ← unfoldered documents
    📄 notas.txt
"""
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QTreeWidget, QTreeWidgetItem, QMenu, QAction,
    QComboBox, QFrame, QFileDialog, QMessageBox, QDialog,
    QFormLayout, QDialogButtonBox, QListWidget, QListWidgetItem,
    QCheckBox, QScrollArea, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QColor, QBrush, QIcon

import database as db
from utils.theme import DOC_STATUS_COLORS

FORMAT_ICONS = {"pdf": "📕", "docx": "📘", "doc": "📘", "md": "📗", "txt": "📄"}
FOLDER_COLORS = [
    "#89b4fa", "#cba6f7", "#f38ba8", "#fab387",
    "#f9e2af", "#a6e3a1", "#94e2d5", "#89dceb",
]

def _fmt_icon(fmt):
    return FORMAT_ICONS.get(fmt.lower(), "📄")


# ─────────────────────────────────────────────────────────────────────────────
# Dialog: create / rename folder
# ─────────────────────────────────────────────────────────────────────────────

class FolderDialog(QDialog):
    def __init__(self, parent=None, existing_name="", existing_icon="📁", existing_color="#89b4fa"):
        super().__init__(parent)
        self.setWindowTitle("Nueva carpeta" if not existing_name else "Renombrar carpeta")
        self.setMinimumWidth(360)
        self.setModal(True)
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(18, 18, 18, 18)

        title = QLabel("📁 " + ("Nueva carpeta" if not existing_name else "Editar carpeta"))
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        self.txt_name = QLineEdit(existing_name)
        self.txt_name.setPlaceholderText("Ej: Manuales, Proyectos, Revisión...")
        form.addRow("Nombre:", self.txt_name)

        # Icon picker
        icon_row = QHBoxLayout()
        icon_row.setSpacing(4)
        self._icon_btns = []
        icons = ["📁","📂","🗂","📚","📋","🗃","📌","🏷","⭐","🔖","💼","🔬","📐","🧩"]
        self._selected_icon = existing_icon
        for ic in icons:
            b = QPushButton(ic)
            b.setFixedSize(32, 32)
            b.setCheckable(True)
            b.setChecked(ic == existing_icon)
            b.clicked.connect(lambda checked, i=ic: self._pick_icon(i))
            icon_row.addWidget(b)
            self._icon_btns.append((ic, b))
        icon_row.addStretch()
        form.addRow("Icono:", icon_row)

        # Color picker
        color_row = QHBoxLayout()
        color_row.setSpacing(4)
        self._color_btns = []
        self._selected_color = existing_color
        for col in FOLDER_COLORS:
            b = QPushButton()
            b.setFixedSize(24, 24)
            b.setStyleSheet(
                f"background:{col};border-radius:12px;border:2px solid "
                f"{'#fff' if col == existing_color else 'transparent'};"
            )
            b.clicked.connect(lambda checked, c=col: self._pick_color(c))
            color_row.addWidget(b)
            self._color_btns.append((col, b))
        color_row.addStretch()
        form.addRow("Color:", color_row)

        layout.addLayout(form)

        btns = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_ok = QPushButton("💾 Guardar")
        btn_ok.setObjectName("primaryBtn")
        btn_ok.clicked.connect(self._validate)
        btns.addStretch()
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_ok)
        layout.addLayout(btns)

    def _pick_icon(self, icon):
        self._selected_icon = icon
        for ic, b in self._icon_btns:
            b.setChecked(ic == icon)

    def _pick_color(self, color):
        self._selected_color = color
        for col, b in self._color_btns:
            b.setStyleSheet(
                f"background:{col};border-radius:12px;border:2px solid "
                f"{'#fff' if col == color else 'transparent'};"
            )

    def _validate(self):
        if not self.txt_name.text().strip():
            QMessageBox.warning(self, "Campo requerido", "Escribe un nombre para la carpeta.")
            return
        self.accept()

    def get_data(self):
        return {
            "name": self.txt_name.text().strip(),
            "icon": self._selected_icon,
            "color": self._selected_color,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Dialog: assign document to folders
# ─────────────────────────────────────────────────────────────────────────────

class AssignFoldersDialog(QDialog):
    def __init__(self, parent=None, document=None, all_folders=None, current_folders=None):
        super().__init__(parent)
        self.setWindowTitle("Asignar a carpetas")
        self.setMinimumWidth(340)
        self.setModal(True)
        self._doc = document or {}
        self._all  = all_folders or []
        self._curr = {f["id"] for f in (current_folders or [])}
        self._checks = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(18, 18, 18, 18)

        title = QLabel(f"📁 Carpetas para\n{self._doc.get('name','')}")
        title.setObjectName("sectionTitle")
        title.setWordWrap(True)
        layout.addWidget(title)

        if not self._all:
            layout.addWidget(QLabel("No hay carpetas creadas aún.\nCrea una desde el panel de biblioteca."))
        else:
            for folder in self._all:
                cb = QCheckBox(f"{folder['icon']} {folder['name']}")
                cb.setChecked(folder["id"] in self._curr)
                cb.setStyleSheet(f"color:{folder.get('color','#89b4fa')};font-size:14px;")
                self._checks[folder["id"]] = cb
                layout.addWidget(cb)

        btns = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_ok = QPushButton("✅ Aplicar")
        btn_ok.setObjectName("primaryBtn")
        btn_ok.clicked.connect(self.accept)
        btns.addStretch()
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_ok)
        layout.addLayout(btns)

    def get_selected_ids(self):
        return {fid for fid, cb in self._checks.items() if cb.isChecked()}


# ─────────────────────────────────────────────────────────────────────────────
# LibraryPanel — main widget
# ─────────────────────────────────────────────────────────────────────────────

# TreeWidget item type constants
TYPE_FOLDER   = 1001
TYPE_DOCUMENT = 1002
TYPE_UNFILED  = 1003   # "Sin carpeta" header


class LibraryPanel(QWidget):
    document_selected = pyqtSignal(dict)
    document_removed  = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._documents = []
        self._setup_ui()
        db.init_folders()
        db.auto_create_folders_from_tags()
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # ── Header ────────────────────────────────────────────────────────────
        header = QHBoxLayout()
        lbl = QLabel("📚 Biblioteca")
        lbl.setObjectName("sectionTitle")

        btn_add_doc = QPushButton("➕ Doc")
        btn_add_doc.setObjectName("primaryBtn")
        btn_add_doc.setFixedHeight(28)
        btn_add_doc.setToolTip("Añadir documentos")
        btn_add_doc.clicked.connect(self.add_documents)

        btn_add_folder = QPushButton("📁 Carpeta")
        btn_add_folder.setFixedHeight(28)
        btn_add_folder.setToolTip("Crear nueva carpeta")
        btn_add_folder.clicked.connect(self._create_folder)

        header.addWidget(lbl)
        header.addStretch()
        header.addWidget(btn_add_doc)
        header.addWidget(btn_add_folder)
        layout.addLayout(header)

        # ── Search ────────────────────────────────────────────────────────────
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 Buscar documentos o carpetas...")
        self.txt_search.textChanged.connect(self.refresh)
        layout.addWidget(self.txt_search)

        # ── Filters ───────────────────────────────────────────────────────────
        filter_row = QHBoxLayout()
        filter_row.setSpacing(4)

        self.cmb_status = QComboBox()
        self.cmb_status.addItem("Todos", "")
        for s in db.DOCUMENT_STATUSES:
            self.cmb_status.addItem(s, s)
        self.cmb_status.currentIndexChanged.connect(self.refresh)

        self.cmb_format = QComboBox()
        self.cmb_format.addItem("Formato", "")
        for fmt in ["pdf", "docx", "md", "txt"]:
            self.cmb_format.addItem(fmt.upper(), fmt)
        self.cmb_format.currentIndexChanged.connect(self.refresh)

        filter_row.addWidget(self.cmb_status)
        filter_row.addWidget(self.cmb_format)
        layout.addLayout(filter_row)

        # ── View toggle ───────────────────────────────────────────────────────
        view_row = QHBoxLayout()
        view_row.setSpacing(4)
        self.lbl_count = QLabel("0 documentos")
        self.lbl_count.setObjectName("subtitle")

        self.btn_expand_all   = QPushButton("⊞")
        self.btn_expand_all.setFixedSize(26, 22)
        self.btn_expand_all.setToolTip("Expandir todo")
        self.btn_expand_all.clicked.connect(lambda: self.tree.expandAll())

        self.btn_collapse_all = QPushButton("⊟")
        self.btn_collapse_all.setFixedSize(26, 22)
        self.btn_collapse_all.setToolTip("Colapsar todo")
        self.btn_collapse_all.clicked.connect(lambda: self.tree.collapseAll())

        view_row.addWidget(self.lbl_count)
        view_row.addStretch()
        view_row.addWidget(self.btn_expand_all)
        view_row.addWidget(self.btn_collapse_all)
        layout.addLayout(view_row)

        # ── Tree widget ───────────────────────────────────────────────────────
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tree.setIndentation(18)
        self.tree.setAnimated(True)
        self.tree.setExpandsOnDoubleClick(True)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._context_menu)
        self.tree.itemClicked.connect(self._on_item_clicked)
        self.tree.setStyleSheet("""
            QTreeWidget::item { padding: 4px 2px; border-radius: 4px; }
            QTreeWidget::item:selected {
                background: #313244; color: #89b4fa;
            }
            QTreeWidget::item:hover:!selected { background: #25253a; }
            QTreeWidget::branch:has-children:!has-siblings:closed,
            QTreeWidget::branch:closed:has-children:has-siblings {
                image: none;
            }
            QTreeWidget::branch:open:has-children:!has-siblings,
            QTreeWidget::branch:open:has-children:has-siblings {
                image: none;
            }
        """)
        layout.addWidget(self.tree)

        # ── FTS section ───────────────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color:#313244;")
        layout.addWidget(sep)

        lbl_fts = QLabel("🔍 Buscar en contenido")
        lbl_fts.setObjectName("sectionTitle")
        lbl_fts.setFont(QFont("Times New Roman", 12, QFont.Bold))
        layout.addWidget(lbl_fts)

        fts_row = QHBoxLayout()
        self.txt_fts = QLineEdit()
        self.txt_fts.setPlaceholderText("Texto dentro de los docs...")
        self.txt_fts.returnPressed.connect(self._fts_search)
        btn_fts = QPushButton("Buscar")
        btn_fts.setFixedWidth(60)
        btn_fts.clicked.connect(self._fts_search)
        fts_row.addWidget(self.txt_fts)
        fts_row.addWidget(btn_fts)
        layout.addLayout(fts_row)

        self.fts_results = QTreeWidget()
        self.fts_results.setHeaderHidden(True)
        self.fts_results.setMaximumHeight(120)
        self.fts_results.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.fts_results.itemClicked.connect(self._on_fts_clicked)
        layout.addWidget(self.fts_results)

    # ─── Public API ───────────────────────────────────────────────────────────

    def refresh(self):
        """Rebuild the entire tree."""
        query       = self.txt_search.text().strip().lower()
        status_f    = self.cmb_status.currentData()
        fmt_f       = self.cmb_format.currentData()

        self._documents = db.get_all_documents()
        all_folders     = db.get_all_folders()

        def _matches(doc):
            return (
                (not query or query in doc["name"].lower()
                           or query in (doc.get("tags") or "").lower())
                and (not status_f or doc.get("status") == status_f)
                and (not fmt_f   or doc.get("format","").lower() == fmt_f)
            )

        self.tree.blockSignals(True)
        # Remember which folders were expanded
        expanded_ids = set()
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            node = root.child(i)
            fid = node.data(0, Qt.UserRole + 1)
            if node.isExpanded() and fid is not None:
                expanded_ids.add(fid)

        self.tree.clear()
        total_docs = 0

        # ── Folder nodes ──────────────────────────────────────────────────────
        for folder in all_folders:
            docs = db.get_documents_in_folder(folder["id"])
            visible = [d for d in docs if _matches(d)]
            # If searching, skip empty folders
            if query and not visible:
                continue

            folder_item = QTreeWidgetItem(self.tree)
            folder_item.setData(0, Qt.UserRole,     None)       # no doc_id
            folder_item.setData(0, Qt.UserRole + 1, folder["id"])
            folder_item.setData(0, Qt.UserRole + 2, TYPE_FOLDER)

            count_str = f" ({len(visible)})" if visible else " (vacía)"
            folder_item.setText(0, f"{folder['icon']} {folder['name']}{count_str}")
            folder_item.setFont(0, QFont("Times New Roman", 13, QFont.Bold))
            folder_item.setForeground(0, QBrush(QColor(folder.get("color", "#89b4fa"))))
            folder_item.setFlags(folder_item.flags() & ~Qt.ItemIsSelectable)

            # Restore expanded state
            should_expand = (folder["id"] in expanded_ids) or (not expanded_ids)
            folder_item.setExpanded(should_expand)

            for doc in visible:
                self._add_doc_item(folder_item, doc)
                total_docs += 1

        # ── Unfiled documents ─────────────────────────────────────────────────
        unfiled = [d for d in db.get_unfoldered_documents() if _matches(d)]
        if unfiled:
            unfiled_item = QTreeWidgetItem(self.tree)
            unfiled_item.setData(0, Qt.UserRole,     None)
            unfiled_item.setData(0, Qt.UserRole + 1, -1)        # special id
            unfiled_item.setData(0, Qt.UserRole + 2, TYPE_UNFILED)
            unfiled_item.setText(0, f"📂 Sin carpeta ({len(unfiled)})")
            unfiled_item.setFont(0, QFont("Times New Roman", 13, QFont.Bold))
            unfiled_item.setForeground(0, QBrush(QColor("#6c7086")))
            unfiled_item.setFlags(unfiled_item.flags() & ~Qt.ItemIsSelectable)
            unfiled_item.setExpanded(-1 in expanded_ids or not expanded_ids)

            for doc in unfiled:
                self._add_doc_item(unfiled_item, doc)
                total_docs += 1

        self.tree.blockSignals(False)
        self.lbl_count.setText(f"{total_docs} documento{'s' if total_docs!=1 else ''}")

    def _add_doc_item(self, parent_item, doc):
        item = QTreeWidgetItem(parent_item)
        item.setData(0, Qt.UserRole,     doc["id"])
        item.setData(0, Qt.UserRole + 1, None)
        item.setData(0, Qt.UserRole + 2, TYPE_DOCUMENT)

        fmt    = doc.get("format","txt")
        icon   = _fmt_icon(fmt)
        status = doc.get("status","Por revisar")
        name   = doc.get("name","")
        short  = name[:32] + "…" if len(name) > 32 else name

        # Status dot
        dot_color = DOC_STATUS_COLORS.get(status, "#89b4fa")
        item.setText(0, f"  {icon} {short}")
        item.setFont(0, QFont("Times New Roman", 13))
        item.setForeground(0, QBrush(QColor("#cdd6f4")))
        item.setToolTip(0,
            f"Nombre: {name}\n"
            f"Estado: {status}\n"
            f"Formato: {fmt.upper()}\n"
            f"Ruta: {doc.get('path','')}\n"
            + (f"Etiquetas: {doc['tags']}" if doc.get('tags') else "")
        )
        return item

    def add_documents(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Seleccionar documentos", "",
            "Documentos (*.pdf *.docx *.doc *.md *.txt);;Todos (*)"
        )
        added = []
        for path in paths:
            if not os.path.isfile(path):
                continue
            name = os.path.basename(path)
            fmt  = os.path.splitext(path)[1].lstrip(".").lower()
            doc_id = db.add_document(name, path, fmt)
            if doc_id:
                added.append(doc_id)
        if added:
            # Ask which folder
            all_folders = db.get_all_folders()
            if all_folders:
                from PyQt5.QtWidgets import QInputDialog
                names = ["Sin carpeta"] + [f"{f['icon']} {f['name']}" for f in all_folders]
                choice, ok = QInputDialog.getItem(
                    self, "Asignar carpeta",
                    "¿En qué carpeta quieres poner los documentos añadidos?",
                    names, 0, False
                )
                if ok and choice != "Sin carpeta":
                    idx = names.index(choice) - 1
                    folder_id = all_folders[idx]["id"]
                    for doc_id in added:
                        db.assign_document_to_folder(doc_id, folder_id)
            self.refresh()

    def highlight_document(self, doc_id):
        """Scroll to and select a document node."""
        root = self.tree.invisibleRootItem()
        def _find(node):
            for i in range(node.childCount()):
                child = node.child(i)
                if child.data(0, Qt.UserRole) == doc_id:
                    self.tree.setCurrentItem(child)
                    self.tree.scrollToItem(child)
                    return True
                if _find(child):
                    return True
            return False
        _find(root)

    # ─── Private ──────────────────────────────────────────────────────────────

    def _on_item_clicked(self, item, col):
        node_type = item.data(0, Qt.UserRole + 2)
        if node_type == TYPE_DOCUMENT:
            doc_id = item.data(0, Qt.UserRole)
            doc = db.get_document(doc_id)
            if doc:
                self.document_selected.emit(doc)
        elif node_type in (TYPE_FOLDER, TYPE_UNFILED):
            # Toggle expand/collapse on single click
            item.setExpanded(not item.isExpanded())

    def _context_menu(self, pos):
        item = self.tree.itemAt(pos)
        if not item:
            # Right-click on blank area — offer to create folder
            menu = QMenu(self)
            act = QAction("📁 Nueva carpeta", self)
            act.triggered.connect(self._create_folder)
            menu.addAction(act)
            menu.exec_(self.tree.viewport().mapToGlobal(pos))
            return

        node_type = item.data(0, Qt.UserRole + 2)
        menu = QMenu(self)

        if node_type == TYPE_FOLDER:
            folder_id = item.data(0, Qt.UserRole + 1)
            folder = next((f for f in db.get_all_folders() if f["id"] == folder_id), None)

            act_rename = QAction("✏️ Renombrar carpeta", self)
            act_rename.triggered.connect(lambda: self._rename_folder(folder))
            menu.addAction(act_rename)

            act_new_sub = QAction("➕ Nueva carpeta", self)
            act_new_sub.triggered.connect(self._create_folder)
            menu.addAction(act_new_sub)

            menu.addSeparator()

            act_del = QAction("🗑 Eliminar carpeta", self)
            act_del.triggered.connect(lambda: self._delete_folder(folder_id))
            menu.addAction(act_del)

        elif node_type == TYPE_DOCUMENT:
            doc_id = item.data(0, Qt.UserRole)
            doc    = db.get_document(doc_id)
            if not doc:
                return

            act_open = QAction("📂 Abrir", self)
            act_open.triggered.connect(lambda: self.document_selected.emit(doc))
            menu.addAction(act_open)

            menu.addSeparator()

            act_assign = QAction("📁 Asignar a carpetas...", self)
            act_assign.triggered.connect(lambda: self._assign_folders(doc))
            menu.addAction(act_assign)

            # Change status submenu
            status_menu = QMenu("📊 Cambiar estado", self)
            for s in db.DOCUMENT_STATUSES:
                act = QAction(s, self)
                act.triggered.connect(lambda ch, _s=s, _id=doc_id: self._change_status(_id, _s))
                status_menu.addAction(act)
            menu.addMenu(status_menu)

            menu.addSeparator()

            act_remove = QAction("🗑 Quitar de biblioteca", self)
            act_remove.triggered.connect(lambda: self._remove_document(doc_id))
            menu.addAction(act_remove)

        menu.exec_(self.tree.viewport().mapToGlobal(pos))

    # ─── Folder CRUD ──────────────────────────────────────────────────────────

    def _create_folder(self):
        dlg = FolderDialog(self)
        if dlg.exec_():
            data = dlg.get_data()
            db.add_folder(data["name"], data["icon"], data["color"])
            self.refresh()

    def _rename_folder(self, folder):
        if not folder:
            return
        dlg = FolderDialog(
            self,
            existing_name=folder["name"],
            existing_icon=folder.get("icon","📁"),
            existing_color=folder.get("color","#89b4fa")
        )
        if dlg.exec_():
            data = dlg.get_data()
            conn = db.get_connection()
            conn.execute(
                "UPDATE folders SET name=?, icon=?, color=? WHERE id=?",
                (data["name"], data["icon"], data["color"], folder["id"])
            )
            conn.commit()
            conn.close()
            self.refresh()

    def _delete_folder(self, folder_id):
        reply = QMessageBox.question(
            self, "Eliminar carpeta",
            "¿Eliminar esta carpeta?\n"
            "Los documentos que contenía pasarán a 'Sin carpeta'.\n"
            "(No se borran los archivos originales)",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            db.delete_folder(folder_id)
            self.refresh()

    def _assign_folders(self, doc):
        all_folders  = db.get_all_folders()
        curr_folders = db.get_folders_for_document(doc["id"])
        dlg = AssignFoldersDialog(self, doc, all_folders, curr_folders)
        if dlg.exec_():
            selected = dlg.get_selected_ids()
            curr_ids = {f["id"] for f in curr_folders}
            # Add new
            for fid in selected - curr_ids:
                db.assign_document_to_folder(doc["id"], fid)
            # Remove deselected
            for fid in curr_ids - selected:
                db.remove_document_from_folder(doc["id"], fid)
            self.refresh()

    # ─── Document actions ─────────────────────────────────────────────────────

    def _change_status(self, doc_id, status):
        db.update_document(doc_id, status=status)
        self.refresh()

    def _remove_document(self, doc_id):
        reply = QMessageBox.question(
            self, "Confirmar",
            "¿Quitar este documento de la biblioteca?\n(No se borrará el archivo original)",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            db.delete_document(doc_id)
            self.document_removed.emit(doc_id)
            self.refresh()

    # ─── FTS ──────────────────────────────────────────────────────────────────

    def _fts_search(self):
        query = self.txt_fts.text().strip()
        self.fts_results.clear()
        if not query:
            return
        results = db.search_documents_fts(query)
        if not results:
            item = QTreeWidgetItem(self.fts_results, ["Sin resultados"])
            item.setFlags(Qt.NoItemFlags)
            return
        for r in results:
            doc_id = int(r["doc_id"])
            doc = db.get_document(doc_id)
            if not doc:
                continue
            snippet = r.get("snippet","")[:70]
            item = QTreeWidgetItem(self.fts_results)
            item.setText(0, f"{_fmt_icon(doc.get('format','txt'))} {doc['name']}")
            item.setData(0, Qt.UserRole, doc_id)
            item.setFont(0, QFont("Times New Roman", 12))
            child = QTreeWidgetItem(item)
            child.setText(0, f"  …{snippet}…")
            child.setForeground(0, QBrush(QColor("#6c7086")))
            child.setData(0, Qt.UserRole, doc_id)
            child.setFont(0, QFont("Times New Roman", 11))
            item.setExpanded(True)

    def _on_fts_clicked(self, item, col):
        doc_id = item.data(0, Qt.UserRole)
        if doc_id:
            doc = db.get_document(doc_id)
            if doc:
                self.document_selected.emit(doc)
