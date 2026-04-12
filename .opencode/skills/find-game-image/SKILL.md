---
name: find-game-image
description: Busca una imagen de portada para un videojuego usando SerpApi Google Images (fuente principal), RAWG como fallback estricto, y generación con IA vía Hugging Face Spaces como último recurso. Devuelve la URL pública de la mejor imagen encontrada o generada. Usar antes de upload-wordpress-image. Requiere SERPAPI_KEY y RAWG_API_KEY en .env. HF_TOKEN es opcional.
compatibility: Requiere acceso a internet, keys de API (SERPAPI_KEY, RAWG_API_KEY) en .env. HF_TOKEN opcional para generación con IA.
metadata:
  author: optimbyte
  version: "2.1"
allowed-tools: webfetch, bash
---

# Skill: Buscar Imagen de Portada

Localiza la mejor imagen disponible para un juego. Devuelve una URL pública lista para pasar a `upload-wordpress-image`.

---

## Herramienta a usar

- Usa **webfetch** para las llamadas HTTP de los Pasos 1 y 2 (SerpApi y RAWG). Especifica siempre `format=markdown` en la llamada.
- Usa **bash** para ejecutar el script `generate_image.py` del Paso 3 (Hugging Face).

---

## Criterios de imagen válida

- **Formatos aceptados:** extensión de la URL debe ser `.jpg`, `.jpeg`, `.png` o `.webp`
- **Tamaño mínimo:** `min(original_width, original_height) >= 600`
- **Peso:** verificar `filesize` solo si el campo está presente. Si no está disponible, ignorar este criterio
- Descartar y pasar al siguiente si no cumple formato o tamaño

---

## Paso 1a — SerpApi con nombre original

Lee `SERPAPI_KEY` del `.env`. Construye y ejecuta con webfetch:
```
https://serpapi.com/search.json?engine=google_images&q={NOMBRE_DEL_JUEGO}+game+cover+art&num=5&api_key={SERPAPI_KEY}
```

- Si la respuesta devuelve error HTTP (503, 429, etc.), **no saltar al fallback todavía** — ir al Paso 1b
- Si la respuesta es válida, aplicar criterios sobre `images_results[]` e iterar en orden
- Si ningún resultado cumple los criterios, ir al Paso 1b

---

## Paso 1b — SerpApi con nombre traducido al inglés

Si el Paso 1a falló o no encontró imagen válida, traducir el nombre del juego al inglés y repetir la búsqueda:
```
https://serpapi.com/search.json?engine=google_images&q={NOMBRE_EN_INGLÉS}+game+cover+art&num=5&api_key={SERPAPI_KEY}
```

Ejemplos de traducción:
- "La Abadía del Crimen" → "The Abbey of Crime"
- "El Capitán Trueno" → "Captain Thunder"

- Aplicar los mismos criterios sobre `images_results[]`
- Si ningún resultado cumple los criterios, ir al Paso 2
- Si ambos Pasos 1a y 1b devuelven error HTTP, ir al Paso 2

---

## Paso 2 — RAWG API (fallback estricto)

Lee `RAWG_API_KEY` del `.env`. Construye y ejecuta con webfetch:
```
https://api.rawg.io/api/games?search={NOMBRE_DEL_JUEGO}&key={RAWG_API_KEY}&page_size=5
```

Extrae y valida con estos criterios **estrictos**:

1. **Coincidencia del juego:** comparar el campo `name` del resultado con el nombre buscado. Solo aceptar si son el mismo juego (ignorar mayúsculas, artículos y acentos). Descartar resultados que sean versiones, remakes o títulos distintos (ej: "Extensum", "Resurrection", "Remastered")
2. **Campo correcto:** usar únicamente `results[0].background_image` — nunca usar screenshots ni otros campos
3. **Formato válido:** la URL debe tener extensión `.jpg`, `.jpeg`, `.png` o `.webp`
4. **No nulo:** `background_image` no debe ser `null`

Si el primer resultado no pasa la coincidencia de nombre, revisar `results[1]` y `results[2]` antes de descartar.

Si ningún resultado pasa todos los criterios, ir al Paso 3.

---

## Paso 3 — Generación con Hugging Face (último recurso)

Si los Pasos 1 y 2 no encontraron imagen válida, intentar generar una imagen de portada con IA usando un Space de Hugging Face.

> **Contexto:** La Inference API gratuita de Hugging Face ha eliminado los modelos de text-to-image (respuesta 410 Gone). La generación automática se realiza a través de **Spaces de Gradio**, que pueden estar saturados o temporalmente no disponibles. Si la generación automática falla, se ofrece una alternativa manual rápida.

### 3a — Ejecutar el script generate_image.py

El script `generate_image.py` se encuentra en el mismo directorio que este SKILL.md. Ejecutar con bash:

```bash
python3 {RUTA_DEL_SKILL}/generate_image.py "{NOMBRE_DEL_JUEGO}" "{SISTEMA}" --output-dir /tmp/game-images
```

Ejemplos:
- `python3 .../generate_image.py "Sonic the Hedgehog 3" "Sega Genesis" --output-dir /tmp/game-images`
- `python3 .../generate_image.py "The Abbey of Crime" "ZX Spectrum" --output-dir /tmp/game-images`

**Parámetros del script:**
- **Posicional 1:** Nombre del juego en inglés (con artículación natural)
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

Si ninguna fuente (búsqueda, RAWG, ni generación con IA) devuelve imagen válida:
- No bloquear el flujo de publicación
- Notificar: `⚠️ IMAGEN PENDIENTE: no se encontró imagen válida para [NOMBRE_DEL_JUEGO]`
- Devolver `null` para que `publish-wordpress` continúe sin `featured_media`

---

## Resultado esperado

Devolver únicamente la URL de la imagen seleccionada, por ejemplo:
```
https://images.nintendolife.com/1dde8816def92/na.large.jpg