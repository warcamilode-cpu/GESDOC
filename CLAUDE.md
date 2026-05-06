# CLAUDE.md — GESDOC

Sistema de gestión documental con árbol de consulta, anotaciones normativas y relaciones entre normas.

---

## Stack

- **Backend:** FastAPI + SQLite (database.py)
- **Frontend:** HTML + CSS + JS vanilla (frontend/index.html)
- **DB:** `~/.docmanager/docmanager.db`
- **Repositorio físico:** `./repositorio/`
- **Servidor:** uvicorn en puerto 8001, nginx como proxy en puerto 80

## Despliegue actual

- **VM Google Cloud:** `instance-20260503-141839` · zona `us-central1-a`
- **IP externa:** `136.119.117.186`
- **URL:** `http://136.119.117.186`
- **Auth temporal:** nginx Basic Auth (`/etc/nginx/.gesdoc_pass`)
- **Servicio:** `sudo systemctl restart gesdoc`
- **Actualizar:** `cd ~/GESDOC && git pull origin main && sudo systemctl restart gesdoc`

---

## 🔐 Sistema de usuarios — DISEÑO PENDIENTE DE IMPLEMENTAR

### Contexto
- Equipo máximo de **20 personas**
- Documentos legales/normativos (EAAB, MEFCL, resoluciones colombianas)
- Trazabilidad de quién anota qué es crítica

### Roles

| Rol    | Puede hacer |
|--------|-------------|
| **Admin**  | Todo: gestionar usuarios, carpetas generales y personales, documentos de cualquier usuario, configuración |
| **Editor** | Subir documentos, anotar, comentar, gestionar su biblioteca personal |
| **Lector** | Solo leer documentos de la biblioteca general y comentar (con su nombre vinculado) |

### Biblioteca dual

| Biblioteca | Quién ve | Quién edita |
|-----------|----------|-------------|
| **General** (del equipo) | Todos | Admin + Editores |
| **Personal** (por usuario) | Solo Admin + el dueño | Solo el dueño |

- Los documentos personales no aparecen en la búsqueda global para otros usuarios
- Un Editor puede "promover" un documento personal a la biblioteca general (con aprobación de Admin)

### Comentarios en biblioteca general
- El autor se toma automáticamente del usuario logueado
- No se puede falsificar el nombre (campo autor bloqueado)
- Los lectores pueden comentar pero no editar documentos

### Modelo de datos a agregar

```sql
-- Usuarios
CREATE TABLE users (
    id         INTEGER PRIMARY KEY,
    username   TEXT UNIQUE NOT NULL,
    email      TEXT UNIQUE,
    password   TEXT NOT NULL,          -- bcrypt hash
    role       TEXT DEFAULT 'lector',  -- admin | editor | lector
    activo     BOOLEAN DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Vincular documentos a usuario dueño
ALTER TABLE documents ADD COLUMN owner_id INTEGER REFERENCES users(id);
ALTER TABLE documents ADD COLUMN biblioteca TEXT DEFAULT 'general'; -- general | personal

-- Sesiones / tokens
CREATE TABLE sessions (
    token      TEXT PRIMARY KEY,
    user_id    INTEGER REFERENCES users(id),
    expires_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### Implementación técnica

- **Auth:** JWT con `python-jose` + `passlib[bcrypt]`
- **Middleware FastAPI:** verifica token en header `Authorization: Bearer ...`
- **Frontend:** pantalla de login antes de la app, token en `localStorage`
- **Comentarios:** `author` se llena automático desde el token, campo readonly en UI
- **Rutas protegidas:** todos los `/api/` endpoints requieren token válido
- **Rutas por rol:** endpoints de admin verifican `role == 'admin'`

---

## 📄 Mejoras al visor de documentos — PENDIENTES DE IMPLEMENTAR

### 1. Indicador de página actual y total
- Mostrar **"Página X / Y"** en el toolbar del visor mientras se lee un PDF
- Actualizar el número de página actual mientras el usuario hace scroll (IntersectionObserver por canvas)
- Flechas ← → para saltar entre páginas directamente
- Para DOCX/MD/TXT: mostrar progreso de scroll (%) en lugar de páginas

### 2. Copiar texto de PDFs
- Agregar **capa de texto (text layer)** de PDF.js sobre cada canvas renderizado
- El texto queda seleccionable y copiable como en cualquier PDF del navegador
- La capa es invisible pero intercepta el mouse para selección
- Usar `page.getTextContent()` + `pdfjsLib.renderTextLayer()` por página
- Agregar CSS del text layer de PDF.js para resaltado de selección

---

## 🚀 Funcionalidades adicionales sugeridas (para equipo de 20)

### Prioridad alta
1. **Historial de cambios en normas** — log de quién cambió el estado de vigencia y cuándo (crítico para documentos legales)
2. **Asignaciones** — un Admin puede asignar un documento a un Editor para que lo revise/clasifique
3. **Menciones en comentarios** — `@username` para notificar a alguien dentro de un comentario

### Prioridad media
4. **Favoritos por usuario** — cada persona marca sus documentos frecuentes
5. **Actividad reciente** — feed de "Fulano subió X", "Mengana comentó en Y" (últimas 48h)
6. **Compartir carpeta personal** — un Editor puede compartir una carpeta personal con usuarios específicos sin hacerla pública

### Prioridad baja
7. **Flujo de aprobación** — Editor sube → Admin aprueba para biblioteca general
8. **Alertas de vigencia** — notificación cuando una norma está próxima a vencer (ej. 30 días antes de `fecha_derogacion`)
9. **Exportar por usuario** — ver todos los comentarios/anotaciones de una persona específica

---

## Proyectos en el mismo VM (planeado)

| Proyecto | Puerto | Ruta nginx |
|----------|--------|-----------|
| GESDOC | 8001 | `/` |
| GES-JUD | 8002 | `/judicante` o subdominio |
| Second Brain | 8003 | `/brain` o subdominio |

El VM actual (e2-micro, 1GB RAM) puede ser insuficiente para 3 apps simultáneas con carga real.
**Recomendado:** upgrade a `e2-small` (2GB RAM, ~$13/mes) antes de agregar más proyectos.

---

## Convenciones del proyecto

- Código y comentarios en **español**
- Variables y funciones en **snake_case** (backend) / **camelCase** (JS frontend)
- Routers en `backend/routers/` registrados en `main.py`
- Frontend en un solo `frontend/index.html`
- Base de datos nunca se sube a git (en `.gitignore`)
