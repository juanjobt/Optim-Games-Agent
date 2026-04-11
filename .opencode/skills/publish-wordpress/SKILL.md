---
name: publish-wordpress
description: Publica o actualiza posts completos en WordPress dado un título y un contenido. Gestiona categorías y tags. Orquesta el flujo completo de publicación. Usa las skills find-game-image y upload-wordpress-image para la imagen de portada. Usar cuando se necesite publicar contenido en optimpixel.com.
compatibility: Requiere WordPress MCP configurado, acceso a internet y credenciales en .env
metadata:
  author: optimbyte
  version: "1.0"
allowed-tools: wp_create_post wp_update_post wp_get_posts wp_get_categories wp_get_tags wp_create_category wp_create_tag
---

# Skill: Publicar en WordPress

Flujo completo de publicación:
1. Las herramientas MCP se usan para publicar el post y gestionar categorías y tags.
2. La skill `find-game-image` se usa para obtener la URL de la imagen de portada antes de publicar
3. La skill `upload-wordpress-image` se usa para subir la imagen de portada
4. No hay llamadas HTTP manuales

---

## Herramientas MCP disponibles

- `wp_create_post` — Crea un nuevo post
- `wp_update_post` — Actualiza un post existente por ID
- `wp_get_posts` — Consulta posts existentes
- `wp_get_categories` — Lista categorías con sus IDs
- `wp_get_tags` — Lista tags con sus IDs
- `wp_create_category` — Crea una categoría si no existe
- `wp_create_tag` — Crea un tag si no existe

---

## Paso 1 — Buscar imagen de portada (pre-publicación)

1. Usa la skill `find-game-image` para obtener la URL de la imagen
2. Guarda la URL para el paso posterior — **NO intentes subir la imagen antes de publicar el post**
3. Si devuelve `null`, continúa sin imagen y anota la advertencia en el reporte final

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
- **Sistema/s:** `Super Nintendo`, `PlayStation`, `Mega Drive`, `Arcade`, `PC`, `Game Boy`…
- **Género/s:** `RPG`, `Plataformas`, `Shooter`, `Puzzle`, `Beat em up`…
- **Saga:** nombre exacto del juego y saga si aplica
- **Época:** `Años 80`, `Años 90`…
- **Año:** `1995`…
- **Desarrolladora:** `Square`, `Nintendo`, `Capcom`, `Konami`…
- **Creador:** `Sakaguchi`, `Toriyama`, `Miyamoto`…
- **País:**  — `España`, `Japón`, `USA`…
- **Técnica:**  — `GoldSrc`, `Source`, `Filmation`, `Gráficos prerenderizados`…
- **Personaje:**  — `Alucard`, `Sabreman`… 
- **Compositor:**  — `Michiru Yamane`…

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
  slug: "slug-del-post",
  content: "<p>Contenido completo en HTML...</p>",
  excerpt: "Meta descripción de 150-160 caracteres",
  status: "publish",
  categories: [ID_categoria],
  tags: [ID_tag_1, ID_tag_2, ...]
  # NOTA: No incluir featured_media aquí — se asigna en Paso 4
)
```

---

## Paso 4 — Subir y asignar imagen de portada

1. Usa la skill `upload-wordpress-image` que ejecuta un script Python para subir la imagen obtenida en el Paso 1 y asignarla al post recién creado. NO con herramientas MCP.
2. Después de ejecutar el script, verifica que `featured_media` tiene valor no-zero en el post.


---

## Paso 5 — Reporte final

```
✅ URL del post publicado
✅ Categoría asignada
✅ Tags asignados
✅ Imagen de portada: asignada correctamente / ⚠️ pendiente (fallo en script)
🕐 Fecha y hora de publicación
```

Si la imagen quedó pendiente, indica en el reporte que el usuario puede añadirla manualmente desde el panel de WordPress.

---

## Manejo de errores comunes

**Token JWT expirado** — Duración máxima 24h. Regenerar en **Ajustes → WordPress MCP → Authentication Tokens** y actualizar `.env`.

**Herramienta no disponible** — Verificar que *Enable Create Tools* y *Enable Update Tools* están activos en **Ajustes → WordPress MCP → General Settings**.

**Categoría o tag no encontrado** — Usar `wp_create_category` o `wp_create_tag` antes de asignar.