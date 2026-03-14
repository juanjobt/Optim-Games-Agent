---
name: upload-wordpress-image
description: Sube una imagen a la biblioteca de medios de WordPress y la asigna como imagen destacada de un post. Recibe una URL pública de imagen y un ID de post. Usar después de find-game-image y antes o durante publish-wordpress.
---

# Skill: Subir Imagen a WordPress

Proceso técnico completo para subir una imagen a WordPress via MCP: descarga, conversión a base64 y asignación como featured image.

---

## Requisitos

- URL pública de la imagen (obtenida de `find-game-image`)
- ID del post destino (obtenido tras `wp_create_post` o de un post existente)

---

## Paso 1 — Verificar el post destino

```
wp_get_post(id: POST_ID, context: "edit")
```

Confirma que el post existe y anota el valor actual de `featured_media`.

---

## Paso 2 — Descargar la imagen

```bash
curl -s -o "/tmp/imagen_temporal.jpg" "https://url-de-la-imagen.jpg"
ls -lh "/tmp/imagen_temporal.jpg"
```

---

## Paso 3 — Convertir a base64

```bash
base64 "/tmp/imagen_temporal.jpg" > "/tmp/imagen_base64.txt"
head -c 100 "/tmp/imagen_base64.txt"
```

El archivo base64 debe contener solo el contenido codificado, sin encabezados como `data:image/jpeg;base64,`.

---

## Paso 4 — Leer el contenido base64

Lee el archivo `/tmp/imagen_base64.txt` completo. Guarda el contenido para el paso siguiente.

---

## Paso 5 — Subir a la biblioteca de medios

```
wp_upload_media(
  file: "CONTENIDO_BASE64",
  title: "Portada de NOMBRE_DEL_JUEGO",
  alt_text: "Portada de NOMBRE_DEL_JUEGO para PLATAFORMA",
  caption: "Portada de NOMBRE_DEL_JUEGO",
  description: "Portada de NOMBRE_DEL_JUEGO"
)
```

Si la respuesta incluye un `id`, guárdalo — es el `media_id` para el paso siguiente.

---

## Paso 6 — Asignar como imagen destacada

```
wp_update_post(
  id: POST_ID,
  featured_media: MEDIA_ID
)
```

---

## Manejo de errores

| Error | Causa probable | Solución |
|-------|---------------|----------|
| `Invalid input` al subir | Base64 con encabezados o malformado | Verifica que no incluya `data:image/jpeg;base64,` |
| Imagen no visible en el post | `featured_media` no asignado | Verifica que el `wp_update_post` devolvió éxito |
| Imagen de baja resolución | Miniatura de API en lugar de portada | Buscar URL de mayor resolución en `find-game-image` |
| Permisos insuficientes | Token sin permisos de subida | Verifica rol del usuario (admin o editor) y renueva el token |

## Formatos soportados

`jpg` / `jpeg` — `png` — `gif` — `webp`

Tamaño máximo por defecto en WordPress: **8MB**