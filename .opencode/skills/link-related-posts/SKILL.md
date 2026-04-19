---
name: link-related-posts
description: Gestiona los internal links entre posts de Optim Pixel. Busca posts relacionados usando la base de datos local (SQLite) con scoring de similitud basado en tag_groups.score_weight, y registra los enlaces creados en la tabla internal_links. La inserción editorial de enlaces se gestiona mediante la regla internal-links-insertion.
---

# Skill: Link Related Posts

Esta skill gestiona los **internal links** entre posts de Optim Pixel. Toda la información se obtiene de la base de datos local (`memory/blog.db`), sin llamadas a la API de WordPress excepto para obtener el contenido HTML de un post.

**Para la inserción editorial de enlaces** (dónde y cómo insertar los links en el HTML del post), lee el archivo `.opencode/skills/link-related-posts/reference/internal-links-insertion.md` antes de insertar cualquier enlace. Este archivo contiene las reglas editoriales obligatorias.

**Antes de usar esta skill**, la base de datos debe estar inicializada y sincronizada con `db_init.py init`, `db_init.py sync-tags-wp` y `db_init.py sync-posts-wp`.

---

## Fuente de datos: SQLite local

Todos los datos se leen de `memory/blog.db`:

| Dato | Tabla | Notas |
|------|-------|-------|
| Tags de un post | `post_tags` + `tags` + `tag_groups` | Se obtienen automáticamente desde la DB |
| Pesos de similitud | `tag_groups.score_weight` | Se leen dinámicamente, no están hardcodeados |
| Posts publicados | `posts` | Catálogo local sincronizado desde WordPress |
| Enlaces existentes | `internal_links` | Para evitar duplicados |

---

## Comandos

La skill usa dos scripts con responsabilidades claras:

| Script | Responsabilidad | Comandos |
|--------|----------------|----------|
| `manage-internal-links.py` | Lógica de similitud y contenido de posts | `find-related`, `needs-links`, `get-post-content` |
| `db_query.py` | Consultas y registro en la DB (interfaz centralizada) | `add-link`, `get-links`, `link-stats` |

### Buscar posts relacionados

```bash
python3 .opencode/skills/link-related-posts/scripts/manage-internal-links.py find-related \
  --wp-id 42 \
  --limit 5
```

Obtiene los tags del post desde la base de datos local (`post_tags` + `tags` + `tag_groups`) y busca otros posts que comparten tags. Los pesos se leen de `tag_groups.score_weight`. Excluye automáticamente los destinos que ya tienen enlace desde el post origen.

**Usar los 2 primeros resultados** del listado como posts a enlazar, siempre que su score sea > 0.

### Registrar un internal link creado

```bash
python3 memory/scripts/db_query.py add-link --from 42 --to 17 --score 8
```

Llamar una vez por cada enlace insertado en el post. El `--score` es el valor que devolvió `find-related` para ese post destino.

### Verificar enlaces de un post

```bash
python3 memory/scripts/db_query.py get-links --wp-id 10
```

Devuelve los enlaces salientes y entrantes de un post. Útil para verificar qué enlaces ya existen antes de procesar un post.

### Obtener el contenido de un post

```bash
python3 .opencode/skills/link-related-posts/scripts/manage-internal-links.py get-post-content --wp-id 42
```

Devuelve el contenido HTML actual del post (campo `content.raw` de la WP REST API). Este es el **único comando que requiere conexión a WordPress**.

Alternativamente, se puede usar `wp_get_post(id, context="edit")` del MCP de WordPress.

### Posts que necesitan links

```bash
python3 .opencode/skills/link-related-posts/scripts/manage-internal-links.py needs-links --limit 20
```

Devuelve los posts con menos de 2 outgoing links, ordenados por fecha de publicación (más antiguos primero). Usa la tabla `posts` local.

### Estadísticas de internal linking

```bash
python3 memory/scripts/db_query.py link-stats
```

Devuelve estadísticas generales: total de posts, total de enlaces, posts sin links, con un solo link, y correctamente enlazados (2+ links).

---

## Flujo de uso

Esta skill procesa **un único post**. Para procesar múltiples posts en lote, usar el comando `/link-posts`.

1. Buscar relacionados con `find-related --wp-id N`
2. Verificar enlaces existentes con `db_query.py get-links --wp-id N`
3. Seleccionar los **2 mejores candidatos** (top 2 por score, > 0). Si solo hay 1, insertar 1 enlace.
4. Obtener el contenido actual con `get-post-content --wp-id N`
5. **Insertar los enlaces siguiendo las reglas de inserción** del archivo `reference/internal-links-insertion.md`
6. Registrar cada link creado con `db_query.py add-link --from N --to N --score N`
7. Actualizar el post en WordPress con `wp_update_post`

---

## Manejo de errores

**El script devuelve `"ok": false`** — Leer el campo `"error"` del JSON y reportarlo. El internal linking es un paso de mejora, no debe bloquear otras operaciones.

**`memory/blog.db` no existe o falta tablas** — Ejecutar `python3 memory/scripts/db_init.py init` primero.

**Post no encontrado en la base de datos local** — Sincronizar con `python3 memory/scripts/db_init.py sync-posts-wp` y `python3 memory/scripts/db_init.py sync-tags-wp`.

---

## Integración con WordPress MCP

La skill delega la manipulación del contenido del post a WordPress MCP:

- **Obtener contenido**: `wp_get_post(id, context="edit")`
- **Actualizar contenido**: `wp_update_post(id, content)`

Alternativamente, usar el comando `get-post-content` del script que hace esta llamada automáticamente.

---

## Dependencias

| Dependencia | Uso | Comandos |
|---|---|---|
| `memory/blog.db` | Base de datos SQLite con `posts`, `post_tags`, `tags`, `tag_groups`, `internal_links` | Todos |
| `memory/scripts/db_query.py` | Interfaz centralizada de consultas a la DB | `add-link`, `get-links`, `link-stats` |
| `memory/scripts/db_init.py` | Inicialización y sincronización de la base de datos | Setup |
| `.opencode/skills/link-related-posts/scripts/manage-internal-links.py` | Lógica de similitud y contenido de posts | `find-related`, `needs-links`, `get-post-content` |
| `.env` | Credenciales WordPress (solo para `get-post-content`) | `get-post-content` |