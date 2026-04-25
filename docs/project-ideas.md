

# home mejora Estructura y UX de la web *(paralelo a Fase 4)*

¿Qué más añadir? Mis propuestas de Editor
Si queremos que Optim Pixel destaque sobre la competencia, yo añadiría estas dos secciones estratégicas:

A. "La Joya Oculta" (Sección de nicho)
Un bloque pequeño, quizás lateral o entre secciones, dedicado a un juego totalmente desconocido o infravalorado.

Por qué funciona: Demuestra que sabemos de lo que hablamos. No solo hablamos de Mario y Sonic; rescatamos juegos de la PC Engine o la WonderSwan que nadie recuerda. Genera mucha fidelidad.

B. "Manual de Supervivencia" (Guías rápidas)
Una sección de tutoriales breves: "Cómo limpiar tus cartuchos", "Los mejores adaptadores HDMI para PS1" o "Cómo configurar RetroArch".

Por qué funciona: Esto es utilidad pura. El lector retro siempre tiene problemas técnicos. Si le solucionas uno, volverá a tu web cada vez que tenga una duda.

C. "Tal día como hoy..." (Engagement dinámico)
Un pequeño widget que diga: "Un 31 de marzo de 1996 se lanzó [Juego X] en Japón".

Por qué funciona: Crea una sensación de "sitio vivo" y actualizado, además de ser contenido muy compartible en redes sociales.

# 💡 PROPUESTAS ADICIONALES CATEGORIAS
## 1. Imagen Destacada para Categorías
Recomiendo añadir una imagen destacada a cada categoría para que se muestre en/archive y结果的 de búsqueda. Ejemplos:
- **Reviews**: Una imagen con varios pads/mandos y el texto "Reviews"
- **Historias**: Una imagen tipo "making of" o documento antiguo
- **Listas**: Una imagen con un trofeo o lista numerada
## 2. Schema Markup
Para páginas de categoría, en Rank Math puedes configurar:
- **Schema Type**: CollectionPage
- **Nombre**: Título de la categoría
- **Descripción**: La meta descripción
## 3. Intro Adicional en el Contenido
WordPress permite añadir contenido encima del loop de posts. Mi recomendación es poner solo la descripción (el HTML que te he dado), que WordPress la muestra antes de los posts.
## 4. Actualizar la Categoría "Listas"
Tiene 0 posts. Primero tendrás que publicar al menos uno para que la página no aparezca vacía. ¿Quieres que genere una idea para un post de lista?

# 🕹️ GUÍA DE ESTILO: OPTIM PIXEL

Este documento define la identidad visual y editorial de **Optim Pixel**. Cualquier sección nueva (Sobre Nosotros, Categorías, Landing Pages) debe seguir estas directrices para mantener la coherencia de marca.

## 1. IDENTIDAD VISUAL (UI/UX)

### A. Tipografías (Jerarquía)
* **Títulos Principales (H1) y Logo:** `Silkscreen`
    * *Uso:* Branding, títulos de banner, nombres de secciones.
    * *Estilo:* Mayúsculas, espaciado de letras (`letter-spacing`) de 2px a 4px para elegancia.
* **Subtítulos y Slogans (H2, H3):** `VT323`
    * *Uso:* Slogans bajo el logo, descripciones cortas de categorías, citas destacadas.
    * *Estilo:* Regular. Evoca diálogos de aventuras gráficas y RPGs.
* **Cuerpo de Texto:** `Inter` o `Roboto` (Sans-serif estándar)
    * *Uso:* Artículos, párrafos largos, pies de página.
    * *Razón:* Máxima legibilidad. No usar fuentes de píxeles para lectura prolongada.

### B. Paleta de Colores
* Colores Enfasis: FF3B1F, FF6A00, FF8C1A
* Colores contraste: 1A202C, 1A202C, 1A202C, 1A202C
* Colores Base: EDF2F7, F7FAFC, FFFFFF


### C. Estética de Imágenes
* **Formato de Archivo:** `.webp` (Optimizado para carga rápida).
* **Banners Hero:** Ratio 1920x600px.
* **Composición:** Siempre dejar "espacio negativo" (oscuro) a la izquierda para superponer textos.
* **Estilo:** Pixel Art de alta densidad o capturas de juego con *Integer Scaling* (píxeles nítidos, no borrosos).

# inter linking
Problemas observados
1. find-related no excluye destinos ya enlazados
La documentación de la skill dice que el comando excluye automáticamente los posts que ya tienen enlace desde el origen. Sin embargo, Chrono Trigger (wp_id:10) apareció en los resultados con score 5 aunque ya tenía un incoming link registrado desde post 86. Tuve que verificar manualmente con get-links y excluirlo.

Habria que revisar la skill y crear el comando que use esa skill, ademas habria que ver si la skill no esta demasiado sobrecargada y hay que llevar carga al comando.


# error al relacionar los post creados en post-ideas

Parece que cuando se inserta un post al final no se termina relacionando el post-idea con ese post recien insertado

# Sugerencias de POSTS

Post 2: Milagros en 8 bits: De Sir Fred a La Abadía del Crimen
Subtítulo: Análisis técnico de una era de "arqueología tecnológica".

Corría el año 1987 y el mercado estaba dominado por máquinas legendarias: el ZX Spectrum, el Commodore 64, el Amstrad CPC y el MSX. Eran tiempos de rituales de paciencia, donde las cintas de cassette tardaban minutos interminables en cargar entre pitidos y ruidos extraños. En este entorno de tecnología precaria, Paco Menéndez logró lo imposible.

Sir Fred (1986): Un prodigio que dejó en evidencia a los estudios británicos. Paco logró exprimir el procesador Z80 para introducir físicas realistas, sistemas de inercia en el salto y animaciones con una fluidez desconocida. Fue tan innovador que la compañía británica Microgen compró los derechos para distribuirlo, un hito rarísimo para un juego español.

La Abadía del Crimen (1987): Junto al arquitecto Juan Delcán, Paco se aisló durante 14 meses. Sin motores gráficos modernos, resolvía los problemas matemáticos en papel cuadriculado antes de pasarlos al código. El resultado fue una obra con perspectiva isométrica donde el monasterio no era un dibujo plano, sino una estructura física pesada y coherente.

Paco no quería que el jugador saltara un abismo por diversión; quería que el ordenador fuera capaz de calcular por qué caía y qué sentía el mundo mientras eso ocurría.

---

Post 3: Las reglas de hierro: IA y el sistema "Obsequium"
Subtítulo: Por qué La Abadía del Crimen es el primer "mundo abierto" español.

La Abadía del Crimen no se diseñó para que nos gustara, se diseñó para ser perfecta. Paco Menéndez no hacía concesiones al jugador y estas son las mecánicas que lo demuestran:

El Monasterio como Reloj: El juego seguía estrictamente las horas canónicas (prima, tercia, sexta...). Si sonaba la campana, debías estar en misa; si era de noche, en tu celda. El tiempo era la ley.

El Sistema de Obsequium: En lugar de una barra de vida, Paco introdujo la barra de obediencia. Desobedecer al abad o llegar tarde a los rezos agotaba tu Obsequium. Si llegaba a cero, eras expulsado. Paco te obligaba a ser monje antes que detective.

Inteligencia Artificial Autónoma: En 1987, mientras otros juegos usaban patrones fijos, los monjes de la Abadía tenían rutinas propias. Comían, rezaban y dormían independientemente de lo que hiciera el jugador. El mundo estaba vivo y tú eras solo un invitado molesto.

Protección Implacable: Paco diseñó un sistema antipiratería cruel: si detectaba una copia ilegal, la paleta de colores mutaba, el audio se volvía un ruido infernal y Guillermo de Baskerville dejaba de obedecerte, vagando por los pasillos como un alma en pena.

---

Post 4: Proyecto Paloma y el silencio definitivo
Subtítulo: El visionario que vio el futuro de la IA antes que nadie.

A principios de los 90, la industria cambió. Llegaron los 16 bits, las consolas japonesas y los presupuestos millonarios. Paco Menéndez, fiel a su integridad, se alejó de los videojuegos: "Los videojuegos han dejado de ser un problema técnico para ser un negocio".

Se mudó a Sevilla para volcarse en su gran obsesión: el Proyecto Paloma (Parallel Logic Machine). Paco entendió décadas antes que el resto que el futuro de la computación no estaba en procesadores más rápidos, sino en miles de ellos trabajando a la vez. Diseñó una arquitectura capaz de albergar 65.535 procesadores en paralelo. Estaba sentando las bases de lo que hoy es la inteligencia artificial moderna y la computación distribuida.

Sin embargo, chocó con el muro del hardware. La España de los 90 no estaba dispuesta a financiar tal locura a un exprogramador de juegos. La soledad del visionario pesó más que el diseño puro. El 23 de septiembre de 1999, Sevilla presenció el último acto de un hombre que prefirió el vacío antes que ver sus sueños convertidos en polvo por una industria que ya no le entendía.

Nos dejó un legado de píxeles y una advertencia: lo que ocurre cuando el futuro llega demasiado pronto a una mente que no supo esperar.