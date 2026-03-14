---
name: find-game-image
description: Busca una imagen de portada para un videojuego consultando RAWG API (fuente principal) y Wikimedia Commons (fallback). Devuelve la URL pública de la imagen encontrada. Usar antes de subir una imagen a WordPress. Requiere haber leído el .env para obtener RAWG_API_KEY.
---

# Skill: Buscar Imagen de Portada

Localiza la mejor imagen disponible para un juego siguiendo el orden de prioridad del blog. Devuelve una URL pública lista para pasar a la skill `upload-wordpress-image`.

---

## Orden de prioridad

1. **RAWG API** — portadas oficiales de alta calidad
2. **Wikimedia Commons** — imágenes con licencia libre
3. **Sin imagen** — si ninguna fuente devuelve resultado válido, continuar sin imagen y notificarlo

> Hugging Face (generación IA) se ha descartado como fuente para mantener consistencia visual con imágenes reales de los juegos.

---

## Paso 1 — RAWG API

Lee `RAWG_API_KEY` del archivo `.env` antes de construir la URL.

```
GET https://api.rawg.io/api/games?search={NOMBRE_DEL_JUEGO}&key={RAWG_API_KEY}
```

Extrae la imagen de `results[0].background_image`:

```json
{
  "results": [{
    "name": "Chrono Trigger",
    "background_image": "https://media.rawg.io/media/games/8d6/8d69f3598aff2f2db6f5f2d3c6d5a5a5.jpg"
  }]
}
```

Criterios de selección:
- Usar `background_image` del primer resultado
- Tamaño mínimo aceptable: 400px en el lado más corto
- Si `background_image` es `null` o la respuesta está vacía, pasar al Paso 2

---

## Paso 2 — Wikimedia Commons (fallback)

```
GET https://en.wikipedia.org/w/api.php?action=query&titles={NOMBRE_DEL_JUEGO}&prop=pageimages&format=json&pithumbsize=800
```

Extrae la URL de `query.pages[ID].thumbnail.source`.

Criterios:
- Verificar que la imagen tiene licencia Creative Commons
- Si no hay resultado válido, pasar al Paso 3

---

## Paso 3 — Sin imagen disponible

Si ninguna fuente devuelve imagen válida:
- No bloquear el flujo de publicación
- Notificar: `⚠️ IMAGEN PENDIENTE: no se encontró imagen de portada para [NOMBRE_DEL_JUEGO]`
- Devolver `null` para que `publish-wordpress` continúe sin `featured_media`