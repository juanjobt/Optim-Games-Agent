---
description: Añade internal links a posts existentes que necesitan enlaces relacionados. Procesa N posts usando la skill link-related-posts.
agent: content-marketer
---

Añade internal links a posts existentes que no tienen suficientes enlaces salientes. Procesa N posts en lote usando la skill `link-related-posts`.

## Parámetros

El comando acepta un número como parámetro indicando la cantidad de posts a procesar. Si no se indica, se procesan 5 posts.

Ejemplos de invocación:
- `/link-posts` → procesa los 5 posts más antiguos que necesitan links
- `/link-posts 3` → procesa los 3 posts más antiguos que necesitan links
- `/link-posts 10` → procesa los 10 posts más antiguos que necesitan links

---

## Paso 1 — Identificar posts que necesitan links

Ejecutar:

```bash
python3 .opencode/skills/link-related-posts/scripts/manage-internal-links.py needs-links --limit N
```

Donde N es la cantidad indicada por el usuario (por defecto 5).

Presentar al usuario la lista de posts encontrados y esperar confirmación antes de continuar:

```
📋 POSTS QUE NECESITAN INTERNAL LINKS
──────────────────────────────────────
1. "Freddy Hardest: El juego que nos traumó..." (ID: 15) — 0 enlaces
2. "Street Fighter II: La Historia..." (ID: 23) — 0 enlaces
3. ...
──────────────────────────────────────
¿Procesamos estos N posts? (sí / cancelar)
```

- **sí** → continuar al Paso 2
- **cancelar** → detener el proceso

Si no hay posts que necesiten links, informar al usuario y finalizar.

---

## Paso 2 — Procesar cada post

Cargar la skill `link-related-posts` y seguir su flujo de uso para procesar **un único post**. Antes de insertar cualquier enlace, leer el archivo `.opencode/skills/link-related-posts/reference/internal-links-insertion.md` con las reglas editoriales.

Para cada post de la lista obtenida en el Paso 1:

1. Aplicar el flujo completo de la skill `link-related-posts` sobre el post
2. Si el post no tiene candidatos con score > 0, saltarlo y registrar advertencia en el log
3. Si el post falla por cualquier error, registrar el error y continuar con el siguiente — **un error no bloquea el resto del lote**

Después de procesar cada post, mostrar un mini-resumen:

```
📝 "Título del post" (ID: X, enlaces: 0→2)
   → Enlace 1: "Post Relacionado 1" (score: 8)
   → Enlace 2: "Post Relacionado 2" (score: 5)
   ✅ Actualizado en WordPress
```

O si se saltó:

```
⚠️ "Título del post" (ID: X) — Sin candidatos con score > 0, saltado
```

O si hubo error:

```
❌ "Título del post" (ID: X) — Error al actualizar: [mensaje de error]
```

---

## Paso 3 — Reporte final

Mostrar resumen global:

```
🔗 INTERNAL LINKING COMPLETADO
─────────────────────────────────
Posts procesados: X
Posts con links añadidos: Y
Posts saltados (sin relacionados): Z
Posts con error: W
Total enlaces creados: N
─────────────────────────────────
```
