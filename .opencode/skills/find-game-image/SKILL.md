---
name: find-game-image
description: Busca imágenes para un videojuego usando SerpApi Google Images (fuente principal), RAWG como fallback estricto, y generación con IA vía Hugging Face Spaces como último recurso para portadas. Soporta búsqueda de portadas, screenshots y concepto artístico. Devuelve un array de URLs públicas. Requiere SERPAPI_KEY y RAWG_API_KEY en .env. HF_TOKEN es opcional.
compatibility: Requiere acceso a internet, keys de API (SERPAPI_KEY, RAWG_API_KEY) en .env. HF_TOKEN opcional para generación con IA.
metadata:
  author: optimbyte
  version: "3.0"
allowed-tools: webfetch, bash
---

# Skill: Buscar Imágenes de Videojuegos

Localiza imágenes de un juego Devuelve un array de URLs públicas listas para pasar a `upload-wordpress-image`.

---

## Parámetros de entrada

| Parámetro | Valores | Default | Descripción |
|-----------|---------|---------|-------------|
| `game_name` | texto (requerido) | — | Nombre del juego a buscar |
| `system` | texto | — | Sistema/plataforma del juego (usado en HuggingFace) |
| `image_type` | `portada` \| `screenshot` \| `concepto` | `portada` | Tipo de imagen a buscar |
| `count` | 1-5 | 1 | Número de imágenes a devolver |

### Comportamiento por tipo

| Tipo | SerpApi query | RAWG fallback | HuggingFace |
|------|---------------|---------------|-------------|
| `portada` | `{game} game cover art` | `background_image` del juego + validación de nombre | Sí (Paso 3) |
| `screenshot` | `{game} gameplay screenshot` | Endpoint `/games/{slug}/screenshots` | No |
| `concepto` | `{game} concept art artwork` | `background_image_additional` | No |

---

## Herramienta a usar

- Usa **webfetch** para las llamadas HTTP de los Pasos 1 y 2 (SerpApi y RAWG). Especifica siempre `format=markdown` en la llamada.
- Usa **bash** para ejecutar el script `generate_image.py` del Paso 3 (Hugging Face, solo para portada).

---

## Criterios de imagen válida

- **Formatos aceptados:** extensión de la URL debe ser `.jpg`, `.jpeg`, `.png` o `.webp`
- **Tamaño mínimo:** `min(original_width, original_height) >= 600`
- **Peso:** verificar `filesize` solo si el campo está presente. Si no está disponible, ignorar este criterio
- Descartar y pasar al siguiente si no cumple formato o tamaño
- Para `count > 1`: devolver hasta `count` imágenes que cumplan los criterios, iterando sobre los resultados disponibles

---

## Paso 1a — SerpApi con nombre original

Lee `SERPAPI_KEY` del `.env`. Construye y ejecuta con webfetch:

### Para portada:
```
https://serpapi.com/search.json?engine=google_images&q={NOMBRE_DEL_JUEGO}+game+cover+art&num=10&api_key={SERPAPI_KEY}
```

### Para screenshot:
```
https://serpapi.com/search.json?engine=google_images&q={NOMBRE_DEL_JUEGO}+gameplay+screenshot&num=10&api_key={SERPAPI_KEY}
```

### Para concepto artístico:
```
https://serpapi.com/search.json?engine=google_images&q={NOMBRE_DEL_JUEGO}+concept+art+artwork&num=10&api_key={SERPAPI_KEY}
```

- Si la respuesta devuelve error HTTP (503, 429, etc.), **no saltar al fallback todavía** — ir al Paso 1b
- Si la respuesta es válida, aplicar criterios sobre `images_results[]` e iterar en orden, recogiendo hasta `count` imágenes válidas
- Si no se encontraron suficientes imágenes, ir al Paso 1b

---

## Paso 1b — SerpApi con nombre traducido al inglés

Si el Paso 1a no encontró suficientes imágenes, traducir el nombre del juego al inglés y repetir la búsqueda con el mismo `image_type`:

### Para portada:
```
https://serpapi.com/search.json?engine=google_images&q={NOMBRE_EN_INGLÉS}+game+cover+art&num=10&api_key={SERPAPI_KEY}
```

### Para screenshot:
```
https://serpapi.com/search.json?engine=google_images&q={NOMBRE_EN_INGLÉS}+gameplay+screenshot&num=10&api_key={SERPAPI_KEY}
```

### Para concepto artístico:
```
https://serpapi.com/search.json?engine=google_images&q={NOMBRE_EN_INGLÉS}+concept+art+artwork&num=10&api_key={SERPAPI_KEY}
```

Ejemplos de traducción:
- "La Abadía del Crimen" → "The Abbey of Crime"
- "El Capitán Trueno" → "Captain Thunder"

- Aplicar los mismos criterios sobre `images_results[]`
- Si ambos Pasos 1a y 1b no encontraron suficientes imágenes, ir al Paso 2
- Si ambos Pasos 1a y 1b devuelven error HTTP, ir al Paso 2

---

## Paso 2 — RAWG API (fallback estricto)

Lee `RAWG_API_KEY` del `.env`.

### Para portada (comportamiento existente):

Construye y ejecuta con webfetch:
```
https://api.rawg.io/api/games?search={NOMBRE_DEL_JUEGO}&key={RAWG_API_KEY}&page_size=5
```

Validación estricta:
1. **Coincidencia del juego:** comparar el campo `name` del resultado con el nombre buscado. Solo aceptar si son el mismo juego (ignorar mayúsculas, artículos y acentos). Descartar versiones, remakes o títulos distintos
2. **Campo correcto:** usar únicamente `results[0].background_image`
3. **Formato válido:** extensión `.jpg`, `.jpeg`, `.png` o `.webp`
4. **No nulo:** `background_image` no debe ser `null`

Si el primer resultado no pasa la coincidencia de nombre, revisar `results[1]` y `results[2]` antes de descartar.

### Para screenshot:

Primero, buscar el juego para obtener su `slug`:
```
https://api.rawg.io/api/games?search={NOMBRE_DEL_JUEGO}&key={RAWG_API_KEY}&page_size=5
```

Validar coincidencia de nombre (igual que portada). Anotar el `slug` y `id` del resultado correcto.

Luego, obtener screenshots del endpoint dedicado:
```
https://api.rawg.io/api/games/{slug}/screenshots?key={RAWG_API_KEY}&page_size={count}
```

Iterar sobre `results[]` validando:
1. Campo `image` no es `null`
2. Extensión válida (`.jpg`, `.jpeg`, `.png`, `.webp`)
3. `min(width, height) >= 600`
4. Descartar duplicados (mismas URLs ya encontradas en Paso 1)

Si se necesitan más screenshots de los disponibles en la primera página, usar `next` para paginar.

### Para concepto artístico:

Usar el mismo endpoint de búsqueda del juego y obtener `background_image_additional`:
```
https://api.rawg.io/api/games?search={NOMBRE_DEL_JUEGO}&key={RAWG_API_KEY}&page_size=5
```

1. Validar coincidencia de nombre (igual que portada)
2. Usar `results[0].background_image_additional` si existe y cumple los criterios de formato
3. Si `background_image_additional` es `null`, no hay fallback para concepto artístico en RAWG

---

## Paso 3 — Generación con Hugging Face (solo para portada)

**Este paso SOLO aplica para `image_type=portada`.** Para `screenshot` y `concepto`, si el Paso 2 no encontró suficientes imágenes, ir directamente al Paso 4.

Si los Pasos 1 y 2 no encontraron imagen válida de portada, intentar generar una con IA usando un Space de Hugging Face.

### 3a — Ejecutar el script generate_image.py

El script `generate_image.py` se encuentra en el mismo directorio que este SKILL.md. Ejecutar con bash:

```bash
python3 {RUTA_DEL_SKILL}/generate_image.py "{NOMBRE_DEL_JUEGO}" "{SISTEMA}" --output-dir /tmp/game-images
```

Ejemplos:
- `python3 .../generate_image.py "Sonic the Hedgehog 3" "Sega Genesis" --output-dir /tmp/game-images`
- `python3 .../generate_image.py "The Abbey of Crime" "ZX Spectrum" --output-dir /tmp/game-images`

**Parámetros del script:**
- **Posicional 1:** Nombre del juego en inglés (con articulación natural)
- **Posicional 2:** Sistema/plataforma del juego (ej: "Sega Genesis", "Super Nintendo", "ZX Spectrum")
- **`--output-dir`:** Directorio donde guardar la imagen generada (por defecto: `generated/` dentro del directorio de la skill)

**Qué hace el script internamente:**
1. Lee `HF_TOKEN` del `.env` del proyecto (para autenticación opcional)
2. Construye un prompt con la plantilla: `retro video game cover art for {NOMBRE}, {SISTEMA} style, vibrant colors, 16-bit aesthetic, box art illustration, detailed character artwork, classic gaming era, high quality, detailed, professional cover art, no text overlay, clean composition`
3. Llama al Space **black-forest-labs/FLUX.1-dev** vía Gradio API (`/gradio_api/call/infer`)
4. Gestiona automáticamente reintentos (hasta 3 intentos) si el Space devuelve error
5. Guarda la imagen generada en el directorio de salida

### 3b — Procesar el resultado del script

El script devuelve por **stdout** la ruta del archivo generado:
- **Éxito:** ruta absoluta al archivo, ej: `/tmp/game-images/Sonic_the_Hedgehog_3_cover.png`
- **Error:** cadena que empieza con `ERROR:`, ej: `ERROR: No se pudo generar imagen...`

Si el resultado empieza con `ERROR:`:
- Ir al Paso 3c (generación manual)

Si el resultado es una ruta de archivo válida:
- Usar esa ruta como la imagen de portada (se pasará a `upload-wordpress-image`)
- La imagen se habrá guardado como `.jpg` o `.png`

### 3c — Generación manual (si el script falla)

Si la generación automática falla (Space saturado, error de GPU, etc.), se puede generar una imagen de forma rápida y gratuita siguiendo estos pasos:

1. Ir a https://huggingface.co/spaces y buscar **"Stable Diffusion"** o **"FLUX"**
2. Abrir un Space gratuito que acepte text-to-image (ej: `black-forest-labs/FLUX.1-dev`)
3. Introducir el prompt construido en el paso 3a
4. Esperar a que se genere (puede haber cola de esperas de unos segundos)
5. Descargar la imagen generada
6. Guardarla en `/tmp/game-images/` con el nombre `{NOMBRE_JUEGO}_cover.png`
7. Continuar con el flujo usando esa ruta como imagen de portada

> **Nota sobre los Spaces:** Son gratuitos pero pueden tener filas de espera durante horas punta. Si un Space da error, probar otro diferente — hay decenas de Spaces de Stable Diffusion y FLUX disponibles.

---

## Paso 4 — Sin imagen disponible

Si ninguna fuente (búsqueda, RAWG, ni generación con IA) devuelve suficientes imágenes:
- No bloquear el flujo de publicación
- Notificar: `⚠️ IMÁGENES PENDIENTES: solo se encontraron {n} de {count} imágenes {image_type} para [NOMBRE_DEL_JUEGO]`
- Devolver las URLs que sí se encontraron (puede ser un array con menos elementos que `count`)
- Si no se encontró ninguna, devolver array vacío `[]`

---

## Resultado esperado

Devolver un array JSON con las imágenes encontradas:

```json
[
  {"url": "https://images.nintendolife.com/1dde8816def92/na.large.jpg", "type": "portada", "alt": "Portada de Chrono Trigger"},
  {"url": "https://media.rawg.io/media/screenshots/162/16230fce.jpg", "type": "screenshot", "alt": "Captura de pantalla de Chrono Trigger"}
]
```

Los campos de cada objeto:

| Campo | Descripción |
|-------|-------------|
| `url` | URL pública directa de la imagen |
| `type` | El `image_type` solicitado (`portada`, `screenshot`, `concepto`) |
| `alt` | Texto alternativo descriptivo para accesibilidad |

### Textos alt por defecto

| Tipo | Formato del alt |
|------|----------------|
| `portada` | `Portada de {game_name}` |
| `screenshot` | `Captura de pantalla de {game_name}` |
| `concepto` | `{game_name} — concepto artístico` |

---

## Ejemplo de uso

### Buscar 1 portada (comportamiento original):
```
game_name: "Chrono Trigger"
image_type: "portada"
count: 1
```

### Buscar 3 screenshots:
```
game_name: "Chrono Trigger"
image_type: "screenshot"
count: 3
```

### Buscar 1 concepto artístico:
```
game_name: "Chrono Trigger"
image_type: "concepto"
count: 1
```