---
name: link-related-posts
description: Gestiona los internal links entre posts de Optim Pixel. Busca posts relacionados via WordPress REST API, aplica scoring de similitud y registra los enlaces creados en una tabla SQLite. La inserción editorial de enlaces se gestiona mediante la regla internal-links-insertion.
---

# Skill: Link Related Posts

Esta skill gestiona los **internal links** entre posts de Optim Pixel. La información de los posts se obtiene directamente desde WordPress via REST API, y solo se guarda un log de los enlaces insertados en SQLite.

**Para la inserción editorial de enlaces** (dónde y cómo insertar los links en el HTML del post), consulta la regla `internal-links-insertion.md`.

---

## El script y sus comandos

Ruta del script: `.opencode/skills/link-related-posts/scripts/manage-internal-links.py`
Ruta de la base de datos: `memory/blog.db` (se crea automáticamente con `init`)

### Inicializar la base de datos (solo la primera vez)

```bash
python3 scripts/manage-internal-links.py init
```

Crea `memory/blog.db` con la tabla `internal_links`. Si ya existe, no hace nada.

### Buscar posts relacionados

```bash
python3 scripts/manage-internal-links.py find-related \
  --wp-id 42 \
  --tags "sistema:Super Nintendo,genero:RPG,saga:Final Fantasy,desarrolladora:Square,epoca:Años 90" \
  --limit 5
```

**Formato de tags**: `tipo:valor` separado por comas.

Tipos soportados y su puntuación:

| Tipo | Puntos | Ejemplo |
|------|--------|---------|
| `saga` | +3 | `saga:Final Fantasy` |
| `sistema` | +2 | `sistema:Super Nintendo` |
| `genero` | +1 | `genero:RPG` |
| `desarrolladora` | +1 | `desarrolladora:Square` |
| `epoca` | +1 | `epoca:Años 90` |
| (sin tipo) | +1 | `Square` (tag común) |

**Cómo funciona**:
1. El agente determina el tipo de cada tag basándose en su contexto
2. Para cada tag, busca posts que contengan ese tag en WordPress
3. Acumula los scores de todos los tags
4. Devuelve los posts ordenados por score descendente

**Usar los 2 primeros resultados** del listado como posts a enlazar, siempre que su score sea > 0.

### Registrar un internal link creado

```bash
python3 scripts/manage-internal-links.py log-link \
  --from-wp-id "42" \
  --to-wp-id "17" \
  --score 8
```

Llamar una vez por cada enlace insertado en el post. El `--score` es el valor que devolvió `find-related` para ese post destino.

### Obtener el contenido de un post

```bash
python3 scripts/manage-internal-links.py get-post-content --wp-id 42
```

Devuelve el contenido HTML actual del post (campo `content.raw` de la WP REST API). Útil para obtener el contenido antes de insertar enlaces.

### Verificar enlaces de un post

```bash
python3 scripts/manage-internal-links.py get-links --wp-id 10
```

Devuelve los enlaces salientes (outgoing) y entrantes (incoming) de un post. Útil para verificar qué enlaces ya existen antes de procesar un post.

**Nota**: El comando `find-related` excluye automáticamente los destinos que ya tienen enlace desde el post origen, para evitar duplicados y hacer la red más dispersiva.

### Posts que necesitan links

```bash
python3 scripts/manage-internal-links.py needs-links --limit 20
```

Devuelve los posts con menos de 2 outgoing links, ordenados por fecha de publicación (más antiguos primero). Útil para el comando `/link-posts`.

### Estadísticas generales

```bash
python3 scripts/manage-internal-links.py stats
```

Útil para dar feedback al usuario o para que el agente decida si vale la pena ejecutar `/link-posts`.

---

## Flujo genérico de uso

### Contexto A: Después de publicar un post (create-post)

1. Preparar los tags con su tipo: `sistema:X,genero:Y,saga:Z...`
2. Buscar relacionados con `find-related`
3. Obtener el contenido actual con `get-post-content`
4. **Insertar los enlaces siguiendo la regla `internal-links-insertion.md`**
5. Registrar cada link creado con `log-link`

### Contexto B: Mejorar posts existentes (/link-posts)

1. Obtener lista de posts que necesitan links: `needs-links`
2. Para cada post:
   a. Obtener el contenido actual con `get-post-content`
   b. Preparar los tags con su tipo: `sistema:X,genero:Y,saga:Z...`
   c. Buscar relacionados con `find-related`
   d. **Insertar los enlaces siguiendo la regla `internal-links-insertion.md`**
   e. Registrar cada link creado con `log-link`

---

## Manejo de errores

**El script devuelve `"ok": false`** — Leer el campo `"error"` del JSON y reportarlo. El internal linking es un paso de mejora, no debe bloquear otras operaciones.

**`memory/blog.db` no existe** — Ejecutar `init` primero. El script crea el directorio `memory/` si no existe.

**Se requiere --tags** — El comando `find-related` ahora requiere el argumento `--tags` con el formato `tipo:valor`.

---

## Integración con WordPress MCP

La skill delega la manipulación del contenido del post a WordPress MCP:

- **Obtener contenido**: `wp_get_post(id, context="edit")`
- **Actualizar contenido**: `wp_update_post(id, content)`

Alternativamente, usar el comando `get-post-content` del script que hace esta llamada automáticamente.
