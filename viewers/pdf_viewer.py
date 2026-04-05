"""
viewers/pdf_viewer.py - Reliable PDF viewer.

Strategy: one background thread renders all pages sequentially.
Each page is appended to a scroll area as it finishes.
Memory is kept reasonable because only rendered pixmaps are in RAM,
and fitz opens/closes the doc per-page so it never holds the whole
file in memory.
"""
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QLabel,
    QPushButton, QFrame, QSizePolicy, QLineEdit, QShortcut,
    QProgressBar, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, pyqtSlot, QTimer, QMutex
from PyQt5.QtGui import QPixmap, QImage, QKeySequence

try:
    import fitz
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False


# ─────────────────────────────────────────────────────────────────────────────
# Sequential render thread — renders all pages one by one
# ─────────────────────────────────────────────────────────────────────────────

class RenderThread(QThread):
    page_ready  = pyqtSignal(int, QPixmap)   # (page_index, pixmap)
    all_done    = pyqtSignal()

    def __init__(self, doc_path, page_count, zoom, parent=None):
        super().__init__(parent)
        self.doc_path   = doc_path
        self.page_count = page_count
        self.zoom       = zoom
        self._stop      = False

    def stop(self):
        self._stop = True

    def run(self):
        mat = fitz.Matrix(self.zoom, self.zoom)
        for i in range(self.page_count):
            if self._stop:
                return
            try:
                doc  = fitz.open(self.doc_path)
                page = doc.load_page(i)
                pix  = page.get_pixmap(matrix=mat, alpha=False)
                doc.close()
                if self._stop:
                    return
                img = QImage(
                    pix.samples, pix.width, pix.height,
                    pix.stride, QImage.Format_RGB888
                )
                self.page_ready.emit(i, QPixmap.fromImage(img))
            except Exception:
                pass
        self.all_done.emit()


# ─────────────────────────────────────────────────────────────────────────────
# PDFViewer
# ─────────────────────────────────────────────────────────────────────────────

class PDFViewer(QWidget):
    selection_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._doc_path    = None
        self._page_count  = 0
        self._zoom        = 1.5
        self._page_labels = []
        self._thread      = None
        self._setup_ui()

    # ─── UI ──────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Toolbar ───────────────────────────────────────────────────────────
        bar = QFrame()
        bar.setFixedHeight(44)
        bar.setStyleSheet("""
            QFrame  { background:#2a2a3a; border-bottom:1px solid #313244; }
            QLabel  { color:#cdd6f4; font-family:'Times New Roman'; font-size:14px;
                      background:transparent; }
            QPushButton { background:#313244; border:none; color:#cdd6f4;
                          font-size:16px; padding:3px 8px; border-radius:4px;
                          min-width:28px; min-height:26px; }
            QPushButton:hover  { background:#45475a; }
            QPushButton:disabled { color:#555; }
            QLineEdit { background:#202020; border:1px solid #45475a;
                        border-radius:4px; color:#e8eaed;
                        font-family:'Times New Roman'; font-size:14px;
                        padding:2px 6px; }
        """)
        tb = QHBoxLayout(bar)
        tb.setContentsMargins(8, 6, 8, 6)
        tb.setSpacing(5)

        def sep():
            s = QFrame()
            s.setFrameShape(QFrame.VLine)
            s.setStyleSheet("QFrame{background:#45475a;border:none;max-width:1px;}")
            return s

        self.lbl_file = QLabel("Sin documento")
        self.lbl_file.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.btn_prev = QPushButton("◀")
        self.btn_prev.setFixedWidth(30)
        self.btn_prev.setToolTip("Página anterior")
        self.btn_prev.clicked.connect(lambda: self._go_page(self._cur_page() - 1))

        self.edt_page = QLineEdit("1")
        self.edt_page.setFixedWidth(42)
        self.edt_page.setAlignment(Qt.AlignCenter)
        self.edt_page.returnPressed.connect(self._on_page_enter)

        self.lbl_total = QLabel("/ 0")
        self.lbl_total.setFixedWidth(48)

        self.btn_next = QPushButton("▶")
        self.btn_next.setFixedWidth(30)
        self.btn_next.setToolTip("Página siguiente")
        self.btn_next.clicked.connect(lambda: self._go_page(self._cur_page() + 1))

        self.btn_zm = QPushButton("−")
        self.btn_zm.setFixedWidth(28)
        self.btn_zm.setToolTip("Reducir zoom  (Ctrl+−)")
        self.btn_zm.clicked.connect(lambda: self._step_zoom(-0.25))

        self.lbl_zoom = QLabel("150%")
        self.lbl_zoom.setFixedWidth(48)
        self.lbl_zoom.setAlignment(Qt.AlignCenter)

        self.btn_zp = QPushButton("+")
        self.btn_zp.setFixedWidth(28)
        self.btn_zp.setToolTip("Aumentar zoom  (Ctrl+=)")
        self.btn_zp.clicked.connect(lambda: self._step_zoom(0.25))

        tb.addWidget(self.lbl_file)
        tb.addWidget(sep())
        tb.addWidget(self.btn_prev)
        tb.addWidget(self.edt_page)
        tb.addWidget(self.lbl_total)
        tb.addWidget(self.btn_next)
        tb.addWidget(sep())
        tb.addWidget(self.btn_zm)
        tb.addWidget(self.lbl_zoom)
        tb.addWidget(self.btn_zp)

        sep2 = sep()
        tb.addWidget(sep2)

        self.btn_copy_text = QPushButton("📋 Copiar texto")
        self.btn_copy_text.setToolTip(
            "Copia el texto de la página actual al portapapeles\n"
            "para pegarlo como texto resaltado en un comentario"
        )
        self.btn_copy_text.clicked.connect(self._copy_page_text)
        tb.addWidget(self.btn_copy_text)

        root.addWidget(bar)

        # ── Progress bar (shown while rendering) ─────────────────────────────
        self.progress = QProgressBar()
        self.progress.setFixedHeight(3)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet(
            "QProgressBar{background:#1e1e2e;border:none;}"
            "QProgressBar::chunk{background:#89b4fa;}"
        )
        self.progress.hide()
        root.addWidget(self.progress)

        # ── Scroll area ───────────────────────────────────────────────────────
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setAlignment(Qt.AlignHCenter)
        self.scroll.setStyleSheet(
            "QScrollArea{background:#525659;border:none;}"
        )
        # Update page indicator while scrolling
        self.scroll.verticalScrollBar().valueChanged.connect(self._update_page_indicator)

        self._container = QWidget()
        self._container.setStyleSheet("background:#525659;")
        self._vbox = QVBoxLayout(self._container)
        self._vbox.setSpacing(10)
        self._vbox.setContentsMargins(20, 20, 20, 20)
        self._vbox.setAlignment(Qt.AlignHCenter)

        self.scroll.setWidget(self._container)
        root.addWidget(self.scroll)

        # Keyboard shortcuts
        QShortcut(QKeySequence("Ctrl+="), self, lambda: self._step_zoom(0.25))
        QShortcut(QKeySequence("Ctrl+-"), self, lambda: self._step_zoom(-0.25))
        QShortcut(QKeySequence("Ctrl+0"), self, lambda: self._set_zoom(1.5))

    # ─── Public API ───────────────────────────────────────────────────────────

    def load_document(self, path):
        if not HAS_FITZ:
            self._show_error("PyMuPDF no instalado.\npip install PyMuPDF")
            return

        # Stop any running render
        self._stop_thread()
        self._doc_path   = path
        self._page_labels = []

        # Get page count quickly
        try:
            doc = fitz.open(path)
            self._page_count = doc.page_count
            doc.close()
        except Exception as e:
            self._show_error(f"Error abriendo PDF:\n{e}")
            return

        name = os.path.basename(path)
        self.lbl_file.setText(name)
        self.lbl_total.setText(f"/ {self._page_count}")
        self.edt_page.setText("1")

        # Clear scroll area
        self._clear_pages()

        # Progress bar
        self.progress.setMaximum(self._page_count)
        self.progress.setValue(0)
        self.progress.show()

        # Start rendering thread
        self._thread = RenderThread(path, self._page_count, self._zoom)
        self._thread.page_ready.connect(self._on_page_ready)
        self._thread.all_done.connect(self._on_all_done)
        self._thread.start()

    def get_text_content(self):
        if not self._doc_path:
            return ""
        try:
            doc   = fitz.open(self._doc_path)
            pages = [doc.load_page(i).get_text() for i in range(doc.page_count)]
            doc.close()
            return "\n".join(pages)
        except Exception:
            return ""

    def get_selected_text(self):
        return ""

    def get_current_page_info(self):
        return f"Página {self._cur_page()}" if self._doc_path else ""

    # ─── Render callbacks ─────────────────────────────────────────────────────

    @pyqtSlot(int, QPixmap)
    def _on_page_ready(self, pnum, pixmap):
        """Called from main thread via signal when a page is rendered."""
        lbl = QLabel()
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setPixmap(pixmap)
        lbl.setFixedSize(pixmap.size())
        lbl.setStyleSheet("background:white; border:1px solid #888;")
        self._vbox.addWidget(lbl, 0, Qt.AlignHCenter)

        # Ensure list is big enough
        while len(self._page_labels) <= pnum:
            self._page_labels.append(None)
        self._page_labels[pnum] = lbl

        self.progress.setValue(pnum + 1)

    @pyqtSlot()
    def _on_all_done(self):
        self.progress.hide()

    # ─── Navigation ───────────────────────────────────────────────────────────

    def _cur_page(self):
        try:
            return int(self.edt_page.text())
        except ValueError:
            return 1

    def _go_page(self, page_num):
        page_num = max(1, min(self._page_count, page_num))
        self.edt_page.setText(str(page_num))
        idx = page_num - 1
        if idx >= len(self._page_labels) or self._page_labels[idx] is None:
            return
        lbl = self._page_labels[idx]
        # Scroll to the label's position within the container
        y = lbl.y()
        self.scroll.verticalScrollBar().setValue(y - 20)

    def _on_page_enter(self):
        try:
            p = int(self.edt_page.text())
        except ValueError:
            p = 1
        self._go_page(p)

    def _update_page_indicator(self, scroll_val):
        """Update the page number box based on scroll position."""
        if not self._page_labels:
            return
        for i, lbl in enumerate(self._page_labels):
            if lbl is None:
                continue
            if lbl.y() + lbl.height() > scroll_val:
                self.edt_page.setText(str(i + 1))
                return

    # ─── Zoom ─────────────────────────────────────────────────────────────────

    def _step_zoom(self, delta):
        self._set_zoom(round(self._zoom + delta, 2))

    def _set_zoom(self, value):
        self._zoom = max(0.5, min(4.0, value))
        self.lbl_zoom.setText(f"{int(self._zoom * 100)}%")
        if self._doc_path:
            self.load_document(self._doc_path)

    # ─── Helpers ─────────────────────────────────────────────────────────────

    def _clear_pages(self):
        while self._vbox.count():
            item = self._vbox.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self._page_labels = []

    def _stop_thread(self):
        if self._thread and self._thread.isRunning():
            self._thread.stop()
            self._thread.wait(2000)
        self._thread = None

    def _show_error(self, msg):
        self._clear_pages()
        lbl = QLabel(f"⚠️ {msg}")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setWordWrap(True)
        lbl.setStyleSheet("color:#f38ba8; font-size:14px;")
        self._vbox.addWidget(lbl)

    def _copy_page_text(self):
        """Extract text from the current page and put it on the clipboard."""
        if not self._doc_path:
            return
        page_num = self._cur_page() - 1
        try:
            doc  = fitz.open(self._doc_path)
            page = doc.load_page(page_num)
            text = page.get_text().strip()
            doc.close()
            if text:
                from PyQt5.QtWidgets import QApplication
                QApplication.clipboard().setText(text)
                # Brief feedback on button
                self.btn_copy_text.setText("✅ Copiado")
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(1800, lambda: self.btn_copy_text.setText("📋 Copiar texto"))
            else:
                self.btn_copy_text.setText("⚠️ Sin texto")
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(1800, lambda: self.btn_copy_text.setText("📋 Copiar texto"))
        except Exception as e:
            pass

    def closeEvent(self, event):
        self._stop_thread()
        super().closeEvent(event)
