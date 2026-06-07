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

## ✅ Fase 5 — Estructura y UX de la web *(paralelo a Fase 4)*

**Impacto:** Mejor experiencia = más tiempo en página = mejor señal para Google.

- [x] Home con destacados por categoría (últimas reviews, últimas curiosidades, última lista). Home con diseño de "revista" (lo veremos luego).
- [x] Aspecto archive + individual post
- [x] Página "Sobre el blog" (necesaria para E-E-A-T y confianza del usuario)
- [x] Configurar el Buscador y los Breadcrumbs.
- [x] diseño paginas de busqueda
- [x] buscador en 404
- [x] Footer
- [x] Buscador interno visible en header o sidebar
- [x] Widget de posts relacionados al final de cada entrada
- [x] Breadcrumbs activados (Rank Math los genera automáticamente)
- [x] Página de Contacto: Fundamental. Usa un formulario sencillo (tipo WPForms o Contact Form 7) para evitar spam.
- [x] Página de "Archivo" o "Mapa del Sitio": Una página donde el usuario pueda ver todos tus posts organizados por mes o por consola/género. A los retro-gamers les encanta navegar por catálogos.
- [x] Aviso Legal y Privacidad: Si piensas monetizar o usar Analytics, son obligatorias por ley.
- [x] Habilitar Comentarios: ¡Sí! Pero con moderación. Instala Akismet o usa un sistema como Cusdis (más ligero) para evitar que los bots llenen tu base de datos de basura.
- [x] Fichas Técnicas: Un bloque visual al principio de cada post con: Desarrolladora, Año de lanzamiento, Sistema y Género.
- [x] Mejora Footer
- [x] Responsive review



## 🔴 Fase 5.5 — Automatización SEO y Enriquecimiento de Datos

Esta fase es el puente entre el contenido bruto y la autoridad en Google.

- [] cumplir https://isitagentready.com/
- [x] Mapeo de Custom Fields para VideoGame: Configurar el agente (OpenCode) para que envíe los datos técnicos (name, system, developer, genre) a los campos específicos del plugin Schema & Structured Data. Así el "verde" de Google será automático.
- [ ] Inyección de Metadatos Rank Math: El agente debe generar y enviar un focus_keyword coherente, un seo_title (máx. 60 caracteres) y una meta_description (máx. 160 caracteres) que invite al clic.
- [x] Lógica de Enlazado Interno (Internal Linking): - Implementar una búsqueda por etiquetas o categorías en la "memoria" del agente.
- Regla: "Cada nuevo post debe enlazar al menos a otros 2 posts antiguos de temática similar". Mejorar lo que ya tenemos. Y añadir a los posts que no tienen.
- [ ] Limpieza de "Slugs" (URLs): Asegurar que el agente genere URLs limpias (ej: optimpixel.com/historia-resident-evil/ en lugar de la URL por defecto larga o con fechas).
- [ ] Consistencia de Marca (E-E-A-T): Configurar al agente para que siempre use el mismo nombre de "Autor" y "Organización" (Optim Pixel) para que Google asocie el contenido con una entidad experta.
- [ ] Optimización de Imágenes (Alt Text): El agente debe generar automáticamente el atributo alt de las imágenes usando la Keyword principal para mejorar el SEO de Google Imágenes.
- [ ] Schema enriquecido para Listas

---

## ✅ Fase 6 — Screenshots en posts *(agente — alta prioridad)*

**Impacto:** Reduce bounce rate, aumenta tiempo en página, Google indexa las imágenes.
**Por qué antes que la memoria:** Beneficio visible para usuarios y bots; la memoria aguanta hasta ~150 posts.

- [x] Diseñar skill `/add-screenshots` para el agente
  - Busca 2-3 screenshots del juego (fuente: MobyGames, Internet Archive, RAWG)
  - Los descarga y sube a la biblioteca de medios de WordPress
  - Los intercala en el contenido del post en posiciones naturales (después del primer párrafo, a mitad del análisis de gameplay, antes de la conclusión)
- [x] Añadir atributos `alt` descriptivos con el nombre del juego y la sistema
- [x] Probar el workflow en un post existente antes de activarlo por defecto

---

## 🔵 Fase 7 — Distribución (meses 2-4)
El contenido existe, pero nadie lo encuentra si no hay canales. Esta fase no se puede delegar al agente: requiere tu presencia, consistencia y criterio humano. Es el cuello de botella real del proyecto.
Impacto: Sin distribución activa, dependes 100% de Google, que tarda 6-12 meses en confiar en un dominio nuevo. La distribución te da tráfico en semanas.
Regla de oro de esta fase: Elige 2 canales máximo y hazlos bien. Es mejor tener presencia real en Reddit + TikTok que presencia fantasma en 5 sitios a la vez.

7.1 — Reddit (semana 1-2: preparación, semana 3+: publicación)
Reddit es el canal con mayor retorno inmediato para retrogaming, pero tiene sus normas no escritas. Si las ignoras te banean.
Protocolo de entrada (obligatorio antes de postear nada tuyo):

Crea la cuenta con un nombre neutro, no pongas "OptimPixel" en el username, parece spam desde el día 1
Durante las primeras 2 semanas solo comenta: responde preguntas, aporta datos, opina sobre posts de otros
Karma mínimo recomendable antes de postear links: 50-100 puntos

Comunidades prioritarias (en orden):
SubredditIdiomaEstrategiar/retrogamingInglésPosts visuales con imagen + pregunta. Nunca solo el linkr/SNES / r/SegaGenesis / r/AtariInglésNicho específico, muy receptivos a datos curiososr/patientgamersInglésLes encanta el análisis profundor/es_gamersEspañolMenos tráfico pero audiencia tuya directar/videojuegosEspañolMás generalista, funciona para listas y curiosidadesr/psx / r/n64 / r/GameboyInglésUno por consola según el post
Formatos que funcionan en Reddit:

"¿Sabíais que [dato curioso del juego]?" con imagen del juego + link al post completo al final
"Escribí sobre la historia de X juego, me sorprendió descubrir que..." (personal, no comercial)
Nunca: "Nuevo post en mi blog sobre X". Eso es spam aunque no lo parezca.

Lo que NO hacer:

No postear el mismo día en 5 subreddits distintos el mismo link (shadowban automático)
No ignorar los comentarios que recibas. Responde siempre.
No usar el agente para escribir los comentarios. Se nota y destruye la confianza.


7.2 — TikTok (el canal con mayor potencial de crecimiento rápido)
El algoritmo de TikTok es el único que puede llevar un vídeo de una cuenta nueva a 50.000 visualizaciones en 48 horas. Para retrogaming funciona muy bien porque el contenido es visual y nostálgico, dos factores que disparan el engagement.
Formato recomendado: 45-90 segundos
Estructura de cada vídeo:

Gancho (primeros 3 segundos): Una pregunta o dato que genere curiosidad. Ejemplo: "Este juego de SNES fue prohibido en 3 países. ¿Sabes cuál es?"
Desarrollo (30-60 seg): 3-4 datos del post, con gameplay de fondo o imágenes del juego
CTA final (5 seg): "El análisis completo en el blog, link en bio"

Fuente de vídeo (sin grabar cámara):

Gameplay capturado con emulador + voz en off (puedes usar ElevenLabs para voz si no quieres grabar tú)
Imágenes estáticas del juego con texto animado (CapCut lo hace automático)
El agente genera el guion con /generate-social-content, tú solo montas el vídeo

Cadencia mínima viable: 3 vídeos por semana. Por debajo de eso el algoritmo no te distribuye.
Hashtags base: #retrogaming #videojuegosretro #snes #megadrive #nostalgia #gamer

7.3 — Facebook Groups (canal lento pero de audiencia hispana fiel)
Menos sexy que TikTok pero el público hispano de retrogaming vive en Facebook, especialmente el segmento 30-45 años que es tu audiencia natural.
Grupos a buscar y unirte:

"Retrogaming España"
"Coleccionistas de videojuegos retro España"
"SNES / Megadrive / PlayStation 1 España"
Grupos por consola específica

Protocolo: Igual que Reddit. Presenta antes de vender. Comenta durante 1-2 semanas, luego comparte posts de forma natural cuando sean relevantes para una conversación activa.

7.4 — Newsletter (actívala antes de lo que tienes planeado)
⚠️ Este punto no estaba en tu Fase 7 original y debería estarlo. La newsletter es el único canal de distribución que no depende de ningún algoritmo externo. Reddit puede banearte, TikTok puede cambiar su algoritmo, Google puede penalizarte. Tu lista de emails es tuya para siempre.
Cuándo empezar: Ahora mismo, no en Fase 10.
Herramienta recomendada: Beehiiv (gratis hasta 2.500 suscriptores, mejor que Mailchimp para blogs de contenido)
Qué enviar: Un email semanal con el mejor post de la semana + 1 curiosidad retro que no esté en el blog. Ese contenido exclusivo es lo que hace que la gente no se dé de baja.
Cómo captar suscriptores: Popup en el blog con oferta concreta ("Recibe cada semana la historia de un juego clásico que no conocías"), no un genérico "suscríbete a mi newsletter".
Objetivo a 6 meses: 500 suscriptores activos. Con eso tienes una audiencia real independiente de Google.

7.5 — Comando /generate-social-content para el agente
El agente debe generar, a partir de cualquier post existente, el siguiente paquete:
INPUT: URL o título del post
OUTPUT:
  - Gancho TikTok (primeros 3 segundos, máx. 15 palabras, formato pregunta o dato impactante)
  - Guion TikTok completo (45-60 seg, estructura gancho > desarrollo > CTA)
  - Texto Reddit (150-200 palabras, tono personal, sin parecer spam, incluye pregunta al final para generar comentarios)
  - Texto Facebook (100 palabras, más informal, incluye emoji y pregunta de nostalgia)
  - Asunto newsletter (máx. 50 caracteres, que genere curiosidad)
  - Fragmento newsletter (200 palabras resumiendo el post con gancho para leer más)

Checklist actualizado Fase 7

 - [ ] Crear cuenta Reddit con nombre neutro
 - [ ] 2 semanas de calentamiento en subreddits objetivo (solo comentarios, sin links propios)
 - [ ] Publicar primer post en Reddit con formato no-spam
 - [ ] Unirse a 5 grupos de Facebook de retrogaming en español
 - [ ] Implementar /generate-social-content en el agente
 - [ ] Crear cuenta TikTok de OptimPixel
 - [ ] Publicar primeros 3 vídeos TikTok con gameplay + voz en off
 - [ ] Instalar plugin de newsletter (Beehiiv) en WordPress
 - [ ] Crear popup de captación con oferta concreta (no genérica)
 - [ ] Enviar primer número de la newsletter
 - [ ] Unirse a grupos de Facebook de retrogaming en español
 - [ ] Cadencia semanal: 1 post Reddit + 3 TikToks + 1 newsletter

---

Dónde ponerla
Va como Fase 7.5, entre la distribución inicial y la memoria del agente. La lógica es esta: empieza TikTok en la Fase 7, validas en 6-8 semanas qué funciona, y con esa información arrancas el canal de YouTube con criterio. No antes.
Aquí tienes la fase completa para añadir al planning:

## 🔵 Fase 7.5 — Canal de YouTube + Sección Gameplays en el Blog (meses 3-6)
Prerequisito: Haber completado al menos 6 semanas de actividad en TikTok (Fase 7) y tener datos reales de qué juegos y formatos generan más engagement. No arrancar esto en paralelo desde el día 1.
Lógica del canal: Cada gameplay es una pieza de contenido que vive en tres sitios a la vez: YouTube (posicionamiento en el segundo buscador del mundo), el blog (artículo asociado que posiciona en Google), y TikTok (clip corto que drena tráfico hacia los otros dos). Un solo juego, triple superficie de indexación.
Impacto: El contenido de retrogaming en YouTube no caduca. Un gameplay de un clásico de SNES publicado hoy seguirá recibiendo visitas en 3 años, a diferencia de TikTok donde la vida útil de un vídeo son 48-72 horas.

7.5.1 — Preparación legal y técnica (semana 1-2)
Antes de grabar nada hay que resolver dos cosas que mucha gente ignora y luego paga caro.
Content ID y derechos:
No todos los juegos retro son iguales en YouTube. Revisa antes de grabar:
PublisherPolítica habitualRiesgoNintendoMuy agresiva. Pueden reclamar ingresos o tumbar el vídeo🔴 AltoSegaPermisiva con gameplay🟢 BajoKonamiVariable según juego🟡 MedioCapcomGeneralmente permisiva🟢 BajoAtari (actual)Permisiva🟢 BajoSony (PS1 era)Variable🟡 Medio
Regla práctica: empieza con juegos de publishers permisivas. Deja los juegos de Nintendo para cuando tengas suficiente autoridad de canal y hayas investigado caso por caso.
Setup técnico mínimo viable:

Emulador con función de grabación integrada (RetroArch graba directamente en alta calidad)
OBS Studio para captura si usas hardware real (gratuito)
Editor de vídeo: DaVinci Resolve (gratuito, más que suficiente para este formato)
Micrófono decente: no hace falta gastarse 200€, un HyperX SoloCast (~50€) es suficiente para empezar
Si no quieres salir en cámara ni poner tu voz: ElevenLabs genera voz en off de calidad por ~5€/mes


7.5.2 — Formato y estructura de los vídeos
Duración objetivo: 8-15 minutos. Es el rango óptimo para retención y para que YouTube lo considere contenido sustancial. Por debajo de 8 minutos pierdes opciones de monetización futura. Por encima de 20 minutos la retención cae mucho si no eres un canal ya establecido.
Estructura de cada vídeo:
00:00 - 00:30  →  Gancho: dato curioso o momento impactante del juego
00:30 - 02:00  →  Contexto: quién hizo el juego, año, plataforma, por qué importa
02:00 - 08:00  →  Gameplay comentado: no es un walkthrough silencioso,
                   comentas decisiones de diseño, curiosidades, comparativas
08:00 - 11:00  →  Análisis: qué hizo bien, qué envejeció mal, legado
11:00 - 12:00  →  CTA: suscripción + link al artículo completo en el blog
Tono: El mismo que el blog. Nostálgico pero informado. No es un speedrun ni un tutorial. Es un análisis jugado.

7.5.3 — Sección Gameplays en el Blog
Cada vídeo de YouTube genera automáticamente una entrada en el blog. Esta es la parte donde el agente puede ayudarte más.
Estructura del artículo asociado:

Ficha técnica del juego (ya la tienes configurada del Fase 5)
Vídeo de YouTube embebido en posición destacada (arriba del fold)
Transcripción editada del análisis del vídeo (no literal, redactada)
Sección "Lo que no cupo en el vídeo": 2-3 datos extra exclusivos del blog para incentivar la lectura
Internal links a otros posts relacionados (el agente ya sabe hacer esto)
CTA a la newsletter al final

Por qué la transcripción editada y no el artículo del agente: Google indexa el texto del artículo independientemente del vídeo. Si el artículo es solo "aquí tienes el vídeo", no posiciona. Si el artículo tiene 800-1000 palabras de análisis real, posiciona en Google Y en YouTube Search al mismo tiempo por el mismo juego.
Comando nuevo para el agente:
INPUT: Título del juego + plataforma + puntos clave del análisis (5-6 bullets)
OUTPUT:
  - Artículo completo de 900 palabras con estructura definida
  - Título SEO optimizado (máx. 60 caracteres)
  - Meta description (máx. 160 caracteres)
  - Título YouTube optimizado (máx. 70 caracteres, con keyword al principio)
  - Descripción YouTube (300 palabras con links al blog y timestamps)
  - Tags YouTube (15 tags relevantes)
  - Gancho TikTok de 15 segundos para el clip de promoción

7.5.4 — Cadencia y producción sostenible
El error más común en YouTube es arrancar con 3 vídeos por semana y quemarse en el mes 2. Para un canal secundario a un blog ya activo, la cadencia realista es:
Mínimo viable: 1 vídeo cada 2 semanas los primeros 3 meses. El algoritmo de YouTube valora la consistencia más que el volumen. Un canal que publica cada 2 semanas de forma fiable cresce más que uno que publica 5 vídeos en enero y desaparece en febrero.
Objetivo a 6 meses: 1 vídeo semanal. Cuando tengas el flujo de producción automatizado (captura → edición → artículo → subida) ese ritmo es alcanzable en 3-4 horas por semana.
Pipeline de producción recomendado:
Lunes    →  Graba el gameplay (1h)
Martes   →  Edita el vídeo (1-2h)
Miércoles → El agente genera el artículo del blog (15 min de supervisión)
Jueves   →  Sube a YouTube con descripción y tags optimizados
Viernes  →  Publica el artículo en el blog con el vídeo embebido
Sábado   →  Clip de TikTok de 60 segundos promocionando ambos

7.5.5 — Monetización específica del canal
YouTube no te va a monetizar hasta los 1.000 suscriptores y 4.000 horas de visualización (YPP). Con un canal de nicho retro en español, eso son aproximadamente 8-14 meses de trabajo consistente. Pero hay ingresos antes del YPP:
Antes del YPP:

Links de afiliación en la descripción (Amazon: consolas, cartuchos, adaptadores HDMI retro)
Link a la newsletter en cada vídeo (construyes audiencia propia independiente de YouTube)
Tráfico hacia el blog donde ya tienes ads o afiliación

Después del YPP:

AdSense (RPM gaming en español: 2-5€ por cada 1.000 visualizaciones, no es alto)
Patrocinios de tiendas de retrogaming español cuando tengas 5.000+ suscriptores


Checklist Fase 7.5

 Auditar publishers y definir lista de juegos seguros para empezar
 Montar setup técnico: emulador + OBS/RetroArch + DaVinci Resolve
 Decidir: ¿voz propia o voz generada con ElevenLabs?
 Crear canal de YouTube con branding consistente con el blog
 Configurar descripción del canal con link al blog y newsletter
 Grabar y publicar los primeros 3 vídeos piloto
 Crear sección "Gameplays" en el blog con página de archivo
 Implementar comando /generate-video-content en el agente
 Establecer pipeline semanal de producción
 Añadir links de afiliación en descripciones de YouTube desde el día 1
 Publicar clip de TikTok por cada vídeo de YouTube como promoción cruzada


Veredicto sobre esta fase: Es la extensión más natural del proyecto y la que tiene mejor ratio esfuerzo/retorno a largo plazo. El contenido de YouTube envejece bien, refuerza el SEO del blog, y abre una segunda vía de monetización. El único riesgo real es el Content ID de Nintendo, que se resuelve simplemente eligiendo bien los juegos al principio.

---



## ✅ Fase 8 — Memoria del agente — migración a DB *(meses 3-5)*

**Impacto:** Operativo. El `.md` empieza a fallar en torno a los 100-150 posts.

- [x] Evaluar opciones cuando se acerque el límite:
  - **SQLite local** — más simple, sin dependencias externas
  - **Notion API** — más visual, fácil de gestionar manualmente
  - **Supabase** — si se quiere escalar a varios agentes o blogs
- [x] Migrar los estados `pendiente / en uso / publicado` al nuevo backend
- [x] Actualizar las skills del agente para leer/escribir desde la nueva fuente

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



