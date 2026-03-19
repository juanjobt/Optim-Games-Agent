---
name: search-game-candidates
description: Busca juegos clásicos candidatos a convertirse en posts para Optim Pixel. Dado un conjunto de filtros opcionales (plataforma, género, época, tipo de post), genera una lista enriquecida de candidatos con contexto editorial suficiente para evaluar su potencial. Usar al generar nuevas ideas para la cola de publicación.
---

# Skill: Search Game Candidates

Genera candidatos editoriales para el blog usando el conocimiento interno del agente sobre la historia de los videojuegos, orientado por las fuentes de referencia indicadas. La gestión de la memoria (evitar repeticiones, actualizar estados) la gestiona la rule `post-ideas-memory`.

---

## Fuentes de referencia

| Fuente | Especialidad |
|---|---|
| MobyGames (mobygames.com) | Base de datos completa por año y plataforma |
| Wikipedia (es.wikipedia.org) | Listas por año, contexto histórico, datos verificables |
| GameFAQs (gamefaqs.gamespot.com) | Catálogos por consola, valoraciones clásicas |
| Arcade History (arcade-history.com) | Especializada en recreativas 1970-2000 |

---

## Filtros disponibles

Todos opcionales. Si no se especifica ninguno, el agente actúa con criterio editorial propio.

- `plataforma` — Ej: Super Nintendo, Mega Drive, Arcade, PC, Game Boy, PlayStation
- `genero` — Ej: RPG, Plataformas, Beat em up, Puzzle, Aventura gráfica
- `epoca` — Ej: Años 80, Años 90, o un año concreto como 1993
- `tipo_post` — Review / Historia y curiosidades / Lista y ranking
- `enfoque_tematico` — Ej: juegos infravalorados, sagas olvidadas, fracasos adelantados a su tiempo
- `cantidad` — Por defecto: 15 (para poder seleccionar los 10 mejores)

Sin filtros, priorizar:
1. Variedad de plataformas y épocas
2. Mezcla equilibrada de los tres tipos de post
3. Juegos con historia interesante, anécdotas curiosas o impacto cultural relevante
4. Equilibrio entre títulos conocidos y joyas poco exploradas

---

## Proceso

### Paso 1 — Generar pool de candidatos

Genera internamente un pool amplio (mínimo el doble de la cantidad solicitada) que cumpla los filtros indicados. Para cada candidato, evaluar mentalmente:

- ¿Tiene una historia de desarrollo interesante?
- ¿Hay curiosidades o datos poco conocidos?
- ¿Ha envejecido bien o mal de forma notable?
- ¿Tiene impacto cultural relevante?
- ¿Encaja con la voz del blog Optim Pixel?

### Paso 2 — Seleccionar y enriquecer

Del pool, seleccionar los mejores según potencial editorial. Para cada candidato generar:

```
- Juego: [nombre exacto]
- Plataforma: [plataforma principal]
- Época: [año o década]
- Tipo de post sugerido: [Review / Historia y curiosidades / Lista y ranking]
- Enfoque sugerido: [una frase describiendo el ángulo editorial más interesante]
- Por qué es buena idea: [1-2 frases de justificación editorial]
```

### Paso 3 — Devolver resultados

Devolver la lista enriquecida al workflow que invocó la skill, lista para convertirse en prompts.

---

## Criterios de calidad editorial

Priorizar candidatos que cumplan al menos uno de estos criterios:

- **Historia de desarrollo fascinante** — Proyectos caóticos, equipos legendarios, plazos imposibles
- **Impacto cultural desproporcionado** — Juegos que cambiaron la industria sin que mucha gente lo sepa hoy
- **Injusticia histórica** — Títulos brillantes que fracasaron por razones ajenas a su calidad
- **Curiosidades técnicas** — Trucos de programación, limitaciones de hardware convertidas en virtud, easter eggs legendarios
- **Antes de su tiempo** — Mecánicas consideradas modernas que llevan décadas existiendo
- **El lado oscuro** — Desarrollos tormentosos, proyectos cancelados famosos, secuelas que destruyeron sagas

Evitar candidatos que sean simplemente "juegos famosos sin ángulo especial". El blog no necesita la décima review de Super Mario Bros sin un giro fresco.