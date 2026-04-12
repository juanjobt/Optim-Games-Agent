---
name: upload-wordpress-image
description: Sube una imagen a la biblioteca de medios de WordPress y la asigna como imagen destacada de un post. Recibe una URL pública de imagen y un ID de post. Usar después de find-game-image y antes o durante publish-wordpress.
compatibility: Requiere Python 3, acceso a internet, credenciales WP_BASE_URL, WP_USER y WP_APP_PASSWORD en .env, y script en .opencode/skills/upload-wordpress-image/scripts/wp_upload_image.py
metadata:
  author: optimbyte
  version: "1.0"
allowed-tools: wp_get_post wp_upload_media wp_update_post
---

# Skill: Subir Imagen a WordPress

Delega la subida completa al script `.opencode/skills/upload-wordpress-image/scripts/wp_upload_image.py`, que gestiona la descarga, el upload multipart y la asignación de featured image sin pasar datos por el contexto del agente.

---

## Requisitos

- URL pública de la imagen (obtenida de `find-game-image`)
- ID del post destino (obtenido tras `wp_add_post` o de un post existente)
- Script `.opencode/skills/upload-wordpress-image/scripts/wp_upload_image.py` presente en el proyecto
- Credenciales `WP_BASE_URL`, `WP_USER` y `WP_APP_PASSWORD` en `.env`

---

## Paso 1 — Verificar el post destino

```
wp_get_post(id: POST_ID, context: "edit")
```

Confirma que el post existe. Anota el valor actual de `featured_media`.

---

## Paso 2 — Ejecutar el script de subida

```bash
python3 .opencode/skills/upload-wordpress-image/scripts/wp_upload_image.py \
  --url "URL_DE_LA_IMAGEN" \
  --post-id POST_ID \
  --game "NOMBRE_DEL_JUEGO" \
  --system "SISTEMA"
```

El script se encarga de todo:
- Descarga la imagen a `/tmp`
- La sube a WordPress via REST API multipart (sin pasar base64 por contexto)
- Actualiza alt_text, caption y description
- Asigna la imagen como `featured_media` del post
- Elimina el archivo temporal

---

## Paso 3 — Verificar el resultado

El script imprime al final:

```
✓ Imagen subida y asignada correctamente
  media_id: 42
  post_id : 123
```

Si ves ese mensaje, la imagen está asignada. No es necesario llamar a `wp_update_post` manualmente.

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