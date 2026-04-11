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

## Paso 2 — Resolver ID de categoría

```
wp_get_categories()
```

**Categorías** (una sola por post):

| Tipo de post | Slug |
|---|---|
| Review | `reviews` |
| Historias | `historias` |
| Listas | `listas` |

Si la categoría no existe, crearla:
```
wp_create_category(name: "Reviews", slug: "reviews")
```

---

## Paso 2.5 — Generar y validar tags del post

**OBLIGATORIO** — Este paso genera los tags basándose en la información del post y los valida contra la memoria.

### 2.5.1 — Recopilar información del post
Extraer del contenido del post la siguiente información:
- Sistema/s del juego
- Género/s
- Desarrolladora
- Año de lanzamiento
- Época (década)
- Saga (si aplica)
- Creador (si aplica)
- Compositor (si aplica)
- País (si aplica)
- Técnica (si aplica)
- Personaje (si aplica)
Si lo requieres, puedes investigar en fuentes externas para completar esta información.

### 2.5.2 — Consultar memoria de tags
1. Leer `memory/tags-usables.md` (fuente de verdad)
2. Consultar los grupos disponibles: Sistema, Género, Época, Año, Desarrolladora, Creador, Saga, País, Técnica, Personaje, Compositor

### 2.5.3 — Mapear info del post a tags
- Por cada elemento del post, buscar el tag equivalente en la memoria
- Si hay variaciones (ej: "SNES" → "Super Nintendo", "action" → "Acción"), USAR SIEMPRE el tag de la memoria
- **Tags obligatorios por grupo**: Sistema, Género, Época/Año, Desarrolladora
- **Tags opcionales**: Saga, Creador, Compositor, País, Técnica, Personaje

### 2.5.4 — Añadir tags nuevos
Si un tag necesario NO existe en `memory/tags-usables.md`:
- Añadirlo automáticamente al archivo con el grupo correspondiente y fecha actual
- Usar el tag en el post

### 2.5.5 — Resolver IDs en WordPress
```
wp_get_tags()  # Para ver qué tags existen ya en WP
```
- Si el tag existe en WP pero con otro nombre → usar el de la memoria
- Si no existe → crear el tag usando el nombre exacto de la memoria

### Resultado del paso
Mostrar en el reporte:
- Lista de tags usados (mapeados a la memoria)
- Tags nuevos añadidos a `memory/tags-usables.md`

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
🏷️ Tags: [lista] (X existentes + Y nuevos añadidos a memoria)
✅ Validación de tags: completada vs memory/tags-usables.md
✅ Imagen de portada: asignada correctamente / ⚠️ pendiente (fallo en script)
🕐 Fecha y hora de publicación
```

**Importante:** En el reporte, indicar cuántos tags nuevos se añadieron a `memory/tags-usables.md`.

Si la imagen quedó pendiente, indica en el reporte que el usuario puede añadirla manualmente desde el panel de WordPress.

---

## Manejo de errores comunes

**Token JWT expirado** — Duración máxima 24h. Regenerar en **Ajustes → WordPress MCP → Authentication Tokens** y actualizar `.env`.

**Herramienta no disponible** — Verificar que *Enable Create Tools* y *Enable Update Tools* están activos en **Ajustes → WordPress MCP → General Settings**.

**Categoría o tag no encontrado** — Usar `wp_create_category` o `wp_create_tag` antes de asignar.