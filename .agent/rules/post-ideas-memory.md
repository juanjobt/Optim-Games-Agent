---
trigger: always_on
---

# Rule: Post Ideas Memory — Optim Games

## Activación
Always On

---

## Propósito

Esta rule define cómo el agente gestiona el archivo de memoria `memory/post-ideas.md`. Su objetivo es que el agente nunca pierda el rastro de qué ideas ya han sido generadas, cuáles están pendientes de usar y cuáles ya se han publicado como posts reales.

---

## El Archivo de Memoria

El archivo de referencia es siempre:

```
memory/post-ideas.md
```

Este archivo es la **única fuente de verdad** sobre el historial de ideas del blog. El agente debe leerlo al inicio de cualquier tarea relacionada con generación de ideas o creación de posts.

---

## Estados Posibles de un Prompt

Cada entrada en la memoria tiene uno de estos tres estados:

| Estado | Significado |
|---|---|
| `pendiente` | El prompt ha sido generado pero aún no se ha usado para crear un post |
| `en uso` | El prompt está siendo usado ahora mismo en el workflow `create-post` |
| `publicado` | El post ya ha sido creado y publicado en WordPress |

---

## Reglas de Comportamiento

### Al generar nuevas ideas (`generate-post-ideas`)
1. Leer `memory/post-ideas.md` antes de generar ningún candidato
2. Extraer todos los juegos registrados (cualquier estado)
3. No incluir ninguno de esos juegos en la nueva lista generada
4. Al finalizar la generación, **añadir** las nuevas entradas al archivo con estado `pendiente`
5. Nunca sobreescribir entradas existentes — solo añadir al final de la tabla

### Al iniciar un workflow `create-post`
1. Si el prompt viene de la memoria, localizar la entrada correspondiente
2. Cambiar su estado de `pendiente` a `en uso`
3. Actualizar la columna `Última actualización`

### Al completar y publicar un post
1. Localizar la entrada en la memoria
2. Cambiar su estado a `publicado`
3. Actualizar la columna `Última actualización`

### Si el prompt viene directamente del usuario (no de la memoria)
- No es obligatorio añadirlo a la memoria
- Si el agente considera que tiene valor para el historial, puede añadirlo con estado `publicado` directamente

---

## Formato de la Tabla de Memoria

El agente debe mantener la tabla exactamente en este formato para garantizar legibilidad y parseo correcto:

```markdown
| # | Juego | Plataforma | Tipo de Post | Enfoque | Estado | Última actualización |
|---|---|---|---|---|---|---|
| 1 | Nombre del juego | Plataforma | Tipo | Enfoque en una frase | pendiente | YYYY-MM-DD |
```

### Reglas de formato
- El campo `#` es un número secuencial que nunca se reutiliza
- El campo `Enfoque` debe ser una frase corta pero descriptiva (no más de 15 palabras)
- La fecha usa siempre formato `YYYY-MM-DD`
- Los estados se escriben siempre en minúsculas: `pendiente`, `en uso`, `publicado`

---

## Consulta de la Memoria

Si el usuario pregunta por el estado de las ideas (ej: "¿qué ideas tenemos pendientes?", "¿qué posts hemos publicado?"), el agente debe:

1. Leer `memory/post-ideas.md`
2. Filtrar por el estado solicitado
3. Presentar la información de forma clara y resumida, no volcando la tabla entera a menos que se pida explícitamente