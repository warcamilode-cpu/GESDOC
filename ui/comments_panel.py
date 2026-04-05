# -*- coding: utf-8 -*-
"""ui/comments_panel.py — Fixed-height comment cards with full-view dialog."""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QScrollArea, QFrame, QComboBox, QSizePolicy,
    QMessageBox, QMenu, QAction, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

import database as db
from utils.theme import (
    PRIORITY_COLORS_DARK, STATUS_COLORS_DARK,
    PRIORITY_COLORS_LIGHT, STATUS_COLORS_LIGHT, CATEGORY_ICONS
)

# Maximum characters shown in the preview inside the fixed-height card
PREVIEW_CHARS = 130
# Fixed pixel height of every comment card — panel stays stable regardless
CARD_H = 158


# ─────────────────────────────────────────────────────────────────────────────
# CommentCard  —  fixed height, truncated preview, action buttons
# ─────────────────────────────────────────────────────────────────────────────

class CommentCard(QFrame):

    edit_requested   = pyqtSignal(dict)
    delete_requested = pyqtSignal(int)
    view_requested   = pyqtSignal(dict)   # opens ViewCommentDialog
    status_changed   = pyqtSignal(int, str)

    def __init__(self, comment, dark_mode=True, parent=None):
        super().__init__(parent)
        self.comment   = comment
        self.dark_mode = dark_mode
        self.setObjectName("commentCard")
        # Fixed height keeps the panel from growing with long text
        self.setFixedHeight(CARD_H)
        # Width follows parent — do NOT set a fixed width here
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._ctx_menu)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 7, 10, 7)
        lay.setSpacing(4)

        pri_colors = PRIORITY_COLORS_DARK if self.dark_mode else PRIORITY_COLORS_LIGHT
        sts_colors = STATUS_COLORS_DARK   if self.dark_mode else STATUS_COLORS_LIGHT

        c       = self.comment
        pri     = c.get("priority", "Media")
        status  = c.get("status",   "Abierto")
        cat     = c.get("category", "General")
        author  = c.get("author",   "") or ""
        loc     = c.get("location_info", "") or ""
        content = c.get("content",  "") or ""
        date    = (c.get("created_at") or "")[:10]
        cat_ico = CATEGORY_ICONS.get(cat, "💬")
        p_col   = pri_colors.get(pri,    "#cdd6f4")
        s_col   = sts_colors.get(status, "#cdd6f4")

        # ── Row 1: chips + date ───────────────────────────────────────────────
        r1 = QHBoxLayout(); r1.setSpacing(4)
        for txt, col in [
            (f"{cat_ico} {cat}", p_col),
            ("·",               "#6c7086"),
            (f"● {pri}",        p_col),
            ("·",               "#6c7086"),
            (f"◆ {status}",     s_col),
        ]:
            l = QLabel(txt)
            l.setFont(QFont("Segoe UI", 8,
                            QFont.Bold if col != "#6c7086" else QFont.Normal))
            l.setStyleSheet(f"color:{col};background:transparent;")
            r1.addWidget(l)
        r1.addStretch()
        dl = QLabel(date)
        dl.setFont(QFont("Segoe UI", 7))
        dl.setStyleSheet("color:#6c7086;background:transparent;")
        r1.addWidget(dl)
        lay.addLayout(r1)

        # ── Row 2: author + page (same line, compact) ─────────────────────────
        if author or loc:
            r2 = QHBoxLayout(); r2.setSpacing(8)
            if author:
                al = QLabel(f"👤 {author}")
                al.setFont(QFont("Segoe UI", 8))
                al.setStyleSheet("color:#89b4fa;background:transparent;")
                r2.addWidget(al)
            if loc:
                pl = QLabel(f"📍 {loc}")
                pl.setFont(QFont("Segoe UI", 8))
                pl.setStyleSheet("color:#a6adc8;background:transparent;")
                r2.addWidget(pl)
            r2.addStretch()
            lay.addLayout(r2)

        # ── Content preview — truncated, max 3 lines ──────────────────────────
        preview = (content[:PREVIEW_CHARS] + "…") if len(content) > PREVIEW_CHARS \
                  else content
        cl = QLabel(preview)
        cl.setWordWrap(True)
        cl.setFont(QFont("Segoe UI", 9))
        cl.setMaximumHeight(50)
        cl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        lay.addWidget(cl)

        lay.addStretch()

        # ── Action buttons ────────────────────────────────────────────────────
        br = QHBoxLayout(); br.setSpacing(4)

        def btn(label, tooltip="", w=None):
            b = QPushButton(label)
            b.setFixedHeight(24)
            b.setFont(QFont("Segoe UI", 8))
            if w:
                b.setFixedWidth(w)
            if tooltip:
                b.setToolTip(tooltip)
            return b

        b_view    = btn("👁 Ver",    "Ver comentario completo")
        b_edit    = btn("✏️ Editar", "Editar comentario")
        new_sts   = "Abierto" if status == "Resuelto" else "Resuelto"
        b_resolve = btn("✅ Reabrir" if status == "Resuelto" else "✅ Resolver")
        b_del     = btn("🗑", "Eliminar comentario", w=26)

        b_view.clicked.connect(   lambda: self.view_requested.emit(self.comment))
        b_edit.clicked.connect(   lambda: self.edit_requested.emit(self.comment))
        b_resolve.clicked.connect(lambda: self.status_changed.emit(
                                      self.comment["id"], new_sts))
        b_del.clicked.connect(    lambda: self.delete_requested.emit(
                                      self.comment["id"]))

        br.addWidget(b_view)
        br.addWidget(b_edit)
        br.addWidget(b_resolve)
        br.addStretch()
        br.addWidget(b_del)
        lay.addLayout(br)

    def _ctx_menu(self, pos):
        menu = QMenu(self)
        for s in db.COMMENT_STATUSES:
            a = QAction(f"Marcar como {s}", self)
            a.triggered.connect(
                lambda checked, _s=s: self.status_changed.emit(self.comment["id"], _s))
            menu.addAction(a)
        menu.addSeparator()
        a_view = QAction("👁 Ver completo", self)
        a_view.triggered.connect(lambda: self.view_requested.emit(self.comment))
        menu.addAction(a_view)
        a_copy = QAction("📋 Copiar texto", self)
        a_copy.triggered.connect(
            lambda: QApplication.clipboard().setText(self.comment.get("content", "")))
        menu.addAction(a_copy)
        menu.exec_(self.mapToGlobal(pos))


# ─────────────────────────────────────────────────────────────────────────────
# CommentsPanel  —  right sidebar with scroll area of fixed-height cards
# ─────────────────────────────────────────────────────────────────────────────

class CommentsPanel(QWidget):

    add_comment_requested  = pyqtSignal()
    edit_comment_requested = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._document  = None
        self._dark_mode = True
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(8)

        # Header
        hdr = QHBoxLayout()
        lbl = QLabel("💬 Comentarios")
        lbl.setObjectName("sectionTitle")
        self.btn_add = QPushButton("➕ Añadir")
        self.btn_add.setObjectName("primaryBtn")
        self.btn_add.setFixedHeight(28)
        self.btn_add.setEnabled(False)
        self.btn_add.clicked.connect(self.add_comment_requested.emit)
        hdr.addWidget(lbl)
        hdr.addStretch()
        hdr.addWidget(self.btn_add)
        lay.addLayout(hdr)

        self.lbl_doc = QLabel("Abre un documento para ver sus comentarios.")
        self.lbl_doc.setObjectName("subtitle")
        self.lbl_doc.setWordWrap(True)
        lay.addWidget(self.lbl_doc)

        # Search
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 Buscar en comentarios...")
        self.txt_search.textChanged.connect(self._reload)
        lay.addWidget(self.txt_search)

        # Filters
        fr = QHBoxLayout(); fr.setSpacing(4)
        self.cmb_cat = QComboBox()
        self.cmb_cat.addItem("Todas", "Todas")
        for cat in db.COMMENT_CATEGORIES:
            self.cmb_cat.addItem(f"{CATEGORY_ICONS.get(cat,'•')} {cat}", cat)
        self.cmb_cat.currentIndexChanged.connect(self._reload)

        self.cmb_pri = QComboBox()
        self.cmb_pri.addItem("Todas", "Todas")
        for p in db.COMMENT_PRIORITIES:
            self.cmb_pri.addItem(p, p)
        self.cmb_pri.currentIndexChanged.connect(self._reload)

        self.cmb_sts = QComboBox()
        self.cmb_sts.addItem("Todos", "Todos")
        for s in db.COMMENT_STATUSES:
            self.cmb_sts.addItem(s, s)
        self.cmb_sts.currentIndexChanged.connect(self._reload)

        fr.addWidget(self.cmb_cat)
        fr.addWidget(self.cmb_pri)
        fr.addWidget(self.cmb_sts)
        lay.addLayout(fr)

        # Stats
        self.lbl_stats = QLabel("")
        self.lbl_stats.setObjectName("subtitle")
        lay.addWidget(self.lbl_stats)

        # Card scroll area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._container    = QWidget()
        self._cards_layout = QVBoxLayout(self._container)
        self._cards_layout.setSpacing(8)
        self._cards_layout.setContentsMargins(2, 2, 2, 2)
        self._cards_layout.setAlignment(Qt.AlignTop)

        self.scroll.setWidget(self._container)
        lay.addWidget(self.scroll)

    # ── Public API ────────────────────────────────────────────────────────────

    def set_document(self, document):
        self._document = document
        self.btn_add.setEnabled(document is not None)
        self.lbl_doc.setText(
            f"📄 {document.get('name','')}" if document
            else "Abre un documento para ver sus comentarios."
        )
        self._reload()

    def reload(self):
        self._reload()

    def set_dark_mode(self, dark):
        self._dark_mode = dark
        self._reload()

    # ── Private ───────────────────────────────────────────────────────────────

    def _reload(self):
        self._clear()
        if not self._document:
            return

        comments = db.get_comments(
            self._document["id"],
            category=self.cmb_cat.currentData(),
            priority=self.cmb_pri.currentData(),
            status  =self.cmb_sts.currentData(),
            search  =self.txt_search.text().strip() or None,
        )
        all_c      = db.get_comments(self._document["id"])
        open_count = sum(1 for c in all_c if c.get("status") == "Abierto")
        self.lbl_stats.setText(
            f"{len(all_c)} total · {open_count} abiertos · mostrando {len(comments)}"
        )

        if not comments:
            lbl = QLabel("No hay comentarios que coincidan con los filtros.")
            lbl.setObjectName("subtitle")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setWordWrap(True)
            self._cards_layout.addWidget(lbl)
            return

        for comment in comments:
            card = CommentCard(comment, dark_mode=self._dark_mode)
            card.view_requested.connect(self._view)
            card.edit_requested.connect(self.edit_comment_requested.emit)
            card.delete_requested.connect(self._delete)
            card.status_changed.connect(self._set_status)
            self._cards_layout.addWidget(card)

        self._cards_layout.addStretch()

    def _clear(self):
        while self._cards_layout.count():
            item = self._cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _view(self, comment):
        from ui.dialogs import ViewCommentDialog
        dlg = ViewCommentDialog(comment, parent=self)
        dlg.exec_()

    def _delete(self, comment_id):
        reply = QMessageBox.question(
            self, "Confirmar eliminación",
            "¿Eliminar este comentario? Esta acción no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            db.delete_comment(comment_id)
            self._reload()

    def _set_status(self, comment_id, new_status):
        db.update_comment(comment_id, status=new_status)
        self._reload()
