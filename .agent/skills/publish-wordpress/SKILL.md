---
name: publish-wordpress
description: Publica posts completos en el blog Optim Games usando las herramientas MCP de WordPress. Gestiona la búsqueda y subida de imágenes desde Wikimedia Commons, asigna categorías y tags correctos, rellena los campos SEO de Yoast y publica el post. Usar cuando se necesite publicar o actualizar contenido en WordPress.
---

# Skill: Publicar en WordPress via MCP

Esta skill gestiona el proceso completo de publicación usando las herramientas MCP que expone el plugin wordpress-mcp. No hay llamadas HTTP manuales — todo se hace a través del protocolo MCP.

## Requisitos previos

El archivo `.env` del proyecto debe contener:

```
WP_BASE_URL=https://games.optim-byte.com
WP_MCP_JWT_TOKEN=tu-token-jwt-aqui
```

El token JWT se genera desde **Ajustes → WordPress MCP → Authentication Tokens** y tiene una duración máxima de 24 horas. Si expira, hay que regenerarlo.

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

**1.1 Buscar en Wikimedia Commons**

Construye la query usando el nombre del juego y la plataforma:

```
https://en.wikipedia.org/w/api.php?action=query&titles=NOMBRE_DEL_JUEGO&prop=pageimages&format=json&pithumbsize=800
```

Criterios de selección:
- Prioriza imágenes de portada oficial del juego (cover art)
- Tamaño mínimo aceptable: 400px en el lado más corto
- Formatos aceptados: jpg, png, webp
- Verifica que la licencia sea dominio público o Creative Commons libre de uso comercial

**1.2 Fallback a OpenGameArt**

Si Wikimedia no devuelve resultados válidos:

```
https://opengameart.org/api/assets?field_art_type=Art&title=NOMBRE_DEL_JUEGO
```

**1.3 Subir la imagen via MCP**

Una vez localizada la imagen, usa la herramienta MCP:

```
wp_upload_media(
  url: "url-de-la-imagen",
  filename: "nombre-del-juego-portada.jpg",
  alt_text: "Portada de NOMBRE_DEL_JUEGO"
)
```

Guarda el `id` devuelto — lo necesitarás como `featured_media` al crear el post.

**1.4 Si no se encuentra ninguna imagen**

Continúa sin imagen de portada y añade una nota interna:
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