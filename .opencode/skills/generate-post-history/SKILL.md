---
name: generate-post-history
description: Estructura y guía para redactar posts de Historias sobre videojuegos para Optim Pixel. Usar cuando el tipo de post sea historia, curiosidades o trasfondo de un juego, saga o momento de la industria. Produce HTML listo para WordPress con la estructura en 5 secciones del blog.
metadata:
  author: optimbyte
  version: "1.0"
---

# Skill: Historias

Guía de estructura para redactar un post de historias siguiendo el formato de Optim Pixel. El tono, la voz y los requisitos de formato HTML ya están definidos en las reglas del blog.

Extensión objetivo: **800-1200 palabras**

---

## Estructura

### 1. Titular gancho (1 párrafo)

Una curiosidad impactante, una pregunta que nadie se había hecho, o una afirmación que contradice lo que el lector cree saber. Tiene que generar curiosidad inmediata.

Ejemplos válidos:
- "¿Sabías que [juego icónico] estuvo a punto de llamarse [nombre ridículo] y lanzarse en [sistema inesperado]?"
- "Hay una razón muy concreta por la que [mecánica famosa] funciona exactamente como funciona, y tiene que ver con [hecho sorprendente]."

### 2. El contexto (2-3 párrafos)

Sitúa al lector en el momento histórico: qué estaba pasando en la industria, en el mundo, en el estudio de desarrollo. El contexto es lo que hace que la historia tenga sentido y resulte interesante.

### 3. Desarrollo narrativo (4-5 párrafos)

La chicha. Cuenta la historia con ritmo, como si fuera un relato. Alterna datos concretos con interpretaciones y comentarios con voz propia. No tengas miedo de opinar sobre lo que pasó.

### 4. Datos curiosos destacados (3-5 datos)

Datos que el lector definitivamente no sabía. Preséntados de forma visual:

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

### 5. Conclusión (1-2 párrafos)

Reflexión corta sobre el legado o la relevancia de lo que se ha contado. Cierre con personalidad, no con resumen de lo dicho.

---

## Imágenes de contenido

Los posts de historias pueden incluir **1-2 imágenes** adicionales a la portada. El agente decide libremente la posición exacta, pero estas son las ubicaciones sugeridas:

- Entre "El contexto" y "Desarrollo narrativo" — imagen que sitúe visualmente la época o el contexto
- En "Datos curiosos destacados" — si hay un dato visual que merezca ilustración

**Reglas:**

- No forzar inserción donde no encaje editorialmente
- Nunca insertar imágenes en el primer párrafo (el gancho)
- Máximo 2 imágenes por historia (1 screenshot + 1 concepto, o 2 screenshots)
- El tipo de imagen depende del tema: si la historia trata sobre desarrollo, un concepto artístico puede encajar mejor que un screenshot

**Formato HTML:**

```html
<figure class="aligncenter">
  <img src="https://optimpixel.com/wp-content/uploads/..." alt="Texto alternativo" />
  <figcaption>Pie de foto descriptivo</figcaption>
</figure>
```

Las imágenes se buscan con `find-game-image` tipo `screenshot` o `concepto`, se suben con `upload-wordpress-image`, y se insertan en el HTML antes de publicar.