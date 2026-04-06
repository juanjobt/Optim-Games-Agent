---
name: link-related-posts
description: Gestiona los internal links entre posts de Optim Pixel. Registra posts publicados en blog.db, busca posts relacionados por scoring de similitud y registra los links creados. Es la base de datos del sistema de internal linking. La inserción editorial de enlaces se gestiona mediante la regla internal-links-insertion.
---

# Skill: Link Related Posts

Esta skill gestiona la **base de datos de internal linking** y sus comandos principales. Toda la lógica de datos se delega al script `scripts/manage-internal-links.py`. El agente nunca escribe SQL directamente — solo llama al script con los argumentos correctos y procesa el JSON que devuelve.

**Para la inserción editorial de enlaces** (dónde y cómo insertar los links en el HTML del post), consulta la regla `internal-links-insertion.md`.

---

## El script y sus comandos

Ruta del script: `scripts/manage-internal-links.py`  
Ruta de la base de datos: `memory/blog.db` (se crea automáticamente con `init`)

### Inicializar la base de datos (solo la primera vez)

```bash
python scripts/manage-internal-links.py init
```

Crea `memory/blog.db` con todas las tablas e índices. Si ya existe, no hace nada. Llamar siempre antes de cualquier otra operación si no se ha usado antes.

### Registrar un post publicado

```bash
python scripts/manage-internal-links.py register \
  --wp-id "42" \
  --title "Chrono Trigger: el caos creativo del desarrollo" \
  --url "https://games.optimbyte.com/chrono-trigger-desarrollo" \
  --tipo "Historias" \
  --plataforma "Super Nintendo" \
  --genero "RPG" \
  --saga "Chrono" \
  --desarrolladora "Square" \
  --epoca "Años 90" \
  --tags "Square,RPG,viajes en el tiempo,Años 90,desarrollo,dream team"
```

- `--wp-id` es el ID que devuelve WordPress al publicar el post (campo `id` en la respuesta de `wp_create_post`)
- `--tags` son los mismos tags que se han asignado en WordPress, separados por comas
- Todos los campos excepto `--wp-id`, `--title` y `--url` son opcionales pero cuantos más se pasen, mejor será el matching futuro
- Si el `wp-id` ya existe en la base de datos, actualiza los metadatos sin duplicar

### Buscar posts relacionados

```bash
python scripts/manage-internal-links.py find-related \
  --wp-id "42" \
  --plataforma "Super Nintendo" \
  --genero "RPG" \
  --saga "Chrono" \
  --desarrolladora "Square" \
  --epoca "Años 90" \
  --tags "Square,RPG,viajes en el tiempo,Años 90" \
  --limit 5
```

Devuelve un JSON con los posts más relacionados ordenados por score. El score se calcula así:

| Coincidencia | Puntos |
|---|---|
| Misma saga | +3 |
| Misma plataforma | +2 |
| Mismo género | +1 |
| Misma desarrolladora | +1 |
| Misma época | +1 |
| Cada tag compartido | +1 |

**Usar los 2 primeros resultados** del listado como posts a enlazar, siempre que su score sea > 0. Si todos tienen score 0, no hay posts suficientemente relacionados.

### Registrar un internal link creado

```bash
python scripts/manage-internal-links.py log-link \
  --from-wp-id "42" \
  --to-wp-id "17" \
  --score 8
```

Llamar una vez por cada enlace insertado en el post. El `--score` es el valor que devolvió `find-related` para ese post destino.

### Obtener el contenido de un post

```bash
python scripts/manage-internal-links.py get-post-content --wp-id "42"
```

Devuelve el contenido HTML actual del post (campo `content.raw` de la WP REST API). Útil para obtener el contenido antes de insertar enlaces.

### Posts que necesitan links

```bash
python scripts/manage-internal-links.py needs-links --limit 20
```

Devuelve los posts con menos de 2 outgoing links, ordenados por fecha de publicación (más antiguos primero). Útil para el comando `/link-posts`.

### Estadísticas generales

```bash
python scripts/manage-internal-links.py stats
```

Útil para dar feedback al usuario o para que el agente decida si vale la pena ejecutar `/link-posts`.

---

## Flujo genérico de uso

Esta skill puede usarse en dos contextos diferentes:

### Contexto A: Después de publicar un post (create-post)

1. Asegurarse de que la DB existe: `python scripts/manage-internal-links.py init`
2. Registrar el post recién publicado con `register`
3. Buscar relacionados con `find-related`
4. Obtener el contenido actual con `get-post-content`
5. **Insertar los enlaces siguiendo la regla `internal-links-insertion.md`**
6. Registrar cada link creado con `log-link`

### Contexto B: Mejorar posts existentes (/link-posts)

1. Obtener lista de posts que necesitan links: `needs-links`
2. Para cada post:
   a. Obtener el contenido actual con `get-post-content`
   b. Buscar relacionados con `find-related`
   c. **Insertar los enlaces siguiendo la regla `internal-links-insertion.md`**
   d. Registrar cada link creado con `log-link`

---

## Manejo de errores

**El script devuelve `"ok": false`** — Leer el campo `"error"` del JSON y reportarlo. El internal linking es un paso de mejora, no debe bloquear otras operaciones.

**`memory/blog.db` no existe** — Ejecutar `init` primero. El script crea el directorio `memory/` si no existe.

**Post no encontrado en `find-related`** — Significa que `register` no se ejecutó correctamente antes. Verificar que el `--wp-id` es el mismo en ambas llamadas.

---

## Integración con WordPress MCP

La skill delega la manipulación del contenido del post a WordPress MCP:

- **Obtener contenido**: `wp_get_post(id, context="edit")`
- **Actualizar contenido**: `wp_update_post(id, content)`

Alternativamente, usar el comando `get-post-content` del script que hace esta llamada automáticamente.
