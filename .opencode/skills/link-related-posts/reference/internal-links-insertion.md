# Rule: Internal Links Insertion — Optim Pixel

## Propósito

Esta regla define **cómo y dónde insertar enlaces internos** en el contenido HTML de un post de Optim Pixel. No cubre cómo se obtienen los posts relacionados — eso lo gestiona la skill `link-related-posts`.

---

## Cuándo se aplica

- Acabas de publicar un post y quieres enlazarlo con contenido relacionado
- Estás enriqueciendo un post existente con más enlaces internos

---

## Requisitos previos

1. El **ID del post** a modificar
2. El **contenido HTML actual** del post
3. Una **lista de posts relacionados** con título y URL

---

## Reglas de inserción

### Regla 1: Nunca insertar enlaces en el primer párrafo

El gancho inicial del post no debe interrumpirse. El primer `<p>` queda excluido de cualquier inserción.

### Regla 2: Buscar el contexto temático más próximo

Para cada post relacionado, buscar en el texto dónde aparece naturalmente el tema:

| Si el post relacionado trata de... | Buscar en el texto... |
|---|---|
| La misma desarrolladora (ej: Square) | Menciones a "Square", "la desarrolladora", etc. |
| La misma saga (ej: Final Fantasy) | Menciones a "Final Fantasy", "la saga", etc. |
| El mismo sistema | Menciones al sistema |
| El mismo género | Menciones al género |

**El punto de inserción ideal** es donde ya se menciona el tema — el enlace aparece como continuación natural, no como elemento forzado.

### Regla 3: Si no hay contexto, usar transición natural

Si no existe ninguna mención al tema, insertar al final del **penúltimo párrafo** con una frase de transición:

```
<p>Si te ha picado la curiosidad por los RPGs de esta época, no te pierdas <a href="URL">Título del post</a>.</p>
```

O con humor, si encaja:

```
<p>Y si quieres más historia de [tema], <a href="URL">aquí tienes un post que te va a molar</a>.</p>
```

### Regla 4: Nunca insertar dos enlaces en el mismo párrafo

Cada enlace ocupa su propio párrafo. Esto mantiene la legibilidad y evita parecer spam SEO.

### Regla 5: El texto del enlace

- ✅ Usar el **título del post** o una variación natural del mismo
- ✅ Usar el nombre del juego si es relevante: `Chrono Trigger`, `Final Fantasy VI`
- ❌ Nunca usar "haz clic aquí", "ver más", "leer más", "aquí"

### Regla 6: Máximo 2 enlaces por post

Seleccionar los 2 posts más relevantes de la lista de relacionados. Más de 2 enlaces satura el contenido y parece SEO forzado.

### Regla 7: No repetir destinos

Si un post ya tiene un enlace a otro post, no crear otro enlace al mismo destino.

---

## Ejemplos

### Contexto natural encontrado

**Post actual**: "Chrono Trigger: el caos creativo del desarrollo"
**Post relacionado**: "Final Fantasy VI: la obra maestra de Square"

El post actual menciona "Square":

```html
<p>Square era conocida por su apuesta por historias ambiciosas,</p>
```

**Resultado**:

```html
<p>Square era conocida por su apuesta por historias ambiciosas, y <a href="https://optimpixel.com/final-fantasy-vi-square">Final Fantasy VI</a> lo demostró.</p>
```

### Sin contexto — transición natural

**Post actual**: "Análisis de Metal Gear Solid"
**Post relacionado**: "La historia de Konami"

El post no menciona "Konami". Inserción en penúltimo párrafo:

```html
<p>Y si te preguntas qué pasó con <a href="https://optimpixel.com/historia-konami">la historia de Konami</a>, tenemos un post que te lo cuenta.</p>
```

---

## Errores frecuentes

| Error | Por qué es malo |
|-------|----------------|
| Insertar enlace en el primer párrafo | Rompe el gancho inicial |
| Usar "haz clic aquí" | Parece spam y rompe el tono del blog |
| Insertar más de 2 enlaces | Satura el contenido, parece SEO forzado |
| Enlazar al mismo post dos veces | Redundante |
| Insertar enlaces en medio de una frase sin sentido | Rompe la lectura |

---

## Checklist antes de publicar los cambios

- [ ] El enlace no está en el primer párrafo
- [ ] El texto del enlace es el título del post o nombre del juego
- [ ] No hay dos enlaces en el mismo párrafo
- [ ] Se insertaron máximo 2 enlaces
- [ ] Cada enlace tiene contexto natural o transición fluida
- [ ] El tono del post no se ha visto interrumpido por los enlaces