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

1. Consultar la cola de ideas pendientes:
   ```bash
   python3 memory/scripts/db_query.py get-pending-ideas --limit 1
   ```
2. Si hay resultados, tomar la primera idea y cambiar su estado a `en_uso`:
   ```bash
   python3 memory/scripts/db_query.py update-idea-state --id IDEA_ID --state en_uso
   ```
3. Guardar el `id` de la idea para mantenerla en `en_uso` mientras el post sea borrador y marcarla `publicado` tras superar el Paso 7.8.
4. Informar brevemente antes de continuar:
   ```
   📋 Usando idea de la cola:
   Título: [title] | Tipo: [tipo] | Sistema: [sistema] | Modo: [modo]
   ```

**Si no hay ideas pendientes:** pregunta al usuario directamente.

### Campos disponibles en la respuesta JSON

La idea devuelta por `get-pending-ideas` contiene campos estructurados listos para usar:

| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| `id` | ID de la idea (para actualizar estado) | 5 |
| `title` | Título del juego o tema | "Chrono Trigger" |
| `sistema` | Plataforma principal | "Super Nintendo" |
| `tipo` | Tipo de post: `Review`, `Historias` o `Listas` | "Review" |
| `modo` | Modo de generación: `editorial` o `seo_master` | "editorial" |
| `angulo_editorial` | Gancho o enfoque del post | "La revolución del Active Time Battle" |
| `justificacion` | Por qué es relevante este post | "Uno de los RPGs más influyentes..." |
| `keyword_sugerida` | Keyword SEO (solo si modo=seo_master) | "chrono trigger snes" |
| `factor_oportunidad` | Factor de oportunidad SEO | "Alto volumen de búsqueda" |
| `genero` | Género del juego | "RPG" |
| `epoca` | Época o década | "Años 90" |
| `post_wp_id` | ID del post en WP (null si no publicado) | null |

**No hace falta parsear ningún campo monolítico** — los datos ya están descompuestos listos para usar.

---

## Paso 0.5 — Preflight de entorno (obligatorio)

Antes de escribir o publicar nada, verifica que el entorno está listo y decide el **modo de publicación**:

1. ¿Están disponibles en la sesión los tools MCP `wp_add_post` / `wp_update_post` / `wp_get_post`?
2. Ejecuta el preflight para comprobar `.env`, JWT de MCP y conectividad WordPress:

```bash
python3 .opencode/skills/publish-wordpress/scripts/preflight_check.py --env .env
```

El JSON devuelve `recommended_mode`:

- **`"mcp"`** (JWT válido y tools presentes) → camino principal: usar las herramientas MCP `wp_*`.
- **`"rest"`** (tools ausentes o JWT caducado) → **fallback REST**: usar los scripts `wp_resolve_terms.py`, `wp_create_post.py`, `wp_update_post.py`, `wp_get_post.py` de `.opencode/skills/publish-wordpress/scripts/`.

**Si `recommended_mode` es `null`** (WP REST no responde o faltan credenciales): **detente**. No continúes; informa del error del preflight y pide revisar `.env`/WordPress.

Si el preflight detecta el JWT MCP caducado, avísalo y continúa en modo REST (no es bloqueante). Registra el modo elegido en el log de ejecución.

---

## Paso 1 — Recopilar información

**Si el post viene de la memoria (Paso 0):**

Los campos ya están disponibles como JSON estructurado. Úsalos directamente:
- `title` → nombre del juego
- `tipo` → tipo de post (Review / Historias / Listas)
- `sistema` → sistema/plataforma
- `genero` → género (si existe)
- `epoca` → época (si existe)
- `angulo_editorial` → enfoque del post
- `justificacion` → por qué es relevante
- `keyword_sugerida` → keyword si modo=seo_master
- `factor_oportunidad` → factor SEO si modo=seo_master

Solo pide aclaración si algo no queda claro en los datos.

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

No insertes enlaces internos en esta fase; la skill `link-related-posts` los selecciona, inserta y verifica en el Paso 7.2 para evitar duplicados y asegurar que apuntan a posts publicados.

---

## Paso 4 — Preparar datos de publicación

Genera estos campos que se usarán al publicar en WordPress:

- **Título** — Atractivo, con la keyword principal incluida de forma natural
- **Slug** — Minúsculas, con guiones, sin artículos innecesarios (ej: `review-chrono-trigger-snes`)
- **Excerpt** — 150-160 caracteres, será el snippet en resultados de búsqueda. Incluye la keyword principal de forma natural

Antes de continuar, cuenta los caracteres del excerpt: debe tener entre 150 y 160, ambos inclusive. Si no cumple, reescríbelo y vuelve a contar; no publiques con una descripción fuera de rango.

**Nota sobre SEO:** La keyword principal se usa como guía interna para redactar un buen título y excerpt, pero no se almacena como campo separado en WordPress. El título del post funciona como título SEO.

---

## Paso 4.5 — Consolidar game_data

Reunir en un solo objeto los datos del juego recopilados en los Pasos 0-2. Este objeto se pasará a la skill `publish-wordpress` para que resuelva tags automáticamente desde la base de datos local.

**Mapeo de tipos de post:**

| `post_ideas.tipo` | `game_data.type` | Categoría WordPress |
|--------------------|------------------|---------------------|
| Review | `"review"` | `reviews` |
| Historias | `"historia"` | `historias` |
| Listas | `"lista"` | `listas` |

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

Los tags NO se generan aquí — la skill `publish-wordpress` se encarga de mapear `game_data` a tags consultando la base de datos local (`memory/blog.db`) vía `db_query.py`.

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

Los “juegos destacados” son los 3-5 más relevantes de la lista, elegidos por el agente.

Guardar todas las URLs de contenido para el Paso 5.5. Si alguna búsqueda devuelve menos imágenes de las esperadas, continúa preparando el borrador, pero anota qué imágenes faltan: no se podrá publicar hasta completar los mínimos editoriales indicados en el Paso 7.8.

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
- Máximo 1 imagen de contenido por párrafo/sección
- Insertar solo las imágenes que encajen editorialmente — no forzar
- Si faltan imágenes de contenido, el borrador puede prepararse, pero no se publicará hasta completar los mínimos del Paso 7.8

---

## Paso 6 — Preparar el borrador

Continúa el flujo creando un borrador privado en WordPress. Todavía no se ha autorizado su publicación pública: la confirmación se solicita una sola vez, en el Paso 7.8, después de aplicar enlaces y completar las verificaciones.

---

## Paso 7 — Crear borrador en WordPress

Invocar la skill `publish-wordpress` con los siguientes inputs:

**Inputs obligatorios:**
- `title` — Título del post (del Paso 4)
- `slug` — Slug del post (del Paso 4)
- `content` — Contenido HTML completo con imágenes de contenido ya incrustadas (del Paso 3 + Paso 5.5)
- `excerpt` — Extracto del post (del Paso 4)
- `type` — Tipo de post: `"review"` | `"historia"` | `"lista"` (del Paso 4.5)
- `game_data` — Objeto con datos del juego (del Paso 4.5)
- `status` — `"draft"` (obligatorio en este flujo; la publicación pública se hace en el Paso 7.8, tras confirmación del usuario)

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
2. Generar y validar tags a partir de `game_data` contra `memory/blog.db` vía `db_query.py`
3. Resolver IDs de tags: si están en la DB local con `wp_id`, usarlos directamente; si no, crear en WordPress y registrar en la DB
4. Crear el post con todos los metadatos
5. Subir y asignar la imagen de portada (si hay URL)
6. Registrar el post y sus tags en la base de datos local (`add-post`, `add-post-tags`)

**Si el preflight indicó modo REST** (tools MCP ausentes), el equivalente es:

```bash
# 1) Categoría (type → id)
python3 .opencode/skills/publish-wordpress/scripts/wp_resolve_terms.py category --type review
# 2) Tags (grupo=nombre, repetible) → resuelve/crea en WP, registra en DB y asigna tag_group
python3 .opencode/skills/publish-wordpress/scripts/wp_resolve_terms.py tags \
  --term "sistema=PC" --term "genero=RPG" --term "epoca=Años 90" --term "ano=1991" --term "desarrolladora=..." --term "saga=..."
# 3) Crear borrador
python3 .opencode/skills/publish-wordpress/scripts/wp_create_post.py \
  --title "..." --slug "..." --content-file /tmp/post.html --excerpt "..." \
  --status draft --categories <ID> --tags <id1,id2,...>
# 4) Registrar en DB local (igual que en modo MCP)
python3 memory/scripts/db_query.py add-post --wp-id POST_ID --title "..." --slug "..." --category-slug reviews
python3 memory/scripts/db_query.py add-post-tags --wp-id POST_ID --tag-ids <id1,id2,...>
```

Inmediatamente después, sincroniza su estado local como borrador:

```bash
python3 memory/scripts/db_query.py update-post --wp-id POST_ID --status draft
```

---

## Paso 7.1 — Verificación obligatoria de contenido

**OBLIGATORIO** — Justo tras recibir el `post_id` de la skill `publish-wordpress`, verificar que el contenido se almacenó realmente en WordPress. Este check detecta el bug documentado en `docs/plans/windows-execution-restriction.md` (posts con `post_content` de 0 bytes por ejecución bajo Windows PowerShell).

```bash
python3 .opencode/skills/publish-wordpress/scripts/verify_post_content.py --post-id POST_ID --env .env
```

Exit code 0 y `content_len > 0` → continuar al Paso 7.2.

**Si la verificación falla (`content_len = 0` o error):**

1. Marcar el paso como **error** en el log de ejecución.
2. **No continuar** con los pasos siguientes — el post debe permanecer como borrador y no registrarse como publicado.
3. Si la idea venía de la cola, mantenerla en `en_uso` para que pueda reanudarse sin crear un post duplicado.
4. Informar al usuario: el borrador existe en WordPress pero quedó vacío; la reinyección debe hacerse desde Linux/WSL.

---

## Paso 7.2 — Internal linking obligatorio

El borrador ya tiene ID y tags locales. Carga la skill `link-related-posts` en **modo obligatorio de `/create-post`** y procésalo antes de solicitar autorización de publicación.

- La skill busca candidatos por tags y puntuación; verifica que cada destino siga con estado `publish` en WordPress antes de usarlo.
- Debe insertar dos enlaces salientes a destinos distintos, positivos y públicos, respetando `.opencode/skills/link-related-posts/reference/internal-links-insertion.md` y el máximo de dos enlaces internos por post.
- Tras `wp_update_post`, vuelve a leer el contenido desde WordPress y comprueba que aparecen ambas URLs destino. Solo entonces registra los enlaces con `db_query.py add-link` y confirma las dos filas con `db_query.py get-links --wp-id POST_ID`.
- Si no encuentra dos destinos válidos, falla la actualización, no puede verificar el HTML o no consigue registrar ambos enlaces, **detén el flujo sin publicar**. Mantén `draft`, informa qué falló y deja la idea en `en_uso` para poder reanudarla sin duplicar el post.

> **Modo REST:** la lectura del contenido ya usa REST (`manage-internal-links.py get-post-content`). Para escribir el HTML con los enlaces, si el preflight fue `"rest"`, usa `python3 .opencode/skills/publish-wordpress/scripts/wp_update_post.py --id POST_ID --content-file /tmp/post.html` en lugar de `wp_update_post`.

---

## Paso 7.5 — Inyectar schema VideoGame

**Solo para posts de tipo Review o Historia sobre un juego concreto. Omitir para Listas y rankings.**

En este flujo el schema es una condición para publicar Review e Historia sobre un juego concreto. Si falla, el post permanece como borrador; informa del error para corregirlo antes de reintentar. Para Listas o rankings se omite.

Carga la skill `set-videogame-schema` y ejecútala con los datos disponibles:

- `post_id` → ID devuelto por WordPress al crear el borrador (Paso 7)
- `name` → game_data.name (del Paso 4.5)
- `description` → excerpt (del Paso 4)
- `system` → game_data.system, separados por coma (del Paso 4.5)
- `genre` → game_data.genre, separados por coma (del Paso 4.5)
- `author_name` → game_data.developer (del Paso 4.5)
- `publisher` → game_data.publisher (del Paso 4.5; usar el mismo valor que author_name si coincide)
- `image` → URL de la imagen de portada subida en el Paso 7
- `url` → URL canónica prevista, construida con el dominio y el slug del borrador
- `rating` → Solo si el post es una Review; omitir en otros tipos

---

## Paso 7.8 — Validación final, revisión y publicación

Antes de cambiar el estado del post, confirma todos los puntos aplicables:

- Excerpt/meta descripción de 150-160 caracteres y con la keyword principal.
- Imagen destacada asignada y `featured_media` distinto de cero.
- Imágenes de contenido: Review, 3 screenshots; Historia, 1 screenshot y 1 concepto; Lista, screenshots de los 3-5 juegos destacados. Si no se cumple, dejar en borrador e informar qué recurso falta.
- Longitud dentro del rango del tipo: Review 1000-1500, Historia 800-1200, Lista 600-900 palabras.
- Ángulo editorial propio, no una descripción oficial reformulada.
- Al menos 2 enlaces internos contextuales insertados y registrados.
- Schema VideoGame configurado para Review/Historia sobre un juego concreto.

Muestra al usuario el contenido final del borrador y un resumen que incluya título, categoría, slug, excerpt, recuento de palabras, portada, imágenes de contenido, los dos posts enlazados y el estado del schema. Después pregunta:

```text
¿Publicamos este post? (sí / revisar / dejar como borrador)
```

- **revisar** → conserva el post como borrador, pregunta qué cambiar y vuelve al paso aplicable; repite las verificaciones antes de pedir confirmación otra vez.
- **dejar como borrador** → no publiques; conserva el estado local `draft` y la idea en `en_uso`.
- **sí** → solo si se cumplen todos los puntos aplicables, publica:

  1. Cambiar el post a público con `wp_update_post(id: POST_ID, status: "publish")` (o, en modo REST, `python3 .opencode/skills/publish-wordpress/scripts/wp_update_post.py --id POST_ID --status publish`).
  2. Sincronizar la memoria: `python3 memory/scripts/db_query.py update-post --wp-id POST_ID --status publish`.
  3. Si falla cualquiera de las dos operaciones, informar del estado real en WordPress y en la DB; no reportar éxito hasta que ambos indiquen `publish`.

Si falla algún requisito, no publiques aunque el usuario haya respondido sí: deja el post en `draft` y explica las tareas concretas pendientes.

---

## Paso 8 — Actualizar la memoria

**Si el post venía de la memoria (Paso 0):**

Actualizar el estado de la idea a `publicado` y vincularla con el ID del post en WordPress:

```bash
python3 memory/scripts/db_query.py update-idea-state --id IDEA_ID --state publicado --wp-id POST_ID
```

Donde `IDEA_ID` es el `id` de la idea obtenido en el Paso 0 y `POST_ID` es el ID devuelto por WordPress en el Paso 7. Solo actualizar la idea a `publicado` después de superar el Paso 7.8.

**Si el post fue especificado directamente por el usuario:**

No es obligatorio, pero si tiene valor para el historial (evitar cubrir el mismo juego en el futuro), se puede registrar en dos pasos:

```bash
# 1. Crear la idea (siempre nace como 'pendiente')
python3 memory/scripts/db_query.py add-idea --title "Nombre del Juego" --sistema "Sistema" --tipo Review --modo editorial --angulo "Breve descripción"

# 2. Actualizar a 'publicado' vinculando el post
python3 memory/scripts/db_query.py update-idea-state --id IDEA_ID --state publicado --wp-id POST_ID
```

**Nota:** El registro del post y sus tags en la DB local ya lo gestiona la skill `publish-wordpress` en su Paso 5 (add-post + add-post-tags). No duplicar aquí.

---

## Paso 9 — Reporte final

```
✅ POST PUBLICADO / 📝 BORRADOR PENDIENTE
─────────────────────────────
🔗 URL: [url del post o enlace de previsualización]
📂 Categoría: [categoría]
🏷️ Tags: [lista]
🖼️ Imagen de portada: [fuente] o ⚠️ pendiente
🖼️ Imágenes de contenido: X screenshots + Y conceptos
🔍 Excerpt: [excerpt]
🗂 Schema VideoGame: ✓ configurado (schema_id: [id]) o ⚠️ pendiente — [motivo]
🕐 Publicado: [fecha y hora] / Borrador: [fecha y hora]
💾 Memoria: idea #IDEA_ID actualizada a `publicado` (post_wp_id: POST_ID) / sigue `en_uso` mientras el post permanezca como borrador
─────────────────────────────
```

Si la imagen de portada quedó pendiente, recuérdalo para que el usuario pueda añadirla manualmente desde el panel de WordPress. Si faltan imágenes de contenido, indicar cuántas se buscaron y cuántas se encontraron.

---

## Paso 10 — Cerrar log de ejecución

Añade el resumen final al log en `memory/execution-logs/YYYY-MM-DD.md`, incluyendo resultado global, pasos exitosos/con advertencia/con error, post ID, URL y cualquier tarea pendiente. Sigue el formato definido en la rule `execution-logging`.
