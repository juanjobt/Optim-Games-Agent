---
name: generate-post
description: Genera posts completos para el blog Optim Games. Usar cuando se necesite redactar contenido de cualquier tipo (review, historia y curiosidades, lista y ranking) sobre videojuegos. Aplica el tono desenfadado y con humor del blog, respeta la estructura de cada tipo de post y produce HTML listo para publicar en WordPress.
---

# Skill: Generar Post para Optim Games

Esta skill contiene las instrucciones detalladas para redactar posts de calidad con la voz y personalidad del blog. Antes de escribir, asegúrate de haber investigado suficientemente el tema (paso 2 del workflow `/create-post`).

---

## La voz del blog

Optim Games no es una enciclopedia ni una revista técnica. Es ese amigo que sabe muchísimo de videojuegos y te lo cuenta de forma entretenida mientras tomáis algo. Tiene criterio propio, no tiene miedo de opinar, y sabe cuándo soltar un buen chiste y cuándo ponerse serio.

**Características concretas de la voz:**

- **Humor natural:** No fuerces los chistes. Un buen chiste en el momento justo vale más que diez chistes mediocres repartidos por el texto. Si no sale solo, no lo pongas.
- **Opinión propia:** El blog tiene voz, no es neutral. "Este juego es una obra maestra" o "este juego no ha envejecido nada bien" son afirmaciones válidas si están justificadas.
- **Referencias a la cultura gaming:** Menciona otros juegos, desarrolladoras, momentos históricos. El lector es gamer y lo agradece.
- **Frases cortas cuando hay que impactar:** Una frase corta sola en un párrafo puede ser más poderosa que un párrafo largo. Úsalo con criterio.
- **Nunca condescendiente:** No expliques lo obvio. El lector ya sabe lo que es un jefe final.

**Lo que nunca debe aparecer:**
- "En este artículo vamos a..." — Empieza directamente
- "Sin más dilación..." — Nunca
- "En conclusión podemos decir que..." — Termina con personalidad, no con fórmulas
- Frases copiadas de Wikipedia o descripciones oficiales sin reescribir
- Exceso de adjetivos vacíos: "impresionante", "increíble", "fantástico" sin justificación

---

## Estructuras por tipo de post

### REVIEW (1000-1500 palabras)

**1. Gancho inicial (1-2 párrafos)**
La primera línea tiene que enganchar. Puede ser una anécdota personal imaginada, una pregunta que el lector se ha hecho alguna vez, un dato sorprendente, o directamente una declaración de intenciones contundente. No empieces con "Hoy vamos a hablar de...".

Ejemplos de buenos ganchos:
- "Hay juegos que te marcan de por vida. Y luego está [juego], que te marca y encima no te deja guardar la partida."
- "¿Cuántos juegos de [género] has terminado en tu vida? Si la respuesta es 'ninguno', [juego] podría ser tu primer mal hábito."

**2. Ficha técnica**
Preséntala de forma visual y directa, no como párrafo sino como bloque de datos:

```html
<ul class="ficha-tecnica">
  <li><strong>Título:</strong> Nombre del juego</li>
  <li><strong>Año:</strong> Año de lanzamiento</li>
  <li><strong>Plataforma/s:</strong> Plataformas</li>
  <li><strong>Desarrolladora:</strong> Nombre</li>
  <li><strong>Género:</strong> Género</li>
</ul>
```

**3. ¿De qué va esto? (2-3 párrafos)**
Explica la premisa del juego sin spoilers importantes. Aquí el tono puede ser más descriptivo pero sin perder la personalidad. Es el momento de contextualizar el juego en su época.

**4. El juego en acción (3-4 párrafos)**
El corazón de la review. Habla del gameplay, las mecánicas, la curva de dificultad, los controles. Sé concreto — menciona mecánicas específicas, niveles, momentos memorables. Las generalidades no sirven.

**5. ¿Cómo ha envejecido? (2-3 párrafos)**
Valora el juego desde la perspectiva actual. Gráficos, sonido, jugabilidad. Sé justo — un juego de 1985 no puede juzgarse con los estándares de hoy, pero sí puede decirse si sigue siendo divertido o si ha quedado obsoleto. Este apartado es donde más puede brillar la opinión propia.

**6. Veredicto final (1-2 párrafos)**
Cierre contundente. Puede incluir una puntuación (si se usa, que sea sobre 10 y que esté justificada) o simplemente una recomendación clara. Termina con una frase que quede en la memoria.

---

### HISTORIA Y CURIOSIDADES (800-1200 palabras)

**1. Titular gancho (1 párrafo)**
Una curiosidad impactante, una pregunta que nadie se había hecho, o una afirmación que contradice lo que el lector cree saber. Tiene que generar curiosidad inmediata.

Ejemplos:
- "¿Sabías que [juego icónico] estuvo a punto de llamarse [nombre ridículo] y lanzarse en [plataforma inesperada]?"
- "Hay una razón muy concreta por la que [mecánica famosa] funciona exactamente como funciona, y tiene que ver con [hecho sorprendente]."

**2. El contexto (2-3 párrafos)**
Sitúa al lector en el momento histórico. Qué estaba pasando en la industria, en el mundo, en el estudio de desarrollo. El contexto es lo que hace que la historia tenga sentido y sea interesante.

**3. Desarrollo narrativo (4-5 párrafos)**
La chicha. Cuenta la historia con ritmo, como si fuera un relato. Alterna datos concretos con interpretaciones y comentarios en primera persona del blog. No tengas miedo de opinar sobre lo que pasó.

**4. Datos curiosos destacados**
Entre 3 y 5 datos que el lector definitivamente no sabía. Preséntalos de forma visual:

```html
<div class="curiosidades">
  <h3>Esto no te lo esperabas</h3>
  <ul>
    <li>Dato curioso 1</li>
    <li>Dato curioso 2</li>
    <li>Dato curioso 3</li>
  </ul>
</div>
```

**5. Conclusión (1-2 párrafos)**
Reflexión corta sobre el legado o la relevancia de lo que se ha contado. Cierre con personalidad, no con resumen.

---

### LISTA Y RANKING (600-900 palabras)

**1. Intro con provocación (1-2 párrafos)**
Las listas generan debate. Empieza reconociéndolo y aprovechándolo. "Sí, sabemos que no vais a estar de acuerdo con el número uno. Y nos alegra." El tono puede ser el más desenfadado de los tres tipos.

**2. Los ítems (el grueso del post)**
Cada ítem debe tener:
- Número y nombre claramente identificados
- 2-4 frases de descripción y justificación de por qué está en la lista
- Al menos una frase de opinión propia

No todos los ítems necesitan el mismo espacio — los más importantes o controvertidos pueden tener más desarrollo.

```html
<h3>5. Nombre del juego (Plataforma, Año)</h3>
<p>Descripción y justificación...</p>
```

**3. El número 1 (destacado)**
El número 1 merece más espacio que el resto. 3-5 párrafos. Explica bien por qué está ahí, anticipa las objeciones del lector y respóndelas. Es el momento más opinativo de todo el post.

**4. Cierre que invite al debate (1 párrafo)**
Termina con una pregunta directa al lector o una afirmación que invite a la discusión en comentarios. "¿Cuál es el tuyo? Nos vemos en los comentarios, que hoy hay debate."

---

## Formato HTML

El contenido debe estar en HTML limpio y semántico:

- `<h2>` para secciones principales
- `<h3>` para subsecciones o ítems de lista
- `<p>` para párrafos
- `<strong>` para énfasis puntuales (no abuses)
- `<em>` para títulos de juegos la primera vez que se mencionan
- `<ul>` y `<li>` para listas
- No uses `<h1>` — WordPress lo reserva para el título
- No uses estilos inline — el tema de WordPress gestiona el diseño

---

## Longitud y ritmo

- Los párrafos no deberían superar las 4-5 líneas. Si se alargan, rómpelos.
- Varía la longitud de los párrafos — alterna párrafos largos con párrafos cortos de impacto.
- Si un apartado se está alargando demasiado sin aportar información nueva, córtalo.
- Mejor quedarse corto con sustancia que llegar al límite con relleno.

---

## Checklist final antes de entregar el contenido

- [ ] La primera línea engancha sin presentaciones
- [ ] El tono es consistente de principio a fin
- [ ] Hay al menos un momento de humor natural en el texto
- [ ] No hay frases copiadas de otras fuentes sin reescribir
- [ ] La estructura corresponde exactamente al tipo de post
- [ ] La extensión está dentro del rango correcto
- [ ] El HTML es limpio y no usa `<h1>` ni estilos inline
- [ ] No hay spoilers sin aviso previo
- [ ] El cierre tiene personalidad y no es una fórmula genérica