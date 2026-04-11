# memory/

Este directorio contiene los archivos de memoria del agente de Optim Pixel.

## Archivos

| Archivo | Descripción |
|---|---|
| `post-ideas.md` | Cola editorial de ideas. Gestionado por `/generate-post-ideas` y `/create-post`. |
| `blog.db` | Base de datos SQLite de posts publicados e internal links. Generada automáticamente por `scripts/manage-internal-links.py init`. **No editar manualmente.** |

## blog.db — Tablas

| Tabla | Propósito |
|---|---|
| `posts` | Catálogo de todos los posts publicados con sus metadatos |
| `tags` | Tags únicos del blog |
| `post_tags` | Relación many-to-many posts ↔ tags |
| `internal_links` | Registro de qué posts enlazan a qué otros, con el score de similitud |