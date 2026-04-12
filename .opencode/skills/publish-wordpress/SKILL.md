---
name: publish-wordpress
description: Publica o actualiza posts completos en WordPress dado un título y un contenido. Gestiona categorías y tags. Orquesta el flujo completo de publicación. Recibe game_data para resolver tags contra la memoria tags-usables.md. Usa la skill upload-wordpress-image para la imagen de portada si se proporciona URL. Usar cuando se necesite publicar contenido en optimpixel.com.
compatibility: Requiere WordPress MCP configurado, acceso a internet y credenciales en .env
metadata:
  author: optimbyte
  version: "2.0"
allowed-tools: wp_add_post wp_update_post wp_get_post wp_posts_search wp_list_categories wp_list_tags wp_add_category wp_add_tag
---

# Skill: Publicar en WordPress

Flujo completo de publicación de un post en WordPress via MCP:
1. Resolver la categoría a partir del tipo de post
2. Generar y validar tags a partir de game_data contra tags-usables.md
3. Crear el post con categoría, tags y contenido
4. Subir y asignar la imagen de portada (si hay URL)

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

---

## Herramientas MCP disponibles

- `wp_add_post` — Crea un nuevo post (usar en vez de wp_create_post)
- `wp_update_post` — Actualiza un post existente por ID
- `wp_posts_search` — Consulta posts existentes
- `wp_list_categories` — Lista categorías con sus IDs
- `wp_list_tags` — Lista tags con sus IDs
- `wp_add_category` — Crea una categoría si no existe
- `wp_add_tag` — Crea un tag si no existe

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

**OBLIGATORIO** — Este paso genera los tags basándose en `game_data` y los valida contra la memoria.

### 2.1 — Extraer información de game_data

Del objeto `game_data` recibido como input, extraer:
- `system` → Sistema/s del juego (array)
- `genre` → Género/s (array)
- `developer` → Desarrolladora
- `era` → Época (década)
- `year` → Año de lanzamiento (si aplica)
- `saga` → Saga (si aplica)

Si se requiere, se puede investigar en fuentes externas para completar información adicional (creador, compositor, país, técnica, personaje).

### 2.2 — Consultar memoria de tags

1. Leer `memory/tags-usables.md` (fuente de verdad)
2. Consultar los grupos disponibles: Sistema, Género, Época, Año, Desarrolladora, Creador, Saga, País, Técnica, Personaje, Compositor

### 2.3 — Mapear game_data a tags

- Por cada elemento de game_data, buscar el tag equivalente en la memoria
- Si hay variaciones (ej: "SNES" → "Super Nintendo", "action" → "Acción"), **USAR SIEMPRE** el tag de la memoria
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

### 2.4 — Añadir tags nuevos

Si un tag necesario NO existe en `memory/tags-usables.md`:
- Añadirlo automáticamente al archivo con el grupo correspondiente y fecha actual
- Usar el tag en el post

### 2.5 — Resolver IDs en WordPress

```
wp_list_tags()
```

- Si el tag existe en WP con el mismo nombre → usar su ID
- Si el tag NO existe en WP → crearlo con `wp_add_tag(name: "Nombre del tag")` y obtener su ID
- Construir el array de IDs de tags para el Paso 3

### Resultado del paso

Anotar:
- Lista de tags usados (nombres, mapeados a la memoria)
- IDs de tags en WordPress
- Tags nuevos añadidos a `memory/tags-usables.md`

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

## Paso 5 — Reporte final

```
✅ URL del post publicado
📂 Categoría asignada
🏷️ Tags: [lista] (X existentes + Y nuevos añadidos a memoria)
✅ Validación de tags: completada vs memory/tags-usables.md
🖼️ Imagen de portada: asignada correctamente / ⚠️ pendiente (sin URL)
🕐 Fecha y hora de publicación
```

**Importante:** En el reporte, indicar cuántos tags nuevos se añadieron a `memory/tags-usables.md`.

Si la imagen quedó pendiente, indica en el reporte que el usuario puede añadirla manualmente desde el panel de WordPress.

---

## Manejo de errores comunes

**Categoría o tag no encontrado** — Usar `wp_add_category` o `wp_add_tag` antes de asignar.

**Token JWT expirado** — Duración máxima 24h. Regenerar en **Ajustes → WordPress MCP → Authentication Tokens** y actualizar `.env`.

**Herramienta no disponible** — Verificar que *Enable Create Tools* y *Enable Update Tools* están activos en **Ajustes → WordPress MCP → General Settings**.