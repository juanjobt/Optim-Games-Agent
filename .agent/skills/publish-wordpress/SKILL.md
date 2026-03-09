---
name: publish-wordpress
description: Publica posts completos en el blog Optim Games usando las herramientas MCP de WordPress. Gestiona la búsqueda de imágenes via RAWG API (fuente principal), Wikimedia Commons (fallback) y Hugging Face FLUX.1-dev (generación IA como último recurso), asigna categorías y tags, rellena campos SEO de Yoast y publica el post. Usar cuando se necesite publicar o actualizar contenido en WordPress.
---

# Skill: Publicar en WordPress via MCP

Esta skill gestiona el proceso completo de publicación usando las herramientas MCP que expone el plugin wordpress-mcp. No hay llamadas HTTP manuales — todo se hace a través del protocolo MCP.

## Requisitos previos

El archivo `.env` del proyecto debe contener:

```
WP_BASE_URL=https://games.optimbyte.com
WP_MCP_JWT_TOKEN=tu-token-jwt-aqui
RAWG_API_KEY=tu-rawg-api-key-aqui
HF_TOKEN=tu-huggingface-token-aqui
```

> **⚠️ IMPORTANTE:** Antes de usar CUALQUIER API externa (RAWG, Hugging Face, etc.), DEBES leer el archivo `.env` del proyecto para obtener los valores reales de las claves. NUNCA uses "demo", placeholders o valores inventados. Si no encuentras el valor, pregunta al usuario.

---

## Herramientas MCP disponibles

El servidor MCP de WordPress expone estas herramientas relevantes para nuestro flujo:

- `wp_create_post` — Crea un nuevo post con título, contenido, slug, estado, categorías y tags
- `wp_update_post` — Actualiza un post existente por ID
- `wp_get_posts` — Consulta posts existentes
- `wp_upload_media` — Sube un archivo a la biblioteca de medios y devuelve su ID
- `wp_get_categories` — Lista las categorías disponibles con sus IDs
- `wp_get_tags` — Lista los tags disponibles con sus IDs
- `wp_create_category` — Crea una nueva categoría si no existe
- `wp_create_tag` — Crea un nuevo tag si no existe

---

## Proceso de publicación

Sigue estos pasos en orden. Si alguno falla, detén el proceso y reporta el error con detalle antes de continuar.

### Paso 1 — Buscar y subir la imagen de portada

**Orden de prioridad:**
1. RAWG API (fuente principal - portadas oficiales)
2. Wikipedia/Wikimedia Commons (fallback)
3. Hugging Face FLUX.1-dev (generación IA como último recurso)

---

#### 1.1 Buscar en RAWG API (RECOMENDADO)

> **⚠️ IMPORTANTE:** Antes de hacer esta llamada, DEBES leer el archivo `.env` del proyecto y extraer el valor de `RAWG_API_KEY`. No continues sin haberlo hecho.

Construye la query usando el nombre del juego y la key real del `.env`:

```
https://api.rawg.io/api/games?search=NOMBRE_DEL_JUEGO&key=744844ef430840ea86411672483d72a6
```

Respuesta esperada - extrae la imagen de `results[0].background_image`:

```json
{
  "count": 1,
  "results": [{
    "name": "Chrono Trigger",
    "background_image": "https://media.rawg.io/media/games/8d6/8d69f3598aff2f2db6f5f2d3c6d5a5a5.jpg",
    "released": "1995-03-11",
    "genres": [{"name": "RPG"}],
    "platforms": [{"platform": {"name": "Super Nintendo"}}]
  }]
}
```

Criterios de selección:
- Prioriza `background_image` (portada oficial)
- Tamaño mínimo: 400px en el lado más corto
- Si RAWG no devuelve resultados, pasa al punto 1.2

---

#### 1.2 Fallback a Wikimedia Commons

Si RAWG no devuelve resultados válidos:

```
https://en.wikipedia.org/w/api.php?action=query&titles=NOMBRE_DEL_JUEGO&prop=pageimages&format=json&pithumbsize=800
```

Criterios:
- Busca `query.pages[].thumbnail.source`
- Verifica licencia Creative Commons

---

#### 1.3 Fallback final: Generación IA con Hugging Face

> **⚠️ IMPORTANTE:** Antes de hacer esta llamada, DEBES leer el archivo `.env` del proyecto y extraer el valor de `HF_TOKEN`. No continues sin haberlo hecho.

Si ninguna fuente haDevuelto imagen, usa Hugging Face Inference Providers para generar una imagen con FLUX.1-dev:

**Opción A - Python (recomendado):**

```python
from huggingface_hub import InferenceClient
import os

client = InferenceClient(token=os.environ["HF_TOKEN"])

image = client.text_to_image(
    prompt=f"Video game box art cover for {nombre_juego}, {genero}, {año}, retro pixel art style, vibrant colors, professional game artwork",
    model="black-forest-labs/FLUX.1-dev"
)

image.save(f"{slug}.jpg")
```

**Opción B - HTTP:**
```
POST https://router.huggingface.co/v1/images/generations
Authorization: Bearer HF_TOKEN
Content-Type: application/json

{
  "model": "black-forest-labs/FLUX.1-dev",
  "inputs": "Video game box art cover for [NOMBRE_JUEGO], [GÉNERO], [AÑO], retro pixel art style"
}
```

**Respuesta (HTTP):** La imagen se devuelve como binary blob. Guárdala localmente como `[slug].jpg` y luego úsala para subir a WordPress.

> ⚠️ **Importante:** Este paso solo debe usarse como último recurso cuando NO se haya encontrado ninguna imagen en RAWG ni Wikimedia.

---

#### 1.4 Subir la imagen via MCP

Una vez localizada la URL de la imagen (o generada localmente), súbela a WordPress:

```
wp_upload_media(
  url: "https://url-completa-de-la-imagen.jpg",
  filename: "nombre-del-juego-portada.jpg",
  alt_text: "Portada de NOMBRE_DEL_JUEGO"
)
```

> ⚠️ **Importante:** El parámetro `url` debe ser la URL pública original de la imagen. Si generaste la imagen con IA (punto 1.3), primero guárdala localmente y usa la ruta local, no una URL.

Si la herramienta devuelve un `id`, guárdalo — lo necesitarás como `featured_media` al crear el post.

#### 1.5 Si ninguna imagen se pudo obtener

Si fallan todas las fuentes (RAWG, Wikimedia, Hugging Face), continúa sin imagen de portada:
```
featured_media: null
// IMAGEN PENDIENTE: no se encontró imagen de dominio público
```

---

### Paso 2 — Resolver IDs de categorías y tags

Usa las herramientas MCP para obtener los IDs actuales:

```
wp_get_categories()
wp_get_tags()
```

Mapeo de categorías principales del blog (una sola por post):
- Reviews → slug `reviews`
- Historia y curiosidades → slug `historia-y-curiosidades`
- Listas y rankings → slug `listas-y-rankings`

No hay subcategorías. Toda la clasificación de plataforma, género, época y desarrolladora va en tags.

Los tags obligatorios por post son:
- **Plataforma/s:** Ej: `Super Nintendo`, `PlayStation`, `Mega Drive`, `Arcade`, `PC`
- **Género/s:** Ej: `RPG`, `Plataformas`, `Shooter`, `Puzzle`
- **Juego y saga:** Ej: `Chrono Trigger`, `Saga Final Fantasy`
- **Época:** Ej: `Años 90`, `1995`
- **Desarrolladora:** Ej: `Square`, `Nintendo`, `Capcom`

Si un tag no existe todavía, créalo antes de asignarlo:

```
wp_create_tag(name: "Nombre", slug: "slug")
```

Si una categoría no existe, créala:

```
wp_create_category(name: "Nombre", slug: "slug")
```

---

### Paso 3 — Publicar el post via MCP

```
wp_create_post(
  title: "Título del post",
  slug: "slug-optimizado-seo",
  content: "<p>Contenido completo en HTML...</p>",
  excerpt: "Meta descripción de 150-160 caracteres",
  status: "publish",
  categories: [ID_categoria_principal],
  tags: [ID_tag_1, ID_tag_2],
  featured_media: ID_imagen_portada,
  meta: {
    "_yoast_wpseo_title": "Título SEO optimizado",
    "_yoast_wpseo_metadesc": "Meta descripción de 150-160 caracteres",
    "_yoast_wpseo_focuskw": "keyword principal"
  }
)
```

Si la herramienta devuelve un `id` y un `link`, el post se ha publicado correctamente.

> **Nota Yoast:** Para que los campos `_yoast_wpseo_*` sean accesibles via MCP, Yoast SEO debe tener activada la integración con la REST API en **Yoast → Configuración → Integraciones → REST API**.

---

### Paso 4 — Reporte final

Una vez completado todo el proceso, genera un resumen con:

- ✅ URL del post publicado
- ✅ Categoría asignada
- ✅ Tags asignados
- ✅ Imagen de portada (fuente y URL) o ⚠️ advertencia si no se encontró
- ✅ Campos Yoast SEO rellenados
- 🕐 Fecha y hora de publicación

---

## Manejo de errores comunes

**Token expirado** — El JWT tiene una duración máxima de 24h. Regenera el token en **Ajustes → WordPress MCP → Authentication Tokens** y actualiza el `.env`.

**Herramienta no disponible** — Verifica que las opciones *Enable Create Tools* y *Enable Update Tools* están activas en **Ajustes → WordPress MCP → General Settings**.

**Categoría no encontrada** — Usa `wp_create_category` para crearla antes de intentar asignarla al post.

**Imagen no subida** — Verifica que el formato es jpg, png o webp y que el tamaño no supera el límite de subida configurado en WordPress (por defecto 8MB).

**RAWG API devuelve error de autenticación**
- Verifica que estás usando la key real del `.env`, NO "demo" ni placeholders
- La URL correcta es: `https://api.rawg.io/api/games?search={juego}&key={TU_RAWG_API_KEY}`
- Si no conoces el valor, Lee el archivo `.env` del proyecto antes de continuar

**Hugging Face devuelve error de autenticación**
- Verifica que estás usando el token real del `.env`, NO un valor inventado
- Si no conoces el valor, Lee el archivo `.env` del proyecto antes de continuar