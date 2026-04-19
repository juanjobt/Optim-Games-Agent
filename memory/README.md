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

1. **Consultar pendientes** — `db_query.py get-pending-ideas`
2. **Idea nueva** — `db_query.py add-idea`
3. **Cambiar estado** — `db_query.py update-idea-state`

**Estados:** pendiente → en_uso → publicado

## Consultas habituales

```bash
# Ideas pendientes
python3 memory/scripts/db_query.py get-pending-ideas

# Detalle de una idea
python3 memory/scripts/db_query.py get-idea --id 5

# Tags de un grupo
python3 memory/scripts/db_query.py get-tags-by-group --group sistema

# Buscar o crear tag
python3 memory/scripts/db_query.py get-or-create-tag --name "Super Nintendo" --group sistema

# Registrar post
python3 memory/scripts/db_query.py add-post --wp-id 123 --title "..." --slug "..." --category-slug reviews
```