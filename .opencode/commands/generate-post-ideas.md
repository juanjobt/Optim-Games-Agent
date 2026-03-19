---
description: Genera 10 prompts editoriales listos para usar con /create-post. Busca juegos clásicos con potencial editorial, evita repetir ideas ya registradas en memoria y guarda los nuevos prompts en memory/post-ideas.md con estado pendiente.
agent: content-marketer
---

Genera una lista de 10 prompts editoriales para el blog Optim Pixel siguiendo estos pasos en orden.

El usuario puede haber especificado filtros opcionales como plataforma, género, época, tipo de post o enfoque temático. Si no especificó nada, actúa con criterio editorial propio.

## Paso 1 — Buscar candidatos

Usa la skill `search-game-candidates` pasándole los filtros recibidos (o ninguno si no se especificaron) y una cantidad objetivo de 20 candidatos para poder seleccionar los 10 mejores.

## Paso 2 — Seleccionar los 10 mejores

De los candidatos obtenidos, selecciona los 10 con mayor potencial editorial aplicando estos criterios de desempate:

1. **Variedad de tipos de post** — La lista final debe mezclar Reviews, Historia y curiosidades, y Listas y rankings
2. **Variedad de plataformas y épocas** — No acumular todo en la misma consola o década
3. **Potencial de engagement** — Priorizar juegos con historias que inviten al debate, la nostalgia o la sorpresa
4. **Equilibrio conocido/desconocido** — Mezclar títulos reconocibles con alguna joya menos evidente

## Paso 3 — Generar los prompts

Para cada uno de los 10 juegos seleccionados, genera un prompt completo en este formato exacto:

```
Ejecuta el comando /create-post con los siguientes datos:

Juego: [nombre del juego]
Tipo de post: [Review / Historia y curiosidades / Lista y ranking]
Plataforma: [plataforma]
Enfoque: [descripción del ángulo editorial en una frase]
```

El enfoque debe ser específico y atractivo, nunca genérico:
- ✅ "El diseñador que creó el sistema de combate en un fin de semana porque el equipo estaba en crisis"
- ✅ "Por qué fracasó en ventas un juego que inventó el género de los metroidvania"
- ❌ "La historia y curiosidades del juego"
- ❌ "Review completa con todo lo importante"

## Paso 4 — Guardar en memoria

Añade las 10 nuevas entradas a `memory/post-ideas.md` siguiendo el formato y las reglas definidas en la rule `post-ideas-memory`.

## Paso 5 — Presentar resultados

Muestra los resultados en este formato:

```
## 🎮 10 nuevas ideas para Optim Pixel

---

### 1. [Nombre del juego] — [Tipo de post]
[Prompt completo listo para copiar]

---

### 2. [Nombre del juego] — [Tipo de post]
[Prompt completo listo para copiar]

[...hasta 10]

---
💾 Ideas guardadas en memory/post-ideas.md con estado pendiente.
```

## Casos especiales

**Si no hay suficientes candidatos con los filtros indicados** — Relajar filtros progresivamente (primero época, luego plataforma) e informar al usuario de qué se ha relajado y por qué.

**Si hay más de 30 ideas pendientes en memoria** — Advertir antes de continuar: "Tienes X ideas pendientes sin usar. ¿Quieres que genere más igualmente?" y esperar confirmación.

**Si el usuario pide más de 20 prompts** — Advertir que puede afectar a la variedad y calidad editorial, y pedir confirmación antes de continuar.