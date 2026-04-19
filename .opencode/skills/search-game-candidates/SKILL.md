---
name: search-game-candidates
description: Busca juegos clásicos candidatos para Optim Pixel. Posee dos modos de operación: uno enfocado en la calidad editorial pura (Nostalgia) y otro en el posicionamiento estratégico (SEO/Tráfico). Filtra duplicados contra la base de datos local antes de devolver resultados.
metadata:
  author: optimbyte
  version: "3.0"
---

# Skill: Search Game Candidates (Hybrid Mode)

Busca y evalúa juegos clásicos para convertirlos en contenido del blog Optim Pixel. La skill ajusta su profundidad de análisis según el modo seleccionado y filtra candidatos que ya existen como ideas o posts publicados.

**Fuente de verdad para memoria:** `memory/blog.db` (SQLite). La gestión de ideas y deduplicación se realiza mediante `memory/scripts/db_query.py` siguiendo la rule `memory-system`.

---

## 🛠 Parámetros de Entrada

- `sistema` (opcional): Consola o sistema (Ej: Super Nintendo, Mega Drive, Arcade, PC, Game Boy, PlayStation).
- `genero` (opcional): Género del juego (Ej:  RPG, Plataformas, Beat em up, Puzzle, Aventura gráfica).
- `epoca` (opcional): Año o década (Ej: Años 80, Años 90, o un año concreto como 1993).
- `tipo` (opcional): Review / Historias / Listas.
- `cantidad` (por defecto 10): Número de candidatos finales a devolver.
- `enfoque_tematico` (opcional): Tema o enfoque específico (Ej: juegos infravalorados, sagas olvidadas, fracasos adelantados a su tiempo)
- `modo` (opcional):
    - `editorial` (Predeterminado): Enfoque en calidad narrativa, hitos históricos y valor emocional.
    - `seo_master`: Enfoque en volumen de búsqueda, baja competencia y detección de "huecos" en Google.

---

## Herramientas de memoria

Ejecutar con `python3 memory/scripts/db_query.py`:

| Comando | Uso en esta skill |
|---------|-------------------|
| `search "keyword"` | Buscar si un juego ya existe como idea o post en la DB |
| `get-pending-ideas [--limit N]` | Listar ideas pendientes para evitar duplicados |
| `get-pending-ideas --tipo Review` | Listar ideas pendientes filtradas por tipo |
| `stats` | Ver cuántas ideas/posts existen en total |

---

## Lógica por Modo de Acción

### MODO A: Editorial (Sencillo)
*Prioridad: Branding y Calidad de Contenido.*
1. **Selección:** Busca juegos que sean "piedras angulares" de su género o que tengan anécdotas de desarrollo legendarias o impacto cultural relevante. Con variedad de sistema, época y tipo_post.
2. **Contenido:** Siempre debe haber un dato que demuestre conocimiento profundo (ej: "el último juego lanzado para X consola")
3. **Filtro:** Evita juegos excesivamente genéricos. No propongas artículos muy publicados.
4. **Meta:** Crear un artículo que posicione a Optim Pixel como un sitio de referencia en cultura e historia.

### MODO B: SEO Master (Estratégico)
*Prioridad: Tráfico Orgánico y Descubrimiento de Nichos.*
1. **Análisis de Oportunidad:** Identifica juegos que cumplen una de estas condiciones:
    - **Competencia Obsoleta:** Los resultados en Google para este juego son wikis automáticas o artículos de hace >10 años.
    - **Efecto Arrastre:** El juego tiene relación con un lanzamiento actual (Remake, Secuela, Serie de TV).
    - **Tendencia de Emulación:** Juegos que están siendo muy comentados en comunidades de consolas portátiles retro.
2. **Keyword Research:** Identifica una "Long-tail Keyword" (ej: "Cómo conseguir el final secreto de [Juego]" en lugar de solo "Review de [Juego]").
3. **Meta:** Dominar la primera página de Google atacando términos con búsquedas pero contenido mediocre en la competencia.

## Fuentes de referencia

| Fuente | Especialidad |
|---|---|
| MobyGames (mobygames.com) | Base de datos completa por año y sistema |
| Wikipedia (es.wikipedia.org) | Listas por año, contexto histórico, datos verificables |
| GameFAQs (gamefaqs.gamespot.com) | Catálogos por sistema, valoraciones clásicas |
| Arcade History (arcade-history.com) | Especializada en recreativas 1970-2000 |


---

## Proceso

### Paso 0 — Sincronización con tendencia (solo `seo_master`)

Sincronización con el mercado: Antes de buscar candidatos, mira qué juegos están siendo tendencia hoy (por remakes, secuelas o series de TV). Busca juegos clásicos relacionados con esa tendencia para aprovechar el "efecto arrastre" del SEO.

### Paso 1 — Generar pool de candidatos

Genera internamente un pool amplio (mínimo el doble de la cantidad solicitada) que cumpla los filtros indicados. Para cada candidato, evaluar mentalmente:

- ¿Tiene una historia de desarrollo interesante?
- ¿Hay curiosidades o datos poco conocidos?
- ¿Ha envejecido bien o mal de forma notable?
- ¿Tiene impacto cultural relevante?
- ¿Encaja con la voz del blog Optim Pixel?

### Paso 1.5 — Deduplicación contra la base de datos

**OBLIGATORIO** — Antes de continuar con la evaluación, filtrar candidatos que ya existen en la memoria del blog.

Para cada candidato del pool, verificar si ya existe como idea o post publicado:

```bash
python3 memory/scripts/db_query.py search "Nombre del juego"
```

Este comando busca en `post_ideas` (todos los estados), `posts` y `tags`. Si el título del juego aparece en los resultados como idea o post, **eliminar ese candidato del pool**.

También es útil revisar las ideas pendientes para evitar solapamientos temáticos:

```bash
python3 memory/scripts/db_query.py get-pending-ideas --limit 50
```

**Reglas de filtrado:**
- Si el juego ya tiene una idea en estado `pendiente` o `en_uso` → eliminar del pool
- Si el juego ya tiene un post publicado → eliminar del pool
- Si un juego muy similar ya está como idea (ej: mismo título distinta plataforma) → considerar si el ángulo editorial es suficientemente diferente; si no lo es, eliminar
- Si el filtro elimina demasiados candidatos, volver al Paso 1 para generar más y repetir la deduplicación

### Paso 2 — Evaluación de SEO (solo `seo_master`)

Para cada candidato en el pool filtrado, el agente debe buscar (simular búsqueda o usar herramientas si las tienes conectadas) los siguientes indicadores:

Volumen de nostalgia vs. Competencia: ¿Es un juego con una comunidad activa (ej: mods, speedruns) pero cuyos artículos en Google son solo wikis antiguas o reseñas de hace 10 años?

Long-tail Keywords: En lugar de "Review de [Juego]", buscar ángulos como "Cómo pasarse el nivel X de [Juego]", "Secretos de [Juego] nunca revelados" o "Mejores alternativas a [Juego Famoso] en [Sistema]".

Intención de búsqueda de "Solución": Priorizar juegos con mecánicas complejas, finales alternativos o bugs famosos que la gente aún busca cómo resolver.

### Paso 3 — Seleccionar y enriquecer

Del pool filtrado, seleccionar los mejores según potencial editorial.

## Criterios de calidad editorial

Priorizar candidatos que cumplan al menos uno de estos criterios:

- **Historia de desarrollo fascinante** — Proyectos caóticos, equipos legendarios, plazos imposibles
- **Impacto cultural desproporcionado** — Juegos que cambiaron la industria sin que mucha gente lo sepa hoy
- **Injusticia histórica** — Títulos brillantes que fracasaron por razones ajenas a su calidad
- **Curiosidades técnicas** — Trucos de programación, limitaciones de hardware convertidas en virtud, easter eggs legendarios
- **Antes de su tiempo** — Mecánicas consideradas modernas que llevan décadas existiendo
- **El lado oscuro** — Desarrollos tormentosos, proyectos cancelados famosos, secuelas que destruyeron sagas
- **Legado vivo** — Juegos que siguen teniendo comunidades activas, mods, speedruns o influencia directa en títulos actuales
- **Evitar lo evidente:** No propongas el 11º artículo sobre "Por qué Super Mario World es bueno" a menos que sea en modo `seo_master` con una keyword muy específica de ayuda técnica.
- **Contexto Histórico:** Siempre debe haber un dato que demuestre conocimiento profundo (ej: "el último juego lanzado para X consola").
- **Variedad:** Si se piden 10, no pueden ser todos del mismo sistema o género.

### Paso 4 — Devolver resultados

Devolver la lista enriquecida al workflow que invocó la skill.

## 📝 Formato de Salida (Output)

Para cada candidato seleccionado, genera una ficha con este formato exacto. Los nombres de campos coinciden con los parámetros de `db_query.py add-idea` para que el comando que invoque esta skill pueda almacenarlos directamente.

- **title:** [Nombre completo del juego]
- **modo:** [editorial | seo_master]
- **tipo:** [Review | Historias | Listas]
- **sistema:** [Sistema principal — exactamente como aparece en la tabla `tags` del grupo `sistema`]
- **genero:** [Género principal — exactamente como aparece en la tabla `tags` del grupo `genero`]
- **epoca:** [Año o década — ej: Años 90, 1995]
- **angulo_editorial:** [Descripción del gancho narrativo en una frase]
- **justificacion:** [1-2 frases sobre el valor de este candidato]
- **keyword_sugerida:** [Palabra clave de larga cola — solo si modo=seo_master]
- **factor_oportunidad:** [Por qué este post atraerá tráfico — solo si modo=seo_master]

### Mapeo a `db_query.py add-idea`

El comando que reciba estos datos puede almacenarlos directamente:

```bash
python3 memory/scripts/db_query.py add-idea \
  --title "Nombre del juego" \
  --sistema "Super Nintendo" \
  --tipo Review \
  --modo editorial \
  --angulo "Gancho narrativo" \
  --justificacion "Por qué es relevante" \
  --keyword "long-tail keyword" \
  --factor "Factor de oportunidad" \
  --genero "RPG" \
  --epoca "Años 90"
```

Los campos `keyword` y `factor` solo se incluyen cuando `modo=seo_master`.

---