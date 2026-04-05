# DocManager — Gestor Personal de Documentos

Aplicación de escritorio en PyQt5 para leer, anotar y organizar documentos
en múltiples formatos (PDF, Word, Markdown, TXT).

---

## 🚀 Instalación

### 1. Requisitos previos
- Python 3.8 o superior
- pip actualizado

### 2. Instalar dependencias

```bash
# Crear entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate        # Linux/macOS
# o
venv\Scripts\activate           # Windows

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Ejecutar

```bash
python main.py
```

---

## 📦 Dependencias

| Paquete       | Uso                                      |
|---------------|------------------------------------------|
| PyQt5         | Interfaz gráfica                         |
| PyMuPDF       | Visor de PDF (renderizado de páginas)    |
| python-docx   | Lectura de archivos Word (.docx)         |
| markdown      | Renderizado de archivos Markdown         |
| openpyxl      | Exportación de comentarios a Excel       |
| reportlab     | Exportación de comentarios a PDF         |
| Pillow        | Procesamiento de imágenes (soporte)      |

---

## 🗂️ Estructura del proyecto

```
docmanager/
├── main.py                  # Punto de entrada
├── database.py              # Capa de datos (SQLite)
├── requirements.txt
├── README.md
├── ui/
│   ├── main_window.py       # Ventana principal
│   ├── library_panel.py     # Panel izquierdo: biblioteca
│   ├── comments_panel.py    # Panel derecho: comentarios
│   └── dialogs.py           # Diálogos (añadir comentario, info doc, exportar)
├── viewers/
│   ├── pdf_viewer.py        # Visor de PDF con zoom y paginación
│   └── text_viewer.py       # Visor de TXT, MD y DOCX
└── utils/
    ├── theme.py             # Temas oscuro y claro
    └── exporter.py          # Exportación a Excel y PDF
```

---

## ✨ Funcionalidades

### 📚 Biblioteca
- Carga de documentos PDF, DOCX, MD, TXT
- Filtros por estado y formato
- Etiquetas personalizadas por documento
- Estados: Por revisar / En progreso / Revisado / Aprobado
- Menú contextual (clic derecho)

### 📄 Visor embebido
- PDF con zoom ajustable (slider) y renderizado por páginas
- DOCX con formato visual (headings, bold, italic, tablas)
- Markdown con resaltado de código, tablas y blockquotes
- TXT con fuente monoespaciada

### 💬 Comentarios
- Vinculados a texto seleccionado (highlight)
- Categorías: General, Importante, Pregunta, Corrección, Referencia, Tarea
- Prioridades: 🔴 Alta / 🟡 Media / 🟢 Baja
- Estados: Abierto / Resuelto / Pendiente
- Filtros: por categoría, prioridad, estado y búsqueda de texto

### 🔍 Búsqueda
- Búsqueda full-text dentro del contenido de los documentos
- Búsqueda en comentarios (texto y texto resaltado)

### 📤 Exportación
- Excel (.xlsx) con formato, colores y hoja de resumen
- PDF (.pdf) con tabla profesional y estadísticas

### 🎨 Temas
- Tema oscuro (Catppuccin Mocha)
- Tema claro (Catppuccin Latte)
- Atajo: Ctrl+T

---

## ⌨️ Atajos de teclado

| Atajo          | Acción                        |
|----------------|-------------------------------|
| Ctrl+O         | Añadir documento              |
| Ctrl+W         | Cerrar pestaña activa         |
| Ctrl+Shift+C   | Añadir comentario             |
| Ctrl+E         | Exportar comentarios          |
| Ctrl+T         | Cambiar tema                  |
| Ctrl+B         | Mostrar/ocultar biblioteca    |
| Ctrl+Shift+B   | Mostrar/ocultar comentarios   |
| Ctrl+Q         | Salir                         |

---

## 💾 Base de datos

Los datos se guardan en: `~/.docmanager/docmanager.db` (SQLite)

Tablas:
- `documents` — Metadatos de documentos
- `comments` — Comentarios con anotaciones
- `documents_fts` — Índice de búsqueda full-text (FTS5)
