---
name: publish-wordpress
description: Publica o actualiza posts completos en WordPress via MCP. Gestiona categorías, tags y campos SEO de Yoast. Orquesta el flujo completo de publicación llamando a find-game-image y upload-wordpress-image para la imagen de portada. Usar cuando se necesite publicar contenido en optimpixel.com.
---

# Skill: Publicar en WordPress

Flujo completo de publicación via MCP. No hay llamadas HTTP manuales — todo se gestiona a través de las herramientas MCP del plugin wordpress-mcp.

---

## Herramientas MCP disponibles

- `wp_create_post` — Crea un nuevo post
- `wp_update_post` — Actualiza un post existente por ID
- `wp_get_posts` — Consulta posts existentes
- `wp_upload_media` — Sube archivos a la biblioteca de medios
- `wp_get_categories` — Lista categorías con sus IDs
- `wp_get_tags` — Lista tags con sus IDs
- `wp_create_category` — Crea una categoría si no existe
- `wp_create_tag` — Crea un tag si no existe

---

## Paso 1 — Buscar y subir imagen de portada

1. Usa la skill `find-game-image` para obtener la URL de la imagen
2. Si devuelve una URL válida, usa `upload-wordpress-image` para subirla y obtener el `media_id`
3. Si devuelve `null`, continúa sin `featured_media` y anota la advertencia en el reporte final

---

## Paso 2 — Resolver IDs de categorías y tags

```
wp_get_categories()
wp_get_tags()
```

**Categorías** (una sola por post):

| Tipo de post | Slug |
|---|---|
| Review | `reviews` |
| Historias | `historias` |
| Listas | `listas` |

**Tags obligatorios** por grupos:
- **Plataforma/s:** `Super Nintendo`, `PlayStation`, `Mega Drive`, `Arcade`, `PC`, `Game Boy`…
- **Género/s:** `RPG`, `Plataformas`, `Shooter`, `Puzzle`, `Beat em up`…
- **Juego y saga:** nombre exacto del juego y saga si aplica
- **Época:** `Años 80`, `Años 90`, `1995`…
- **Desarrolladora:** `Square`, `Nintendo`, `Capcom`, `Konami`…

Si un tag o categoría no existe, créalo antes de asignarlo:

```
wp_create_tag(name: "Nombre", slug: "slug")
wp_create_category(name: "Nombre", slug: "slug")
```

---

## Paso 3 — Publicar el post

```
wp_create_post(
  title: "Título del post",
  slug: "slug-optimizado-seo",
  content: "<p>Contenido completo en HTML...</p>",
  excerpt: "Meta descripción de 150-160 caracteres",
  status: "publish",
  categories: [ID_categoria],
  tags: [ID_tag_1, ID_tag_2, ...],
  featured_media: MEDIA_ID,
  meta: {
    "_yoast_wpseo_title": "Título SEO",
    "_yoast_wpseo_metadesc": "Meta descripción 150-160 caracteres",
    "_yoast_wpseo_focuskw": "keyword principal"
  }
)
```

> **Yoast SEO:** Para que los campos `_yoast_wpseo_*` funcionen via MCP, activa la integración REST API en **Yoast → Configuración → Integraciones → REST API**.

---

## Paso 4 — Reporte final

```
✅ URL del post publicado
✅ Categoría asignada
✅ Tags asignados
✅ Imagen de portada (fuente: RAWG / Wikimedia) o ⚠️ imagen pendiente
✅ Campos Yoast SEO rellenados
🕐 Fecha y hora de publicación
```

---

## Manejo de errores comunes

**Token JWT expirado** — Duración máxima 24h. Regenerar en **Ajustes → WordPress MCP → Authentication Tokens** y actualizar `.env`.

**Herramienta no disponible** — Verificar que *Enable Create Tools* y *Enable Update Tools* están activos en **Ajustes → WordPress MCP → General Settings**.

**Categoría o tag no encontrado** — Usar `wp_create_category` o `wp_create_tag` antes de asignar.