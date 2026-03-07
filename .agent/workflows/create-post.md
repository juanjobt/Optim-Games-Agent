---
description: Genera y publica automáticamente un post completo en el blog Optim Games. El workflow guía al agente desde la elección del tema hasta la publicación final en WordPress via MCP, siguiendo siempre la identidad y estilo del blog definidos en las rules.
---

# Workflow: Crear y Publicar un Post en Optim Games

## Descripción
Genera y publica automáticamente un post completo en el blog Optim Games. El workflow guía al agente desde la elección del tema hasta la publicación final en WordPress via MCP, siguiendo siempre la identidad y estilo del blog definidos en las rules.

## Uso
```
/create-post
```

---

## Pasos

### Paso 0 — Determinar el tema del post (nuevo)

Antes de hacer ninguna pregunta al usuario, evalúa si ya se ha proporcionado un juego o tema en el mensaje de invocación.

**Si el usuario ya especificó un juego o tema:** continúa directamente al Paso 1 con esos datos. No consultes la memoria.

**Si el usuario NO especificó ningún juego o tema:**
1. Lee el archivo `memory/post-ideas.md`
2. Localiza la primera entrada con estado `pendiente` (el número `#` más bajo)
3. Usa ese prompt directamente como base para este post — juego, plataforma, tipo de post y enfoque ya están definidos
4. Cambia el estado de esa entrada a `en uso` y actualiza la columna `Última actualización` con la fecha actual
5. Informa al usuario brevemente antes de continuar:

```
📋 Usando idea de la cola:
Juego: [nombre] | Tipo: [tipo] | Plataforma: [plataforma]
Enfoque: [enfoque]
```

**Si la memoria está vacía o no existe:**
- Continúa al Paso 1 y pregunta al usuario normalmente

---

### Paso 1 — Recopilar información del post

Pregunta al usuario lo siguiente. Si ya ha proporcionado alguno de estos datos en el mensaje de invocación o desde el Paso 0, úsalos directamente sin volver a preguntar:

**Preguntas obligatorias:**
- ¿Sobre qué juego o tema es el post?
- ¿Qué tipo de post es? (Review / Historia y curiosidades / Lista y ranking)
- ¿En qué plataforma o plataformas aparece el juego?

**Preguntas opcionales** (si el usuario no las responde, el agente decide):
- ¿Hay algún enfoque o ángulo concreto que quieras darle?
- ¿Alguna instrucción especial de tono o contenido?

No hagas todas las preguntas a la vez si el usuario ya ha dado contexto suficiente. Usa el sentido común.

---

### Paso 2 — Investigar el tema

Antes de escribir una sola línea, investiga el juego o tema usando tu conocimiento y las herramientas disponibles:

- Año de lanzamiento, desarrolladora, plataformas originales
- Contexto histórico y recepción en su época
- Datos curiosos, anécdotas de desarrollo, récords, controversias
- Legado e influencia en juegos posteriores
- Estado actual: remasters, ports, disponibilidad

Cuanta más información tengas, mejor será el post. No inventes datos — si no estás seguro de algo, omítelo o indícalo claramente.

---

### Paso 3 — Generar el contenido

Escribe el post completo siguiendo las reglas de `blog-identity` y la estructura correspondiente al tipo de post elegido.

**Checklist antes de continuar:**
- [ ] El tono es desenfadado y con humor natural, no forzado
- [ ] La estructura sigue exactamente el formato del tipo de post elegido
- [ ] La extensión está dentro del rango correcto para ese tipo
- [ ] No hay spoilers sin aviso previo
- [ ] No se han copiado descripciones oficiales sin reescribir
- [ ] El contenido está en español

**Formato del contenido:**
- Escribe el contenido en HTML limpio, listo para WordPress
- Usa `<h2>` para secciones principales y `<h3>` para subsecciones
- Usa `<p>` para párrafos, `<strong>` para énfasis puntuales
- No uses `<h1>` — WordPress lo reserva para el título del post

---

### Paso 4 — Preparar los metadatos SEO

Genera los siguientes campos antes de publicar:

- **Título del post** — Atractivo, con la keyword principal incluida de forma natural
- **Slug** — En minúsculas, con guiones, sin artículos (ej: `review-chrono-trigger-snes`)
- **Keyword principal** — Una sola, específica y con intención de búsqueda clara
- **Keywords secundarias** — Entre 2 y 4 relacionadas
- **Meta descripción** — Entre 150 y 160 caracteres, incluye la keyword principal, tono atractivo
- **Título SEO** — Puede coincidir con el título del post o estar ligeramente optimizado

**Tags a asignar** — Sé generoso, cada post debe llevar obligatoriamente:
- Plataforma/s: ej. `Super Nintendo`, `PlayStation`, `Arcade`, `PC`
- Género/s: ej. `RPG`, `Plataformas`, `Shooter`, `Puzzle`
- Nombre del juego y saga si aplica: ej. `Chrono Trigger`, `Saga Final Fantasy`
- Década o año: ej. `Años 90`, `1995`
- Desarrolladora: ej. `Square`, `Nintendo`, `Capcom`

---

### Paso 5 — Buscar imagen de portada

Sigue el proceso definido en la skill `publish-wordpress`:

1. Busca en Wikimedia Commons usando el nombre del juego
2. Si no hay resultado válido, busca en OpenGameArt
3. Si no hay nada disponible, continúa sin imagen y anótalo en el reporte final

---

### Paso 6 — Revisión antes de publicar

Muestra al usuario un resumen del post antes de publicar:

```
📝 RESUMEN DEL POST
─────────────────────────────
Título: [título]
Tipo: [tipo de post]
Categoría: [categoría]
Slug: /[slug]
Keyword principal: [keyword]
Meta descripción: [meta]
Tags: [lista de tags]
Imagen: [fuente y nombre] o ⚠️ Sin imagen
Palabras: ~[número]
─────────────────────────────
¿Publicamos? (sí / revisar / cancelar)
```

Si el usuario responde **revisar**, pregunta qué quiere cambiar y vuelve al paso correspondiente.
Si el usuario responde **cancelar**, detén el proceso y guarda el borrador localmente.
Si el usuario responde **sí**, continúa al paso 7.

---

### Paso 7 — Publicar en WordPress

Usa la skill `publish-wordpress` para:

1. Subir la imagen de portada a la biblioteca de medios (si se encontró)
2. Resolver o crear los IDs de categoría y tags necesarios
3. Publicar el post con todos los metadatos SEO via MCP
4. Confirmar que el post está publicado y accesible

---

### Paso 8 — Actualizar la memoria (nuevo)

Una vez confirmada la publicación en WordPress, actualiza `memory/post-ideas.md`:

**Si el post venía de la memoria (Paso 0 lo cargó automáticamente):**
1. Localiza la entrada correspondiente por nombre de juego y número `#`
2. Cambia el estado de `en uso` a `publicado`
3. Actualiza la columna `Última actualización` con la fecha actual
4. Actualiza el contador del encabezado del archivo: resta 1 a `Pendientes`, suma 1 a `Publicados`

**Si el post fue especificado directamente por el usuario:**
- No es obligatorio añadirlo a la memoria
- Si el agente considera que tiene valor para el historial (por ejemplo, para evitar cubrir el mismo juego en el futuro), puede añadirlo con estado `publicado` directamente

**Si el usuario canceló en el Paso 6:**
- Si la entrada estaba en estado `en uso`, revertirla a `pendiente`
- Actualizar la columna `Última actualización`

---

### Paso 9 — Reporte final

Una vez publicado, muestra al usuario:

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

Si la imagen quedó pendiente, recuérdalo claramente para que el usuario pueda añadirla manualmente desde el panel de WordPress.