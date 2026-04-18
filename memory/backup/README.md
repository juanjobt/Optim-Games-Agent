# memory/

Este directorio contiene los archivos de memoria del agente de Optim Pixel.

## Archivos

| Archivo | Descripción |
|---|---|
| `post-ideas.md` | Cola editorial de ideas. Gestionado por `/generate-post-ideas` y `/create-post`. |
| `blog.db` | Base de datos SQLite de posts publicados e internal links. Generada automáticamente por `.opencode/skills/link-related-posts/scripts/manage-internal-links.py init`. **No editar manualmente.** |
| `tags-usables.md` | Léxico controlado de tags disponibles. Validado automáticamente por `publish-wordpress` antes de cada post. |

## Sistema de Tags

Los tags se gestionan desde `tags-usables.md`:

1. **Antes de publicar** — El agente valida cada tag contra la lista
2. **Tag nuevo** — Se añade automáticamente con fecha actual
3. **Normalización** — Usar siempre el formato exacto del archivo (mayúsculas/minúsculas)

**Grupos de tags:** Sistema, Género, Época, Año, Desarrolladora, Creador, Saga, País, Técnica, Personaje, Compositor

## blog.db — Tablas

| Tabla | Propósito |
|---|---|
| `posts` | Catálogo de todos los posts publicados con sus metadatos |
| `tags` | Tags únicos del blog |
| `post_tags` | Relación many-to-many posts ↔ tags |
| `internal_links` | Registro de qué posts enlazan a qué otros, con el score de similitud |