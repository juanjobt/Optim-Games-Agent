---
name: upload-wordpress-image
description: Sube una imagen a la biblioteca de medios de WordPress y, si es portada, la asigna como imagen destacada de un post. Soporta portada, screenshots y concepto artístico. Recibe una URL pública de imagen. Usar después de find-game-image y antes o durante publish-wordpress.
compatibility: Requiere Python 3, acceso a internet, credenciales WP_BASE_URL, WP_USER y WP_APP_PASSWORD en .env, y script en .opencode/skills/upload-wordpress-image/scripts/wp_upload_image.py
metadata:
  author: optimbyte
  version: "2.0"
allowed-tools: wp_get_post wp_upload_media wp_update_post
---

# Skill: Subir Imagen a WordPress

Delega la subida completa al script `.opencode/skills/upload-wordpress-image/scripts/wp_upload_image.py`, que gestiona la descarga, el upload multipart y la asignación de featured image (si aplica) sin pasar datos por el contexto del agente.

---

## Parámetros de entrada

| Parámetro | Requerido | Valores | Descripción |
|-----------|-----------|---------|-------------|
| `url` | Sí | URL pública | URL de la imagen (obtenida de `find-game-image`) |
| `type` | Sí | `portada` \| `screenshot` \| `concepto` | Tipo de imagen |
| `post_id` | No | ID numérico | ID del post destino. Solo obligatorio para `portada`. Para contenido, se puede omitir y subir solo a biblioteca |
| `game` | Sí | texto | Nombre del juego |
| `system` | No | texto | Sistema (ej: Super Nintendo). Usado solo en alt de portada |
| `alt_text` | No | texto | Texto alternativo personalizado. Sobreescribe el texto por defecto |

### Comportamiento por tipo

| Tipo | Asigna featured_media | Alt text por defecto | Caption |
|------|----------------------|--------------------| ---------|
| `portada` | Sí | `Portada de {game} para {system}` | `Portada de {game}` |
| `screenshot` | No | `Captura de pantalla de {game}` | `Captura de pantalla de {game}` |
| `concepto` | No | `{game} — concepto artístico` | `{game} — concepto artístico` |

---

## Paso 1 — Verificar el post destino (solo para portada)

Si `type=portada` y se proporcionó `post_id`:

```
wp_get_post(id: POST_ID, context: "edit")
```

Confirma que el post existe. Anota el valor actual de `featured_media`.

Si `type` no es `portada` y no se proporcionó `post_id`, se omite este paso — la imagen solo se subirá a la biblioteca de medios.

---

## Paso 2 — Ejecutar el script de subida

### Para portada (con post_id):
```bash
python3 .opencode/skills/upload-wordpress-image/scripts/wp_upload_image.py \
  --url "URL_DE_LA_IMAGEN" \
  --post-id POST_ID \
  --game "NOMBRE_DEL_JUEGO" \
  --system "SISTEMA" \
  --type portada
```

### Para screenshot o concepto (sin post_id, solo biblioteca):
```bash
python3 .opencode/skills/upload-wordpress-image/scripts/wp_upload_image.py \
  --url "URL_DE_LA_IMAGEN" \
  --game "NOMBRE_DEL_JUEGO" \
  --type screenshot
```

### Con alt_text personalizado:
```bash
python3 .opencode/skills/upload-wordpress-image/scripts/wp_upload_image.py \
  --url "URL_DE_LA_IMAGEN" \
  --game "NOMBRE_DEL_JUEGO" \
  --type concepto \
  --alt-text "Diseño original de personajes de Chrono Trigger"
```

El script se encarga de todo:
- Descarga la imagen a `/tmp`
- La sube a WordPress via REST API multipart (sin pasar base64 por contexto)
- Actualiza alt_text, caption y description según el tipo
- Si `type=portada`, asigna la imagen como `featured_media` del post
- Si `type` no es portada, solo sube a biblioteca (no asigna featured_media)
- Elimina el archivo temporal

---

## Paso 3 — Verificar el resultado

El script imprime al final:

### Para portada:
```
✓ Imagen subida y asignada correctamente
  media_id: 42
  post_id : 123
  type    : portada
  featured: yes
  source_url: https://optimpixel.com/wp-content/uploads/2026/04/imagen.jpg
```

### Para screenshot/concepto:
```
✓ Imagen subida a la biblioteca de medios
  media_id: 43
  type    : screenshot
  featured: no
  source_url: https://optimpixel.com/wp-content/uploads/2026/04/imagen.jpg
```

Anotar el `media_id` y `source_url` para cada imagen subida. El `source_url` se usará para insertar imágenes en el contenido HTML del post.

Si ves ese mensaje, la operación está completa. No es necesario llamar a `wp_update_post` manualmente, salvo en caso de error con `featured_media`.

---

## Manejo de errores

| Error | Causa probable | Solución |
|-------|---------------|----------|
| `ERROR descargando imagen` | URL inválida o inaccesible | Verificar URL manualmente; volver a `find-game-image` |
| `archivo descargado demasiado pequeño` | URL redirige a página de error | Buscar URL directa de la imagen |
| `ERROR HTTP 401` | Credenciales incorrectas | Verificar `WP_USER` y `WP_APP_PASSWORD` en `.env` |
| `ERROR HTTP 403` | Usuario sin permisos de subida | Verificar que el usuario tiene rol admin o editor |
| `WP_BASE_URL, WP_USER y WP_APP_PASSWORD son obligatorios` | `.env` no encontrado o incompleto | Verificar que el script se ejecuta desde la raíz del proyecto |
| `featured_media devuelto no coincide` | Asignación parcialmente fallida | Ejecutar manualmente `wp_update_post(id: POST_ID, featured_media: MEDIA_ID)` con el media_id impreso |

## Formatos soportados

`jpg` / `jpeg` — `png` — `gif` — `webp`

Tamaño máximo por defecto en WordPress: **8MB**