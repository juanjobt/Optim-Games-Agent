---
name: find-game-image
description: Busca una imagen de portada para un videojuego usando SerpApi Google Images (fuente principal, con reintento en inglés) y RAWG como fallback estricto. Devuelve la URL pública de la mejor imagen encontrada. Usar antes de upload-wordpress-image. Requiere SERPAPI_KEY y RAWG_API_KEY en .env.
---

# Skill: Buscar Imagen de Portada

Localiza la mejor imagen disponible para un juego. Devuelve una URL pública lista para pasar a `upload-wordpress-image`.

---

## Herramienta a usar

Usa **webfetch** para todas las llamadas HTTP de esta skill. Especifica siempre `format=markdown` en la llamada.

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

## Paso 3 — Sin imagen disponible

Si ninguna fuente devuelve imagen válida:
- No bloquear el flujo de publicación
- Notificar: `⚠️ IMAGEN PENDIENTE: no se encontró imagen válida para [NOMBRE_DEL_JUEGO]`
- Devolver `null` para que `publish-wordpress` continúe sin `featured_media`

---

## Resultado esperado

Devolver únicamente la URL de la imagen seleccionada, por ejemplo:
```
https://images.nintendolife.com/1dde8816def92/na.large.jpg