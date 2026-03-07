---
name: search-game-candidates
description: Busca juegos clásicos candidatos a convertirse en posts para Optim Games. Consulta fuentes externas de referencia y devuelve una lista enriquecida de candidatos con contexto suficiente para evaluar su potencial editorial.
---

# Skill: Search Game Candidates

## Propósito

Dado un conjunto de filtros opcionales (plataforma, género, época, tipo de post), este skill es capaz de generar una lista de juegos clásicos con alto potencial editorial para el blog Optim Games.

La búsqueda no es una llamada a API en tiempo real, sino un proceso de razonamiento enriquecido basado en:
- El conocimiento interno del agente sobre la historia de los videojuegos
- Las fuentes de referencia recomendadas para videojuegos clásicos
- El historial de ideas ya registradas en memoria (para evitar repeticiones)

---

## Fuentes de Referencia

El agente debe orientar su conocimiento usando estas fuentes como referencia mental de autoridad:

| Fuente | Especialidad | URL |
|---|---|---|
| MobyGames | Base de datos completa, todos los juegos por año y plataforma | mobygames.com |
| Wikipedia | Listas por año, contexto histórico, datos verificables | es.wikipedia.org |
| GameFAQs | Catálogos por consola, comunidad, valoraciones clásicas | gamefaqs.gamespot.com |
| Arcade History | Especializada en recreativas 1970-2000 | arcade-history.com |
| OpenGameArt | Recursos visuales libres (uso secundario para imágenes) | opengameart.org |

---

## Inputs del Skill

El skill recibe los filtros que haya especificado el usuario. Todos son opcionales:

- `plataforma` — Ej: Super Nintendo, Mega Drive, Arcade, PC, Game Boy, PlayStation
- `genero` — Ej: RPG, Plataformas, Beat em up, Puzzle, Aventura gráfica
- `epoca` — Ej: Años 70, Años 80, Años 90, o un año concreto como 1993
- `tipo_post` — Ej: Review, Historia y curiosidades, Lista y ranking
- `enfoque_tematico` — Ej: juegos infravalorados, fracasos que se adelantaron a su tiempo, sagas olvidadas
- `cantidad` — Número de candidatos a generar (por defecto: 15, para poder seleccionar los 10 mejores)

Si no se especifica ningún filtro, el agente actúa con criterio editorial propio, priorizando:
1. Variedad de plataformas y épocas
2. Mezcla equilibrada de los tres tipos de post
3. Juegos con historia interesante, anécdotas curiosas o impacto cultural relevante
4. Equilibrio entre títulos conocidos y joyas poco exploradas

---

## Proceso de Búsqueda

### Paso 1 — Leer la memoria
Antes de generar ningún candidato, el agente **debe** consultar `memory/post-ideas.md` y extraer todos los juegos ya registrados (independientemente de su estado). Ninguno de esos juegos puede aparecer como candidato nuevo.

### Paso 2 — Generar pool de candidatos
El agente genera internamente un pool amplio (mínimo el doble de la cantidad solicitada) de juegos que cumplan los filtros indicados, usando su conocimiento sobre la historia de los videojuegos orientado por las fuentes de referencia.

Para cada candidato, el agente evalúa mentalmente:
- ¿Tiene una historia de desarrollo interesante?
- ¿Hay curiosidades o datos poco conocidos?
- ¿Ha envejecido bien o mal de forma notable?
- ¿Tiene impacto cultural relevante?
- ¿Encaja con la voz del blog Optim Games?

### Paso 3 — Seleccionar y enriquecer
Del pool, selecciona los mejores candidatos según potencial editorial. Para cada uno genera:

```
- Juego: [nombre exacto]
- Plataforma: [plataforma principal]
- Época: [año o década]
- Tipo de post sugerido: [Review / Historia y curiosidades / Lista y ranking]
- Enfoque sugerido: [una frase describiendo el ángulo editorial más interesante]
- Por qué es buena idea: [1-2 frases de justificación editorial]
```

### Paso 4 — Devolver resultados
El skill devuelve la lista enriquecida de candidatos al workflow que lo invocó, listo para ser convertido en prompts.

---

## Criterios de Calidad Editorial

El agente debe priorizar candidatos que cumplan al menos uno de estos criterios:

- **Historia de desarrollo fascinante** — Proyectos caóticos, equipos legendarios, plazos imposibles, canciones de desarrollo que se convirtieron en leyenda
- **Impacto cultural desproporcionado** — Juegos que cambiaron la industria sin que mucha gente lo sepa hoy
- **Injusticia histórica** — Títulos brillantes que fracasaron comercialmente por razones ajenas a su calidad
- **Curiosidades técnicas** — Trucos de programación, limitaciones de hardware convertidas en virtud, easter eggs legendarios
- **Antes de su tiempo** — Mecánicas que se consideran modernas pero llevan décadas existiendo
- **El lado oscuro** — Desarrollos tormentosos, proyectos cancelados famosos, secuelas que destruyeron sagas

Evitar candidatos que sean simplemente "juegos famosos sin ángulo especial". El blog no necesita la décima review de Super Mario Bros sin un giro fresco.