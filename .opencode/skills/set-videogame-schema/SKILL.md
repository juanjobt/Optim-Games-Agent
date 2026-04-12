---
name: set-videogame-schema
description: Inyecta los metadatos del schema `VideoGame` (Schema.org) del plugin **Schema & Structured Data for WP & AMP**, en un post de WordPress ya publicado usando al api de wordpress atraves de un script de python.
compatibility: Requiere Python 3, credenciales de Application Password (WP_USER, WP_APP_PASSWORD) en .env, y script en .opencode/skills/set-videogame-schema/scripts/wp_set_schema.py
metadata:
  author: optimbyte
  version: "1.0"
allowed-tools: wp_get_post wp_update_post
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

Recopilar del Paso 4.5 (`game_data`) y del Paso 7 de `create-post`:

| Input | Fuente | Descripción |
|-------|--------|-------------|
| `post_id` | Paso 7: respuesta de WordPress al publicar | ID numérico del post recién creado |
| `name` | Paso 4.5: `game_data.name` | Nombre oficial del juego |
| `description` | Paso 4: `excerpt` | Excerpt del post (máx. 160 caracteres) |
| `system` | Paso 4.5: `game_data.system` | Sistemas separados por coma. Ej: `"PlayStation, PC, Sega Saturn"` |
| `genre` | Paso 4.5: `game_data.genre` | Géneros separados por coma. Ej: `"Survival Horror, Aventura"` |
| `author_name` | Paso 4.5: `game_data.developer` | Desarrolladora. Ej: `"Capcom"` |
| `publisher` | Paso 4.5: `game_data.publisher` | Distribuidora (usar `game_data.developer` si coincide) |
| `image` | Paso 7: URL de la imagen subida | URL completa de la imagen de portada en WP |
| `url` | Paso 7: respuesta de WordPress | URL pública del post |
| `rating` | Solo Reviews | Puntuación numérica si el post es una Review. Dejar vacío si no aplica |

> **Nota:** El `schema_id` se obtiene automáticamente del .env (`WP_VIDEOGAME_SCHEMA_ID`). **No es necesario pasarlo como argumento**.

---

## Cómo ejecutar

Ejecutar el script con los datos recopilados:

```bash
python3 .opencode/skills/set-videogame-schema/scripts/wp_set_schema.py \
  --post-id {post_id} \
  --name "{name}" \
  --description "{description}" \
  --system "{system}" \
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
  Sistema : PlayStation, PC, Sega Saturn

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