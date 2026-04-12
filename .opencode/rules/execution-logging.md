# Rule: Execution Logging — Optim Pixel

## Propósito

Esta regla define cómo el agente registra cada ejecución de un workflow (como `/create-post` o `/generate-post-ideas`). El objetivo es tener un historial de fallos, advertencias y comportamientos inesperados que permitan mejorar el proceso con el tiempo.

**No es un sistema de recuperación** — si algo falla, el agente lo anota y continúa (o informa al usuario). No intenta recuperarse automáticamente.

---

## Archivo de Log

Los logs se guardan en:

```
memory/execution-logs/YYYY-MM-DD.md
```

Un archivo por día. Si ya existe un archivo para el día actual, se **añade** al final sin sobreescribir nada.

---

## Cuándo registrar un log

El agente DEBE registrar un log al ejecutar CUALQUIER comando slash (`/create-post`, `/generate-post-ideas`, etc.). El registro ocurre:

- Al **inicio** del workflow: crear la cabecera del log con timestamp de inicio
- Al **final** del workflow: añadir el resumen y el resultado global
- Durante el workflow: ir añadiendo entradas por cada paso completado

---

## Formato del Log

### Cabecera (al inicio del workflow)

```markdown
## [HH:MM] /create-post — Nombre del Juego

- **Comando:** /create-post
- **Iniciado:** YYYY-MM-DD HH:MM
- **Tema:** Nombre del juego o tema del post
- **Tipo:** Review / Historia / Lista
```

### Entrada por paso (durante el workflow)

Cada paso tiene su propia subsección:

```markdown
### Paso X — [Nombre del paso]

- **Estado:** éxito / advertencia / error / omitido
- **Duración:** Xs (estimada si es posible)
- **Detalle:** Descripción breve de qué pasó

#### Advertencias (si hubo)
- [Descripción de la advertencia]

#### Errores (si hubo)
- [Descripción del error]
- **Recuperación:** Qué se hizo para continuar (ej: "Se usó fallback RAWG", "Se continuó sin imagen")
```

#### Estados posibles

| Estado | Significado |
|--------|-------------|
| `éxito` | El paso se completó sin problemas |
| `advertencia` | Se completó pero con algún problema menor |
| `error` | El paso falló y no se pudo completar correctamente |
| `omitido` | El paso no se ejecutó por alguna razón justificada |

### Resumen final (al terminar el workflow)

```markdown
### Resumen

- **Resultado final:** completado / completado con advertencias / fallido
- **Pasos exitosos:** X de Y
- **Pasos con advertencia:** X
- **Pasos con error:** X
- **Pasos omitidos:** X
- **Finalizado:** YYYY-MM-DD HH:MM
- **Duración total:** X min (estimada)
- **URL del post:** [URL] (si aplica)
- **Post ID:** [ID] (si aplica)
```

---

## Qué registrar en cada paso

### Errores que deben registrarse

- Llamadas a APIs que fallan (RAWG, SerpApi, WordPress MCP, Hugging Face)
- Respuestas inesperadas de APIs (campos faltantes, errores de formato)
- Uintentos fallidos antes de un fallback (ej: SerpApi no devuelve resultados → se usa RAWG)
- Datos incorrectos o incompletos devueltos por una API (ej: juego no encontrado en RAWG)
- Posts que no se pudieron publicar por error de WordPress
- Imágenes que no se pudieron subir o asignar
- Schemas que no se pudieron inyectar
- Cualquier paso que requirió más intentos de lo esperado

### Advertencias que deben registrarse

- Uso de fallback cuando la fuente principal no funcionó
- Datos que tuvieron que ser inferidos o aproximados (ej: época aproximada)
- Menos imágenes de las esperadas
- Tags que no se encontraron en `tags-usables.md` y tuvieron que crearse desde cero
- Slugs que tuvieron que modificarse por colisión
- Contenido que pudo quedar con longitud fuera del rango esperado

### Información útil que conviene registrar

- Qué fuentes de datos se usaron (RAWG, conocimiento propio, etc.)
- Tiempo estimado que tomó cada paso
- URLs de recursos encontrados (imágenes, posts relacionados)
- IDs de WordPress generados (post ID, media ID, schema ID)
- Decisions tomadas durante el proceso (ej: "Se eligió la imagen 2 de SerpApi porque la imagen 1 tenía baja resolución")

---

## Ejemplo completo de log

```markdown
# Execution Log — 2026-04-12

## 14:30 /create-post — Chrono Trigger

- **Comando:** /create-post
- **Iniciado:** 2026-04-12 14:30
- **Tema:** Chrono Trigger
- **Tipo:** Review

### Paso 0 — Determinar tema

- **Estado:** éxito
- **Detalle:** Tema proporcionado directamente por el usuario

### Paso 1 — Recopilar información

- **Estado:** éxito
- **Detalle:** Datos obtenidos de conocimiento propio y RAWG API

### Paso 2 — Investigar tema

- **Estado:** advertencia
- **Detalle:** La API de RAWG tardó más de lo esperado (3 reintentos)
- **Advertencias:**
  - RAWG devolvió 2 resultados para "Chrono Trigger", se seleccionó el primero por relevancia

### Paso 3 — Generar contenido

- **Estado:** éxito
- **Detalle:** Review generada con ~1200 palabras usando skill generate-post-review

### Paso 4 — Preparar datos de publicación

- **Estado:** éxito
- **Detalle:** Slug: review-chrono-trigger-snes, keyword principal: Chrono Trigger SNES

### Paso 5 — Buscar imágenes

- **Estado:** advertencia
- **Detalle:** SerpApi no devolvió resultados para "Chrono Trigger portada", se usó fallback RAWG
- **Advertencias:**
  - SerpApi devolvió 0 resultados para portada. Fallback a RAWG exitoso.
  - Solo se encontraron 2 screenshots de las 3 esperadas para review

### Paso 5.5 — Subir imágenes de contenido

- **Estado:** éxito
- **Detalle:** 2 screenshots subidos correctamente a biblioteca de medios

### Paso 6 — Revisión

- **Estado:** éxito
- **Detalle:** Usuario confirmó publicación

### Paso 7 — Publicar en WordPress

- **Estado:** éxito
- **Detalle:** Post publicado con ID 12345
- **Post ID:** 12345
- **URL:** https://optimpixel.com/review-chrono-trigger-snes

### Paso 7.5 — Inyectar schema VideoGame

- **Estado:** error
- **Detalle:** El script de schema falló con error de conexión
- **Errores:**
  - Error: "Connection refused" al intentar inyectar schema
  - **Recuperación:** Se continuó sin schema. Pendiente de inyección manual.

### Paso 8 — Actualizar memoria

- **Estado:** éxito
- **Detalle:** Estado cambiado a `publicado` en memory/post-ideas.md

### Resumen

- **Resultado final:** completado con advertencias
- **Pasos exitosos:** 8 de 10
- **Pasos con advertencia:** 2
- **Pasos con error:** 1 (schema inyección)
- **Pasos omitidos:** 0
- **Finalizado:** 2026-04-12 14:45
- **URL del post:** https://optimpixel.com/review-chrono-trigger-snes
- **Post ID:** 12345
- **Pendiente:** Inyectar schema VideoGame cuando se resuelva el error de conexión
```

---

## Reglas adicionales

1. **No registrar datos sensibles** — Nunca incluir API keys, tokens, credenciales o contraseñas en los logs
2. **Ser específico, no vago** — En lugar de "falló la API", escribir "RAWG API devolvió error 429 (rate limit) al buscar Chrono Trigger"
3. **Registrar tiempos estimados** — Ayuda a identificar pasos que toman más tiempo del esperado
4. **No sobreescribir logs** — Siempre añadir al final del archivo existente
5. **Incluir contexto** — Si un paso falló por segunda vez подряд, mencionar que es un error recurrente
6. **Cero logs vacíos** — Si un workflow se ejecutó, debe tener log. Si se canceló antes de empezar, no generar log.

---

## Consulta de logs

Si el usuario pregunta por el estado de los logs (ej: "¿qué fallos ha habido últimamente?", "¿hay errores pendientes?"), el agente debe:

1. Leer los archivos en `memory/execution-logs/`
2. Filtrar por errores y advertencias
3. Presentar un resumen claro y accionable, agrupado por tipo de problema