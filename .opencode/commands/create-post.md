---
description: Genera y publica un post completo en el blog Optim Pixel. Guía al agente desde la elección del tema hasta la publicación final en WordPress via MCP, siguiendo la identidad y estilo del blog.
agent: content-marketer
---

Genera y publica un post completo en Optim Pixel siguiendo estos pasos en orden.

## Registro de ejecución

Antes de empezar el Paso 0, crea la cabecera del log en `memory/execution-logs/YYYY-MM-DD.md` (añade al final si ya existe) siguiendo la rule `execution-logging`. Registra cada paso a medida que se completa. Al finalizar el workflow, añade el resumen según el formato definido en la rule.

---

## Paso 0 — Determinar el tema

Antes de hacer ninguna pregunta, evalúa si ya se ha proporcionado un juego o tema en el mensaje de invocación.

**Si el usuario ya especificó un juego o tema:** continúa directamente al Paso 1 con esos datos.

**Si el usuario NO especificó nada:**
1. Lee `memory/post-ideas.md`
2. Localiza la primera entrada con estado `pendiente` (el `#` más bajo)
3. Extrae el campo `Prompt` — contiene todos los datos necesarios para este post
4. Cambia su estado a `en uso` y actualiza `Última actualización`
5. Informa brevemente antes de continuar:

```
📋 Usando idea de la cola:
Título: [título] | Tipo: [tipo] | Sistema: [sistema]
Prompt guardado listo para usar.
```

**Si la memoria está vacía:** pregunta al usuario directamente.

---

## Paso 1 — Recopilar información

**Si el post viene de la memoria (campo Prompt):**
- Parsea el campo `Prompt` de la entrada para extraer:
  - Título
  - Tipo de post (Review / Historias / Listas)
  - Sistema
  - Género
  - Época
  - Ángulo Editorial
  - Justificación
  - Keyword Sugerida (si modo=seo_master)
  - Factor de Oportunidad (si modo=seo_master)
- Usa estos datos directamente sin preguntar de nuevo.
- Solo pide clarification si algo no queda claro del parseo.

**Si el usuario especificó el tema directamente:**
- Pide los datos que falten:
  - ¿Sobre qué juego o tema es el post?
  - ¿Qué tipo de post es? (Review / Historias / Listas)
  - ¿En qué sistema o sistemas?
  - (Opcional) ¿Hay algún enfoque o ángulo concreto?

---

## Paso 2 — Investigar el tema

Antes de escribir, investiga usando tu conocimiento y las herramientas disponibles:

- Año de lanzamiento, desarrolladora, distribuidora, sistemas originales
- Contexto histórico y recepción en su época
- Datos curiosos, anécdotas de desarrollo, controversias
- Legado e influencia en juegos posteriores
- Estado actual: remasters, ports, disponibilidad

No inventes datos — si no estás seguro de algo, omítelo o indícalo claramente.

---

## Paso 3 — Generar el contenido

Según el tipo de post, carga la skill correspondiente y sigue su estructura:

- Review → skill `generate-post-review`
- Historias → skill `generate-post-history`
- Listas → skill `generate-post-list`

Escribe el post completo en HTML limpio siguiendo la estructura de la skill y la voz del blog definida en `blog-identity`.

---

## Paso 4 — Preparar datos de publicación

Genera estos campos que se usarán al publicar en WordPress:

- **Título** — Atractivo, con la keyword principal incluida de forma natural
- **Slug** — Minúsculas, con guiones, sin artículos innecesarios (ej: `review-chrono-trigger-snes`)
- **Excerpt** — 150-160 caracteres, será el snippet en resultados de búsqueda. Incluye la keyword principal de forma natural

**Nota sobre SEO:** La keyword principal se usa como guía interna para redactar un buen título y excerpt, pero no se almacena como campo separado en WordPress. El título del post funciona como título SEO.

---

## Paso 4.5 — Consolidar game_data

Reunir en un solo objeto los datos del juego recopilados en los Pasos 0-2. Este objeto se pasará a la skill `publish-wordpress` para que resuelva tags automáticamente:

```
game_data = {
  name: "Chrono Trigger",
  type: "review",            // review | historia | lista
  system: ["Super Nintendo"],
  genre: ["RPG"],
  developer: "Square",
  publisher: "Square",
  era: "Años 90",
  year: 1995,
  saga: "Saga Chrono"        // si aplica, omitir si no
}
```

Los tags NO se generan aquí — la skill `publish-wordpress` se encarga de mapear game_data a tags usando `memory/tags-usables.md`.

---

## Paso 5 — Buscar imágenes

Usa la skill `find-game-image` para localizar todas las imágenes del post. El número y tipo depende del tipo de post:

| Tipo de post | Portada | Imágenes de contenido |
|-------------|---------|----------------------|
| Review | 1 (`portada`) | 3 (`screenshot`) |
| Historia | 1 (`portada`) | 1 `screenshot` + 1 `concepto` |
| Lista | 1 (`portada`) | 1 `screenshot` por cada juego destacado del top 3-5 |

### 5.1 — Buscar portada

```
find-game-image(game_name: "Nombre del juego", image_type: "portada", count: 1)
```

Guardar la URL de la portada para el Paso 7.

### 5.2 — Buscar imágenes de contenido

**Para Review e Historia:** buscar screenshots y/o concepto artístico del juego principal:

```
find-game-image(game_name: "Nombre del juego", image_type: "screenshot", count: 3)
find-game-image(game_name: "Nombre del juego", image_type: "concepto", count: 1)
```

**Para Lista:** buscar 1 screenshot por cada juego destacado:

```
find-game-image(game_name: "Juego destacado #1", image_type: "screenshot", count: 1)
find-game-image(game_name: "Juego destacado #2", image_type: "screenshot", count: 1)
...
```

Los "juegos destacados" son los 3-5 más relevantes de la lista, elegidos por el agente.

Guardar todas las URLs de contenido para el Paso 5.5. Si alguna búsqueda devuelve menos imágenes de las esperadas, continuar con las que haya.

---

## Paso 5.5 — Subir imágenes de contenido

Las imágenes de contenido (screenshots y conceptos) se suben a la biblioteca de medios de WordPress **antes** de publicar el post, para obtener sus `source_url`.

Para cada imagen de contenido encontrada en el Paso 5.2:

```bash
python3 .opencode/skills/upload-wordpress-image/scripts/wp_upload_image.py \
  --url "URL_DE_LA_IMAGEN" \
  --game "NOMBRE_DEL_JUEGO" \
  --type screenshot \
  --env .env
```

Para concepto artístico:
```bash
python3 .opencode/skills/upload-wordpress-image/scripts/wp_upload_image.py \
  --url "URL_DE_LA_IMAGEN" \
  --game "NOMBRE_DEL_JUEGO" \
  --type concepto \
  --env .env
```

**No incluir `--post-id`** — las imágenes de contenido se suben solo a la biblioteca, no se asignan como featured image.

Anotar cada resultado:
```
media_id: 43, source_url: https://optimpixel.com/wp-content/uploads/..., type: screenshot, alt: "Captura de pantalla de Chrono Trigger"
```

### Insertar imágenes en el HTML

Después de subir todas las imágenes de contenido, insertarlas en el contenido HTML usando el formato:

```html
<figure class="aligncenter">
  <img src="https://optimpixel.com/wp-content/uploads/..." alt="Captura de pantalla de Chrono Trigger" />
  <figcaption>Chrono Trigger en la Super Nintendo</figcaption>
</figure>
```

El agente decide la posición exacta de cada imagen en el texto, siguiendo las indicaciones de la skill de generación correspondiente (review, historia o lista).

**Reglas de inserción:**
- Nunca insertar imágenes en el primer párrafo (el gancho)
- Máximo 1 imagen de contenido por párrafo/sepcción
- Insertar solo las imágenes que encajen editorialmente — no forzar
- Si no se encontró ninguna imagen de contenido, publicar sin ellas y anotarlo

---

## Paso 6 — Revisión antes de publicar

Muestra al usuario este resumen y espera confirmación:

```
📝 RESUMEN DEL POST
──────────────────────────────────────
Título: [título]
Tipo: [tipo de post]
Categoría: [categoría: Reviews / Historias / Listas]
Slug: /[slug]
Excerpt: [excerpt]
Datos del juego: [sistema], [género], [desarrolladora], [época]
Imagen de portada: [fuente y nombre] o ⚠️ Sin imagen
Imágenes de contenido: X screenshots + Y conceptos o ⚠️ Sin imágenes de contenido
Palabras: ~[número]
──────────────────────────────────────
¿Publicamos? (sí / revisar / cancelar)
```

- **revisar** → pregunta qué cambiar y vuelve al paso correspondiente
- **cancelar** → detén el proceso; si la entrada estaba `en uso` en memoria, reviértela a `pendiente`
- **sí** → continúa al Paso 7

---

## Paso 7 — Publicar en WordPress

Invocar la skill `publish-wordpress` con los siguientes inputs:

**Inputs obligatorios:**
- `title` — Título del post (del Paso 4)
- `slug` — Slug del post (del Paso 4)
- `content` — Contenido HTML completo con imágenes de contenido ya incrustadas (del Paso 3 + Paso 5.5)
- `excerpt` — Extracto del post (del Paso 4)
- `type` — Tipo de post: `"review"` | `"historia"` | `"lista"` (del Paso 4.5)
- `game_data` — Objeto con datos del juego (del Paso 4.5)
- `status` — `"publish"`

**Inputs opcionales:**
- `image_url` — URL de la imagen de portada (del Paso 5.1), o `null`
- `content_images` — Array de imágenes de contenido subidas (del Paso 5.5):
  ```
  [
    {"media_id": 43, "source_url": "https://...", "alt": "Captura de pantalla de Chrono Trigger", "type": "screenshot", "caption": "Chrono Trigger en la Super Nintendo"},
    ...
  ]
  ```

La skill se encarga de:
1. Resolver la categoría (type → slug → ID de WordPress)
2. Generar y validar tags a partir de game_data contra `memory/tags-usables.md`
3. Crear el post con todos los metadatos
4. Subir y asignar la imagen de portada (si hay URL)

---

## Paso 7.5 — Inyectar schema VideoGame

**Solo para posts de tipo Review o Historia sobre un juego concreto. Omitir para Listas y rankings.**

Este paso es **no bloqueante**: si falla, continúa al Paso 8 y reporta el error al final.

Carga la skill `set-videogame-schema` y ejecútala con los datos disponibles:

- `post_id` → ID devuelto por WordPress al publicar (Paso 7)
- `name` → game_data.name (del Paso 4.5)
- `description` → excerpt (del Paso 4)
- `system` → game_data.system, separados por coma (del Paso 4.5)
- `genre` → game_data.genre, separados por coma (del Paso 4.5)
- `author_name` → game_data.developer (del Paso 4.5)
- `publisher` → game_data.publisher (del Paso 4.5; usar el mismo valor que author_name si coincide)
- `image` → URL de la imagen de portada subida en el Paso 7
- `url` → URL pública del post devuelta por WordPress
- `rating` → Solo si el post es una Review; omitir en otros tipos

---

## Paso 8 — Actualizar la memoria

**Si el post venía de la memoria:**
1. Cambia el estado de `en uso` a `publicado`
2. Actualiza `Última actualización`

**Si el post fue especificado directamente por el usuario:**
- No es obligatorio, pero si tiene valor para el historial (evitar cubrir el mismo juego en el futuro), añádelo con estado `publicado`

---

## Paso 9 — Reporte final

```
✅ POST PUBLICADO
─────────────────────────────
🔗 URL: [url del post]
📂 Categoría: [categoría]
🏷️ Tags: [lista]
🖼️ Imagen de portada: [fuente] o ⚠️ pendiente
🖼️ Imágenes de contenido: X screenshots + Y conceptos
🔍 Excerpt: [excerpt]
🗂 Schema VideoGame: ✓ configurado (schema_id: [id]) o ⚠️ pendiente — [motivo]
🕐 Publicado: [fecha y hora]
💾 Memoria: entrada actualizada a `publicado`
─────────────────────────────
```

Si la imagen de portada quedó pendiente, recuérdalo para que el usuario pueda añadirla manualmente desde el panel de WordPress. Si faltan imágenes de contenido, indicar cuántas se buscaron y cuántas se encontraron.

---

## Paso 10 — Cerrar log de ejecución

Añade el resumen final al log en `memory/execution-logs/YYYY-MM-DD.md`, incluyendo resultado global, pasos exitosos/con advertencia/con error, post ID, URL y cualquier tarea pendiente. Sigue el formato definido en la rule `execution-logging`.