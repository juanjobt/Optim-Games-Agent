

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

# Footer

Mi veredicto sobre la distribución actual:
Para que el footer no quede descompensado (mucho peso a la izquierda con el logo y descripción, y mucho a la derecha con los menús), yo lo organizaría en 4 columnas (si tu plantilla lo permite):

Columna 1: Logo + Slogan + Descripción corta.

Columna 2: Menú Principal (Navegación).

Columna 3: Suscripción (El "Insert Coin").

Columna 4: Contacto + Tu correo.

Columna 5: Microiconos de sistemas

# Tag gestion

El problema con crear un tag por cada juego:
WordPress trata los tags como taxonomías con sus propias páginas de archivo. Si tienes un tag "Chrono Trigger" pero solo un artículo lo usa, esa página de archivo existe, está casi vacía, y Google la puede ver como contenido duplicado o thin content. Eso puede perjudicarte.
Para que un tag tenga valor SEO real necesita agrupar al menos 3-5 artículos. Si escribes sobre Chrono Trigger una sola vez, el tag no aporta nada y solo genera ruido.
Lo que realmente funciona mejor para un blog retro:

Tags por saga (como ya tienes): agrupan varios juegos y varios artículos
Tags por género, sistema, desarrolladora, época: son los que la gente realmente busca navegando
Tags por juego específico solo si planeas escribir varios artículos sobre ese juego (análisis, historia, curiosidades, comparativas...)

Mi recomendación práctica:
No crees el tag del juego en el momento de publicar el artículo. Créalo solo cuando vayas a publicar el segundo artículo sobre ese mismo juego. Así nunca tendrás páginas de archivo con un solo resultado.
El SEO de un blog de nicho como el tuyo se construye mejor con autoridad temática (contenido profundo y bien enlazado internamente) que con proliferación de tags.