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

## Comandos útiles para inspeccionar blog.db manualmente

```bash
# Ver todos los posts registrados
sqlite3 memory/blog.db "SELECT wp_post_id, title, plataforma, genero, saga FROM posts;"

# Ver posts sin links salientes
sqlite3 memory/blog.db "
  SELECT p.title, COUNT(il.id) as links
  FROM posts p
  LEFT JOIN internal_links il ON il.from_post_id = p.id
  GROUP BY p.id HAVING links < 2;
"

# Ver todos los internal links registrados
sqlite3 memory/blog.db "
  SELECT f.title as desde, t.title as hacia, il.score
  FROM internal_links il
  JOIN posts f ON f.id = il.from_post_id
  JOIN posts t ON t.id = il.to_post_id
  ORDER BY il.created_at DESC;
"

# Estadísticas rápidas
python scripts/manage-internal-links.py stats
```