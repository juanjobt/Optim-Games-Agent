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

## Mejora #2 — Chequeo de colisión de `wp_id` al crear tags (P1 · alta) — ✅ COMPLETADA

**Evidencia:** log 2026-05-11 (Cadillacs and Dinosaurs). El `wp_id 277` ya existía en DB local para "Nazca Corporation" (stale). El agente lo corrigió a mano ("DB corregida manualmente tras publicación") y dejó a Nazca con `wp_id=0`.

**Causa raíz (verificada en `db_query.py`):**
- `cmd_add_tag` (líneas 248-273) y `cmd_get_or_create_tag` (líneas 276-304) solo buscan duplicados por `name`, **nunca por `wp_id`**.
- La PRIMARY KEY de SQLite aborta el INSERT con `IntegrityError` genérico (líneas 269-271, 299-301) → se reporta como `str(e)` sin diagnosticar el conflicto. El agente no tiene forma de entender qué pasó.

**Implementación (sobre `db_query.py`):**
- Antes del INSERT en ambos subcomandos, consultar `SELECT name, slug FROM tags WHERE wp_id = ?` y, si la fila existe con `name` distinto al solicitado, devolver error específico con instrucción de reconciliación (`db_init.py sync-tags-wp`).
- Añadir nuevo subcomando **`detect-stale-tags`** que recorra la tabla local contra WordPress y reporte filas cuyo `wp_id` apunta a un tag con `name` distinto en WP.

**Esfuerzo estimado:** ~45 min. **Impacto:** evita desincronizaciones latentes y elimina "correcciones manuales" que dejan wp_id=0 huérfano.

---

## Mejora #3 — Auditoría y reconciliación de `post_tags` (P1 · alta) — ✅ COMPLETADA

**Evidencia:** log 2026-06-07. El post 120 (Portal) tiene en DB local `Dinamic Software, 1987, España, Años 80, Arcade` (cualquier cosa salvo Valve). `find-related` produjo enlaces a Pang y Freddy Hardest — técnicamente correctos dado el estado de la DB, editorialmente absurdos.

**Causa raíz (verificada en `manage-internal-links.py` y `db_init.py`):**
- `find_related` (`manage-internal-links.py:88-171`) confía ciegamente en `post_tags` local (líneas 89-95). No contrasta con WordPress, no valida coherencia semántica.
- `sync-posts-wp` (`db_init.py:361-424`) usa `INSERT OR IGNORE` en `post_tags` (líneas 406-408): **aditivo, no reemplaza**. Aunque en WP el post ya tenga Valve/2007/PC, el histórico erróneo persiste.
- **No existe ningún comando de auditoría.** Confirmado por grep exhaustivo de `audit|conflict|stale|reconcil|verific` en todos los `.py`.

**Implementación:**
1. Nuevo subcomando **`audit-post-tags --wp-id N | --all`** en `db_query.py`: fetch `GET /wp/v2/posts/{id}?_fields=id,title,slug,tags` + `_wp_fetch_all_tags`, reportar `in_wp_not_in_db`, `in_db_not_in_wp` y `name_mismatches` (caso stale tags en tabla tags).
2. Nuevo subcomando **`reconcile-post-tags --wp-id N | --all [--dry-run]`** en `db_query.py`: DELETE de las `post_tags` cuyo `tag_wp_id` no está en WP para ese post + INSERT de las que WP tiene y local falta (solo si el tag existe en tabla tags local; las ausentes se reportan en `tags_in_wp_not_in_local_db`). El dry-run no toca la DB.
3. Flag **`--reconcile`** en `sync-posts-wp` (`db_init.py`): reescribe `post_tags` (DELETE+INSERT) en vez de `INSERT OR IGNORE` aditivo, y refresca `posts.title/slug/category_slug/published_at` de los posts existentes (en vez de `INSERT OR IGNORE`). Reporta `posts_updated` y `post_tags_deleted`.
4. Flag **`--validate`** en `find-related` (`manage-internal-links.py`): añade un bloque `validation` al output con `is_valid`, `in_wp_not_in_db`, `in_db_not_in_wp` y `name_mismatches` para el post fuente. No bloquea, solo advierte.
5. Helpers `_wp_fetch_post` y `_wp_fetch_all_posts` añadidos a `db_query.py`; helpers `_fetch_all_wp_tags` (con `html.unescape`) y `_fetch_wp_post` añadidos a `manage-internal-links.py` (autocontenidos, sin dependencia recíproca entre scripts).

**Pruebas (6 tests unitarios, todos pasan sobre DB SQLite temporal con HTTP mock):**
- T1: audit-post-tags detecta tag stale (#281/>1988 vs WC>Toaplan) + tag extra en WP no en DB local.
- T2: audit-post-tags sobre post sano devuelve 0 issues.
- T3: reconcile-post-tags --dry-run no toca la DB (verifica con diff antes/después).
- T4: reconcile-post-tags real ejecuta DELETE de post_tag extra (tag 888 → WP no lo tiene) y deja intactas las demás.
- T5: db_init.py sync-posts-wp --reconcile reescribe post_tags de todos los posts, omite tags de WP no en tabla tags local, y refresca posts existentes.
- T6: find-related --validate genera bloque `validation` con `is_valid=False` + `in_wp_not_in_db` correctamente.

**Aplicación contra DB de producción (5 fases):**

1. **Backup preventivo:** `blog.db.bak_20260705_102229` (147 KB) conservado.
2. **Auditoría inicial con `audit-post-tags --all`:** detectados **7 posts con divergencia** sobre 54:
   - 3 posts con `in_db_not_in_wp` (tags en DB local ausentes en WP): Saboteur (#337 - tag 80 FPS), Day of the Tentacle (#700 - tag 265 Atlus), Metal Slug (#769 - tags 277/278/279 Cadillacs/Saga Metal Slug/Metal Slug). Reason: el agente antiguo añadió tags a estos posts mediante `add-post-tags` y luego los tags se eliminaron de WP manualmente.
   - 4 posts con `name_mismatches` (stale tags en tabla tags): Tetris Arcade (#859, 278/279), Snow Bros (#950, 281/282), KOF '94 (#956, 285/286), 1941 (#981, 286). Reasons: bug de swap wp_id de Mejora #2 — los wp_ids 278/279/281/282/285/286 estaban asignados en DB local a names errados frente a WP.
   - 0 casos de `in_wp_not_in_db`.
3. **Dry-run de `reconcile-post-tags --all`:** 3 posts con cambios propuestos (5 DELETE post_tags extra, 0 INSERT).
4. **Fase A — `reconcile-post-tags --all` ejecutado:** 5 DELETE sobre 3 posts (Saboteur, DotT, Metal Slug), 0 INSERT. Posts ahora cuadran con WP en número de tags.
5. **Fase B — Swap de 6 wp_ids stale en tabla tags** (transacción atómica con `PRAGMA foreign_keys = OFF`):
   - Renombrado atómico en 2 fases (temporales `__TMP_SWAP_<id>` → destino final) para evitar violar UNIQUE de `name` y `slug`.
   - Mapping aplicado:
     | wp_id | nombre antes (local errado) | nombre después (alineado con WP) | group_id antes | group_id después |
     |-------|------------------------------|----------------------------------|----------------|------------------|
     | 278 | Saga Metal Slug              | 1988                             | 7 (Saga)       | 4 (Año)          |
     | 279 | Metal Slug                   | Atari Games                      | 7 (Saga)       | 5 (Desarrol.)    |
     | 281 | 1988                         | Toaplan                          | 4 (Año)        | 5 (Desarrol.)    |
     | 282 | Atari Games                  | 1990                             | 5 (Desarrol.)  | 4 (Año)          |
     | 285 | Toaplan                      | The King of Fighters '94         | 5 (Desarrol.)  | 7 (Saga)         |
     | 286 | 1990                         | Saga The King of Fighters        | 4 (Año)        | 7 (Saga)         |
   - `group_id` realineado por consistencia con tags análogos (verificado patrón: todos los tags `199X` con slug año van a `group_id=4`, todos los `Capcom`/`SNK`/`Square` van a `group_id=5`, todos los `Saga X` van a `group_id=7`).
   - **Importante:** las `post_tags` NO se tocaron. Hacer el swap de `name`/`slug` en tabla `tags` es suficiente porque las `post_tags` referencian `wp_id`, y los `wp_id` ya son correctos (solo divergían los names).

**Verificación post-fix:**
- `detect-stale-tags`: `stale_count=0` ✅ (de 6 → 0). Solo permanece el caso histórico `Nazca Corporation wp_id=0` (huérfano del log 2026-05-11, sin post_tags, sin efecto).
- `audit-post-tags --all`: `posts_with_issues_count=0` ✅ (de 7 → 0). Cero divergencias en in_wp_not_in_db, in_db_not_in_wp y name_mismatches sobre los 54 posts.
- `manage-internal-links.py find-related --wp-id 950 --validate` sobre post previamente afectado (Snow Bros.): output incluye `validation.is_valid=True`, `count=3` posts relacionados (Ghosts 'n Goblins, Street Fighter II, máquinas recreativas) — todos coherentes editorialmente y consistentes con los tags reales del post en WP.

**Decisiones clave durante implementación:**
- No ejecutar `detect-stale-tags --fix` ni `sync-tags-wp` a ciegas (corraborado por predict previo de Mejora #2): rompería `post_tags` por FK no-cascada y/o crearía tags duplicados en WP. Se hizo swap atómico en su lugar.
- `reconcile-post-tags` no crea tags nuevos en WP ni modifica tabla `tags`. Sanea solo relaciones `post_tags`. Para fix de names en tabla `tags` se aplicó la fase B complementaria en el mismo workflow.
- `audit-post-tags --all` solo procesa posts en la tabla local `posts`. Detectó 3 orphan post_tags en post 853 (post_wp_id no presente en `posts` local) durante análisis adicional — fuera del scope del subcomando (no es su responsabilidad cubrir orphans); registrados para limpieza futura si hace falta.

**Archivos tocados:**
- `memory/scripts/db_query.py`: añadidos `_wp_fetch_post`, `_wp_fetch_all_posts`, `_audit_one_post`, `cmd_audit_post_tags`, `cmd_reconcile_post_tags`. Parser + dispatch actualizados. Bug typo `missing_in_local_db` (vs `missing_in_local`) corregido en 2 sitios.
- `memory/scripts/db_init.py`: `cmd_sync_posts_wp` refactorizado para soportar `--reconcile`. Ahora hace UPDATE en `posts` existentes (no solo `INSERT OR IGNORE`) y DELETE+INSERT en `post_tags` cuando se pasa `--reconcile`. Reporta `posts_updated` y `post_tags_deleted`.
- `.opencode/skills/link-related-posts/scripts/manage-internal-links.py`: añadidos helpers `_fetch_all_wp_tags`, `_fetch_wp_post` y función `_validate_post_tags`; `find_related` actualizado para pasar `validate` flag e incluir bloque `validation` en output; `cmd_find_related` resuelve `wp_config` cuando `--validate` se usa; parser con flag nuevo.

**Siguiente:** Mejora #4 (validación HTTP previa de URLs en `find-game-image`).

---

## Mejora #4 — Validación HTTP previa de URLs en `find-game-image` (P2 · media) — ✅ COMPLETADA

**Evidencia:** log 2026-06-26 (Final Fantasy Tactics). El screenshot 3 venía de `fantasyanime.com/.../Chapter%201/...jpg`. Pasó todos los filtros del Paso 5 (extensión .jpg válida, metadatos de tamaño declarados OK) y rompió en el Paso 5.5. El agente tuvo que improvisar un fallback a RAWG. Adicionalmente, en 2026-05-11 el agente filtró "a mano" imágenes de YouTube/TikTok/Instagram — criterio que **no estaba formalizado** en ningún sitio.

**Causa raíz (verificada en `find-game-image/`):**
- La skill solo tenía dos archivos: `SKILL.md` (prompt) y `generate_image.py` (Paso 3 HF). **Toda la validación de URLs de SerpApi/RAWG vivía como prosa Markdown** y dependía de que el LLM la obedezca.
- No existía ni un HEAD, ni un GET parcial, ni lectura de `status_code`/`Content-Type`. El filtro anti-hotlink y el de dominios no existían como código.

**Implementación:**
1. Creado `find-game-image/scripts/validate_image_urls.py` con:
   - **HEAD opcional** + **GET con `Range: bytes=0-2047`** para inspeccionar magic bytes (`\xff\xd8\xff` JPG, `\x89PNG` PNG, `RIFF...WEBP` WEBP, `GIF87a/89a` GIF).
   - **User-Agent realista** (Chrome 124 desktop), `timeout=10s`, `max_retries=3` con backoff exponencial base 2s. Reintenta en 429/503/500/502/504.
   - **Detección anti-hotlink**: segundo HEAD sin `Referer` y comparación de `Content-Length` y status code con el HEAD original. Si sin Referer devuelve 401/403 y con Referer 200 → anti-hotlink confirmado. Si `Content-Length` difiere >30% → sospechoso. Descarta en ambos casos.
   - **HTTP 416 (Range Not Satisfiable)**: fallback automático a GET completo (algunos CDN no soportan Range en imágenes pequeñas).
   - **Normalización de URLs**: `urllib.parse.urlsplit` + `quote` solo de path/query (conservando `%XX` ya codificado). Lowercase en `netloc`. Forzar scheme `http`/`https`.
   - **Salida JSON enriquecida**: `valid_urls` (array filtrado), `results` (detalle por URL con `http_status`, `content_type`, `content_length`, `magic_bytes`, `format`, `validated_at`, warnings). `upload-wordpress-image` puede usar `valid_urls` directamente y ahorrar re-validación.
2. Formalizadas listas de dominios en el script:
   - **Whitelist preferente**: `media.rawg.io`, `archive.org`, `mobygames.com`, `nintendo.com`, `playstation.com`, `cdn.cloudflare.steamstatic.com`, `gamefaqs.gamespot.com`, `static.wikia.nocookie.net`.
   - **Blacklist**: `youtube.com`, `*.ytimg.com`, `tiktok.com`, `instagram.com`, `*.fbcdn.net`, `x.com`, `twitter.com`, `pbs.twimg.com`, `pinimg.com`, **`fantasyanime.com`** (anti-hotlink conocido, log 2026-06-26).
   - Dominios desconocidos se aceptan **provisionalmente** con un warning en el reporte.
3. Actualizado `SKILL.md` (versión 4.0):
   - Añadido **Paso 0 — Validación final de URLs** antes de devolver el array, invocando el script vía bash.
   - Sección **Listas de dominios (deterministas)** con todas las tablas whitelist/blacklist.
   - Criterio **Magic bytes** añadido a la sección de criterios de imagen válida.
   - **Refuerzo screenshots (3 capas)**: se documenta que para `image_type=screenshot` debe haber al menos 2 URLs de `media.rawg.io` en el resultado final (la fuente más estable), y si SerpApi aporta <1 y RAWG screenshots endpoint da <2, ejecutar búsqueda adicional con `background_image_additional`.
4. `allowed-tools` de `SKILL.md` ampliado para mencionar `bash` al script de validación (implícito en la frase de "Herramienta a usar").

**Pruebas unitarias (9 tests, todos pasan sobre `urllib.request.urlopen` mockeado):**
- T1: URL inválida (sin scheme) → rechazada en seco.
- T2: URL en blacklist (`ytimg.com`) → rechazada sin HTTP call (corta circuito por dominio).
- T3: URL en whitelist (`media.rawg.io`) + magic bytes JPG válidos → ok=True, `format=jpg`, `domain_whitelisted=True`, `anti_hotlink_ok=True`.
- T4: URL en whitelist pero magic bytes son HTML (`<!DOCTYPE...`) → ok=False, `magic_bytes_ok=False`, warning en reporte.
- T5: Anti-hotlink HEAD 200 con Referer / 403 sin Referer → ok=False, `anti_hotlink_ok=False`, error menciona "anti-hotlink".
- T6: HTTP 404 → ok=False, `http_status=404`, error `HEAD HTTP 404`.
- T7: Range Not Satisfiable 416 → fallback automático a GET completo → ok=True, magic bytes correctos.
- T8: URL con path no-ASCII (`Chapter 1/shot%20one.jpg`) → normalizado a `Chapter%201/shot%20one.jpg`, dry-syntax-only OK.
- T9: Dominio desconocido + magic bytes válidos → ok=True con warning "no en whitelist; considerando OK provisional".

**Bug encontrado y fixeado durante tests:** `validate_magic_bytes` era laxa por defecto (default OK si no matches formato conocido, "trusting Content-Type"). Cambiado a estricta (`(None, False)` si no matches). Importante: si el server dice `image/jpeg` pero los primeros bytes son HTML, ahora se descarta.

**Archivos tocados:**
- `find-game-image/scripts/validate_image_urls.py` (nuevo, ~340 líneas) — todo el motor de validación.
- `find-game-image/SKILL.md` — versión 3.0 → 4.0, añadidos: Paso 0 de validación, sección listas de dominios, criterio magic bytes, refuerzo screenshots 3 capas.

**Siguiente:** Mejora #5 (consistencia y timestamps en logs).

---

## Mejora #5 — Consistencia y formato de los logs (P3 · baja) — ✅ COMPLETADA

**Evidencia:** inconsistencias temporales:
- log 2026-06-26: `Iniciado 17:30` / `Finalizado 13:47` (del día anterior literalmente).
- log 2026-06-01: `Iniciado 16:17` / `Finalizado 21:57` (≈5h40 reales vs `~20 min` declarado).
- log 2026-05-23: `~1h 16min` declarado.
- Adicionalmente `Schema ID: 118` repetido en todos los logs (sin aclarar si es el mismo tipo reusable o un bug).

**Causa raíz (verificada en `.opencode/rules/execution-logging.md`):**
- La regla exigía `Iniciado: YYYY-MM-DD HH:MM` y `Duración total: X min (estimada)` — formato sin zona horaria y con estimación editorial explícita. Sin captura real de `date`, el agente recurría a ojo → inconsistencias.
- La mención a `Schema ID` en la sección "Información útil" no distinguía entre el *tipo* de schema (reutilizable, ID 118 fijo del plugin configurado en `.env` como `WP_VIDEOGAME_SCHEMA_ID`) y la *asignación* a un post concreto.

**Implementación (sobre `execution-logging.md`):**
1. Añadida nueva sección **`## Formato de timestamps (OBLIGATORIO)`** que impone ISO 8601 con offset explícito (`2026-06-26T17:30+02:00`), captura real con `date` en bash, y duración **calculada** (no estimada). `N/A` solo si no se pudo capturar el timestamp final.
2. Cabecera del log: `Iniciado` pasa de `YYYY-MM-DD HH:MM` a `YYYY-MM-DDTHH:MM±HH:MM` con nota aclarando que el `[HH:MM]` del titular se mantiene sin offset solo por legibilidad.
3. Entrada por paso: `Duración` ahora describe cálculo por resta de timestamps reales (no "estimada si es posible").
4. Resumen final: `Finalizado` en ISO 8601 con offset; `Duración total` como resta `Finalizado − Iniciado`.
5. Añadida sección **`## Schema ID: tipo vs asignación`** que aclara que `WP_VIDEOGAME_SCHEMA_ID=118` es un *tipo* reutilizable (mismo ID para todos los posts), exige nombrarlo `schema_type_id` (no `Schema ID`), y reserva `schema_assignment_id` por si el plugin devuelve someday un ID único por post.
6. Sección "Información útil" actualizada: eliminado `schema ID` genérico, añadido `schema_type_id` con referencia a la nueva sección.
7. Ejemplo completo del log actualizado: `Iniciado`/`Finalizado` en ISO 8601, paso 7.5 menciona `schema_type_id: 118 (tipo reutilizable del plugin)`.
8. Regla adicional #3 cambiada de "Registrar tiempos estimados" → "Registrar tiempos calculados" (alineada con la nueva sección de timestamps; antes se contradecía).

**Verificación:**
- Confirmado el statu quo técnico del schema: `set-videogame-schema/SKILL.md:31` y `wp_set_schema.py:22,46,190` usan `WP_VIDEOGAME_SCHEMA_ID=118` / `DEFAULT_SCHEMA_ID = "118"`. La inyección solo escribe metadatos `saswp_*_118` en el post — no devuelve un ID de asignación único. Por eso `Schema ID: 118` era literalmente el mismo en todos los logs (`2026-06-20`, `2026-06-26`) sin que fuera un bug: es el tipo reutilizable del plugin, ahora correctamente nombrado.
- Lectura completa del archivo regla (274 líneas tras la edit) confirma coherencia interna entre la sección de timestamps, los templates y el ejemplo.

**Archivos tocados:**
- `.opencode/rules/execution-logging.md`: 8 ediciones puntuales. Sin cambios de comportamiento en scripts — mejora puramente editorial/normativa.

**Siguiente:** Mejora #6 (verificar bug post-idea↔post de `project-ideas.md`).

---

## Mejora #6 — Verificar bug "post-idea no se relaciona con el post creado" (P3 · baja) — ✅ COMPLETADA

**Evidencia:** anotación en `docs/route/project-ideas.md:51-53`: *"parece que cuando se inserta un post al final no se termina relacionando el post-idea con ese post recien insertado"*. **No aparece reproducción en los 10 logs recientes** — en todos ellos el Paso 8 actualiza la idea a `publicado` con `post_wp_id` correctamente. **Posible regresión resuelta** o caso no logueado.

**Verificación ejecutada contra DB de producción (`memory/blog.db`):**
- `db_query.py stats`: 53 ideas `publicado`, 54 posts, 7 ideas `pendiente`.
- Consulta directa a SQLite:
  - Ideas `publicado` con `post_wp_id IS NULL`: **0**.
  - `post_wp_id` de ideas que NO existen en tabla `posts`: **0** (todas las ideas pubblicado apuntan a un post existente).
  - `wp_id` en `posts` que NO tienen idea asociada: **1** → post 15 (`Freddy Hardest: El juego que nos traumó (y amamos) en los 80`, slug `review-freddy-hardest-zx-spectrum`).

**Conclusión:** El bug descrito (idea → no se relaciona con post) está **resuelto** — no hay ni una sola idea `publicado` sin `post_wp_id`, ni una cuyo `post_wp_id` falte en `posts`. La única asimetría es **1 post en dirección contraria** (post sin idea), probablemente creado fuera del flujo de `/create-post` (sin pasar por la cola de ideas) — no es el bug anotado y no requiere fix en el workflow.

**Acciones aplicadas:**
1. Eliminada la nota obsoleta `# error al relacionar los post creados en post-ideas` de `docs/route/project-ideas.md:51-53` (deuda cerrada).
2. No se añadió assertion al Paso 8 de `/create-post` — el flujo actual ya funciona correctamente según la evidencia empírica de la DB y de los logs. Añadir un assertion sería over-engineering sin valor.

**Decisiones clave:**
- No se的追求 retroactivo de cuándo/por qué se creó el post 15 (Freddy Hardest) sin idea: está fuera de scope y es inofiencivo. Queda registrado por si aparece un patrón.
- La verificación empírica (DB + 10 logs) se consideró suficiente — no se añade test unitario porque no hay bug que reproducir.

**Archivos tocados:**
- `docs/route/project-ideas.md`: eliminadas 5 líneas (cabecera `# error...` + párrafo descriptivo + líneas en blanco).

**Siguiente:** Todas las mejoras (1-6) del plan están completadas. Plan cerrado.

---

## Resumen priorizado

| # | Mejora | Prioridad | Esfuerzo | Estado |
|---|--------|-----------|----------|--------|
| 1 | Fix `FileNotFoundError` en subida de imágenes | **P0** | ~30 min | ✅ COMPLETADA |
| 2 | Chequeo colisión `wp_id` en `add-tag`/`get-or-create-tag` | P1 | ~45 min | ✅ COMPLETADA |
| 3 | Auditoría + reconciliación de `post_tags` | P1 | ~2-3 h | ✅ COMPLETADA |
| 4 | Validación HTTP previa de URLs en `find-game-image` | P2 | ~3-4 h | ✅ COMPLETADA |
| 5 | Consistencia/timestamps en logs | P3 | ~15 min | ✅ COMPLETADA |
| 6 | Verificar bug post-idea↔post de `project-ideas.md` | P3 | ~20 min | ✅ COMPLETADA |

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

### 2026-07-04 — Mejora #2 completada
- Editado `db_query.py`:
  1. `cmd_add_tag`: añadido chequeo explicito de colision de `wp_id` antes del INSERT. Si el `wp_id` ya existe en DB local mapeado a otro `name`, devuelve error accionable con `conflict_with` y `hint: "db_init.py sync-tags-wp"` (en vez de `IntegrityError` generico).
  2. `cmd_get_or_create_tag`: mismo chequeo, solo cuando se pasa `--wp-id` explicitamente (evita falsos positivos al buscar existentes por nombre).
  3. Añadido nuevo subcomando `detect-stale-tags [--fix]` que:
     - Fetch de todos los tags de WordPress via `wp_api_get_all`.
     - Reporta 3 categorias: `stale` (wp_id local mapea a name distinto en WP), `missing_in_wp` (wp_id local no existe en WP), `wp_only` (tags en WP no registrados localmente).
     - Con `--fix` lanza `db_init.py sync-tags-wp` via subprocess para reconciliar.
  4. Refactorizado a helpers autocontenidos (`_load_env`, `_wp_get_config`, `_wp_fetch_all_tags`) para no depender de un import dinamico de `db_init.py` (mas testeable y robusto).
- Pruebas (7 tests, todas pasan): colision rechazada en `add-tag`, colision rechazada en `get-or-create-tag`, no-colision aceptada, existente devuelto sin crear, error claro sin credenciales WP, deteccion mockeada de stale, cero falsos positivos en DB limpia.
- Regression contra DB real:
  - `stats` OK (158 tags, 54 posts, 60 ideas — 53 publicadas, 7 pendientes).
  - `get-or-create-tag --name "Super Nintendo" --group sistema` OK.
  - **`detect-stale-tags` contra WP real detectó 7 stale + 1 missing** en la DB de produccion.

### 2026-07-04 — Accion seguible aplicada (Sonic + HTML entity unescape)
**Ejecucion del fix sugerido:** revisar manualmente los 7 stale + 1 missing detectados y aplicar correccion selectiva solo donde fuera seguro.

**Impacto analizado (en `post_tags`):**
- Caso #260 (Sonic 3 & Knuckles vs `Sonic 3 &amp; Knuckles`): WP REST devuelve siempre el name escapado → falso positivo del detector. Posts afectados: 1 (post "Sonic 3 & Knuckles: cuando Michael Jacks...").
- Casos #281/#282/#285/#286 (1988, Atari Games, Toaplan, 1990): swap de wp_id entre tags consecutivos. `sync-tags-wp` los resolveria con `UPDATE wp_id` PERO dejaria `post_tags` huerfanas (FK no actualiza en cascada y `db_init` no activa `PRAGMA foreign_keys`). Posts afectados: 1-2 cada uno (Snow Bros, Tetris, KOF '94, 1941).
- Casos #278/#279 (Saga Metal Slug, Metal Slug): crear en WP nuevo DISPATCH duplicaria (esos names NO existen por nombre en WP). Posts afectados: 2 (Metal Slug, Tetris).
- Missing: Nazca Corporation con `wp_id=0` (huérfano por correccion manual del log 2026-05-11). Sin post_tags (limpio).

**Acciones aplicadas:**
1. **Corregido el caso Sonic en WordPress**: cambiado el name del tag WP ID 260 para asegurar storage interno sin HTML entity (`Sonic 3 & Knuckles`). WP siempre lo devolvera escapado por API REST, asi que fue necesario:
2. **Añadido `html.unescape()` en `_wp_fetch_all_tags`** (`db_query.py`) — normaliza los names devueltos por WP antes de usarlos. Esto elimina el falso positivo Sonic (stale_count 7 → 6).
3. **NO se ejecuto `--fix` ni `sync-tags-wp`**: el predict confirmo que romperia post_tags huerfanas y/o generaria tags duplicados en WordPress. El scope seguro de esta mejora eraSolo el fix Sonic.

**Verificacion:**
- Tests unitarios post-fix: Test add-tag colision-rechazo OK, Test detect-stale-tags con HTML entities (caso Sonic) OK (mock urlopen + check que NO stale), Test detect-stale-tags con swap real (1988 vs Toaplan) OK.
- `detect-stale-tags` contra WP real: stale_count=6 (Sonic fuera; restantes son swap real y Metal Slug/Nazca).

**Conclusion y transferencia a Mejora #3:**
- Los 6 stale restantes + 1 missing requieren reconciliacion integral: cambiar `tags.wp_id` alone rompe `post_tags` (FK no cascada). Hay que hacerlo en paralelo con update de las post_tags referenciadoras.
- Eso es justo lo que implementara la **Mejora #3** (`audit-post-tags` + `reconcile-post-tags`) — debe lidiar no solo con caso Portal (post 120 con tags errados) sino tambien con estos stales que se originan por una version anterior del agente que mal-asigno wp_ids consecutivos en 2026-05-13..2026-05-16.

- Siguiente: Mejora #3 (sustancialmente ampliado para cubrir estos stales+ sus post_tags asociadas, no solo el caso Portal).

### 2026-07-05 — Mejora #5 completada
- 8 ediciones puntuales sobre `.opencode/rules/execution-logging.md` (mejora puramente editorial/normativa, sin tocar scripts).
- Nueva sección `## Formato de timestamps (OBLIGATORIO)`: ISO 8601 con offset (`2026-06-26T17:30+02:00`), captura real con `date` en bash, duración calculada por resta de timestamps reales (`N/A` solo si no se pudo capturar).
- Templates de cabecera/entrada-resumen actualizados al nuevo formato ISO 8601.
- Nueva sección `## Schema ID: tipo vs asignación`: `WP_VIDEOGAME_SCHEMA_ID=118` identificado como `schema_type_id` (tipo reutilizable del plugin, mismo ID para todos los posts). Verificado contra `set-videogame-schema/SKILL.md:31` y `wp_set_schema.py:22,46,190`.
- Ejemplo completo del log reescrito con timestamps ISO 8601 y `schema_type_id: 118`.
- Regla adicional #3 corregida: "Registrar tiempos estimados" → "Registrar tiempos calculados" (antes se contradecía con la nueva sección).
- Siguiente: Mejora #6 (verificar bug post-idea↔post de `project-ideas.md`).

### 2026-07-05 — Mejora #6 completada
- `db_query.py stats`: 53 ideas `publicado`, 54 posts, 7 `pendiente`.
- Consulta SQLite directa: 0 ideas `publicado` con `post_wp_id` NULL; 0 ideas cuyo `post_wp_id` no está en `posts`; 1 post (wp_id=15, Freddy Hardest) sin idea asociada (dirección contraria al bug, fuera de scope).
- Bug descrito en `project-ideas.md:51-53` verificado como **resuelto** — eliminada la nota obsoleta.
- No se añadió assertion al Paso 8: el flujo actual funciona correctamente, sin evidencia de regresión en DB ni en 10 logs. Over-engineering evitado.
- **Plan de mejoras 1-6 cerrado.**