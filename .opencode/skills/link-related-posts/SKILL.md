---
name: link-related-posts
description: Gestiona los internal links entre posts de Optim Pixel. Busca posts relacionados usando la base de datos local (SQLite) con scoring de similitud basado en tag_groups.score_weight, y registra los enlaces creados en la tabla internal_links. La inserción editorial de enlaces se gestiona mediante la regla internal-links-insertion.
---

# Skill: Link Related Posts

Esta skill gestiona los **internal links** entre posts de Optim Pixel. La búsqueda de posts relacionados se realiza contra la base de datos local (`memory/blog.db`), usando tags y sus grupos para calcular el score de similitud. Solo se guarda un log de los enlaces insertados en SQLite.

**Para la inserción editorial de enlaces** (dónde y cómo insertar los links en el HTML del post), consulta la regla `internal-links-insertion`.

**Antes de usar esta skill**, la base de datos debe estar inicializada y sincronizada con `db_init.py init`, `db_init.py migrate-tags`, `db_init.py sync-tags-wp` y `db_init.py sync-posts-wp`.

---

## El script y sus comandos

Ruta del script: `.opencode/skills/link-related-posts/scripts/manage-internal-links.py`
Ruta de la base de datos: `memory/blog.db` (gestionada por `memory/scripts/db_init.py`)

### Buscar posts relacionados

```bash
python3 .opencode/skills/link-related-posts/scripts/manage-internal-links.py find-related \
  --wp-id 42 \
  --limit 5
```

**Modo automático (sin `--tags`)**: Obtiene los tags del post desde la base de datos local (`post_tags` + `tags` + `tag_groups`) y busca otros posts que compartan tags. Los pesos de cada grupo se leen dinámicamente desde `tag_groups.score_weight`.

```bash
python3 .opencode/skills/link-related-posts/scripts/manage-internal-links.py find-related \
  --wp-id 42 \
  --tags "sistema:Super Nintendo,genero:RPG,saga:Final Fantasy" \
  --limit 5
```

**Modo manual (con `--tags`)**: Usa los tags proporcionados en formato `tipo:valor` separados por comas. Útil cuando el post aún no tiene tags en la base de datos local.

Tipos soportados (se corresponden con slugs de `tag_groups`):

| Tipo (slug) | Peso | Ejemplo |
|---|---|---|
| `saga` | 4 | `saga:Final Fantasy` |
| `sistema` | 3 | `sistema:Super Nintendo` |
| `genero` | 2 | `genero:RPG` |
| `desarrolladora` | 1 | `desarrolladora:Square` |
| `epoca` | 1 | `epoca:Años 90` |
| `ano` | 1 | `ano:1995` |
| `creador` | 1 | `creador:Sakaguchi` |
| `pais` | 1 | `pais:Japón` |
| `tecnica` | 1 | `tecnica:Mode 7` |
| `personaje` | 1 | `personaje:Cloud` |
| `compositor` | 1 | `compositor:Uematsu` |
| (sin tipo) | 1 | `Square` (tag común) |

> **Nota**: Los pesos se leen dinámicamente desde `tag_groups.score_weight` en la base de datos. La tabla anterior refleja los valores actuales pero pueden cambiar.

**Cómo funciona**:
1. Modo automático: consulta `post_tags` + `tags` + `tag_groups` para el `--wp-id` dado
2. Modo manual: resuelve cada tag en la tabla `tags` local por nombre o slug
3. Para cada tag, encuentra otros posts que lo comparten en `post_tags`
4. Pondera por `tag_groups.score_weight` del grupo del tag
5. Excluye posts ya enlazados (registrados en `internal_links`)
6. Devuelve resultados ordenados por score descendente

**Usar los 2 primeros resultados** del listado como posts a enlazar, siempre que su score sea > 0.

### Registrar un internal link creado

```bash
python3 .opencode/skills/link-related-posts/scripts/manage-internal-links.py log-link \
  --from-wp-id 42 \
  --to-wp-id 17 \
  --score 8
```

Llamar una vez por cada enlace insertado en el post. El `--score` es el valor que devolvió `find-related` para ese post destino.

### Obtener el contenido de un post

```bash
python3 .opencode/skills/link-related-posts/scripts/manage-internal-links.py get-post-content --wp-id 42
```

Devuelve el contenido HTML actual del post (campo `content.raw` de la WP REST API). Útil para obtener el contenido antes de insertar enlaces. Este es el **único comando que requiere conexión a WordPress**.

### Verificar enlaces de un post

```bash
python3 .opencode/skills/link-related-posts/scripts/manage-internal-links.py get-links --wp-id 10
```

Devuelve los enlaces salientes (outgoing) y entrantes (incoming) de un post. Útil para verificar qué enlaces ya existen antes de procesar un post.

**Nota**: El comando `find-related` excluye automáticamente los destinos que ya tienen enlace desde el post origen, para evitar duplicados y hacer la red más dispersiva.

### Posts que necesitan links

```bash
python3 .opencode/skills/link-related-posts/scripts/manage-internal-links.py needs-links --limit 20
```

Devuelve los posts con menos de 2 outgoing links, ordenados por fecha de publicación (más antiguos primero). Usa la tabla `posts` local. Útil para el comando `/link-posts`.

### Estadísticas generales

```bash
python3 .opencode/skills/link-related-posts/scripts/manage-internal-links.py stats
```

Útil para dar feedback al usuario o para que el agente decida si vale la pena ejecutar `/link-posts`. Usa la tabla `posts` local para el conteo.

---

## Flujo genérico de uso

### Contexto A: Después de publicar un post (create-post)

1. Buscar relacionados con `find-related --wp-id N` (sin `--tags`, se obtienen del post automáticamente)
2. Obtener el contenido actual con `get-post-content`
3. **Insertar los enlaces siguiendo la regla `internal-links-insertion`**
4. Registrar cada link creado con `log-link`

### Contexto B: Mejorar posts existentes (/link-posts)

1. Obtener lista de posts que necesitan links: `needs-links`
2. Para cada post:
   a. Obtener los tags del post desde la DB local o el contenido
   b. Buscar relacionados con `find-related --wp-id N`
   c. **Insertar los enlaces siguiendo la regla `internal-links-insertion`**
   d. Registrar cada link creado con `log-link`

---

## Manejo de errores

**El script devuelve `"ok": false`** — Leer el campo `"error"` del JSON y reportarlo. El internal linking es un paso de mejora, no debe bloquear otras operaciones.

**`memory/blog.db` no existe o falta tablas** — Ejecutar `python3 memory/scripts/db_init.py init` primero.

**Post no encontrado en la base de datos local** — Si el post no está en la tabla `posts`, usar `--tags` para especificar los tags manualmente, o ejecutar `python3 memory/scripts/db_init.py sync-posts-wp` primero.

---

## Integración con WordPress MCP

La skill delega la manipulación del contenido del post a WordPress MCP:

- **Obtener contenido**: `wp_get_post(id, context="edit")`
- **Actualizar contenido**: `wp_update_post(id, content)`

Alternativamente, usar el comando `get-post-content` del script que hace esta llamada automáticamente.

---

## Dependencias

| Dependencia | Uso |
|---|---|
| `memory/blog.db` | Base de datos SQLite con tablas `posts`, `post_tags`, `tags`, `tag_groups`, `internal_links` |
| `memory/scripts/db_init.py` | Inicialización y sincronización de la base de datos |
| `memory/scripts/db_query.py` | Consultas sobre tags, posts e ideas |
| `.env` | Credenciales WordPress (solo para `get-post-content`) |