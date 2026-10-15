# Plan de actuación SEO — Mejora de indexación en Google

> Diagnóstico a partir de Google Search Console (datos hasta el 21/09/2026) y de los CSV exportados en `tmp/`.
> Objetivo: frenar el crecimiento de la bolsa "rastreadas, sin indexar", indexar el contenido que ya merece estarlo y evitar que el problema se repita con los próximos posts.

---

## Estado de progreso

| Fase | Descripción | Estado |
|------|-------------|--------|
| Fase 0 | Limpieza técnica (noindex + redirects) | ✅ Completada (06/10/2026) |
| Fase 1 | Rescate de los 16 posts sin indexar | 🔄 15/16 revisados; 13 solicitudes GSC enviadas y 3 pendientes por cuota |
| Fase 2 | Internal linking masivo (36 huérfanos) | ✅ Completada (06/10/2026): 124 enlaces, 0 posts huérfanos |
| Fase 3 | Cambios en el proceso de publicación | 🔄 Guardrails de publicación implementados; pendientes 3 medidas editoriales de ritmo, descubrimiento y calidad |
| Fase 4 | Monitorización | ⏳ Continua |

---

## 1. Diagnóstico

### Señales positivas
- Las **impresiones crecen** de forma clara: de ~54 diarias (julio) a ~74 de media (septiembre).
- No hay acción manual, ni desindexación, ni penalización. El sitio no está penalizado.

### Señales preocupantes
- Las **indexadas no crecen e incluso bajan**: llegaron a 49 y ahora son 41.
- Las **páginas sin indexar pasan de 153 a 213**. De las nuevas que Google va conociendo, prácticamente ninguna se indexa.

### Desglose de las 213 sin indexar
| Estado | Cantidad | ¿Problema? |
|--------|----------|------------|
| `noindex` | 104 | No, si son archivos/tags/categorías/paginación |
| **Rastreadas, sin indexar** | **75** | **Sí, aquí está el problema** |
| 404 | 18 | Parcial: ver Fase 0 |
| Descubiertas, sin indexar | 13 | No crítico (Google aún no las rastreó) |
| Redirección | 3 | Normal |

### Qué hay realmente dentro de las "75 rastreadas, sin indexar"
El CSV `tmp/sin-indexar-Tabla.csv` mezcla varios tipos. Al clasificarlo:

- **La gran mayoría son ruido** que debería llevar `noindex`: feeds (`/feed/`), páginas de tag, páginas de categoría, paginación (`/reviews/page/3/`), `author/.../feed/`, `comments/feed/` y assets JS.
- **Solo 16 son posts reales** (contenido que debería indexarse). Ver Fase 1.

### Hallazgo inicial: internal linking incompleto (resuelto en Fase 2)
El diagnóstico inicial de `memory/blog.db` detectó 36 posts sin enlaces internos. Tras completar la Fase 2:
- 63 posts publicados; **los 63 tienen al menos un enlace interno**.
- 124 enlaces internos insertados editorialmente y registrados en `internal_links`.
- 61 posts tienen 2 o más enlaces salientes; 2 tienen uno.

La orfandad interna detectada inicialmente queda resuelta. La mejora de enlaces facilita el descubrimiento y aporta contexto, aunque por sí sola no garantiza la indexación.

### Estado del sitemap (correcto)
- `robots.txt` apunta a `sitemap_index.xml` (Rank Math).
- `post-sitemap.xml` contiene los 63 posts.
- No hay sitemap de tags (correcto).
- `pagina-ejemplo` y `el-catalogo` ya no están en el sitemap.

---

## 2. Fase 0 — Limpieza técnica (404 + noindex) ✅ COMPLETADA

> Requiere acceso manual al panel de WordPress / Rank Math (confirmado disponible).

### Estado real (06/10/2026)

- **Rank Math → Titles & Meta**: tags, archivos de autor, paginación/subpáginas y búsquedas internas marcadas `noindex`. ✅
- **Redirect 301** `el-catalogo` → `catalogo`. ✅
- **Página `pagina-ejemplo`** borrada (papelera). ✅
- **Redirects de tags antiguos** configurados (ver mapeo completo en §2.1). ✅

### Mapeo de redirects aplicado (tags antiguos → destino)

| Tag antiguo (404) | Destino |
|---|---|
| `/tag/phantasy-star-iv/` | `/tag/saga-phantasy-star/` |
| `/tag/chrono-trigger/` | `/tag/saga-chrono/` |
| `/tag/donkey-kong-country/` | `/tag/saga-donkey-kong/` |
| `/tag/sonic-the-hedgehog/` | `/tag/saga-sonic/` |
| `/tag/super-metroid/` | `/tag/metroidvania/` |
| `/tag/desarrolladora-konami/` | `/tag/konami/` |
| `/tag/half-life/` | `/tag/valve/` (o `/tag/goldsrc/`) |
| `/tag/quake/` | `/tag/doom/` (misma desarrolladora, id Software) |
| `/tag/cave-story/` | `/historia-cave-story-desarrollador-solitario/` (post) |
| `/tag/earthbound/` | `/earthbound-fracaso-comercial-occidente/` (post) |

### Pendiente menor de Fase 0

- Tag local `Nazca Corporation` con `wp_id 0` (huérfano en DB). Revisar y corregir con `detect-stale-tags`/`sync-tags-wp`.
- Contaminación de tags detectada (ej: `Head Over Heels` tiene `Saga Resident Evil` y `FPS`). Auditar tags de posts con `audit-post-tags --all`.

### 2.1 — Redirects y páginas muertas

| URL problemática | Acción |
|------------------|--------|
| `/el-catalogo/` | 301 → `/catalogo/` |
| `/pagina-ejemplo/` | Borrar página (o 301 → home) |
| `/tag/quake/`, `/tag/super-metroid/`, `/tag/chrono-trigger/`, `/tag/cave-story/`, `/tag/donkey-kong-country/`, `/tag/half-life/`, `/tag/sonic-the-hedgehog/`, `/tag/earthbound/`, `/tag/phantasy-star-iv/` | Tags antiguos renombrados al formato `Saga X`. 301 → tag nuevo si existe, o dejar 404 (son archives de tag, no contenido real) |
| `/tag/desarrolladora-konami/` | 301 → `/tag/konami/` |

Los tags antiguos (`quake`, `chrono-trigger`, etc.) fueron reemplazados por el formato `Saga X` (ej: `Saga Donkey Kong`, `Saga Phantasy Star`, `Saga Sonic`). El nombre sin prefijo (`quake`, `super-metroid`) ya no existe como tag en WordPress.

### 2.2 — Configurar noindex en Rank Math

En **Rank Math → Titles & Meta**, marcar como `noindex`:
- **Feeds** (author feed, tag feed, category feed, comments feed)
- **Tag archives**
- **Author archives**
- **Paginación** de archives (o al menos las páginas 2+)

Decisión sobre **categorías**: como `reviews`, `historias` y `listas` son las categorías principales y aportan navegación, se pueden dejar indexables si tienen intro + imagen (ver `docs/plans/ui-blog-ideas.md`). En caso de duda, dejarlas indexables de momento.

### 2.3 — Sincronizar tags locales con WordPress

Ejecutar para detectar tags de la DB local cuyo `wp_id` ya no coincide con WordPress (residuo de los renombrados):

```bash
python3 memory/scripts/db_query.py detect-stale-tags
```

Si hay stale, revisar antes de corregir con `--fix` (que ejecuta `sync-tags-wp`).

### 2.4 — Corregir enlaces internos que apunten a 404

Auditar si algún post enlaza a `/el-catalogo/`, `pagina-ejemplo` o a los tags antiguos. Para cada post afectado:

```bash
python3 .opencode/skills/link-related-posts/scripts/manage-internal-links.py get-post-content --wp-id N
```

Corregir el enlace con `wp_update_post`.

---

## 3. Fase 1 — Rescate de los 16 posts reales sin indexar

Estrategia acordada: **enriquecer y re-indexar** todos los que tengan contenido aprovechable (no noindexarlos).

### Los 16 posts (con wp_id y categoría)

| # | wp_id | Slug | Tipo | Publicado |
|---|-------|------|------|-----------|
| 1 | 42 | review-phantasy-star-iv-mega-drive-jrpg | Review | 2026-03-10 |
| 2 | 36 | metal-gear-1987-historia-konami | Historia | 2026-03-09 |
| 3 | 30 | earthbound-fracaso-comercial-occidente | Historia | 2026-03-07 |
| 4 | 89 | sonic-marketing-estrategia-mario-rival | Historia | 2026-03-16 |
| 5 | 272 | 5-maquinas-recreativas-que-mas-robaron-paga-semanal | Lista | 2026-04-09 |
| 6 | 33 | review-castlevania-symphony-of-the-night | Review | 2026-03-07 |
| 7 | 250 | juegos-infravalorados-playstation | Lista | 2026-04-06 |
| 8 | 325 | review-head-over-heels-zx-spectrum | Review | 2026-04-12 |
| 9 | 15 | review-freddy-hardest-zx-spectrum | Review | 2026-03-01 |
| 10 | 75 | historia-cave-story-desarrollador-solitario | Historia | 2026-03-14 |
| 11 | 729 | review-shin-megami-tensei-snes | Review | 2026-05-03 |
| 12 | 199 | historia-panzer-dragoon-saga-satoshi | Historia | 2026-04-03 |
| 13 | 595 | historia-xenogears-playstation-disco-2 | Historia | 2026-04-24 |
| 14 | 320 | review-the-last-ninja-commodore-64 | Review | 2026-04-12 |
| 15 | 628 | link-to-the-past-mundos-ocultos-secretos | Historia | 2026-04-25 |
| 16 | 39 | review-tetris-game-boy-fenomeno-guerra-fria | Review | 2026-03-09 |

> **Nota (06/10/2026):** 12 de estos 16 ya tenían 2 enlaces internos (los "viejos" de marzo-abril). Los 4 que faltaban ya se enlazaron: `325`, `729`, `595`, `628`. Su problema principal es calidad/contenido/antigüedad, no orfandad.

### Por cada post, verificar y corregir

1. **Imagen destacada** — asignar si falta (skill `upload-wordpress-image`).
2. **Meta descripción** — entre 150-160 caracteres con la keyword principal (Rank Math o `excerpt`).
3. **Longitud mínima** — Review 1000-1500, Historia 800-1200, Lista 600-900 palabras.
4. **Contenido con voz propia** — opinión/dato/contexto que no esté en la fuente original. Si el post es fino, reescribirlo antes que dejarlo.
5. **≥2 enlaces internos** — ver Fase 2.
6. **Schema VideoGame** — inyectar si es Review/Historia y no lo tiene (skill `set-videogame-schema`).

### Progreso de enriquecimiento (06/10/2026)

| # | wp_id | Post | Estado |
|---|-------|------|--------|
| 16 | 39 | Tetris Game Boy | ✅ Enriquecido (590→993 palabras, review completa) |
| 3 | 30 | EarthBound | ✅ Enriquecido (596→865 palabras, dato falso corregido) |
| 6 | 33 | Castlevania SOTN | ✅ Enriquecido (799→1062 palabras, datos corregidos) |
| 8 | 325 | Head Over Heels | ✅ Enriquecido (869→1011 palabras, meta 196→157) |
| 14 | 320 | The Last Ninja | ✅ Enriquecido (926→1023 palabras, meta 196→158) |
| 1 | 42 | Phantasy Star IV | ✅ Enriquecido (981→1003 palabras, meta 175→157) |
| 2 | 36 | Metal Gear | ⚠️ Contenido OK (854 palabras), meta descripción atascada en API (98 caracteres, requiere manual) |
| 9 | 15 | Freddy Hardest | ✅ Corregido (ofendido, videojuego, https en imágenes, frase cortada completada, meta 129→153) |
| 4 | 89 | Sonic marketing | ✅ Corregido CJK `扭转`→"remontada" + meta 133→154 |
| 7 | 250 | Infravalorados PS | ✅ Meta 117→157 |
| 10 | 75 | Cave Story | ✅ Meta 143→155 |
| 11 | 729 | Shin Megami Tensei | ✅ Meta 204→150 |
| 5 | 272 | Máquinas recreativas | ✅ OK (meta 147, aceptable) |
| 12 | 199 | Panzer Dragoon Saga | ✅ OK (meta 146, aceptable) |
| 13 | 595 | Xenogears | ✅ OK (meta 157, sin cambios) |
| 15 | 628 | Link to the Past | ✅ OK (meta 155, sin cambios) |

> **Pendiente manual (06/10/2026):** wp_id 36 (Metal Gear) devuelve HTTP 500 en cualquier POST/PUT a la API REST (fallo de plugin al guardar). Actualizar la meta descripción desde el editor de WordPress: *"Metal Gear (1987): la historia de Hideo Kojima, Konami y cómo nació el género stealth con Solid Snake infiltrándose en Outer Heaven."* (152 caracteres).

### Pedir re-indexación en GSC

**Avance (06/10/2026):** se solicitaron reindexaciones para 13 de los 16 posts mediante **Google Search Console → Inspección de URL → Solicitar indexación**. Se alcanzó la cuota diaria; quedan estos 3 por solicitar en una sesión futura:

- `https://optimpixel.com/historia-xenogears-playstation-disco-2/`
- `https://optimpixel.com/link-to-the-past-mundos-ocultos-secretos/`
- `https://optimpixel.com/5-maquinas-recreativas-que-mas-robaron-paga-semanal/`

Las solicitudes no garantizan la indexación. Las URLs que GSC ya muestra como indexadas no necesitan otra solicitud; revisar el estado más adelante.

---

## 4. Fase 2 — Internal linking masivo ✅ COMPLETADA

Se completó el enlazado de los 36 posts que inicialmente estaban huérfanos, priorizando los 16 de la Fase 1. La cola debe revisarse de nuevo solo para detectar posts nuevos que queden sin enlaces.

**Resultado final (06/10/2026):** 124 enlaces internos insertados editorialmente y registrados en `internal_links`. Los 63 posts publicados tienen al menos un enlace saliente; 61 tienen 2 o más. **No quedan posts huérfanos.**

```bash
# Ver la cola de posts que necesitan enlaces
python3 .opencode/skills/link-related-posts/scripts/manage-internal-links.py needs-links --limit 40
```

Ejecutar el comando `/link-posts` en lotes (recomendado 5-10 por sesión) para no saturar:

```bash
# La skill procesa N posts con la lógica de find-related + inserción editorial
```

Reglas a respetar (ver `reference/internal-links-insertion.md`): máximo 2 enlaces por post, nunca en el primer párrafo, contexto natural, sin "clic aquí".

Prioridad:
1. Los 16 posts de la Fase 1.
2. El resto de huérfanos, de más antiguo a más reciente.

Meta final: **0 posts sin enlaces salientes**.

---

## 5. Fase 3 — Cambios en el proceso de publicación (preventivo)

Modificar la checklist de `publish-wordpress` / `create-post` para que **ningún post se considere "publicado" sin**:

- [x] Meta descripción de 150-160 caracteres con keyword principal
- [x] Imagen destacada asignada
- [x] Imágenes de contenido (según tipo de post)
- [x] **≥2 enlaces internos** a posts relacionados (usar `find-related` antes de publicar)
- [x] Schema VideoGame (Review/Historia)
- [x] Contenido con ángulo propio (no descripción oficial reescrita)

Medidas editoriales todavía pendientes:
- [ ] **Reducir el ritmo de publicación** y priorizar calidad sobre cantidad.
- [ ] **Enlazar cada post nuevo desde portada o categorías** (verificar que la home/categoría muestra los últimos posts).
- [ ] Si un post queda fino y no merece indexación, **marcarlo `noindex`** en vez de dejarlo engordar la bolsa de no-indexadas.

Acciones técnicas incorporadas al flujo del agente:
- [x] Internal linking obligatorio dentro de `create-post`; `/link-posts` queda para mantenimiento de posts ya publicados.
- [x] Filtrar y verificar destinos públicos; comprobar que las URLs quedaron en el contenido de WordPress antes de registrar los enlaces.
- [x] Validar meta descripción, imagen destacada, imágenes de contenido, longitud, ángulo editorial y schema antes de publicar.
- [x] Mostrar el contenido final y pedir confirmación explícita justo antes de cambiar el borrador a `publish`.

**Implementado (06/10/2026):** `create-post` crea un borrador, aplica `link-related-posts` en modo bloqueante, verifica el estado público de los destinos en WordPress, comprueba las dos URLs en el contenido guardado y solo entonces registra los enlaces. Tras comprobar imágenes, longitud, meta descripción, ángulo propio y schema cuando aplica, muestra el contenido final y pide confirmación antes de cambiar WordPress y la memoria a `publish`. La búsqueda de candidatos y la cola de `/link-posts` excluyen borradores. Validado con compilación Python y prueba aislada de que ambas consultas descartan posts `draft`.

**Nota de operación:** los posts nuevos se enlazan dentro de `/create-post`; no ejecutar `/link-posts` para ellos. `/link-posts` se reserva para añadir o completar enlaces en posts ya publicados.

---

## 6. Fase 4 — Monitorización

### Revisión mensual en Google Search Console
| Métrica | Meta |
|---------|------|
| Páginas indexadas | Crecer de 41 → 57+ (63 posts totales) |
| Rastreadas, sin indexar | Reducir de 75 → <20 (y que el resto sea ruido) |
| 404 | Reducir de 18 → <5 (solo ruido de uploads) |
| Impresiones | Mantener la tendencia al alza |

### Auditoría interna (mensual)
```bash
# Tags desincronizados
python3 memory/scripts/db_query.py detect-stale-tags

# Coherencia post_tags vs WordPress
python3 memory/scripts/db_query.py audit-post-tags --all

# Estado del internal linking
python3 memory/scripts/db_query.py link-stats
```

### Criterio de éxito
- Las 16 URLs de la Fase 1 pasan a indexadas.
- El nº de posts sin enlaces internos llega a 0.
- La bolsa de "rastreadas sin indexar" deja de crecer con contenido nuevo.

---

## 7. Siguientes acciones

Las Fases 0 y 2 están completadas, y los guardrails técnicos de la Fase 3 ya están implementados. El trabajo pendiente inmediato es:

1. **Cerrar Fase 1:** actualizar desde el editor de WordPress la meta descripción de Metal Gear (wp_id 36; texto propuesto en §3) y, cuando se restablezca la cuota diaria, solicitar la indexación de las tres URLs indicadas en §3.
2. **Completar las medidas editoriales de Fase 3:** mantener un ritmo de publicación más bajo, comprobar la visibilidad de los posts nuevos desde portada/categorías y decidir cuándo un contenido fino debe quedar `noindex`.
3. **Continuar Fase 4:** revisar mensualmente GSC y ejecutar la auditoría interna; comparar las métricas con los criterios de éxito de §6.

---

## Anexo — Herramientas y comandos de referencia

| Herramienta | Comando |
|-------------|---------|
| Posts que necesitan links | `python3 .opencode/skills/link-related-posts/scripts/manage-internal-links.py needs-links --limit N` |
| Relacionados de un post | `.../manage-internal-links.py find-related --wp-id N --limit 5` |
| Contenido de un post | `.../manage-internal-links.py get-post-content --wp-id N` |
| Tags desincronizados | `python3 memory/scripts/db_query.py detect-stale-tags` |
| Auditar tags de posts | `python3 memory/scripts/db_query.py audit-post-tags --all` |
| Estadísticas de enlaces | `python3 memory/scripts/db_query.py link-stats` |
| Internal linking en lote | comando slash `/link-posts N` |
| Inyectar schema | skill `set-videogame-schema` |
