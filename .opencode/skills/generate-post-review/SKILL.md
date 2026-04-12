---
name: generate-post-review
description: Estructura y guía para redactar reviews de videojuegos para Optim Pixel. Usar cuando el tipo de post sea una review. Produce HTML listo para WordPress con la estructura en 6 secciones del blog.
metadata:
  author: optimbyte
  version: "1.0"
---

# Skill: Review de Videojuego

Guía de estructura para redactar una review siguiendo el formato de Optim Pixel. El tono, la voz y los requisitos de formato HTML ya están definidos en las reglas del blog.

Extensión objetivo: **1000-1500 palabras**

---

## Estructura

### 1. Gancho inicial (1-2 párrafos)

La primera línea tiene que enganchar. Puede ser una anécdota imaginada, una pregunta que el lector se ha hecho alguna vez, un dato sorprendente, o una declaración contundente. No empieces con "Hoy vamos a hablar de...".

Ejemplos válidos:
- "Hay juegos que te marcan de por vida. Y luego está [juego], que te marca y encima no te deja guardar la partida."
- "¿Cuántos juegos de [género] has terminado en tu vida? Si la respuesta es 'ninguno', [juego] podría ser tu primer mal hábito."

### 2. Ficha técnica

Bloque de datos visual, no como párrafo:

```html
<ul class="ficha-tecnica">
  <li><strong>Título:</strong> Nombre del juego</li>
  <li><strong>Año:</strong> Año de lanzamiento</li>
  <li><strong>Sistema/s:</strong> Sistema</li>
  <li><strong>Desarrolladora:</strong> Nombre</li>
  <li><strong>Género:</strong> Género</li>
</ul>
```

### 3. ¿De qué va esto? (2-3 párrafos)

Premisa del juego sin spoilers importantes. Contextualiza el juego en su época sin perder la personalidad del blog.

### 4. El juego en acción (3-4 párrafos)

El corazón de la review. Gameplay, mecánicas, curva de dificultad, controles. Sé concreto — menciona mecánicas específicas, niveles, momentos memorables. Las generalidades no sirven.

### 5. ¿Cómo ha envejecido? (2-3 párrafos)

Valora el juego desde la perspectiva actual: gráficos, sonido, jugabilidad. Un juego de 1985 no se juzga con los estándares de hoy, pero sí puede decirse si sigue siendo divertido o ha quedado obsoleto. Es el apartado donde más puede brillar la opinión propia.

### 6. Veredicto final (1-2 párrafos)

Cierre contundente. Puede incluir puntuación sobre 10 (si se usa, que esté justificada) o una recomendación clara. Termina con una frase que quede en la memoria.

---

## Imágenes de contenido

Las reviews pueden incluir hasta **3 screenshots** entre las secciones del texto. El agente decide libremente la posición exacta, pero estas son las ubicaciones sugeridas donde una imagen encaja de forma natural:

- Entre "El juego en acción" y "¿Cómo ha envejecido?" — mostrar gameplay en acción
- Al inicio de "¿Cómo ha envejecido?" — ilustrar cómo se ve hoy
- Antes del "Veredicto final" — imagen memorable de cierre

**Reglas:**

- No forzar inserción donde no encaje editorialmente. Si solo hay 1-2 screenshots disponibles, solo insertar esos
- Nunca insertar imágenes en el primer párrafo (el gancho)
- Máximo 3 screenshots por review

**Formato HTML:**

```html
<figure class="aligncenter">
  <img src="https://optimpixel.com/wp-content/uploads/..." alt="Captura de pantalla de {juego}" />
  <figcaption>{juego} en {sistema}</figcaption>
</figure>
```

Las imágenes se buscan con `find-game-image` tipo `screenshot`, se suben con `upload-wordpress-image` tipo `screenshot`, y se insertan en el HTML antes de publicar.