# Roadmap — Optim Pixel Blog 🎮

> **Regla de oro:** Dominio → SEO técnico → Screenshots → Distribución → Memoria → Backlinks → Monetización.
> Cada fase desbloquea la siguiente. No saltar pasos.

---

### ✅ Fase 1 — Blog en WordPress
- [x] Hosting + subdominio: `optimpixel.com`
- [x] WordPress instalado y configurado
- [x] Usuario administrador y clave de API lista

---

### ✅ Fase 2 — Agente con OpenCode

Esta es la parte más interesante. El agente tendrá básicamente dos responsabilidades: generar contenido y publicarlo.
En cuanto a las Rules, definirán la personalidad y el estilo del agente: qué tipo de posts genera, en qué tono escribe (nostálgico, informativo, entusiasta), qué estructura sigue un post (intro, historia del juego, gameplay, por qué es un clásico, conclusión), y qué restricciones tiene.
En cuanto a las Skills, serán las capacidades concretas del agente. Por ahora necesitarías al menos dos: una skill de generación de contenido (que dada una temática o un juego, produzca el post completo) y una skill de publicación en WordPress (que tome ese contenido y lo suba vía API REST).

- [x] Rules base (personalidad, tono, estructura de posts)
- [x] Skill de generación de contenido
- [x] Skill de publicación en WordPress
- [x] Workflow `/create-post`
- [x] Workflow `/generate-post-ideas`
- [x] Sistema de memoria en `memory/post-ideas.md`
- [x] Prueba y depuración del workflow
- [x] 20 posts publicados con imagen destacada
- [x] Diseño del blog mejorado con 3 secciones en el menú

---

## ✅ Fase 3 — Dominio propio

Lo más urgente es el dominio. Busca algo como optimgames.com, retrooptim.com, o algo más temático como pixelchronicles.com. Herramientas como Namecheap o Porkbun tienen buscadores buenos. Una vez registrado, el proceso en WordPress es: apuntar las DNS, cambiar la URL en Ajustes, instalar un plugin de redirecciones (Redirection es el más sencillo), y dar de alta el nuevo dominio en Google Search Console. Los 20 posts que tienes ya empezarán a acumular autoridad en el dominio correcto.

**Impacto:** Todo el SEO acumulado pasa a beneficiar un activo tuyo, independiente y vendible.

- [x] Elegir y registrar dominio temático (corto, sin guiones, sin subdominio). Será optimpixel.com
- [x] Apuntar DNS al hosting actual
- [x] Migrar WordPress al nuevo dominio (Ajustes → General → URL)
- [x] Dar de alta el nuevo dominio en Google Search Console
- [x] Configurar Google Analytics 4 en el nuevo dominio
- [x] Enviar sitemap actualizado desde Search Console
- [x] en google search console: Ve a Configuración → Asociaciones y asegúrate de que apunta a https://optimpixel.com.

---

## ✅ Fase 4 — SEO técnico base *(semanas 1-4 tras migración)*

Con el agente generando posts a buen ritmo, el siguiente cuello de botella es el SEO técnico. Prioridades concretas: instalar Rank Math o Yoast para controlar metadatos, añadir schema markup de tipo VideoGame y Article en los posts (esto da rich snippets en Google), asegurarte de que el tiempo de carga está por debajo de 2.5s (usa PageSpeed Insights), y crear una red de internal links entre posts relacionados. Este último punto es especialmente potente con tu volumen de contenido.

**Impacto:** Sin esto, el contenido existe pero Google no lo prioriza.

- [x] Instalar Rank Math o Yoast SEO
- [x] Configurar schema markup de tipo `VideoGame` y `Article` en cada post
- [x] Auditar velocidad con PageSpeed Insights y llegar a <2.5s
- [x] Revisar y limpiar estructura de URLs (sin fechas, sin IDs)
- [x] Crear red de internal links entre posts relacionados
- [x] Definir categorías definitivas y asegurarse de que cada post está bien clasificado
- [x] Crear y optimizar las páginas de categoría (descripción, H1, intro de texto)

---

## 🔴 Fase 5 — Estructura y UX de la web *(paralelo a Fase 4)*

**Impacto:** Mejor experiencia = más tiempo en página = mejor señal para Google.

- [ ] Home con destacados por categoría (últimas reviews, últimas curiosidades, última lista). Home con diseño de "revista" (lo veremos luego).
- [x] Página "Sobre el blog" (necesaria para E-E-A-T y confianza del usuario)
- [ ] Configurar el Buscador y los Breadcrumbs.
- [x] Footer
- [x] Buscador interno visible en header o sidebar
- [x] Widget de posts relacionados al final de cada entrada
- [ ] Breadcrumbs activados (Rank Math los genera automáticamente)
- [ ] Página de Contacto: Fundamental. Usa un formulario sencillo (tipo WPForms o Contact Form 7) para evitar spam.
- [ ] Página de "Archivo" o "Mapa del Sitio": Una página donde el usuario pueda ver todos tus posts organizados por mes o por consola/género. A los retro-gamers les encanta navegar por catálogos.
- [ ] Aviso Legal y Privacidad: Si piensas monetizar o usar Analytics, son obligatorias por ley.
- [ ] Habilitar Comentarios: ¡Sí! Pero con moderación. Instala Akismet o usa un sistema como Cusdis (más ligero) para evitar que los bots llenen tu base de datos de basura.
- [ ] Sistema de Valoración (Estrellas): Deja que los usuarios voten los juegos de los que hablas. Esto genera "Rich Snippets" (estrellas en los resultados de Google) y atrae más clics.
- [ ] Modo Oscuro (Dark Mode): En el mundo gaming es casi un estándar. Un interruptor "Luna/Sol" en el menú mejora mucho la UX.
- [ ] Barra de Lectura: Una línea fina que avanza según haces scroll. Ayuda a retener al usuario en posts largos.
- [ ] Fichas Técnicas: Un bloque visual al principio de cada post con: Desarrolladora, Año de lanzamiento, Plataforma y Género.
- [ ] Mejora Footer
- [ ] Aviso Legal



## 🔴 Fase 5.5 — Automatización SEO y Enriquecimiento de Datos

Esta fase es el puente entre el contenido bruto y la autoridad en Google.

- [x] Mapeo de Custom Fields para VideoGame: Configurar el agente (OpenCode) para que envíe los datos técnicos (name, platform, developer, genre) a los campos específicos del plugin Schema & Structured Data. Así el "verde" de Google será automático.
- [ ] Inyección de Metadatos Rank Math: El agente debe generar y enviar un focus_keyword coherente, un seo_title (máx. 60 caracteres) y una meta_description (máx. 160 caracteres) que invite al clic.
- [ ] Lógica de Enlazado Interno (Internal Linking): - Implementar una búsqueda por etiquetas o categorías en la "memoria" del agente.
- Regla: "Cada nuevo post debe enlazar al menos a otros 2 posts antiguos de temática similar". Mejorar lo que ya tenemos. Y añadir a los posts que no tienen.
- [ ] Limpieza de "Slugs" (URLs): Asegurar que el agente genere URLs limpias (ej: optimpixel.com/historia-resident-evil/ en lugar de la URL por defecto larga o con fechas).
- [ ] Consistencia de Marca (E-E-A-T): Configurar al agente para que siempre use el mismo nombre de "Autor" y "Organización" (Optim Pixel) para que Google asocie el contenido con una entidad experta.
- [ ] Optimización de Imágenes (Alt Text): El agente debe generar automáticamente el atributo alt de las imágenes usando la Keyword principal para mejorar el SEO de Google Imágenes.



---

## 🟣 Fase 6 — Screenshots en posts *(agente — alta prioridad)*

**Impacto:** Reduce bounce rate, aumenta tiempo en página, Google indexa las imágenes.
**Por qué antes que la memoria:** Beneficio visible para usuarios y bots; la memoria aguanta hasta ~150 posts.

- [ ] Diseñar skill `/add-screenshots` para el agente
  - Busca 2-3 screenshots del juego (fuente: MobyGames, Internet Archive, RAWG)
  - Los descarga y sube a la biblioteca de medios de WordPress
  - Los intercala en el contenido del post en posiciones naturales (después del primer párrafo, a mitad del análisis de gameplay, antes de la conclusión)
- [ ] Añadir atributos `alt` descriptivos con el nombre del juego y la plataforma
- [ ] Probar el workflow en un post existente antes de activarlo por defecto

---

## 🔵 Fase 7 — Distribución *(meses 2-4)*

El contenido existe, pero nadie lo encuentra si no hay canales. Las apuestas más rentables para un blog de retrogaming son Reddit (r/retrogaming, r/SNES, r/SegaGenesis tienen millones de suscriptores), grupos de Facebook de retrogaming en español, y TikTok/Instagram Reels con clips cortos de curiosidades que dirijan al post completo. Aquí el agente puede ayudarte generando guiones o resúmenes para redes, aunque la publicación y la comunidad requieren tu presencia.

**Impacto:** El contenido ya existe; toca que la gente lo encuentre fuera de Google.
**Nota:** Esta fase no se puede delegar al agente. Requiere presencia y consistencia tuya.

- [ ] Crear cuenta en Reddit y publicar en comunidades relevantes:
  - r/retrogaming, r/SNES, r/SegaGenesis, r/patientgamers
  - Comunidades en español: r/es_gamers, r/videojuegos
- [ ] Grupos de Facebook de retrogaming en español
- [ ] Instagram o TikTok con clips cortos de curiosidades (el agente puede generar los guiones)
- [ ] Añadir comando al agente: `/generate-social-content` — genera resumen, gancho para redes y guion de vídeo corto a partir de un post existente

---

## 🟣 Fase 8 — Memoria del agente — migración a DB *(meses 3-5)*

**Impacto:** Operativo. El `.md` empieza a fallar en torno a los 100-150 posts.

- [ ] Evaluar opciones cuando se acerque el límite:
  - **SQLite local** — más simple, sin dependencias externas
  - **Notion API** — más visual, fácil de gestionar manualmente
  - **Supabase** — si se quiere escalar a varios agentes o blogs
- [ ] Migrar los estados `pendiente / en uso / publicado` al nuevo backend
- [ ] Actualizar las skills del agente para leer/escribir desde la nueva fuente

---

## 🔵 Fase 9 — Autoridad y backlinks *(meses 5-10)*

Los backlinks siguen siendo el factor de ranking más importante. Estrategias concretas para tu nicho: contactar a wikis de gaming (Giant Bomb, The Cutting Room Floor) cuando tengas información relevante, escribir como guest en blogs de coleccionismo retro, y aparecer en podcasts de gaming español. Cada enlace externo que apunte a tu dominio vale mucho más que 10 posts nuevos.

**Impacto:** El factor de ranking más difícil de conseguir y el más valioso.
**Nota:** No se puede automatizar. Requiere tiempo y relaciones.

- [ ] Identificar blogs de retrogaming y coleccionismo en español susceptibles de guest post
- [ ] Contactar wikis de gaming (The Cutting Room Floor, Giant Bomb) cuando tengas datos únicos
- [ ] Aparecer en podcasts de gaming en español como invitado
- [ ] Registrar el blog en directorios de blogs de videojuegos
- [ ] Crear al menos una pieza de contenido "linkable asset" por trimestre (ranking definitivo, guía histórica, comparativa exhaustiva)

---

## 🟡 Fase 10 — Monetización *(cuando llegues a 5k+ visitas/mes)*

El programa de afiliados de Amazon (juegos físicos, consolas retro, accesorios) encaja perfectamente con tu audiencia. No es intrusivo y tiene sentido contextual. Más adelante, Mediavine o Ezoic para display ads. El umbral de Mediavine son 50k sesiones/mes, que con un agente de contenido activo es alcanzable en 12-18 meses si la distribución funciona.

**Impacto:** El volumen de contenido llega solo con el agente activo. Solo falta el tráfico.

- [ ] Programa de afiliados de Amazon (juegos físicos, consolas, accesorios retro)
  - Añadir enlaces en los posts existentes de reviews
- [ ] Display ads con Ezoic (umbral: 10k visitas/mes) o Mediavine (50k sesiones/mes)
- [ ] Posts patrocinados cuando la audiencia esté consolidada
- [ ] Evaluar productos propios: guías en PDF, newsletter de pago, merchandising

---

## 📊 Métricas a seguir desde el día 1

| Métrica | Herramienta | Objetivo inicial |
|---|---|---|
| Tráfico orgánico | Google Analytics 4 | Crecimiento mensual sostenido |
| Impresiones y clics | Google Search Console | Detectar qué posts rankean |
| Backlinks | Ahrefs Free / Ubersuggest | Al menos 1 dominio nuevo/mes |
| Tiempo en página | GA4 | >2 minutos por post |
| Bounce rate | GA4 | <70% |

---

*Última actualización del roadmap: marzo 2026*



