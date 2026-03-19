---
description: Genera y publica un post completo en el blog Optim Pixel. Guía al agente desde la elección del tema hasta la publicación final en WordPress via MCP, siguiendo la identidad y estilo del blog.
agent: content-marketer
---

Genera y publica un post completo en Optim Pixel siguiendo estos pasos en orden.

## Paso 0 — Determinar el tema

Antes de hacer ninguna pregunta, evalúa si ya se ha proporcionado un juego o tema en el mensaje de invocación.

**Si el usuario ya especificó un juego o tema:** continúa directamente al Paso 1 con esos datos.

**Si el usuario NO especificó nada:**
1. Lee `memory/post-ideas.md`
2. Localiza la primera entrada con estado `pendiente` (el `#` más bajo)
3. Úsala como base para este post
4. Cambia su estado a `en uso` y actualiza `Última actualización`
5. Informa brevemente antes de continuar:

```
📋 Usando idea de la cola:
Juego: [nombre] | Tipo: [tipo] | Plataforma: [plataforma]
Enfoque: [enfoque]
```

**Si la memoria está vacía:** pregunta al usuario directamente.

---

## Paso 1 — Recopilar información

Si ya tienes datos del Paso 0 o del mensaje de invocación, úsalos sin preguntar de nuevo. Solo pregunta lo que falte:

- ¿Sobre qué juego o tema es el post?
- ¿Qué tipo de post es? (Review / Historia y curiosidades / Lista y ranking)
- ¿En qué plataforma o plataformas?
- (Opcional) ¿Hay algún enfoque o ángulo concreto? ¿Alguna instrucción especial?

---

## Paso 2 — Investigar el tema

Antes de escribir, investiga usando tu conocimiento y las herramientas disponibles:

- Año de lanzamiento, desarrolladora, plataformas originales
- Contexto histórico y recepción en su época
- Datos curiosos, anécdotas de desarrollo, controversias
- Legado e influencia en juegos posteriores
- Estado actual: remasters, ports, disponibilidad

No inventes datos — si no estás seguro de algo, omítelo o indícalo claramente.

---

## Paso 3 — Generar el contenido

Según el tipo de post, carga la skill correspondiente y sigue su estructura:

- Review → skill `generate-post-review`
- Historia y curiosidades → skill `generate-post-historia`
- Lista o ranking → skill `generate-post-lista`

Escribe el post completo en HTML limpio siguiendo la estructura de la skill y la voz del blog definida en `blog-identity`.

---

## Paso 4 — Preparar metadatos SEO

Genera estos campos antes de publicar:

- **Título** — Atractivo, con la keyword principal incluida de forma natural
- **Slug** — Minúsculas, con guiones, sin artículos (ej: `review-chrono-trigger-snes`)
- **Keyword principal** — Una sola, específica, con intención de búsqueda clara
- **Keywords secundarias** — Entre 2 y 4 relacionadas
- **Meta descripción** — 150-160 caracteres, incluye la keyword principal
- **Título SEO** — Puede coincidir con el título o estar ligeramente optimizado

**Tags obligatorios por grupos:**
- Plataforma/s: `Super Nintendo`, `PlayStation`, `Arcade`…
- Género/s: `RPG`, `Plataformas`, `Shooter`…
- Juego y saga: `Chrono Trigger`, `Saga Final Fantasy`…
- Época: `Años 90`, `1995`…
- Desarrolladora: `Square`, `Nintendo`, `Capcom`…

---

## Paso 5 — Buscar imagen de portada

Usa la skill `find-game-image` para localizar la imagen de portada del juego.

---

## Paso 6 — Revisión antes de publicar

Muestra al usuario este resumen y espera confirmación:

```
📝 RESUMEN DEL POST
──────────────────────────────────────
Título: [título]
Tipo: [tipo de post]
Categoría: [categoría]
Slug: /[slug]
Keyword principal: [keyword]
Meta descripción: [meta]
Tags: [lista de tags]
Imagen: [fuente y nombre] o ⚠️ Sin imagen
Palabras: ~[número]
──────────────────────────────────────
¿Publicamos? (sí / revisar / cancelar)
```

- **revisar** → pregunta qué cambiar y vuelve al paso correspondiente
- **cancelar** → detén el proceso; si la entrada estaba `en uso` en memoria, reviértela a `pendiente`
- **sí** → continúa al Paso 7

---

## Paso 7 — Publicar en WordPress

1. Si se encontró imagen en el Paso 5, usa la skill `upload-wordpress-image` para subirla y obtener el `media_id`
2. Usa la skill `publish-wordpress` para resolver categorías y tags, publicar el post con todos los metadatos SEO y confirmar que está accesible

---

## Paso 8 — Actualizar la memoria

**Si el post venía de la memoria:**
1. Cambia el estado de `en uso` a `publicado`
2. Actualiza `Última actualización`

**Si el post fue especificado directamente por el usuario:**
- No es obligatorio, pero si tiene valor para el historial (evitar cubrir el mismo juego en el futuro), añádelo con estado `publicado`

---

## Paso 9 — Reporte final

```
✅ POST PUBLICADO
─────────────────────────────
🔗 URL: [url del post]
📂 Categoría: [categoría]
🏷️ Tags: [lista]
🖼️ Imagen: [fuente] o ⚠️ pendiente
🔍 SEO: keyword "[keyword]" configurada
🕐 Publicado: [fecha y hora]
💾 Memoria: entrada actualizada a `publicado`
─────────────────────────────
```

Si la imagen quedó pendiente, recuérdalo para que el usuario pueda añadirla manualmente desde el panel de WordPress.