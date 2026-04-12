---
description: Genera prompts editoriales listos para usar con /create-post. Busca candidatos con potencial editorial para el blog Optim Pixel, evita repetir ideas ya registradas en memoria y guarda los nuevos prompts en memory/post-ideas.md con estado pendiente.
agent: content-marketer
---

Genera una lista de prompts editoriales para el blog Optim Pixel siguiendo estos pasos en orden.

## Registro de ejecución

Antes de empezar el Paso 1, crea la cabecera del log en `memory/execution-logs/YYYY-MM-DD.md` (añade al final si ya existe) siguiendo la rule `execution-logging`. Registra cada paso a medida que se completa. Al finalizar el workflow, añade el resumen según el formato definido en la rule.

---

## 🛠 Parámetros de Entrada

Antes de ejecutar el Paso 1, analiza la petición del usuario para definir los valores para la skill de ese paso:

- `sistema` (opcional): Consola o sistema (Ej: Super Nintendo, Mega Drive, Arcade, PC, Game Boy, PlayStation).
- `genero` (opcional): Género del juego (Ej:  RPG, Plataformas, Beat em up, Puzzle, Aventura gráfica).
- `epoca` (opcional): Año o década (Ej: Años 80, Años 90, o un año concreto como 1993).
- `tipo_post` (opcional): Review / Historias / Listas.
- `cantidad` (por defecto 10): Número de candidatos iniciales a evaluar.
- `enfoque_tematico` (opcional): Tema o enfoque específico (Ej: juegos infravalorados, sagas olvidadas, fracasos adelantados a su tiempo)
- `modo_estrategia` (opcional): 
    - `editorial` (Predeterminado): Enfoque en calidad narrativa, hitos históricos y valor emocional.
    - `seo_master`: Enfoque en volumen de búsqueda, baja competencia y detección de "huecos" en Google.

---

## Paso 1 — Buscar candidatos

Usa la skill `search-game-candidates` pasándole los filtros recibidos (o ninguno si no se especificaron) y una cantidad objetivo de 20 candidatos para poder seleccionar los 10 mejores.

---

## Paso 2 — Generar los prompts

Para cada uno de los candidatos devueltos por la skill `search-game-candidates`, genera un prompt completo utilizando toda la información devuelta

El formato del prompt sera:

```
Ejecuta el comando /create-post con los siguientes datos:- Título: [Nombre completo] - Modo aplicado: [editorial / seo_master] - Tipo de post: [Review / Historias / Listas] - sistema: [Sistema principal] - genero: [Género principal] - epoca:  [Año o década] - Ángulo Editorial: [Descripción del gancho narrativo en una frase] - Justificación: [Breve explicación de 1-2 frases sobre el valor de este candidato] - Keyword Sugerida (Solo si modo=seo_master): [Palabra clave de larga cola] - Factor de Oportunidad (Solo si modo=seo_master): [Por qué este post atraerá tráfico: competencia baja, tendencia actual, búsqueda específica no resuelta]
```

## Paso 3 — Guardar en memoria

Añade los prompts a `memory/post-ideas.md` siguiendo el formato y las reglas definidas en la rule `post-ideas-memory`.

El campo `Prompt` en la tabla debe contener el prompt completo generado en el Paso 2 (toda la línea starting with "Ejecuta el comando /create-post...").

## Paso 4 — Presentar resultados

Muestra los resultados en este formato:

```
## 🎮 10 nuevas ideas para Optim Pixel

---

### 1. [Prompt completo listo para copiar]

---

### 2. [Prompt completo listo para copiar]

[...hasta 10]

---
💾 Ideas guardadas en memory/post-ideas.md con estado pendiente.
```

## Casos especiales

**Si no hay suficientes candidatos con los filtros indicados** — Relajar filtros progresivamente (primero época, luego sistema) e informar al usuario de qué se ha relajado y por qué.

**Si hay más de 30 ideas pendientes en memoria** — Advertir antes de continuar: "Tienes X ideas pendientes sin usar. ¿Quieres que genere más igualmente?" y esperar confirmación.

**Si el usuario pide más de 20 prompts** — Advertir que puede afectar a la variedad y calidad editorial, y pedir confirmación antes de continuar.

---

## Paso 5 — Cerrar log de ejecución

Añade el resumen final al log en `memory/execution-logs/YYYY-MM-DD.md`, incluyendo resultado global, pasos exitosos/con advertencia/con error y número de ideas generadas. Sigue el formato definido en la rule `execution-logging`.