# Rule: Internal Links Insertion — Optim Pixel

## Propósito

Esta regla define **cómo y dónde insertar enlaces internos** en los posts de Optim Pixel. Se aplica cuando ya tienes identificados los posts relacionados mediante la skill `link-related-posts` y el script `manage-internal-links.py`.

Esta regla es **independiente del flujo de creación de posts** — funciona igual para posts nuevos (create-post) que para posts existentes que necesitan más enlaces internos (/link-posts).

---

## Cuándo se aplica

Usa esta regla cuando:

- Acabas de publicar un post y quieres enlazarlo con contenido relacionado
- Estás ejecutando `/link-posts` y necesitas insertar enlaces en posts existentes
- Tienes una lista de posts relacionados con sus URLs y títulos

---

## Requisitos previos

Antes de insertar enlaces, necesitas:

1. El **ID del post** en WordPress que vas a modificar
2. El **contenido HTML actual** del post (obtenido via `wp_get_post` de WordPress MCP)
3. Una **lista de posts relacionados** obtenidos de `manage-internal-links.py find-related`

---

## Reglas de inserción

### Regla 1: Nunca insertar enlaces en el primer párrafo

El gancho inicial del post no debe interrumpirse. El primer `<p>` del contenido queda excluido de cualquier inserción de enlace.

### Regla 2: Buscar el contexto temático más próximo

Para cada post relacionado, buscar en el texto dónde aparece naturalmente el tema del post destino:

| Si el post relacionado trata de... | Buscar en el texto... |
|---|---|
| La misma desarrolladora (ej: Square) | Menciones a "Square", "la desarrolladora", etc. |
| La misma saga (ej: Final Fantasy) | Menciones a "Final Fantasy", "la saga", etc. |
| La misma plataforma | Menciones a la plataforma |
| El mismo género | Menciones al género |

**El punto de inserción ideal** es donde ya se menciona el tema relacionado — el enlace aparece como continuación natural, no como elemento forzado.

### Regla 3: Si no hay contexto, usar transición natural

Si no existe ninguna mención al tema del post relacionado, insertar al final del **penúltimo párrafo** con una frase de transición que venga del tono del blog:

```
<p>Si te ha picado la curiosidad por los RPGs de esta época, no te pierdas <a href="URL">Título del post</a>.</p>
```

O bien con humor, si encaja:
```
<p>Y si quieres más historia de [tema], <a href="URL">aquí tienes un post que te va a molar</a>.</p>
```

### Regla 4: Nunca insertar dos enlaces en el mismo párrafo

Cada enlace ocupa su propio párrafo. Esto mantiene la legibilidad y evita parecer spam SEO.

### Regla 5: El texto del enlace

- ✅ Usar el **título del post** o una variación natural del mismo
- ✅ Usar el nombre del juego si es relevante: `Chrono Trigger`, `Final Fantasy VI`
- ❌ Nunca usar "haz clic aquí", "ver más", "leer más", "aquí"

### Regla 6: Limitar a 2 enlaces por post

El número máximo de outgoing links por post es **2**. Esto evita saturar el contenido y mantener la calidad editorial. Usar los 2 con mayor score de la lista de relacionados.

### Regla 7: No repetir destinos

Si un post ya tiene un enlace a otro post, no crear otro enlace al mismo destino aunque salga en la lista de relacionados.

---

## Proceso paso a paso

### Paso 1: Obtener el contenido actual

```python
# Via WordPress MCP
wp_get_post(id: post_id, context: "edit")
# Extraer el campo "content" -> "rendered"
```

### Paso 2: Dividir el contenido en párrafos

El contenido viene como HTML con `<p>...</p>`. Separar en array de párrafos:

```python
import re
parrafos = re.split(r'(</?p>)', contenido_html)
# Reconstruir array de párrafos limpios
parrafos_limpios = []
for i, p in enumerate(partes):
    if p == '<p>':
        continue  # skip opening tag
    elif p == '</p>':
        parrafos_limpios.append(partes[i-1])  # add the text before closing
    elif i % 2 == 0:  # text content
        if p.strip():
            parrafos_limpios.append(p)
```

### Paso 3: Analizar cada post relacionado

Para cada post relacionado (máximo 2):

1. Extraer palabras clave del post destino (plataforma, saga, desarrolladora, género)
2. Buscar en qué párrafos aparecen essas palabras
3. Si se encuentra → marcar ese párrafo como punto de inserción
4. Si no se encuentra → marcar penúltimo párrafo para transición

### Paso 4: Insertar el enlace

Construir el HTML del enlace:

```html
<a href="https://optimpixel.com/slug-del-post">Título del post</a>
```

Insertar en el lugar determinado, envuelto en su propio `<p>` si es transición, o directamente en el texto si es contexto natural.

### Paso 5: Actualizar el post

```python
wp_update_post(
  id: post_id,
  content: html_actualizado
)
```

---

## Ejemplos concretos

### Ejemplo 1: Contexto natural encontrado

**Post actual**: "Chrono Trigger: el caos creativo del desarrollo"  
**Post relacionado**: "Final Fantasy VI: la obra maestra de Square"

El post actual menciona "Square" en un párrafo:

```html
<p>Square era已知 por apuesta por historias ambiciosas...</p>
```

**Resultado**:

```html
<p>Square era conocida por apuesta por historias ambiciosas, y <a href="https://optimpixel.com/final-fantasy-vi-square">Final Fantasy VI</a> lo demostró.</p>
```

### Ejemplo 2: Sin contexto, usar transición

**Post actual**: "Análisis de Metal Gear Solid"  
**Post relacionado**: "La historia de Konami"

El post no menciona "Konami" en ningún lugar.  
**Resultado** (penúltimo párrafo):

```html
<p>Y si te preguntas qué pasó con <a href="https://optimpixel.com/historia-konami">la historia de Konami</a>, tenemos un post que te lo cuenta.</p>
```

---

## Errores frecuentes a evitar

| Error | Por qué es malo |
|-------|----------------|
| Insertar enlace en el primer párrafo | Rompe el gancho inicial |
| Usar "haz clic aquí" | Parece spam y rompe el tono del blog |
| Insertar más de 2 enlaces | Satura el contenido, parece SEO forzado |
| Enlazar al mismo post dos veces | Redundante |
|插入 enlaces en medio de una frase sin sentido | Rompe la lectura |

---

## Checklist antes de publicar los cambios

- [ ] El enlace no está en el primer párrafo
- [ ] El texto del enlace es el título del post o nombre del juego
- [ ] No hay dos enlaces en el mismo párrafo
- [ ] Se insertaron máximo 2 enlaces
- [ ] Cada enlace tiene contexto natural o transición fluida
- [ ] El tono del post no se ha visto interrumpido por los enlaces
