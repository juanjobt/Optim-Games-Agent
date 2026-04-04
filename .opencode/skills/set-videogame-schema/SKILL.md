---
name: set-videogame-schema
description: Inyecta los metadatos del schema `VideoGame` (Schema.org) del plugin **Schema & Structured Data for WP & AMP**, en un post de WordPress ya publicado usando al api de wordpress atraves de un script de python.
---

# Skill: Set Videogame Schema

Esta skill es **no bloqueante**: si falla, reporta el error pero no interrumpe el flujo de `create-post`.

---

## Cuándo usar esta skill

Invocar desde el **Paso 7.5 de `create-post`**, justo después de confirmar que el post se ha publicado correctamente y antes del reporte final. Solo aplica a posts de tipo **Review** e **Historia** sobre un juego concreto. Para Listas y rankings, omitir esta skill.

---

## Prerequisitos

El archivo `.env` debe contener:

```
WP_BASE_URL=https://optimpixel.com
WP_USER=tu_usuario_wordpress
WP_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx
WP_VIDEOGAME_SCHEMA_ID=118
```

> `WP_APP_PASSWORD` es una **Application Password** de WordPress (Usuarios → Editar → Application Passwords), distinta del password de acceso al panel y distinta del JWT token.
>
> `WP_VIDEOGAME_SCHEMA_ID` es el ID interno del schema VideoGame en el plugin. Por defecto es **118**. Solo cambiar si el plugin se ha reinstalado y el ID ha cambiado (editar `DEFAULT_SCHEMA_ID = "118"` en el script si el .env no tiene este valor).

---

## Inputs que necesita el agente

Recopilar de los pasos anteriores del flujo `create-post`:

| Input | Fuente | Descripción |
|-------|--------|-------------|
| `post_id` | Respuesta de WordPress al publicar | ID numérico del post recién creado |
| `name` | Datos del juego | Nombre oficial del juego |
| `description` | Post generado | Primera frase del post o la meta descripción SEO (máx. 160 caracteres) |
| `platform` | Datos del juego | Plataformas separadas por coma. Ej: `"PlayStation, PC, Sega Saturn"` |
| `genre` | Datos del juego | Géneros. Ej: `"Survival Horror, Aventura"` |
| `author_name` | Datos del juego | Desarrolladora. Ej: `"Capcom"` |
| `publisher` | Datos del juego | Distribuidora (puede coincidir con desarrolladora si es el mismo) |
| `image` | URL de la imagen subida en Paso 7 | URL completa de la imagen de portada en WP |
| `url` | Respuesta de WordPress al publicar | URL pública del post |
| `rating` | Solo Reviews | Puntuación numérica si el post es una Review. Dejar vacío si no aplica |

> **Nota:** El `schema_id` se obtiene automáticamente del .env (`WP_VIDEOGAME_SCHEMA_ID`). **No es necesario pasarlo como argumento**.

---

## Cómo ejecutar

Ejecutar el script con los datos recopilados:

```bash
python3 wp_set_schema.py \
  --post-id {post_id} \
  --name "{name}" \
  --description "{description}" \
  --platform "{platform}" \
  --genre "{genre}" \
  --author-name "{author_name}" \
  --publisher "{publisher}" \
  --image "{image}" \
  --url "{url}" \
  --rating "{rating}"
```

**Omitir `--rating`** si el post no es una Review.

---

## Output esperado

Si todo va bien, el script imprime:

```
=== wp_set_schema ===
  Post ID : 456
  Juego   : Resident Evil
  Plataforma: PlayStation, PC, Sega Saturn

  Meta fields a actualizar:
    saswp_modify_this_schema_118 = 118
    saswp_vg_schema_id_118 = VideoGame
    saswp_vg_schema_application_category_118 = Games
    saswp_vg_schema_name_118 = Resident Evil
    ...

  ✓ Schema VideoGame actualizado correctamente

✓ Proceso completado
  post_id   : 456
  schema_id : 118
  juego     : Resident Evil
```

---

## Errores frecuentes y qué hacer

### `ERROR HTTP 401`

Las credenciales `WP_USER` o `WP_APP_PASSWORD` son incorrectas o la Application Password fue revocada. Regenerar en **Usuarios → Editar → Application Passwords**.

### `ERROR HTTP 403`

El usuario no tiene permisos suficientes para editar posts. Debe tener rol **Editor** o **Administrador**.

---

## Cómo reportar el resultado en el Paso 9

Añadir esta línea al reporte final de `create-post`:

**Si fue bien:**
```
🗂 Schema VideoGame: ✓ configurado (schema_id: {schema_id})
```

**Si falló o se omitió:**
```
🗂 Schema VideoGame: ⚠ pendiente — {motivo breve}
```