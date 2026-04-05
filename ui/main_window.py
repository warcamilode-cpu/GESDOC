"""
ui/main_window.py - Main application window.
Layout: [Library Panel] | [Document Viewer Tabs] | [Comments Panel]
"""
import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QSplitter, QTabWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLabel, QStatusBar, QToolBar,
    QAction, QMenuBar, QMenu, QMessageBox, QFileDialog,
    QFrame, QApplication
)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QFont, QIcon

import database as db
from utils.theme import apply_theme
from utils.exporter import export_to_excel, export_to_pdf
from ui.library_panel import LibraryPanel
from ui.comments_panel import CommentsPanel
from ui.dialogs import AddCommentDialog, DocumentInfoDialog, ExportDialog


class ViewerTab(QWidget):
    """A single viewer tab containing the appropriate viewer widget."""

    def __init__(self, document, parent=None):
        super().__init__(parent)
        self.document = document
        self._viewer = None
        self._setup_viewer()

    def _setup_viewer(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        path = self.document.get("path", "")

        if not os.path.isfile(path):
            lbl = QLabel(f"⚠️ Archivo no encontrado:\n{path}")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setObjectName("subtitle")
            layout.addWidget(lbl)
            return

        from viewers.web_viewer import SmartViewer
        self._viewer = SmartViewer()
        self._viewer.load_document(path)
        layout.addWidget(self._viewer)

        # Index content for full-text search after page loads
        QTimer.singleShot(1500, self._index_content)

    def _index_content(self):
        """Index document content in FTS — async for PDFs to avoid UI freeze."""
        if not self._viewer:
            return
        fmt = self.document.get("format", "").lower()
        inner = getattr(self._viewer, "_viewer", self._viewer)
        if fmt == "pdf" and hasattr(inner, "request_text_content_async"):
            inner.request_text_content_async(self._on_content_ready)
        else:
            try:
                text = self._viewer.get_text_content()
                if text:
                    self._on_content_ready(text)
            except Exception:
                pass

    def _on_content_ready(self, content):
        if content:
            try:
                db.update_document_fts(
                    self.document["id"],
                    self.document.get("name", ""),
                    content
                )
            except Exception:
                pass

    def get_selected_text(self):
        if self._viewer and hasattr(self._viewer, "get_selected_text"):
            return self._viewer.get_selected_text()
        return ""

    def get_location_info(self):
        if self._viewer and hasattr(self._viewer, "get_current_page_info"):
            return self._viewer.get_current_page_info()
        return ""


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("DocManager — Gestor de Documentos")
        self.setMinimumSize(1200, 700)
        self.resize(1400, 860)
        self._dark_mode = True
        self._open_tabs = {}   # doc_id → tab index
        self._setup_ui()
        self._setup_menus()
        self._setup_toolbar()
        apply_theme(QApplication.instance(), dark=self._dark_mode)

    # ── UI Setup ──────────────────────────────────────────────────────────────

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Main splitter
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(3)

        # ── Left panel: Library ───────────────────────────────────────────────
        self.library = LibraryPanel()
        self.library.setMinimumWidth(220)
        self.library.setMaximumWidth(360)
        self.library.document_selected.connect(self._open_document)
        self.library.document_removed.connect(self._close_document_tab)

        # ── Center: Tab viewer ────────────────────────────────────────────────
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.tabCloseRequested.connect(self._close_tab)
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

        # Welcome page
        self._welcome_tab = self._make_welcome_tab()
        self.tab_widget.addTab(self._welcome_tab, "🏠 Inicio")
        self.tab_widget.tabBar().setTabButton(0, self.tab_widget.tabBar().RightSide, None)

        # ── Right panel: Comments ─────────────────────────────────────────────
        self.comments = CommentsPanel()
        self.comments.setMinimumWidth(280)
        self.comments.setMaximumWidth(420)
        self.comments.add_comment_requested.connect(self._add_comment)
        self.comments.edit_comment_requested.connect(self._edit_comment)

        self.splitter.addWidget(self.library)
        self.splitter.addWidget(self.tab_widget)
        self.splitter.addWidget(self.comments)
        self.splitter.setSizes([260, 800, 340])

        main_layout.addWidget(self.splitter)

        # ── Status bar ────────────────────────────────────────────────────────
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.lbl_status = QLabel("Listo")
        self.status_bar.addWidget(self.lbl_status)

    def _make_welcome_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel("📚 DocManager")
        title.setFont(QFont("Segoe UI", 28, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel(
            "Tu espacio para leer, anotar y organizar documentos.\n"
            "Usa el panel izquierdo para añadir y abrir documentos."
        )
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setObjectName("subtitle")
        subtitle.setFont(QFont("Segoe UI", 13))

        btn_add = QPushButton("➕ Añadir primer documento")
        btn_add.setObjectName("primaryBtn")
        btn_add.setFixedHeight(40)
        btn_add.setFixedWidth(240)
        btn_add.setFont(QFont("Segoe UI", 12))
        btn_add.clicked.connect(self.library.add_documents)

        layout.addStretch()
        layout.addWidget(title)
        layout.addSpacing(12)
        layout.addWidget(subtitle)
        layout.addSpacing(24)
        layout.addWidget(btn_add, alignment=Qt.AlignCenter)
        layout.addStretch()
        return widget

    def _setup_menus(self):
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("📁 Archivo")
        act_open = QAction("Añadir documento...", self)
        act_open.setShortcut("Ctrl+O")
        act_open.triggered.connect(self.library.add_documents)
        file_menu.addAction(act_open)

        act_close = QAction("Cerrar pestaña activa", self)
        act_close.setShortcut("Ctrl+W")
        act_close.triggered.connect(lambda: self._close_tab(self.tab_widget.currentIndex()))
        file_menu.addAction(act_close)

        file_menu.addSeparator()
        act_quit = QAction("Salir", self)
        act_quit.setShortcut("Ctrl+Q")
        act_quit.triggered.connect(self.close)
        file_menu.addAction(act_quit)

        # Comments menu
        comments_menu = menubar.addMenu("💬 Comentarios")
        act_add_comment = QAction("Añadir comentario", self)
        act_add_comment.setShortcut("Ctrl+Shift+C")
        act_add_comment.triggered.connect(self._add_comment)
        comments_menu.addAction(act_add_comment)

        comments_menu.addSeparator()
        act_export = QAction("Exportar comentarios...", self)
        act_export.setShortcut("Ctrl+E")
        act_export.triggered.connect(self._export_comments)
        comments_menu.addAction(act_export)

        # View menu
        view_menu = menubar.addMenu("🖼 Vista")
        self.act_theme = QAction("☀️ Tema claro", self)
        self.act_theme.setShortcut("Ctrl+T")
        self.act_theme.triggered.connect(self._toggle_theme)
        view_menu.addAction(self.act_theme)

        act_lib = QAction("Mostrar/ocultar biblioteca", self)
        act_lib.setShortcut("Ctrl+B")
        act_lib.triggered.connect(self._toggle_library)
        view_menu.addAction(act_lib)

        act_comments = QAction("Mostrar/ocultar comentarios", self)
        act_comments.setShortcut("Ctrl+Shift+B")
        act_comments.triggered.connect(self._toggle_comments)
        view_menu.addAction(act_comments)

        # Help menu
        help_menu = menubar.addMenu("❓ Ayuda")
        act_about = QAction("Acerca de DocManager", self)
        act_about.triggered.connect(self._show_about)
        help_menu.addAction(act_about)

    def _setup_toolbar(self):
        toolbar = QToolBar("Principal")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(toolbar)

        act_open = QAction("➕ Añadir", self)
        act_open.setToolTip("Añadir documento (Ctrl+O)")
        act_open.triggered.connect(self.library.add_documents)
        toolbar.addAction(act_open)

        toolbar.addSeparator()

        act_comment = QAction("💬 Comentario", self)
        act_comment.setToolTip("Añadir comentario al doc activo (Ctrl+Shift+C)")
        act_comment.triggered.connect(self._add_comment)
        toolbar.addAction(act_comment)

        act_export = QAction("📤 Exportar", self)
        act_export.setToolTip("Exportar comentarios (Ctrl+E)")
        act_export.triggered.connect(self._export_comments)
        toolbar.addAction(act_export)

        toolbar.addSeparator()

        act_theme = QAction("🌓 Tema", self)
        act_theme.setToolTip("Cambiar tema (Ctrl+T)")
        act_theme.triggered.connect(self._toggle_theme)
        toolbar.addAction(act_theme)

        toolbar.addSeparator()

        act_doc_info = QAction("📋 Info doc", self)
        act_doc_info.setToolTip("Información y metadatos del documento activo")
        act_doc_info.triggered.connect(self._show_doc_info)
        toolbar.addAction(act_doc_info)

    # ── Document management ───────────────────────────────────────────────────

    def _open_document(self, document):
        doc_id = document["id"]

        # Check if already open
        if doc_id in self._open_tabs:
            self.tab_widget.setCurrentIndex(self._open_tabs[doc_id])
            self.comments.set_document(document)
            return

        db.update_last_opened(doc_id)
        # Reload fresh doc data
        document = db.get_document(doc_id) or document

        # Create viewer tab
        viewer = ViewerTab(document)
        fmt = document.get("format", "txt").upper()
        icon = {"PDF": "📕", "DOCX": "📘", "DOC": "📘", "MD": "📗", "TXT": "📄"}.get(fmt, "📄")
        name = document.get("name", "Documento")
        short_name = name[:20] + "..." if len(name) > 20 else name

        idx = self.tab_widget.addTab(viewer, f"{icon} {short_name}")
        self.tab_widget.setTabToolTip(idx, name)
        self._open_tabs[doc_id] = idx
        self.tab_widget.setCurrentIndex(idx)

        self.comments.set_document(document)
        self.lbl_status.setText(f"Abierto: {name}")

    def _close_tab(self, index):
        widget = self.tab_widget.widget(index)
        if widget is self._welcome_tab:
            return
        # Find doc_id for this tab
        doc_id_to_remove = None
        for doc_id, tab_idx in list(self._open_tabs.items()):
            if tab_idx == index:
                doc_id_to_remove = doc_id
                break

        self.tab_widget.removeTab(index)

        if doc_id_to_remove is not None:
            del self._open_tabs[doc_id_to_remove]
            # Remap indices
            new_open_tabs = {}
            for doc_id, tab_idx in self._open_tabs.items():
                new_idx = tab_idx - 1 if tab_idx > index else tab_idx
                new_open_tabs[doc_id] = new_idx
            self._open_tabs = new_open_tabs

        if self.tab_widget.count() == 0:
            self.tab_widget.addTab(self._welcome_tab, "🏠 Inicio")
            self.tab_widget.tabBar().setTabButton(0, self.tab_widget.tabBar().RightSide, None)
            self.comments.set_document(None)

    def _close_document_tab(self, doc_id):
        if doc_id in self._open_tabs:
            self._close_tab(self._open_tabs[doc_id])

    def _on_tab_changed(self, index):
        if not hasattr(self, "comments"):
            return
        widget = self.tab_widget.widget(index)
        if widget is None or widget is self._welcome_tab:
            self.comments.set_document(None)
            return
        # Find document for this tab
        for doc_id, tab_idx in self._open_tabs.items():
            if tab_idx == index:
                doc = db.get_document(doc_id)
                if doc:
                    self.comments.set_document(doc)
                    self.library.highlight_document(doc_id)
                break

    def _get_active_document(self):
        index = self.tab_widget.currentIndex()
        widget = self.tab_widget.widget(index)
        if widget is None or widget is self._welcome_tab:
            return None, None
        for doc_id, tab_idx in self._open_tabs.items():
            if tab_idx == index:
                return db.get_document(doc_id), widget
        return None, None

    # ── Comments ──────────────────────────────────────────────────────────────

    def _add_comment(self):
        document, viewer_widget = self._get_active_document()
        if not document:
            QMessageBox.information(
                self, "Sin documento activo",
                "Abre un documento primero para añadir comentarios."
            )
            return

        # Try to get selected text
        highlighted_text = ""
        location_info = ""
        if isinstance(viewer_widget, ViewerTab):
            highlighted_text = viewer_widget.get_selected_text() or ""
            location_info = viewer_widget.get_location_info() or ""

        dlg = AddCommentDialog(
            parent=self,
            document=document,
            highlighted_text=highlighted_text,
            location_info=location_info
        )
        if dlg.exec_():
            data = dlg.get_data()
            db.add_comment(
                doc_id=document["id"],
                content=data["content"],
                category=data["category"],
                priority=data["priority"],
                status=data["status"],
                location_info=data["location_info"],
                highlighted_text=data["highlighted_text"],
            )
            self.comments.reload()
            self.lbl_status.setText("Comentario añadido.")

    def _edit_comment(self, comment):
        document, _ = self._get_active_document()
        dlg = AddCommentDialog(
            parent=self,
            document=document,
            highlighted_text=comment.get("highlighted_text", ""),
            location_info=comment.get("location_info", ""),
            existing_comment=comment
        )
        if dlg.exec_():
            data = dlg.get_data()
            db.update_comment(
                comment["id"],
                content=data["content"],
                category=data["category"],
                priority=data["priority"],
                status=data["status"],
            )
            self.comments.reload()
            self.lbl_status.setText("Comentario actualizado.")

    def _export_comments(self):
        docs = db.get_all_documents()
        dlg = ExportDialog(self, documents=docs)
        if dlg.exec_():
            data = dlg.get_data()
            doc_id = data["doc_id"]
            fmt = data["format"]
            path = data["path"]
            title = "Todos los documentos"
            if doc_id:
                doc = db.get_document(doc_id)
                title = doc["name"] if doc else "Documento"

            comments = db.get_all_comments_for_export(doc_id=doc_id)
            if not comments:
                QMessageBox.information(self, "Sin comentarios",
                                        "No hay comentarios para exportar.")
                return
            try:
                if fmt == "xlsx":
                    export_to_excel(comments, path, title=title)
                else:
                    export_to_pdf(comments, path, title=title)
                QMessageBox.information(self, "Exportación completa",
                                        f"Archivo guardado en:\n{path}")
                self.lbl_status.setText(f"Exportado: {path}")
            except Exception as e:
                QMessageBox.critical(self, "Error al exportar", str(e))

    # ── View actions ──────────────────────────────────────────────────────────

    def _toggle_theme(self):
        self._dark_mode = not self._dark_mode
        apply_theme(QApplication.instance(), dark=self._dark_mode)
        self.comments.set_dark_mode(self._dark_mode)
        self.act_theme.setText("🌙 Tema oscuro" if not self._dark_mode else "☀️ Tema claro")

    def _toggle_library(self):
        visible = self.library.isVisible()
        self.library.setVisible(not visible)

    def _toggle_comments(self):
        visible = self.comments.isVisible()
        self.comments.setVisible(not visible)

    def _show_doc_info(self):
        document, _ = self._get_active_document()
        if not document:
            QMessageBox.information(self, "Sin documento activo",
                                    "Abre un documento primero.")
            return
        dlg = DocumentInfoDialog(self, document=document)
        if dlg.exec_():
            data = dlg.get_data()
            db.update_document(document["id"], **data)
            self.library.refresh()
            self.lbl_status.setText("Información del documento actualizada.")

    def _show_about(self):
        QMessageBox.about(
            self, "Acerca de DocManager",
            "📚 <b>DocManager</b><br><br>"
            "Gestor personal de documentos con anotaciones.<br>"
            "Soporta PDF, DOCX, Markdown y TXT.<br><br>"
            "Características:<br>"
            "• Visor embebido multi-formato<br>"
            "• Comentarios con categorías, prioridad y estado<br>"
            "• Resaltado de texto vinculado a comentarios<br>"
            "• Búsqueda full-text en documentos<br>"
            "• Exportación a Excel y PDF<br>"
            "• Tema oscuro y claro<br><br>"
            "Base de datos: ~/.docmanager/docmanager.db"
        )
