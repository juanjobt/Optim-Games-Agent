---
name: generate-post-ideas
description: Genera una lista de 10 prompts listos para usar con el workflow create-post. Busca juegos clásicos con potencial editorial, evita repetir ideas ya registradas en memoria y guarda los nuevos prompts en memory/post-ideas.md con estado pendiente.
---

# Workflow: Generate Post Ideas

## Propósito

Generar una lista de 10 prompts editoriales listos para ejecutar directamente con el workflow `create-post`. Cada prompt representa una idea de post para el blog Optim Games, seleccionada con criterio editorial, sin repetir juegos ya presentes en la memoria del agente.

---

## Inputs

El usuario puede especificar filtros opcionales al invocar este workflow. Si no especifica nada, el agente actúa con criterio editorial propio.

| Parámetro | Descripción | Ejemplo |
|---|---|---|
| `plataforma` | Filtrar por consola o sistema | `Super Nintendo`, `Arcade`, `PC` |
| `genero` | Filtrar por género de juego | `RPG`, `Beat em up`, `Puzzle` |
| `epoca` | Filtrar por década o año | `Años 80`, `1994`, `Años 90` |
| `tipo_post` | Filtrar por tipo de contenido | `Review`, `Historia y curiosidades`, `Lista y ranking` |
| `enfoque_tematico` | Ángulo editorial general | `juegos infravalorados`, `fracasos legendarios` |
| `cantidad` | Número de prompts a generar | Por defecto: `10` |

**Ejemplo de invocación con filtros:**
```
Ejecuta el workflow /generate-post-ideas con los siguientes filtros:
Plataforma: Mega Drive
Época: Años 90
Tipo de post: Historia y curiosidades
```

**Ejemplo de invocación libre:**
```
Ejecuta el workflow /generate-post-ideas. Decide tú qué juegos son más interesantes.
```

---

## Pasos del Workflow

### PASO 1 — Leer la memoria
**Acción:** Leer el archivo `memory/post-ideas.md`

- Extraer todos los juegos registrados en la tabla, sin importar su estado
- Construir internamente una lista de exclusión con esos juegos
- Si el archivo no existe o está vacío, continuar sin lista de exclusión
- Anotar mentalmente: "estos juegos están off-limits"

---

### PASO 2 — Buscar candidatos
**Acción:** Ejecutar el skill `search-game-candidates`

---

### PASO 2½ — Leer skill search-game-candidates (OBLIGATORIO)

**ANTES de ejecutar el skill, DEBES:**

1. Lee el archivo `.agent/skills/search-game-candidates/SKILL.md` completo
2. Confirma mentalmente los criterios de calidad editorial
3. Recuerda las fuentes de referencia (MobyGames, Wikipedia, GameFAQs, etc.)
4. Luego ejecuta el skill pasando los filtros correctos

> ⚠️ **Esta lectura es obligatoria.** No puedes ejecutar el skill sin haberlo leído antes.

---

Pasar al skill:
- Los filtros recibidos del usuario (o ninguno si no se especificó nada)
- La lista de exclusión del paso anterior
- Cantidad objetivo: el doble de la cantidad final (por defecto 20 candidatos para seleccionar 10)

El skill devolverá una lista enriquecida de candidatos con juego, plataforma, tipo de post sugerido, enfoque y justificación editorial.

---

### PASO 3 — Seleccionar los 10 mejores
**Acción:** Filtrado y selección editorial

De los candidatos recibidos, seleccionar los 10 con mayor potencial editorial aplicando estos criterios de desempate:

1. **Variedad de tipos de post** — La lista final debe tener idealmente una mezcla de Reviews, Historia y curiosidades, y Listas y rankings. Evitar que los 10 sean del mismo tipo.
2. **Variedad de plataformas y épocas** — No acumular todo en la misma consola o la misma década.
3. **Potencial de engagement** — Priorizar juegos con historias que inviten al debate, la nostalgia o la sorpresa.
4. **Equilibrio conocido/desconocido** — Mezclar títulos reconocibles con alguna joya menos evidente.

---

### PASO 4 — Generar los prompts
**Acción:** Para cada uno de los 10 juegos seleccionados, generar un prompt completo y listo para usar

Cada prompt debe seguir exactamente este formato:

```markdown
Ejecuta el workflow /create-post con los siguientes datos:

Juego: [nombre del juego]
Tipo de post: [Review / Historia y curiosidades / Lista y ranking]
Plataforma: [plataforma]
Enfoque: [descripción del ángulo editorial en una frase]

Sigue todos los pasos del workflow en orden: investiga primero, redacta después, prepara los metadatos SEO, busca imagen de portada en Wikimedia Commons y muéstrame el resumen de revisión antes de publicar.
```

El enfoque debe ser específico y atractivo, no genérico. Ejemplos de enfoques buenos:
- ✅ "El diseñador que creó el sistema de combate en un fin de semana porque el equipo estaba en crisis"
- ✅ "Por qué fracasó en ventas un juego que inventó el género de los metroidvania"
- ❌ "La historia y curiosidades del juego"
- ❌ "Review completa con todo lo importante"

---

### PASO 5 — Actualizar la memoria
**Acción:** Añadir las 10 nuevas entradas a `memory/post-ideas.md`

Para cada prompt generado, añadir una fila a la tabla con:
- `#` — Número secuencial siguiendo el último registrado
- `Juego` — Nombre exacto
- `Plataforma` — Plataforma principal
- `Tipo de Post` — El tipo asignado
- `Enfoque` — Versión resumida del enfoque (máximo 15 palabras)
- `Estado` — `pendiente`
- `Última actualización` — Fecha actual en formato `YYYY-MM-DD`

Actualizar también el resumen del encabezado del archivo:
- `Última generación`: fecha actual
- `Total de entradas`: nuevo total
- `Pendientes`: nuevo conteo

---

### PASO 6 — Presentar los resultados al usuario
**Acción:** Mostrar la lista generada de forma clara y usable

Formato de presentación:

```
## 🎮 Lista de ideas generadas para Optim Games

Se han generado 10 prompts nuevos y guardados en memoria/post-ideas.md

---

### 1. [Nombre del juego] — [Tipo de post]
[El prompt completo listo para copiar y pegar]

---

### 2. [Nombre del juego] — [Tipo de post]
[El prompt completo listo para copiar y pegar]

[...hasta 10]

---
💾 Todas las ideas han sido guardadas en memoria con estado `pendiente`.
Para usar una, copia el prompt y ejecútalo con /create-post.
```

---

## Comportamiento ante Errores o Casos Especiales

### Si no hay suficientes candidatos que cumplan los filtros
- Relajar los filtros progresivamente (primero época, luego plataforma) hasta encontrar suficientes
- Informar al usuario de qué filtros se han relajado y por qué

### Si la memoria está casi llena de pendientes (más de 30 entradas pendientes)
- Advertir al usuario antes de generar: "Tienes X ideas pendientes sin usar. ¿Quieres que genere más igualmente?"
- Esperar confirmación antes de continuar

### Si el usuario pide más de 10 prompts
- Aceptar cantidades de hasta 20
- Para más de 20, advertir que puede afectar a la variedad y calidad editorial, y pedir confirmación

---

## Archivos que usa este Workflow

| Archivo | Tipo | Acción |
|---|---|---|
| `memory/post-ideas.md` | Memoria | Leer al inicio, escribir al final |
| `skills/search-game-candidates.md` | Skill | Invocar en paso 2 |
| `rules/blog-identity.md` | Rule | Consultar para mantener coherencia editorial |
| `rules/post-ideas-memory.md` | Rule | Governa la escritura en memoria |