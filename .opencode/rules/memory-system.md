# Rule: Memory System — Optim Pixel

## Propósito

El agente usa `memory/blog.db` (SQLite) como única fuente de verdad para tags, posts, ideas y enlaces internos. El schema está definido en `memory/blog.dbml` — consultar ese archivo si se necesita entender la estructura de las tablas.

Los archivos markdown legacy (`memory/tags-usables.md`, `memory/post-ideas.md`) están en `memory/backup/` y **no deben usarse**.

---

## Interfaz de consultas

Todas las operaciones sobre la memoria se realizan mediante `memory/scripts/db_query.py`. El agente no debe leer ni escribir directamente sobre `blog.db` con SQL — debe usar siempre los subcomandos del script, que devuelven JSON.

### Post Ideas

| Operación | Comando |
|-----------|---------|
| Ideas pendientes | `python3 memory/scripts/db_query.py get-pending-ideas [--limit N]` |
| Detalle de una idea | `python3 memory/scripts/db_query.py get-idea --id N` |
| Cambiar estado | `python3 memory/scripts/db_query.py update-idea-state --id N --state pendiente\|en_uso\|publicado [--wp-id N]` |
| Añadir idea | `python3 memory/scripts/db_query.py add-idea --title "..." --sistema "..." --tipo Review --modo editorial --angulo "..." [...]` |

### Tags

| Operación | Comando |
|-----------|---------|
| Tags por grupo | `python3 memory/scripts/db_query.py get-tags-by-group --group sistema` |
| Buscar o crear tag | `python3 memory/scripts/db_query.py get-or-create-tag --name "Super Nintendo" --group sistema` |
| Añadir tag nuevo | `python3 memory/scripts/db_query.py add-tag --name "..." --slug "..." --group sistema --wp-id N` |

### Posts

| Operación | Comando |
|-----------|---------|
| Registrar post | `python3 memory/scripts/db_query.py add-post --wp-id N --title "..." --slug "..." --category-slug reviews` |
| Consultar post | `python3 memory/scripts/db_query.py get-post --wp-id N` |
| Sincronizar desde WP | `python3 memory/scripts/db_query.py sync-posts-from-wp` |

---

## Tablas principales

| Tabla | Propósito |
|-------|-----------|
| `tag_groups` | 11 grupos de tags con `score_weight` para similitud |
| `tags` | Tags del blog con `wp_id`, `slug` y relación a grupos |
| `posts` | Catálogo local de posts publicados |
| `post_tags` | Relación many-to-many posts ↔ tags |
| `post_ideas` | Cola editorial con campos estructurados |
| `internal_links` | Registro de enlaces entre posts con score |

El schema completo con tipos, restricciones y relaciones está en `memory/blog.dbml`.

---

## Estados de una idea

| Estado | Significado |
|--------|-------------|
| `pendiente` | Generada pero sin usar |
| `en_uso` | En proceso de creación |
| `publicado` | Publicado en WordPress, con `post_wp_id` vinculado |

La tabla `post_ideas` tiene restricción `UNIQUE` en `title` — no se pueden registrar dos ideas con el mismo juego. Los campos `keyword_sugerida` y `factor_oportunidad` solo se rellenan en modo `seo_master`.

---

## Pesos de similitud

Los pesos están en `tag_groups.score_weight`:

| Grupo | Peso |
|-------|------|
| Saga | 4 |
| Sistema | 3 |
| Género | 2 |
| Época / Año / Desarrolladora / Creador / País / Técnica / Personaje / Compositor | 1 |

El script `manage-internal-links.py find-related` usa estos pesos automáticamente desde la tabla `tag_groups`.

---

## Reglas generales

1. **No editar `blog.db` directamente** — usar siempre `db_query.py`
2. **No usar archivos markdown legacy** — están en `memory/backup/` como referencia histórica
3. **Consultar `blog.dbml`** para entender el schema completo
4. **Los `wp_id` de tags se resuelven automáticamente** — si un tag existe en la DB con `wp_id`, se usa ese ID; si no existe, se crea en WordPress y se registra

---

## Consulta de la memoria

Si el usuario pregunta por el estado de las ideas (ej: "¿qué ideas tenemos pendientes?", "¿qué posts hemos publicado?"), el agente debe:

1. Ejecutar el subcomando correspondiente de `db_query.py`
2. Presentar la información de forma clara y resumida
3. No volcar datos técnicos (IDs internos) a menos que se pidan explícitamente