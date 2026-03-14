# Plan Global

Plan para tu Blog de Juegos con IA 🎮

## Fase 1 — Montar el Blog en WordPress
Lo primero es tener la casa lista. Necesitarás:
- [x] Hosting + Sub Dominio: games.optimbyte.com.
- [x] WordPress instalado y configurado.
- [x] usuario administrador y su clave de API lista.

## Fase 2 — Diseñar el Agente con Antigravity (Rules + Skills)

Esta es la parte más interesante. El agente tendrá básicamente dos responsabilidades: generar contenido y publicarlo.
En cuanto a las Rules, definirán la personalidad y el estilo del agente: qué tipo de posts genera, en qué tono escribe (nostálgico, informativo, entusiasta), qué estructura sigue un post (intro, historia del juego, gameplay, por qué es un clásico, conclusión), y qué restricciones tiene.
En cuanto a las Skills, serán las capacidades concretas del agente. Por ahora necesitarías al menos dos: una skill de generación de contenido (que dada una temática o un juego, produzca el post completo) y una skill de publicación en WordPress (que tome ese contenido y lo suba vía API REST).

- [x] Rules base
- [x] skill de generación de contenido
- [x] skill de publicación en WordPress
- [x] workflow crear-post
- [] prueba y depuracion de workflow

## Fase 3 — Expansión a Redes Sociales

Una vez que el flujo WordPress funcione bien, añadirás nuevas skills para cada red. Cada una tendrá sus propias reglas de adaptación del contenido, porque un post de blog de 800 palabras se convierte en un hilo de Twitter/X, un caption corto para Instagram y una publicación más elaborada para Facebook. El agente ya tendrá el contenido base generado, solo necesitará reformatearlo.

