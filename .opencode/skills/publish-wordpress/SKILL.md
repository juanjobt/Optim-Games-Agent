---
name: publish-wordpress
description: Publica o actualiza posts completos en WordPress dado un título y un contenido. Gestiona categorías y tags. Orquesta el flujo completo de publicación. Recibe game_data para resolver tags contra la base de datos local (memory/blog.db). Usa la skill upload-wordpress-image para la imagen de portada si se proporciona URL. Usar cuando se necesite publicar contenido en optimpixel.com.
compatibility: Requiere WordPress MCP configurado, acceso a internet y credenciales en .env
metadata:
  author: optimbyte
  version: "3.0"
  allowed-tools: wp_add_post wp_update_post wp_get_post wp_posts_search wp_list_categories wp_list_tags wp_add_category wp_add_tag
---

# Skill: Publicar en WordPress

Flujo completo de publicación de un post en WordPress via MCP:
1. Resolver la categoría a partir del tipo de post
2. Generar y validar tags a partir de game_data contra la base de datos local
3. Crear el post con categoría, tags y contenido
4. Subir y asignar la imagen de portada (si hay URL)
5. Registrar el post y sus tags en la base de datos local

**Fuente de verdad para tags:** `memory/blog.db` (tabla `tags`). Todas las consultas de tags se hacen mediante `memory/scripts/db_query.py`.

---

## Inputs

Obligatorios:
- `title` — Título del post
- `slug` — Slug para la URL (minúsculas, guiones, sin artículos)
- `content` — Contenido HTML completo del post
- `excerpt` — Extracto/snippet de 150-160 caracteres
- `type` — Tipo de post: `"review"` | `"historia"` | `"lista"`
- `game_data` — Objeto con los datos del juego:
  ```
  {
    name: "Chrono Trigger",
    system: ["Super Nintendo"],
    genre: ["RPG"],
    developer: "Square",
    publisher: "Square",
    era: "Años 90",
    year: 1995,
    saga: "Saga Chrono"       // si aplica
  }
  ```
- `status` — `"publish"` o `"draft"`

Opcionales:
- `image_url` — URL pública de la imagen de portada (obtenida previamente con find-game-image). Si es `null`, se publica sin imagen.
- `content_images` — Array de imágenes de contenido ya subidas a WordPress (screenshots, conceptos). Cada elemento:
  ```
  {
    "media_id": 42,
    "source_url": "https://optimpixel.com/wp-content/uploads/...",
    "alt": "Captura de pantalla de Chrono Trigger",
    "type": "screenshot",
    "caption": "Chrono Trigger en la Super Nintendo"
  }
  ```
  Estas imágenes ya están incrustadas en el `content` HTML como `<figure>` por el comando create-post. La skill no las inserta — son solo para el reporte final.

---

## Herramientas MCP disponibles

- `wp_add_post` — Crea un nuevo post
- `wp_update_post` — Actualiza un post existente por ID
- `wp_posts_search` — Consulta posts existentes
- `wp_list_categories` — Lista categorías con sus IDs
- `wp_list_tags` — Lista tags con sus IDs
- `wp_add_category` — Crea una categoría si no existe
- `wp_add_tag` — Crea un tag si no existe

## Herramientas de memoria local

Ejecutar con `python3 memory/scripts/db_query.py`:

| Comando | Uso |
|---------|-----|
| `get-tags-by-group --group <grupo>` | Lista tags existentes de un grupo (con wp_id) |
| `get-tag --name "Nombre"` | Busca un tag por nombre exacto |
| `get-or-create-tag --name "Nombre" --group <grupo>` | Obtiene un tag o lo crea si no existe |
| `add-tag --name "Nombre" --slug "slug" --group <grupo> --wp-id N` | Crea un tag nuevo en la DB |
| `add-post --wp-id N --title "..." --slug "..." --category-slug <slug>` | Registra un post publicado en la DB |
| `add-post-tags --wp-id N --tag-ids 12,34,56` | Registra relaciones post↔tags en la DB |

---

## Paso 1 — Resolver ID de categoría

```
wp_list_categories()
```

**Mapeo de tipos a categorías** (una sola por post):

| type | Slug de categoría | Nombre |
|---|---|---|
| `review` | `reviews` | Reviews |
| `historia` | `historias` | Historias |
| `lista` | `listas` | Listas |

Buscar la categoría cuyo slug coincida con el mapeo. Si no existe, crearla:
```
wp_add_category(name: "Reviews", slug: "reviews")
```

Anotar el `ID` de la categoría para el Paso 3.

---

## Paso 2 — Generar y validar tags del post

**OBLIGATORIO** — Este paso genera los tags basándose en `game_data` y los valida contra la base de datos local.

### 2.1 — Extraer información de game_data

Del objeto `game_data` recibido como input, extraer:
- `system` → Sistema/s del juego (array)
- `genre` → Género/s (array)
- `developer` → Desarrolladora
- `era` → Época (década)
- `year` → Año de lanzamiento (si aplica)
- `saga` → Saga (si aplica)

Si se requiere, se puede investigar en fuentes externas para completar información adicional (creador, compositor, país, técnica, personaje).

### 2.2 — Consultar tags disponibles en la DB

Para cada grupo relevante según `game_data`, consultar los tags existentes en la base de datos local:

```bash
python3 memory/scripts/db_query.py get-tags-by-group --group sistema
python3 memory/scripts/db_query.py get-tags-by-group --group genero
python3 memory/scripts/db_query.py get-tags-by-group --group epoca
python3 memory/scripts/db_query.py get-tags-by-group --group ano
python3 memory/scripts/db_query.py get-tags-by-group --group desarrolladora
python3 memory/scripts/db_query.py get-tags-by-group --group saga
```

Consultar también grupos opcionales si game_data los incluye:
```bash
python3 memory/scripts/db_query.py get-tags-by-group --group creador
python3 memory/scripts/db_query.py get-tags-by-group --group compositor
python3 memory/scripts/db_query.py get-tags-by-group --group pais
python3 memory/scripts/db_query.py get-tags-by-group --group tecnica
python3 memory/scripts/db_query.py get-tags-by-group --group personaje
```

Cada comando devuelve JSON estructurado con la lista de tags del grupo, incluyendo `wp_id`, `name`, `slug` y `group_slug`. Los tags que ya estén en la DB local con `wp_id` se usan directamente sin necesidad de consultar WordPress.

### 2.3 — Mapear game_data a tags

- Por cada elemento de game_data, buscar el tag equivalente en los resultados del paso 2.2
- Si hay variaciones (ej: "SNES" → "Super Nintendo", "action" → "Acción"), **USAR SIEMPRE** el tag que aparece en la DB local
- **Tags obligatorios por grupo**: Sistema, Género, Época, Año, Desarrolladora
- **Tags opcionales**: Saga, Creador, Compositor, País, Técnica, Personaje

#### Regla especial: Tags de Sistema para juegos multiplataforma

Muchos juegos clásicos salieron en múltiples sistemas. No todos los sistemas tienen la misma relevancia para un juego dado. Aplicar la regla de **sistema principal + sistema secundario relevante**:

**Principio:** Se añade el sistema donde el juego nació o fue más icónico obligatoriamente, y opcionalmente un segundo sistema solo si el juego tuvo impacto cultural real en esa plataforma. Nunca añadir ports menores.

**Reglas:**

1. **Sistema principal** (obligatorio, 1): la plataforma donde el juego se lanzó originalmente o donde es más recordado/icónico
2. **Sistema secundario** (opcional, máximo 1): solo si el juego tuvo un impacto cultural real en esa plataforma — no añadir ports que nadie recuerda
3. **Máximo 2 tags de sistema por post individual** (review o historia)
4. **Para posts de lista**: máximo 1 tag de sistema por juego mencionado (el principal), se añaden los sistemas principales de los juegos destacados en la lista
5. **Nunca añadir tags de sistema para ports irrelevantes** — si la versión de Amiga fue un port mediocre, no se añade "Amiga"

**Criterio para decidir si un sistema secundario es relevante:**

- ¿Esa versión se menciona frecuentemente como referencia del juego? (ej: The Last Ninja en ZX Spectrum sí se menciona)
- ¿El juego fue exclusivo o significativamente diferente en esa plataforma?
- ¿Esa versión tiene una base de jugadores que la recuerdan como "su" versión?

Si la respuesta a todas es "no", solo se añade el sistema principal.

**Ejemplos:**

| Juego | Tags de sistema | Justificación |
|---|---|---|
| The Last Ninja | Commodore 64, ZX Spectrum | Icónico en C64, relevante en Spectrum. Los ports de Amiga/Atari ST fueron menores |
| Chrono Trigger | Super Nintendo | Exclusivo de SNES (originalmente) |
| Metal Gear Solid | PlayStation | Exclusivo de PS1 en su momento |
| Lista "Top 10 de los 80" | Los sistemas principales de cada juego | 1 sistema por juego, sin repetir ports menores |

**Cuando game_data.system traiga múltiples sistemas**, el agente debe filtrar aplicando esta regla antes de convertirlos a tags. No pasar el array completo sin filtrar.

### 2.4 — Resolver IDs de WordPress

Para **cada tag** necesario del paso 2.3, resolver su ID de WordPress siguiendo este flujo:

#### Caso A: Tag encontrado en la DB local

Si el tag aparece en los resultados del paso 2.2 con un `wp_id` válido, usar ese `wp_id` directamente. **No es necesario llamar a `wp_list_tags`.**

Este es el caso más común — la DB local ya tiene los `wp_id` sincronizados con WordPress.

#### Caso B: Tag no encontrado en la DB local

Si un tag necesario no aparece en los resultados del paso 2.2:

1. **Derivar el slug esperado** del nombre:
   - Minúsculas, espacios → guiones, sin acentos (ej: "Años 80" → `anos-80`)

2. **Buscar en WordPress por slug**:
   ```
   wp_list_tags(slug=["slug-derivado"])
   ```

3. **Si existe en WordPress**: Obtener su `id` real y registrarlo en la DB local:
   ```bash
   python3 memory/scripts/db_query.py add-tag --name "Nombre" --slug "slug-derivado" --group grupo --wp-id ID_DE_WP
   ```
   Anotar el `wp_id` para el post.

4. **Si no existe en WordPress**: Crear el tag en WordPress:
   ```
   wp_add_tag(name: "Nombre del Tag")
   ```
   Anotar el `id` devuelto por WordPress y registrarlo en la DB local:
   ```bash
   python3 memory/scripts/db_query.py add-tag --name "Nombre del Tag" --slug "slug-derivado" --group grupo --wp-id ID_DE_WP
   ```

#### Ejemplo completo

Tags necesarios: ZX Spectrum, Action-Adventure, Puzzle, Años 80, Commodore 64, Ocean Software

Consulta local (`get-tags-by-group` para cada grupo relevante) → Resultados:
- ZX Spectrum → wp_id: 45 (en DB local)
- Action-Adventure → wp_id: 80 (en DB local)
- Puzzle → wp_id: 19 (en DB local)
- Años 80 → wp_id: 28 (en DB local)
- Commodore 64 → wp_id: 107 (en DB local)
- Ocean Software → no está en DB local → resolver vía WordPress

Tag Ocean Software:
1. Derivar slug: `ocean-software`
2. `wp_list_tags(slug=["ocean-software"])` → no encontrado
3. `wp_add_tag(name: "Ocean Software")` → id: 233
4. `add-tag --name "Ocean Software" --slug "ocean-software" --group desarrolladora --wp-id 233`

Array final para `wp_add_post`: `tags: [45, 80, 19, 28, 107, 233]`

#### Verificación

Antes de pasar al Paso 3, confirmar que cada ID del array corresponde al tag correcto mostrando la tabla:

```
| Tag            | Slug esperado     | Origen     | ID en WP |
|----------------|-------------------|------------|----------|
| ZX Spectrum    | zx-spectrum       | DB local   | 45       |
| Puzzle         | puzzle            | DB local   | 19       |
| Ocean Software | ocean-software    | WP (nuevo) | 233      |
| ...            | ...               | ...        | ...      |
```

### Resultado del paso

Anotar:
- Lista de tags usados (nombres, grupo, origen)
- IDs de tags en WordPress
- Tags nuevos creados y registrados en la DB local

---

## Paso 3 — Publicar el post

```
wp_add_post(
  title: "Título del post",
  slug: "slug-del-post",
  content: "<p>Contenido completo en HTML...</p>",
  excerpt: "Extracto de 150-160 caracteres",
  status: "publish",
  categories: [ID_categoria],
  tags: [ID_tag_1, ID_tag_2, ...]
  # NOTA: No incluir featured_media aquí — se asigna en Paso 4
)
```

Anotar el `post_id` devuelto y la `URL` pública del post.

---

## Paso 4 — Subir y asignar imagen de portada

**Si `image_url` no es null:**
1. Usa la skill `upload-wordpress-image` para subir la imagen y asignarla al post recién creado
2. Ejecuta el script con la URL y el `post_id`
3. Verifica que `featured_media` tiene valor no-zero en el post

**Si `image_url` es null:**
- Continúa sin imagen y anota la advertencia en el reporte final

**Importante:** La skill `upload-wordpress-image` ejecuta un script Python que gestiona la descarga, subida multipart y asignación de featured image. No usar herramientas MCP para la subida de imagen.

---

## Paso 5 — Registrar en la base de datos local

Tras publicar el post en WordPress, registrar tanto el post como sus tags en la DB local para mantener sincronizada la memoria. Esto es esencial para que `find-related` (internal links) funcione correctamente con los posts nuevos.

### 5.1 — Registrar el post

```bash
python3 memory/scripts/db_query.py add-post \
  --wp-id POST_ID \
  --title "Título del post" \
  --slug "slug-del-post" \
  --category-slug reviews
```

Usar `reviews`, `historias` o `listas` según el tipo de post.

### 5.2 — Registrar las relaciones post↔tags

```bash
python3 memory/scripts/db_query.py add-post-tags --wp-id POST_ID --tag-ids "45,80,19,28,107,233"
```

Los IDs son los `wp_id` de los tags obtenidos en el Paso 2 (los mismos usados para crear el post en WordPress).

Este paso es **obligatorio** — sin él, el post no tendrá tags en la DB local y el sistema de internal links no podrá encontrar posts relacionados por tags.

---

## Paso 6 — Reporte final

```
✅ URL del post publicado
📂 Categoría asignada
🏷️ Tags: [lista] (X desde DB local + Y nuevos creados y registrados)
✅ Validación de tags: completada vs memory/blog.db
🖼️ Imagen de portada: asignada correctamente / ⚠️ pendiente (sin URL)
🖼️ Imágenes de contenido: X screenshots + Y conceptos / ⚠️ pendientes
📝 Post registrado en DB local: sí (wp_id=X, tags=Y)
🕐 Fecha y hora de publicación
```

**Verificación de tags:** Incluir la tabla de mapeo tag → ID en WordPress para confirmar que los IDs son correctos. Si algún ID no corresponde al tag esperado, detener la publicación y corregir.

Si la imagen de portada quedó pendiente, indica en el reporte que el usuario puede añadirla manualmente desde el panel de WordPress.

---

## Manejo de errores comunes

**Categoría no encontrada** — Usar `wp_add_category` antes de asignar.

**Tag no encontrado en la DB local ni en WordPress** — Crear con `wp_add_tag` y luego registrar en la DB local con `db_query.py add-tag`.

**Error al registrar post/Tags en DB local** — No bloquea la publicación del post en WordPress. Reportar el error y ejecutar `python3 memory/scripts/db_init.py sync-posts-wp` para resincronizar.

**Token JWT expirado** — Duración máxima 24h. Regenerar en **Ajustes → WordPress MCP → Authentication Tokens** y actualizar `.env`.

**Herramienta no disponible** — Verificar que *Enable Create Tools* y *Enable Update Tools* están activos en **Ajustes → WordPress MCP → General Settings**.