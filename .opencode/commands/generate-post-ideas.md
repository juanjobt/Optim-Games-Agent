---
description: Genera ideas editoriales para el blog Optim Pixel. Busca candidatos con potencial editorial, evita duplicados contra la base de datos y guarda las nuevas ideas en memory/blog.db con estado pendiente.
agent: content-marketer
---

Genera una lista de ideas editoriales para el blog Optim Pixel siguiendo estos pasos en orden.

## Registro de ejecución

Antes de empezar el Paso 1, crea la cabecera del log en `memory/execution-logs/YYYY-MM-DD.md` (añade al final si ya existe) siguiendo la rule `execution-logging`. Registra cada paso a medida que se completa. Al finalizar el workflow, añade el resumen según el formato definido en la rule.

---

## 🛠 Parámetros de Entrada

Antes de ejecutar el Paso 1, analiza la petición del usuario para definir los valores para la skill de ese paso:

- `sistema` (opcional): Consola o sistema (Ej: Super Nintendo, Mega Drive, Arcade, PC, Game Boy, PlayStation).
- `genero` (opcional): Género del juego (Ej: RPG, Plataformas, Beat em up, Puzzle, Aventura gráfica).
- `epoca` (opcional): Año o década (Ej: Años 80, Años 90, o un año concreto como 1993).
- `tipo` (opcional): Review / Historias / Listas.
- `cantidad` (por defecto 10): Número de ideas finales a generar.
- `enfoque_tematico` (opcional): Tema o enfoque específico (Ej: juegos infravalorados, sagas olvidadas, fracasos adelantados a su tiempo).
- `modo` (opcional):
    - `editorial` (Predeterminado): Enfoque en calidad narrativa, hitos históricos y valor emocional.
    - `seo_master`: Enfoque en volumen de búsqueda, baja competencia y detección de "huecos" en Google.

---

## Paso 1 — Buscar candidatos

Usa la skill `search-game-candidates` pasándole los filtros recibidos (o ninguno si no se especificaron). Pasa como `cantidad` el doble de las ideas solicitadas (ej: si el usuario pide 10, pasar 20) para tener un pool amplio del que seleccionar las mejores en el Paso 2.

La skill ya realiza la deduplicación contra la base de datos local en su Paso 1.5, por lo que los candidatos devueltos no duplicarán ideas ni posts existentes.

---

## Paso 2 — Seleccionar y estructurar las ideas

Del pool de candidatos devueltos por `search-game-candidates`, selecciona los mejores según los criterios de calidad editorial de la skill y la cantidad indicada por el usuario.

Para cada idea seleccionada, estructura los datos en campos que mapean directamente a los parámetros de `db_query.py add-idea`:

| Campo `add-idea` | Descripción | Obligatorio |
|-------------------|-------------|-------------|
| `--title` | Nombre completo del juego | Sí |
| `--sistema` | Sistema principal (ej: Super Nintendo) | Sí |
| `--tipo` | Review / Historias / Listas | Sí |
| `--modo` | editorial / seo_master | Sí (default: editorial) |
| `--angulo` | Ángulo editorial en una frase | Sí |
| `--justificacion` | 1-2 frases sobre el valor del candidato | No |
| `--keyword` | Keyword long-tail (solo si modo=seo_master) | Solo seo_master |
| `--factor` | Factor de oportunidad SEO (solo si modo=seo_master) | Solo seo_master |
| `--genero` | Género principal | No |
| `--epoca` | Época (ej: Años 90, 1995) | No |

Los campos `keyword` y `factor` solo se incluyen cuando `modo=seo_master`.

---

## Paso 3 — Guardar en memoria

Para cada idea estructurada en el Paso 2, ejecutar:

```bash
python3 memory/scripts/db_query.py add-idea \
  --title "Nombre del juego" \
  --sistema "Super Nintendo" \
  --tipo Review \
  --modo editorial \
  --angulo "Gancho narrativo en una frase" \
  --justificacion "Por qué es relevante" \
  --keyword "long-tail keyword" \
  --factor "Factor de oportunidad" \
  --genero "RPG" \
  --epoca "Años 90"
```

Si `add-idea` devuelve un error por `title` duplicado (restricción UNIQUE en la tabla `post_ideas`), omitir esa idea y continuar con la siguiente.

Al final del paso, informar de cuántas ideas se guardaron correctamente y cuántas se omitieron por duplicado.

Sigue las reglas de gestión de ideas definidas en la rule `memory-system`.

---

## Paso 4 — Presentar resultados

Muestra los resultados en este formato:

```
## 🎮 N nuevas ideas para Optim Pixel

---

### 1. **Nombre del Juego** — Review (editorial)
- Sistema: Super Nintendo | Género: RPG | Época: Años 90
- Ángulo: Gancho narrativo en una frase
- Justificación: Por qué es relevante

---

### 2. **Nombre del Juego 2** — Historias (seo_master)
- Sistema: Mega Drive | Género: Plataformas | Época: Años 90
- Ángulo: Gancho narrativo
- Justificación: Por qué es relevante
- Keyword: long-tail keyword
- Factor de oportunidad: Por qué atraerá tráfico

---

[...hasta N]

---
💾 Ideas guardadas en memory/blog.db con estado pendiente (X guardadas, Y omitidas por duplicado).
```

---

## Casos especiales

**Si no hay suficientes candidatos con los filtros indicados** — Relajar filtros progresivamente (primero época, luego sistema) e informar al usuario de qué se ha relajado y por qué.

**Si hay más de 30 ideas pendientes en memoria** — Verificar con:
```bash
python3 memory/scripts/db_query.py stats
```
Si el campo `pendiente` en `ideas_by_state` supera 30, advertir antes de continuar: "Tienes X ideas pendientes sin usar. ¿Quieres que genere más igualmente?" y esperar confirmación.

**Si el usuario pide más de 20 ideas** — Advertir que puede afectar a la variedad y calidad editorial, y pedir confirmación antes de continuar.

---

## Paso 5 — Cerrar log de ejecución

Añade el resumen final al log en `memory/execution-logs/YYYY-MM-DD.md`, incluyendo resultado global, pasos exitosos/con advertencia/con error y número de ideas generadas. Sigue el formato definido en la rule `execution-logging`.