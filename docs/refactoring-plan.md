# Plan de Refactorización de Memoria — Optim Pixel

Migrar la memoria del agente desde archivos markdown (`tags-usables.md`, `post-ideas.md`) a la base de datos SQLite (`memory/blog.db`), cuya estructura está definida en `memory/blog.dbml`. Actualizar todas las reglas, comandos, skills y scripts para que operen contra SQLite en lugar de markdown.

---

## Estado Actual

| Componente | Formato | Problema |
|------------|---------|----------|
| Tags y grupos | `memory/tags-usables.md` (markdown) | Parseo frágil, sin prevención de duplicados, IDs de WordPress desconectados |
| Post ideas | `memory/post-ideas.md` (markdown) | Gestión de estados propensa a errores, parseo del campo Prompt monolítico |
| Internal links | `memory/blog.db` (SQLite) | Ya migrado, pero schema incompleto (solo tabla `internal_links`) |
| Posts publicados | Ningún registro local | Sin caché local,依赖 API WordPress para cada consulta |
| Scores de similitud | Hardcodeados en `manage-internal-links.py` | `TYPE_SCORES` desconectado de los datos reales |

## Estado Objetivo

Toda la memoria operativa en SQLite. El schema completo está definido en `memory/blog.dbml` y consta de:

- `tag_groups` — 11 grupos de tags con `score_weight`
- `tags` — ~88 tags con `wp_id`, `slug` y relación a grupos
- `posts` — Catálogo local de posts publicados
- `post_tags` — Relación many-to-many entre posts y tags
- `post_ideas` — Cola editorial con campos estructurados
- `internal_links` — Registro de enlaces entre posts (ya existente, sin `status`)

Los archivos markdown (`tags-usables.md`, `post-ideas.md`) se mueven a `memory/backup/` tras verificar que todo funciona.

---

## ✅ Fase 0 — Scripts Base

### ✅ 0.1 — Crear `memory/scripts/db_init.py`

Script de inicialización y migración que:

1. Lee el schema de `blog.dbml` (o lo tiene hardcodeado como SQL)
2. Crea las tablas `tag_groups`, `tags`, `posts`, `post_tags`, `post_ideas` si no existen
3. Migra datos existentes:
   - 11 grupos de tags (desde records del DBML o hardcodeados)
   - ~88 tags desde `tags-usables.md`, resolviendo `wp_id` y `slug` via `wp_list_tags`
   - 38 post_ideas desde `post-ideas.md`, descomponiendo el campo Prompt en campos estructurados
   - Preserva los 6 registros existentes de `internal_links`
4. Reconstruye la tabla `internal_links` con el nuevo schema (sin `status`, con FKs)

Uso:
```bash
python3 memory/scripts/db_init.py init          # Crear tablas
python3 memory/scripts/db_init.py migrate-tags  # Migrar tags-usables.md
python3 memory/scripts/db_init.py migrate-ideas  # Migrar post-ideas.md
python3 memory/scripts/db_init.py sync-tags-wp   # Resolver wp_ids desde WordPress
python3 memory/scripts/db_init.py sync-posts-wp  # Poblar posts y post_tags desde WordPress
```

Dependencias: Acceso a WordPress MCP para `sync-tags-wp` y `sync-posts-wp`.

### ✅ 0.2 — Crear `memory/scripts/db_query.py`

Interfaz de consultas para el agente (ejecutado via Bash, devuelve JSON). Subcomandos:

```bash
# Post Ideas
python3 memory/scripts/db_query.py get-pending-ideas [--limit N]
python3 memory/scripts/db_query.py get-idea --id N
python3 memory/scripts/db_query.py update-idea-state --id N --state pendiente|en_uso|publicado [--wp-id N]
python3 memory/scripts/db_query.py add-idea --title "..." --sistema "..." --tipo Review --modo editorial --angulo "..." [...]

# Tags
python3 memory/scripts/db_query.py get-tags-by-group --group sistema
python3 memory/scripts/db_query.py get-or-create-tag --name "Super Nintendo" --group sistema
python3 memory/scripts/db_query.py add-tag --name "..." --slug "..." --group sistema --wp-id N

# Posts
python3 memory/scripts/db_query.py add-post --wp-id N --title "..." --slug "..." --category-slug reviews
python3 memory/scripts/db_query.py get-post --wp-id N
python3 memory/scripts/db_query.py sync-posts-from-wp  # Sincronizar desde WordPress
```

Todos los comandos devuelven JSON para que el agente los parsee.

---

## ✅ Fase 1 — Migración de Datos

### ✅ 1.1 — Ejecutar migración inicial

```bash
python3 memory/scripts/db_init.py init
python3 memory/scripts/db_init.py migrate-tags
python3 memory/scripts/db_init.py migrate-ideas
```

Verificar:
- 11 filas en `tag_groups`
- ~88 filas en `tags` (sin `wp_id` todavía, se resolverá en 1.3)
- 38 filas en `post_ideas`
- 6 filas en `internal_links` preservadas

### ✅ 1.2 — Refactorizar `manage-internal-links.py`

Cambios realizados:
- ✅ Eliminado `cmd_init()` — `db_init.py` es el encargado centralizado de crear tablas
- ✅ Eliminado `TYPE_SCORES` hardcodeado → `get_score_weights(conn)` lee desde `tag_groups.score_weight`
- ✅ `cmd_find_related()` consulta `post_tags` + `tags` + `tag_groups` localmente sin llamar a la API de WordPress
- ✅ `cmd_needs_links()` consulta `posts` localmente sin llamar a la API de WordPress
- ✅ `cmd_stats()` usa `SELECT COUNT(*) FROM posts` localmente sin llamar a la API de WordPress
- ✅ `--tags` es ahora opcional: si no se proporciona, se obtienen automáticamente del post desde la DB local
- ✅ Resultados de `find-related` incluyen `shared_tags` con nombre, grupo y peso para mayor transparencia
- ✅ Eliminado código muerto: `get_post_metadata()`, `calculate_score()`, `search_posts_by_tag()`, `parse_tag_with_type()`, `wp_get_with_headers()`
- ✅ Eliminado `cmd_init` del CLI y de la documentación

### ✅ 1.3 — Poblar `wp_id` en `tags`

Para cada tag en la tabla `tags`:
1. Derivar el slug esperado del `name`
2. Consultar `wp_list_tags(slug=[slug])` para obtener el `wp_id`
3. Si no existe en WordPress, crear con `wp_add_tag(name=...)` y registrar el ID devuelto
4. Actualizar la fila en `tags` con `wp_id` y `slug`

### ✅ 1.4 — Poblar `post_wp_id` en `post_ideas`

Las 28 ideas con estado `publicado` fueron vinculadas con sus posts en WordPress mediante matching local contra la tabla `posts` (sin llamadas a la API). Solo 1 post (Freddy Hardest, wp_id=15) no tiene idea correspondiente en la cola editorial, por haberse publicado fuera del sistema.

### ✅ 1.5 — Poblar `posts` y `post_tags`

```bash
python3 memory/scripts/db_init.py sync-posts-wp
```

Consulta todos los posts publicados en WordPress y los inserta en `posts`. También pobla `post_tags` con las relaciones actuales.

---

## Fase 2 — Actualizar Reglas

### ✅ 2.1 — `.opencode/rules/post-ideas-memory.md` → `.opencode/rules/memory-system.md`

**Enfoque cambiado:** En lugar de reescribir la regla vieja, se elimina y se crea una nueva regla general de memoria.

La regla `post-ideas-memory.md` estaba escrita enteramente alrededor de un archivo markdown que ya no existe. En su lugar se crea `memory-system.md` que cubre **todo el sistema de memoria SQLite** — no solo `post_ideas`, sino también `tags`, `posts`, `post_tags` e `internal_links`.

**Acciones realizadas:**

| Acción | Detalle |
|--------|---------|
| Eliminar | `.opencode/rules/post-ideas-memory.md` |
| Crear | `.opencode/rules/memory-system.md` |
| Actualizar | `opencode.json` — cambiar referencia a la nueva regla |

**Contenido de `memory-system.md`:**

- Fuente de verdad: `memory/blog.db` (SQLite), schema en `memory/blog.dbml`
- Interfaz de consultas: `db_query.py` con subcomandos para post_ideas, tags y posts
- Ciclo de vida de ideas: `pendiente → en_uso → publicado`
- Tags y similitud: pesos desde `tag_groups.score_weight`
- Tags y WordPress: resolución automática de `wp_id`
- Reglas generales: no editar DB directamente, no usar archivos markdown legacy
- Archivos legacy en `memory/backup/` como referencia histórica

### 2.2 — `.opencode/rules/internal-links-insertion.md`

Cambios menores:
- Referenciar que `score_weight` ahora viene de `tag_groups` en la DB
- Mencionar que los posts relacionados pueden consultarse localmente via `posts` y `post_tags`

### ✅ 2.3 — `.opencode/rules/execution-logging.md`

Cambios realizados:
- ~`memory/post-ideas.md` → `memory/blog.db` (tabla `post_ideas`)~ Cambiado a referencia a la tabla `post_ideas` de la DB
- ~`memory/tags-usables.md` → `memory/blog.db` (tabla `tags`)~ Cambiado a referencia a la tabla `tags` de la DB

### ✅ 2.4 — `.opencode/rules/env-access.md`

Sin cambios — no referencia archivos de memoria.

---

## Fase 3 — Actualizar Skills

### 3.1 — `.opencode/skills/publish-wordpress/SKILL.md`

**Paso 2.2 — Consultar memoria de tags:**

| Antes | Después |
|-------|---------|
| Leer `memory/tags-usables.md` | `db_query.py get-tags-by-group --group sistema` |
| Parsear tabla markdown | Recibir JSON estructurado |

**Paso 2.4 — Añadir tags nuevos:**

| Antes | Después |
|-------|---------|
| Añadir fila a `tags-usables.md` | `db_query.py add-tag --name "..." --slug "..." --group sistema --wp-id N` |
| Warning sobre números de fila ≠ IDs de WordPress | Eliminar — los `wp_id` están directamente en la tabla `tags` |

**Paso 2.5 — Resolver IDs en WordPress:**

Simplificación importante:
- Si el tag ya está en la DB local con `wp_id`, usar ese ID directamente — no hace falta llamar a `wp_list_tags`
- Solo llamar a `wp_list_tags` / `wp_add_tag` para tags que NO estén en la DB local
- Tras crear un tag en WordPress, insertarlo en la DB con su `wp_id`

### 3.2 — `.opencode/skills/link-related-posts/SKILL.md`

Actualizar:
- Documentar que los scores de peso provienen de `tag_groups.score_weight` en la DB
- Los tags de un post pueden obtenerse localmente de `post_tags` en vez de la API
- El script `manage-internal-links.py` ha sido refactorizado (Fase 1.2)

### 3.3 — `.opencode/skills/search-game-candidates/SKILL.md`

Actualizar referencia a la rule `post-ideas-memory` para que apunte a la DB en vez de markdown.

---

## Fase 4 — Actualizar Comandos

### 4.1 — `.opencode/commands/create-post.md`

**Paso 0 — Determinar el tema:**

| Antes | Después |
|-------|---------|
| Leer `memory/post-ideas.md` | `db_query.py get-pending-ideas --limit 1` |
| Parsear la tabla markdown para extraer Prompt | Recibir JSON con campos estructurados |
| Editar markdown para cambiar estado a `en_uso` | `db_query.py update-idea-state --id N --state en_uso` |

**Paso 4.5 — Consolidar game_data:**

Los campos ya están descompuestos en la DB. Ya no hace falta parsear un Prompt monolítico. Se leen directamente:
- `title`, `sistema`, `tipo`, `genero`, `epoca`, `modo`, `angulo_editorial`, `justificacion`, `keyword_sugerida`, `factor_oportunidad`

**Paso 8 — Actualizar la memoria:**

| Antes | Después |
|-------|---------|
| Cambiar estado en `memory/post-ideas.md` | `db_query.py update-idea-state --id N --state publicado --wp-id N` |

### 4.2 — `.opencode/commands/generate-post-ideas.md`

**Paso 3 — Guardar en memoria:**

| Antes | Después |
|-------|---------|
| Añadir filas a `memory/post-ideas.md` | `db_query.py add-idea --title "..." --sistema "..." --tipo Review --modo editorial --angulo "..." ...` |
| Seguir formato de tabla markdown | Campos estructurados separados |

**Paso 2 — Formato del prompt:**

El prompt generado ya no es un campo monolítico. Los datos se almacenan en campos separados:
- `title`, `sistema`, `tipo`, `modo`, `angulo_editorial`, `justificacion`, `keyword_sugerida`, `factor_oportunidad`, `genero`, `epoca`

---

## Fase 5 — Scripts Python

### 5.1 — Refactorizar `manage-internal-links.py`

Cambios principales:
- `cmd_init()` crea TODAS las tablas según el schema de `blog.dbml`
- `TYPE_SCORES` eliminado → `SELECT score_weight FROM tag_groups WHERE slug = ?`
- `cmd_find_related()` puede consultar `post_tags` y `tags` localmente
- `cmd_needs_links()` puede consultar `posts` localmente

### 5.2 — `db_query.py` (nuevo)

Ver especificación completa en Fase 0.2. Script con subcomandos que el agente invoca via Bash. Devuelve JSON.

---

## Fase 6 — Actualizar Documentación

### 6.1 — `memory/README.md`

Reescribir completamente:

```markdown
# memory/

Base de datos SQLite como fuente de verdad del agente.

## Archivos

| Archivo | Descripción |
|---|---|
| `blog.db` | Base de datos SQLite. Ver schema en `blog.dbml`. **No editar manualmente.** |
| `blog.dbml` | Definición del schema en formato DBML. Referencia para humanos y agentes. |
| `scripts/db_init.py` | Inicialización y migración de la base de datos. |
| `scripts/db_query.py` | Consultas para el agente (devuelve JSON). |
| `execution-logs/` | Logs de ejecución por fecha. |

## Tablas

| Tabla | Propósito |
|---|---|
| `tag_groups` | Grupos de tags con peso de similitud. Seed init. |
| `tags` | Tags del blog con wp_id y slug de WordPress. |
| `posts` | Catálogo local de posts publicados. |
| `post_tags` | Relación many-to-many posts ↔ tags. |
| `post_ideas` | Cola editorial de ideas para posts. |
| `internal_links` | Registro de enlaces entre posts con score. |

## Sistema de Post Ideas

Las ideas se gestionan desde `post_ideas`:

1. **Antes de publicar** — `db_query.py get-pending-ideas`
2. **Idea nueva** — `db_query.py add-idea`
3. **Cambiar estado** — `db_query.py update-idea-state`

**Estados:** pendiente → en_uso → publicado
```

### 6.2 — `AGENTS.md`

Actualizar sección "Sistema de memoria":

```markdown
## Sistema de memoria

`memory/blog.db` (SQLite) es la fuente de verdad. Schema definido en `memory/blog.dbml`.

Las ideas se gestionan mediante `memory/scripts/db_query.py`.

| Estado | Significado |
|--------|-------------|
| `pendiente` | Generada pero sin usar |
| `en_uso` | En proceso de creación |
| `publicado` | Publicado en WordPress |
```

### 6.3 — `README.md` (raíz)

Actualizar menciones de `memory/post-ideas.md` para apuntar a `memory/blog.db`.

---

## Fase 7 — Eliminación de Archivos Depreciados

### 7.1 — Backup

```bash
mkdir -p memory/backup
mv memory/tags-usables.md memory/backup/tags-usables.md.bak
mv memory/post-ideas.md memory/backup/post-ideas.md.bak
```

Mantener como backup durante al menos 2 sesiones de agente exitosas antes de eliminar.

### 7.2 — Verificar `.gitignore`

Asegurar que `memory/blog.db` está trackeado en git (los datos son esenciales). `memory/execution-logs/` puede seguir ignorado si corresponde.

---

## Fase 8 — Verificación

### 8.1 — Test `/create-post`

Ejecutar con una idea existente y verificar:
1. La idea se lee correctamente desde SQLite
2. Los tags se resuelven desde SQLite (sin llamar a `wp_list_tags` para tags existentes)
3. El post se publica en WordPress
4. La idea cambia a estado `publicado` en SQLite
5. El post se registra en la tabla `posts`
6. Los tags se registran en `post_tags`

### 8.2 — Test `/generate-post-ideas`

Generar 1 idea y verificar:
1. Se guarda en `post_ideas` con campos estructurados
2. El estado es `pendiente`
3. `keyword_sugerida` y `factor_oportunidad` existen solo para modo `seo_master`
4. Los tags existentes no se duplican (verificar por `title`)

### 8.3 — Test de internal links

Verificar que:
1. `manage-internal-links.py init` crea todas las tablas
2. `find-related` usa `score_weight` desde `tag_groups`
3. Los resultados son consistentes con el comportamiento anterior

---

## Orden de Ejecución

| Fase | Prioridad | Dependencias | Estimación |
|------|-----------|-------------|------------|
| 0.1 | Alta | Ninguna | 1-2 sesiones |
| 0.2 | Alta | 0.1 | 1 sesión |
| 1.1 | Alta | 0.1 | Media sesión |
| 1.2 | Media | 1.1 | Media sesión |
| 1.3 | Alta | 1.1 | Media sesión |
| 1.4 | Media | 1.1, 1.3 | Media sesión |
| 1.5 | Baja | 1.3 | Media sesión |
| 2.1 | Alta | 0.2 | 1 sesión |
| 2.2 | Media | 1.2 | Media sesión |
| 2.3 | Media | 0.2 | 15 min |
| 3.1 | Alta | 2.1 | Media sesión |
| 3.2 | Media | 1.2 | Media sesión |
| 3.3 | Baja | 2.1 | 10 min |
| 4.1 | Alta | 2.1, 0.2 | Media sesión |
| 4.2 | Alta | 2.1, 0.2 | Media sesión |
| 5.1 | Media | 1.2 | Media sesión |
| 5.2 | Alta | 0.1 | 1 sesión |
| 6.1-6.3 | Media | Todas las anteriores | Media sesión |
| 7.1-7.2 | Baja | Tras fase 8 | 10 min |
| 8.1-8.3 | Alta | Todas | 1 sesión |

---

## Archivos Afectados

| Archivo | Tipo de Cambio |
|---------|---------------|
| `memory/blog.dbml` | Ya actualizado |
| `memory/blog.db` | Modificar — Añadir tablas, migrar datos |
| `memory/scripts/db_init.py` | **Nuevo** |
| `memory/scripts/db_query.py` | **Nuevo** |
| `.opencode/rules/memory-system.md` | **Nuevo** — Regla general de memoria (reemplaza `post-ideas-memory.md`) |
| `.opencode/rules/post-ideas-memory.md` | **Eliminado** — Reemplazado por `memory-system.md` |
| `.opencode/rules/execution-logging.md` | Actualizar referencias |
| `.opencode/rules/internal-links-insertion.md` | Actualizar score_weight |
| `.opencode/commands/create-post.md` | Reescribir pasos 0, 4.5, 8 |
| `.opencode/commands/generate-post-ideas.md` | Reescribir paso 3 |
| `.opencode/skills/publish-wordpress/SKILL.md` | Reescribir paso 2 |
| `.opencode/skills/link-related-posts/SKILL.md` | Actualizar docs |
| `.opencode/skills/link-related-posts/scripts/manage-internal-links.py` | Refactorizar |
| `.opencode/skills/search-game-candidates/SKILL.md` | Actualizar referencia |
| `memory/README.md` | Reescribir |
| `AGENTS.md` | Actualizar sección memoria |
| `README.md` | Actualizar referencias |
| `memory/tags-usables.md` | Mover a backup |
| `memory/post-ideas.md` | Mover a backup |

---

## Schema de Referencia

El schema completo está en `memory/blog.dbml`. Resumen de tablas:

```
tag_groups (id, slug, name, score_weight, description, created_at)
    ↓
tags (wp_id PK, name, slug, group_id → tag_groups, created_at)

posts (wp_id PK, title, slug, category_slug, status, published_at, created_at, updated_at)
    ↓
post_tags (post_wp_id → posts, tag_wp_id → tags)

post_ideas (id, title, sistema, tipo[enum], estado[enum], modo[enum], angulo_editorial, justificacion, keyword_sugerida, factor_oportunidad, genero, epoca, post_wp_id → posts, created_at, updated_at)

internal_links (id, from_wp_id → posts, to_wp_id → posts, score, created_at)

Enums: post_tipo(Review, Historias, Listas), post_idea_estado(pendiente, en_uso, publicado), post_modo(editorial, seo_master)
```