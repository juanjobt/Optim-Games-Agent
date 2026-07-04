# Plan de Mejoras — Análisis de Logs de Ejecución

**Origen:** Revisión de los 10 logs en `memory/execution-logs/` (2026-05-11 → 2026-06-26) · 11 workflows `/create-post`, 1 `/generate-post-ideas`, 1 `/link-posts`.

**Resultado global:** 13 completados, 0 fallidos. Pero bajo ese 100% de éxito hay **dos bugs recurrentes** que el agente siempre recupera con workaround, más **un defecto latente de calidad de datos**.

---

## Mejora #1 — Fix del bug `FileNotFoundError` en subida de imágenes (P0 · CRÍTICA) — ✅ COMPLETADA

**Evidencia:** Aparece en **9 de 11 logs de /create-post**:
- 2026-05-16 (×2 sesiones), 2026-05-23, 2026-05-29, 2026-06-07, 2026-06-13 (`:` en el nombre), 2026-06-20, 2026-06-26.

**Síntoma:** `FileNotFoundError` al ejecutar `os.remove(tmp_path)` en el Paso 5.5 (subida de screenshots). El upload siempre completa correctamente, pero el traceback ensucia el log y obliga al agente a improvisar.

**Causa raíz (verificada en `wp_upload_image.py:281-298`):**

- **Causa A — Nombre no saneado:** `safe_name` (línea 282) solo reemplaza espacios y `/`. No filtra `: * ? " < > |`. En Windows, `:` se interpreta como separador de Alternate Data Stream → `open()` escribe OK, pero `os.remove()` falla con `FileNotFoundError`. Casos reales: `Street Fighter II: World Warrior`, `1941: Counter Attack`.
- **Causa B — Nombre temporal determinista + paralelismo:** El `tmp_path` se construye solo con `type+screenshot+game+ext`, sin `mkstemp`. La skill lanza los 3 screenshots en calls bash paralelas → todos escriben el mismo path literal → el primer `os.remove` gana, los demás fallan. El screenshot afectado varía (2 o 3, no siempre el mismo) y ocurre incluso en títulos sin `:` (Doom, Chrono Trigger).

**Implementación (sobre `wp_upload_image.py`):**
1. Sanear `safe_name` descartando todo carácter no alfanumérico salvo `-_` (alinear con `generate_image.py:226-228`).
2. Sustituir el path determinista por `tempfile.mkstemp(suffix=ext, prefix=...)` → nombre único atómico por proceso.
3. Envolver `os.remove` en `try/except FileNotFoundError` (defense in depth) y reorganizar el flujo con `try/finally` desde `download_image` para que la limpieza ocurra incluso si `upload_to_wordpress` lanza.
4. Cerrar el descriptor devuelto por `mkstemp` antes de `download_image` para que pueda reabrir el path en `wb`.

**Verificación:**
- Lanzar 2 screenshots en paralelo del mismo juego (reproducir el escenario de carrera).
- Lanzar 1 screenshot de un juego con `:` en el título (ej: `1941: Counter Attack`).
- En ambos casos no debe aparecer `FileNotFoundError` y el log debe decir "Archivo temporal eliminado".

**Esfuerzo estimado:** ~30 min. **Impacto:** elimina el warning más repetido del histórico.

---

## Mejora #2 — Chequeo de colisión de `wp_id` al crear tags (P1 · alta) — PENDIENTE

**Evidencia:** log 2026-05-11 (Cadillacs and Dinosaurs). El `wp_id 277` ya existía en DB local para "Nazca Corporation" (stale). El agente lo corrigió a mano ("DB corregida manualmente tras publicación") y dejó a Nazca con `wp_id=0`.

**Causa raíz (verificada en `db_query.py`):**
- `cmd_add_tag` (líneas 248-273) y `cmd_get_or_create_tag` (líneas 276-304) solo buscan duplicados por `name`, **nunca por `wp_id`**.
- La PRIMARY KEY de SQLite aborta el INSERT con `IntegrityError` genérico (líneas 269-271, 299-301) → se reporta como `str(e)` sin diagnosticar el conflicto. El agente no tiene forma de entender qué pasó.

**Implementación (sobre `db_query.py`):**
- Antes del INSERT en ambos subcomandos, consultar `SELECT name, slug FROM tags WHERE wp_id = ?` y, si la fila existe con `name` distinto al solicitado, devolver error específico con instrucción de reconciliación (`db_init.py sync-tags-wp`).
- Añadir nuevo subcomando **`detect-stale-tags`** que recorra la tabla local contra WordPress y reporte filas cuyo `wp_id` apunta a un tag con `name` distinto en WP.

**Esfuerzo estimado:** ~45 min. **Impacto:** evita desincronizaciones latentes y elimina "correcciones manuales" que dejan wp_id=0 huérfano.

---

## Mejora #3 — Auditoría y reconciliación de `post_tags` (P1 · alta) — PENDIENTE

**Evidencia:** log 2026-06-07. El post 120 (Portal) tiene en DB local `Dinamic Software, 1987, España, Años 80, Arcade` (cualquier cosa salvo Valve). `find-related` produjo enlaces a Pang y Freddy Hardest — técnicamente correctos dado el estado de la DB, editorialmente absurdos.

**Causa raíz (verificada en `manage-internal-links.py` y `db_init.py`):**
- `find_related` (`manage-internal-links.py:88-171`) confía ciegamente en `post_tags` local (líneas 89-95). No contrasta con WordPress, no valida coherencia semántica.
- `sync-posts-wp` (`db_init.py:361-424`) usa `INSERT OR IGNORE` en `post_tags` (líneas 406-408): **aditivo, no reemplaza**. Aunque en WP el post ya tenga Valve/2007/PC, el histórico erróneo persiste.
- **No existe ningún comando de auditoría.** Confirmado por grep exhaustivo de `audit|conflict|stale|reconcil|verific` en todos los `.py`.

**Implementación:**
1. Nuevo subcomando **`audit-post-tags --wp-id N [--all]`** en `db_query.py`: fetch `GET /wp/v2/posts/{id}?_fields=tags,title,slug` y reportar `tags_en_wp_no_en_db`, `tags_en_db_no_en_wp`, mismatches de nombre.
2. Nuevo subcomando **`reconcile-post-tags --wp-id N [--dry-run]`** que tras `DELETE FROM post_tags WHERE post_wp_id = N` reinserta con los `tag_wp_id` reales de WordPress.
3. Añadir flag **`--reconcile`** a `sync-posts-wp` para que refresque (no solo ignore) `posts.title/slug` y `post_tags`.
4. Añadir un `--validate` en `find-related` que advierta si los tags locales del post origen no cuadran con los de WordPress, sin bloquear.

**Esfuerzo estimado:** ~2-3 h. **Impacto:** sanea la base de datos de relaciones internas, hace determinista que los enlaces internos sean coherentes. Altísimo valor SEO: cada enlace absurdo es ruido.

**Nota:** es la mejora más invasiva (toca `db_init.py`, `db_query.py`, `manage-internal-links.py` y añade 2 subcomandos). Evaluaremos hacerla en rama aparte.

---

## Mejora #4 — Validación HTTP previa de URLs en `find-game-image` (P2 · media) — PENDIENTE

**Evidencia:** log 2026-06-26 (Final Fantasy Tactics). El screenshot 3 venía de `fantasyanime.com/.../Chapter%201/...jpg`. Pasó todos los filtros del Paso 5 (extensión .jpg válida, metadatos de tamaño declarados OK) y rompió en el Paso 5.5. El agente tuvo que improvisar un fallback a RAWG. Adicionalmente, en 2026-05-11 el agente filtró "a mano" imágenes de YouTube/TikTok/Instagram — criterio que **no está formalizado** en ningún sitio.

**Causa raíz (verificada en `find-game-image/`):**
- La skill solo tiene dos archivos: `SKILL.md` (prompt) y `generate_image.py` (Paso 3 HF). **Toda la validación de URLs de SerpApi/RAWG vive como prosa Markdown** y depende de que el LLM la obedezca.
- No existe ni un HEAD, ni un GET parcial, ni lectura de `status_code`/`Content-Type`. El filtro anti-hotlink y el de dominios no existen como código.

**Implementación:**
1. Crear `find-game-image/scripts/validate_image_urls.py` con:
   - HEAD opcional + GET con `Range: bytes=0-2047` para inspeccionar magic bytes (`\x89PNG`, `\xff\xd8`, `RIFF...WEBP`).
   - `User-Agent` realista, `timeout=10s`, `max_retries=3` con backoff (replicar patrón de `generate_image.py:36-37, 83-137`).
   - Detección de anti-hotlink: segundo GET sin `Referer` y comparar tamaño.
2. Formalizar en `SKILL.md` una **lista blanca preferente** (`media.rawg.io`, `archive.org`, `mobygames.com`, `nintendo.com`, `playstation.com`, `steamstatic.com`) y una **lista negra** (`ytimg.com`, `tiktok.com`, `instagram.com`, `fbcdn.net`, fansites con anti-hotlink conocido como FantasyAnime). Convierte en determinista lo que hoy es heurística del LLM.
3. Normalizar URLs (`urllib.parse.urlsplit` + `quote`) y enriquecer el JSON de salida con `http_status`, `content_type`, `validated_at` para que `upload-wordpress-image` pueda saltar re-validación.
4. Especial refuerzo del flujo **screenshot** (hoy solo 2 capas frente a las 3 de portada) — exigir mínimo 2 URLs de `media.rawg.io` cuando `image_type=screenshot`.

**Esfuerzo estimado:** ~3-4 h. **Impacto:** elimina los puntos de fallo en descarga y hace el comportamiento determinista entre ejecuciones.

---

## Mejora #5 — Consistencia y formato de los logs (P3 · baja) — PENDIENTE

**Evidencia:** inconsistencias temporales:
- log 2026-06-26: `Iniciado 17:30` / `Finalizado 13:47` (del día anterior literalmente).
- log 2026-06-01: `Iniciado 16:17` / `Finalizado 21:57` (≈5h40 reales vs `~20 min` declarado).
- log 2026-05-23: `~1h 16min` declarado.
- Adicionalmente `Schema ID: 118` repetido en todos los logs (sin aclarar si es el mismo tipo reusable o un bug).

**Implementación (carácter editorial en `execution-logging.md`):**
- Añadir una regla explícita: usar **UTC con offset explícito** (`2026-06-26T17:30+02:00`) y calcular la duración a partir de timestamps reales, no como "estimación" editorial.
- Especificar que `Schema ID 118` se refiere al ID del *schema type* reutilizable (no a un ID único por post), o distinguir `schema_type_id` de `schema_assignment_id`.

**Esfuerzo estimado:** ~15 min. **Impacto:** analítica fiable de tiempos por paso (hoy imposible).

---

## Mejora #6 — Verificar bug "post-idea no se relaciona con el post creado" (P3 · baja) — PENDIENTE

**Evidencia:** anotación en `docs/route/project-ideas.md:51-53`: *"parece que cuando se inserta un post al final no se termina relacionando el post-idea con ese post recien insertado"*. **No aparece reproducción en los 10 logs recientes** — en todos ellos el Paso 8 actualiza la idea a `publicado` con `post_wp_id` correctamente. **Posible regresión resuelta** o caso no logueado.

**Implementación:**
- Antes de tocar nada, ejecutar `db_query.py stats` y comparar `COUNT(post_ideas con estado 'publicado' y post_wp_id IS NOT NULL)` vs `COUNT(posts)`. Si cuadran, cerrar como "ya resuelto" y eliminar la nota obsoleta de `project-ideas.md`.
- Si hay discrepancias, añadir un assertion al final del Paso 8 del command `/create-post` que verifique `update-idea-state` devolvió `ok: true`.

**Esfuerzo estimado:** ~20 min de verificación. **Impacto:** cerrar una deuda documentada abierta.

---

## Resumen priorizado

| # | Mejora | Prioridad | Esfuerzo | Estado |
|---|--------|-----------|----------|--------|
| 1 | Fix `FileNotFoundError` en subida de imágenes | **P0** | ~30 min | ✅ COMPLETADA |
| 2 | Chequeo colisión `wp_id` en `add-tag`/`get-or-create-tag` | P1 | ~45 min | PENDIENTE |
| 3 | Auditoría + reconciliación de `post_tags` | P1 | ~2-3 h | PENDIENTE |
| 4 | Validación HTTP previa de URLs en `find-game-image` | P2 | ~3-4 h | PENDIENTE |
| 5 | Consistencia/timestamps en logs | P3 | ~15 min | PENDIENTE |
| 6 | Verificar bug post-idea↔post de `project-ideas.md` | P3 | ~20 min | PENDIENTE |

**Orden de ejecución acordado con el usuario:** 1 → 2 → 3 → 4 → 5 → 6, enfrentando una a una.

---

## Bitácora de implementación

### 2026-07-04 — Mejora #1 iniciada
- Plan plasmado en este archivo.
- Lectura de `wp_upload_image.py` completa (317 líneas) para confirmar los cambios exactos.

### 2026-07-04 — Mejora #1 completada
- Editado `wp_upload_image.py:281-323` con 3 fixes:
  1. `safe_name` ahora sanea todo caracter no alfanumerico salvo `-_` (fix Causa A: ADS por `:` en Windows).
  2. `tempfile.mkstemp` sustituye al path determinista (fix Causa B: colision por paralelismo).
  3. `try/finally` + `try/except FileNotFoundError` en la limpieza (defense in depth).
- Sintaxis validada con `python -c "import ast; ast.parse(...)"`.
- Pruebas runtime:
  - Prueba A: 7 juegos problematicos (Street Fighter II:, 1941:, KOF '94, etc.) crean/escriben/borran sin FileNotFoundError.
  - Prueba B: 5 threads en paralelo con mismo prefix → 5 paths unicos, 0 colisiones.
  - Prueba C: inspeccion visual de nombres resultantes (legibles y safe).
- `python wp_upload_image.py --help` OK (no regression en el parser).
- Siguiente: Mejora #2 (chequeo de colision de wp_id en add-tag/get-or-create-tag).