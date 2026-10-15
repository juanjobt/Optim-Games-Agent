---
name: link-related-posts
description: Gestiona los internal links entre posts de Optim Pixel. Busca posts relacionados usando la base de datos local (SQLite) con scoring de similitud basado en tag_groups.score_weight, y registra los enlaces creados en la tabla internal_links. La inserción editorial de enlaces se gestiona mediante la regla internal-links-insertion.
---

# Skill: Link Related Posts

Esta skill gestiona los **internal links** entre posts de Optim Pixel. Los candidatos, tags y scores se obtienen de la base local (`memory/blog.db`); el contenido se lee y actualiza en WordPress para insertar y verificar los enlaces.

**Para la inserción editorial de enlaces** (dónde y cómo insertar los links en el HTML del post), lee el archivo `.opencode/skills/link-related-posts/reference/internal-links-insertion.md` antes de insertar cualquier enlace. Este archivo contiene las reglas editoriales obligatorias.

**Antes de usar esta skill**, la base de datos debe estar inicializada y sincronizada con `db_init.py init`, `db_init.py sync-tags-wp` y `db_init.py sync-posts-wp`.

La skill se usa de dos formas:

- **Desde `/create-post` (modo obligatorio):** procesa un borrador recién creado. Debe conseguir dos enlaces salientes a posts públicos antes de permitir que el post se publique. Si no hay dos candidatos válidos o falla la actualización/verificación, el borrador se queda en `draft`.
- **Desde `/link-posts` (mantenimiento):** procesa posts ya publicados en lote. Si solo hay un candidato positivo, puede añadir un enlace; si no hay ninguno, salta ese post y continúa el lote.

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

Obtiene los tags del post desde la base de datos local (`post_tags` + `tags` + `tag_groups`) y busca otros posts publicados que comparten tags. Los pesos se leen de `tag_groups.score_weight`. Excluye automáticamente los destinos que ya tienen enlace desde el post origen.

Para `/create-post`, seleccionar 2 destinos distintos con score > 0 y verificar cada candidato con `wp_get_post`: el estado actual de WordPress también debe ser `publish`. Para mantenimiento, aplicar el flujo descrito en `/link-posts`.

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

Devuelve el contenido HTML actual del post (campo `content.raw` de la WP REST API). Entre los comandos CLI de esta skill, es el que requiere conexión a WordPress; la actualización se realiza con `wp_update_post`.

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

1. Buscar relacionados con `find-related --wp-id N` y verificar enlaces existentes con `db_query.py get-links --wp-id N`.
2. Obtener el contenido actual con `get-post-content --wp-id N` y revisar sus enlaces internos existentes. Contar solo destinos públicos, no repetirlos y no superar 2 enlaces internos salientes en total.
3. Elegir candidatos distintos con score > 0. Antes de enlazar, comprobar con `wp_get_post(id, context="view")` que cada destino sigue en estado `publish`; descartar cualquier destino privado, inexistente o no disponible. Insertar solo los que hagan falta para alcanzar el objetivo: 2 enlaces en modo `/create-post`; en mantenimiento, hasta 2 en total.
4. Aplicar las reglas de `reference/internal-links-insertion.md`: nunca en el primer párrafo, máximo uno por párrafo y ancla contextual natural.
5. Actualizar el contenido con `wp_update_post`.
6. Volver a obtener el contenido desde WordPress y verificar que cada URL de destino está realmente presente. Si falta alguna, no registrar ese enlace como completado.
7. Registrar los enlaces verificados con `db_query.py add-link --from N --to N --score SCORE` y confirmar con `db_query.py get-links --wp-id N`.
8. En modo `/create-post`, si no quedan exactamente dos enlaces válidos y verificados, informar del fallo y mantener el borrador como `draft`.

---

## Manejo de errores

**El script devuelve `"ok": false`** — Leer el campo `"error"` del JSON y reportarlo. En el modo de mantenimiento, saltar el post afectado y continuar el lote. En `/create-post`, es un bloqueo de publicación: conservar el borrador y reportar la causa.

**`memory/blog.db` no existe o falta tablas** — Ejecutar `python3 memory/scripts/db_init.py init` primero.

**Post no encontrado en la base de datos local** — Sincronizar con `python3 memory/scripts/db_init.py sync-posts-wp` y `python3 memory/scripts/db_init.py sync-tags-wp`.

---

## Integración con WordPress MCP

La skill delega la manipulación del contenido del post a WordPress MCP:

- **Obtener contenido**: `wp_get_post(id, context="edit")`
- **Actualizar contenido**: `wp_update_post(id, content)`

Alternativamente, usar el comando `get-post-content` del script que hace esta llamada automáticamente.

**Fallback REST (si el preflight de `/create-post` devolvió modo `rest`):** la lectura ya es REST vía `get-post-content`. Para la escritura, usar el script equivalente en lugar de `wp_update_post`:

```bash
python3 .opencode/skills/publish-wordpress/scripts/wp_update_post.py --id POST_ID --content-file /tmp/post.html
```

---

## Dependencias

| Dependencia | Uso | Comandos |
|---|---|---|
| `memory/blog.db` | Base de datos SQLite con `posts`, `post_tags`, `tags`, `tag_groups`, `internal_links` | Todos |
| `memory/scripts/db_query.py` | Interfaz centralizada de consultas a la DB | `add-link`, `get-links`, `link-stats` |
| `memory/scripts/db_init.py` | Inicialización y sincronización de la base de datos | Setup |
| `.opencode/skills/link-related-posts/scripts/manage-internal-links.py` | Lógica de similitud y contenido de posts | `find-related`, `needs-links`, `get-post-content` |
| `.env` | Credenciales WordPress (solo para `get-post-content`) | `get-post-content` |
