# 🔴 Fase 5.5 — Automatización SEO y Enriquecimiento de Datos

Esta fase es el puente entre el contenido bruto y la autoridad en Google. Sin esto, tienes posts publicados pero Google no sabe exactamente qué son, de quién son, ni por qué debería posicionarlos. Cada tarea aquí tiene impacto directo y medible en rankings.
Prerequisito: Tener Rank Math instalado y el plugin Schema & Structured Data configurado (Fase 4 completada).
Criterio de éxito de esta fase: Que cada post nuevo publicado por el agente salga con el 100% de los campos SEO rellenos sin intervención manual tuya.

## 5.5.0 - Prioridad

Lo siguiente por orden de impacto real:

1. Metadatos Rank Math — es lo siguiente sí o sí
Es el que más duele tener sin hacer. Si el agente publica posts sin focus_keyword, seo_title y meta_description configurados, Google decide por su cuenta qué mostrar en los resultados. Y casi nunca elige bien.
Es también el más fácil de implementar porque es simplemente añadir tres campos más al body de la llamada API que ya tienes funcionando. No es un cambio de arquitectura, es añadir parámetros a algo que ya existe.

2. Slugs limpios — segundo porque afecta a todo lo nuevo
Si lo resuelves ahora, todos los posts que publiques a partir de hoy ya salen bien. Si lo dejas, acumulas deuda técnica que luego cuesta limpiar con redirects.
Los 60 posts existentes los puedes ir corrigiendo en lotes sin prisa. Los nuevos deben salir ya con el formato correcto.

3. Alt text de imágenes — tercero por volumen de oportunidad
Con 60 posts y las imágenes que irás añadiendo, Google Imágenes puede ser un canal de tráfico relevante para retrogaming. Los screenshots de juegos clásicos se buscan mucho. Sin alt text correcto ese tráfico no llega.
Además es otro cambio pequeño en el agente, no un desarrollo nuevo.

Lo que dejaría para el final de esta fase:
El cumplimiento de isitagentready.com y la validación contra IGDB API son mejoras de calidad importantes pero no urgentes. Cuando tengas los tres puntos anteriores funcionando y el blog esté en distribución activa, entonces tiene sentido afinar ese nivel de detalle.
Resumen ejecutivo: Rank Math primero, slugs segundo, alt text tercero. En ese orden y sin saltarse ninguno.

## 5.5.1 — Metadatos Rank Math (inyección automática del agente)
Es la tarea de mayor impacto inmediato. Sin metadatos bien configurados, Google usa lo que le parece, que casi nunca es lo óptimo.
Lo que el agente debe generar y enviar via API en cada post:
focus_keyword     → Keyword principal. Formato: "nombre del juego + plataforma"
                    Ejemplo: "Castlevania IV SNES"
                    Regla: debe aparecer en el título, en el primer párrafo y en al menos 2 subtítulos

seo_title         → Máx. 60 caracteres. Formato recomendado:
                    "[Nombre del juego] ([Año]) — Historia, Gameplay y Legado | Optim Pixel"
                    Nunca el mismo que el título del post

meta_description  → Máx. 160 caracteres. Debe:
                    - Contener la keyword principal
                    - Tener un verbo de acción ("Descubre", "Conoce", "Revive")
                    - Terminar con un gancho que invite al clic
                    Ejemplo: "Descubre la historia completa de Castlevania IV para SNES: su desarrollo, 
                    gameplay y por qué sigue siendo un referente del género. ¡Revive el clásico!"

canonical_url     → Siempre la URL limpia del post (sin parámetros, sin trailing slash variable)

og_title          → Igual que seo_title (para redes sociales)
og_description    → Igual que meta_description
og_image          → ID de la imagen destacada del post (para que al compartir en redes salga bien)
Cómo enviarlo via API REST de WordPress + Rank Math:
javascript// En la llamada de publicación del agente, añadir al body:
{
  "meta": {
    "rank_math_focus_keyword": "castlevania iv snes",
    "rank_math_title": "Castlevania IV (1991) — Historia y Legado | Optim Pixel",
    "rank_math_description": "Descubre la historia de Castlevania IV para SNES...",
    "rank_math_canonical_url": "https://optimpixel.com/castlevania-iv-snes/"
  }
}
Checklist de validación por post:

 Focus keyword aparece en H1
 Focus keyword aparece en los primeros 100 caracteres del contenido
 SEO title tiene entre 50-60 caracteres
 Meta description tiene entre 140-160 caracteres
 Meta description contiene la focus keyword
 Rank Math score objetivo: verde (>80 puntos)


## 5.5.2 — Slugs limpios (URLs definitivas)
Una URL limpia es mejor para el usuario, para Google y para compartir en redes. Es un cambio pequeño con impacto acumulativo grande.
Regla de formato para el agente:
FORMATO:  optimpixel.com/[nombre-juego]-[plataforma]/
EJEMPLOS:
  ✅  optimpixel.com/castlevania-iv-snes/
  ✅  optimpixel.com/sonic-the-hedgehog-megadrive/
  ✅  optimpixel.com/final-fantasy-vi-snes/
  ❌  optimpixel.com/2024/03/castlevania-iv-super-nintendo-analisis-completo/
  ❌  optimpixel.com/?p=347
  ❌  optimpixel.com/castlevania-iv-super-nintendo-analisis-gameplay-historia/
Reglas específicas que el agente debe aplicar:

Solo minúsculas
Guiones medios, nunca guiones bajos ni espacios
Sin artículos (el, la, los, un, una)
Sin preposiciones (de, del, en, para)
Sin caracteres especiales ni tildes
Máximo 5-6 palabras
Siempre terminar en /

Para los 60 posts existentes: Antes de cambiar slugs antiguos, instala el plugin Redirection y configura redirects 301 automáticos de la URL vieja a la nueva. Si no, pierdes el SEO acumulado. Hazlo en lotes de 10, no todos a la vez.

## 5.5.3 — Schema markup completo (VideoGame + Article)
Ya tienes el mapeo de Custom Fields hecho, pero hay campos que probablemente faltan y que Google valora para rich snippets.
Schema VideoGame — campos completos que el agente debe enviar:
json{
  "@type": "VideoGame",
  "name": "Castlevania: Super Castlevania IV",
  "alternateName": "Super Castlevania IV",
  "gamePlatform": "Super Nintendo Entertainment System",
  "operatingSystem": "SNES",
  "genre": ["Acción", "Plataformas", "Aventura"],
  "datePublished": "1991-10-31",
  "publisher": {
    "@type": "Organization",
    "name": "Konami"
  },
  "developer": {
    "@type": "Organization", 
    "name": "Konami"
  },
  "numberOfPlayers": {
    "@type": "QuantitativeValue",
    "minValue": 1,
    "maxValue": 1
  },
  "applicationCategory": "Game",
  "countriesAvailable": ["ES", "US", "JP"],
  "description": "Meta description del post aquí"
}
Schema Article — envolver el post siempre con esto:
json{
  "@type": "Article",
  "headline": "SEO title del post",
  "author": {
    "@type": "Organization",
    "name": "Optim Pixel",
    "url": "https://optimpixel.com"
  },
  "publisher": {
    "@type": "Organization",
    "name": "Optim Pixel",
    "logo": {
      "@type": "ImageObject",
      "url": "https://optimpixel.com/logo.png"
    }
  },
  "datePublished": "fecha ISO del post",
  "dateModified": "fecha ISO de última edición",
  "image": "URL de la imagen destacada",
  "mainEntityOfPage": "URL canónica del post"
}
Schema para posts de tipo Lista (cuando el post sea "Los 10 mejores juegos de..."):
json{
  "@type": "ItemList",
  "name": "Título de la lista",
  "numberOfItems": 10,
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "name": "Nombre del juego",
      "url": "URL del post individual de ese juego si existe"
    }
  ]
}
Esto último es especialmente potente porque Google puede mostrar los ítems de la lista directamente en los resultados de búsqueda.
Cómo validar: Usa la herramienta de Google Rich Results Test (search.google.com/test/rich-results) en cada post antes de darlo por bueno.

## 5.5.4 — E-E-A-T y Consistencia de Marca
E-E-A-T (Experience, Expertise, Authoritativeness, Trustworthiness) es cómo Google evalúa si tu contenido merece posicionarse. Para un blog de nicho nuevo, la consistencia de señales es lo más importante.
Configuración del agente — campos fijos en cada publicación:
author_name:         "Optim Pixel"
author_type:         "Organization"  (no Person, para evitar tener que mantener un perfil personal)
organization_name:   "Optim Pixel"
organization_url:    "https://optimpixel.com"
organization_logo:   "https://optimpixel.com/logo.png"
Señales de E-E-A-T que debes tener en el blog (fuera del agente):

Página "Sobre el blog" con: misión del blog, criterio editorial, qué tipo de fuentes se usan. No hace falta ser una persona real, puede ser la voz de "Optim Pixel como proyecto".
Página de Política de Privacidad y Aviso Legal (ya las tienes en tu checklist de Fase 5, confirma que estén publicadas)
Footer con: nombre del proyecto, año, links a páginas legales y contacto
Cada post debe tener fecha de publicación visible y, si se actualiza, fecha de modificación

Lo que el agente debe incluir al final de cada post:
Un bloque de "Fuentes y Referencias" aunque sea breve. Ejemplo:
Fuentes: MobyGames, Internet Archive, GameFAQs, documentación oficial de Konami.
Esto es una señal de E-E-A-T barata y efectiva que casi nadie hace en blogs automatizados.

## 5.5.5 — Optimización de Imágenes (Alt Text + metadatos)
Google Imágenes es un canal de tráfico infravalorado para retrogaming. La gente busca screenshots de juegos clásicos constantemente.
Formato del alt text que el agente debe generar:
FORMATO:  "[Nombre del juego] - [descripción de la escena] - [Plataforma] ([Año])"
EJEMPLOS:
  ✅  "Castlevania IV - Batalla contra el jefe final Simon Belmont - SNES (1991)"
  ✅  "Sonic the Hedgehog - Green Hill Zone primer nivel - Mega Drive (1991)"
  ❌  "imagen1.jpg"
  ❌  "screenshot"
  ❌  "Castlevania juego retro Super Nintendo clásico nostalgia gameplay"  (keyword stuffing)
Nombre del archivo de imagen (antes de subir):
FORMATO:  [nombre-juego]-[plataforma]-[descripcion-corta].jpg
EJEMPLO:  castlevania-iv-snes-boss-fight.jpg
El agente debe renombrar las imágenes antes de subirlas a la biblioteca de WordPress. Subir screenshot_001.jpg es una oportunidad de SEO perdida.
Campos adicionales al subir imagen via API:
javascript{
  "title": "Castlevania IV SNES - Boss Fight",
  "alt_text": "Castlevania IV - Batalla contra el jefe final - SNES (1991)",
  "caption": "Super Castlevania IV (1991) — Konami / SNES",
  "description": "Screenshot del combate final en Super Castlevania IV para Super Nintendo"
}

## 5.5.6 — Internal Linking mejorado
Ya tienes la lógica básica implementada. Estas son las reglas que le faltaban:
Reglas para el agente:
Regla 1: Cada post nuevo enlaza a mínimo 2 posts anteriores de temática similar
Regla 2: El texto ancla del enlace debe ser descriptivo, nunca "haz clic aquí" o "ver más"
          ✅  "tal y como analizamos en nuestra review de Castlevania III"
          ❌  "haz clic aquí para ver otro juego similar"
Regla 3: Al menos 1 enlace interno debe ir a un post de la misma consola/plataforma
Regla 4: Al menos 1 enlace interno debe ir a un post de la misma categoría temática
Regla 5: No más de 5 enlaces internos por post (más de eso parece spam)
Regla 6: Los enlaces internos deben estar en el cuerpo del texto, no solo al final
Para los 60 posts existentes sin enlaces internos:
Crea un workflow específico /update-internal-links que el agente ejecute en lotes:

Lee el post existente
Busca en la memoria posts relacionados por consola y género
Identifica 2 puntos naturales en el texto donde insertar el enlace
Actualiza el post via API

Hazlo en lotes de 10 posts por semana para no generar cambios masivos de golpe que Google pueda interpretar como manipulación.

## 5.5.7 — Cumplimiento de isitagentready.com
Esta checklist evalúa si tu contenido generado por IA cumple los estándares de calidad que los motores de búsqueda y plataformas empiezan a exigir. Los puntos habituales que fallan en blogs automatizados:
Lo que debes verificar y configurar:

Transparencia de IA: Decide si declaras o no que el contenido es asistido por IA. En el contexto actual de Google, no es obligatorio pero sí recomendable en la página "Sobre el blog". Algo como "Usamos herramientas de IA para investigar y estructurar contenido, que luego revisamos y enriquecemos editorialmente" es honesto y protege ante futuros cambios de política.
Originalidad verificable: El agente no debe copiar estructuras idénticas post tras post. Varía el orden de las secciones, el tipo de introducción, la longitud.
Contenido sin alucinaciones: Para datos técnicos (año, publisher, plataforma) el agente debe contrastar con una fuente fiable, no generar de memoria. Configura una validación contra MobyGames o IGDB API antes de publicar.


##  Checklist completo Fase 5.5
### Metadatos Rank Math:

- [] Agente genera focus_keyword en formato "juego + plataforma"
- [] Agente genera seo_title de máx. 60 caracteres distinto al título del post
- [] Agente genera meta_description de máx. 160 caracteres con verb de acción
- [] Agente envía og_title, og_description y og_image en cada publicación
- [] Verificar Rank Math score >80 en los primeros 5 posts con el nuevo sistema

### Slugs:

- [] Agente aplica regla de formato en todos los posts nuevos
- [] Auditar y limpiar slugs de los 60 posts existentes (en lotes de 10)
- [] Configurar redirects 301 para cada slug cambiado

### Schema:

- [] Schema VideoGame completo con todos los campos definidos arriba
- [] Schema Article con autor "Optim Pixel" como Organization
- [] Schema ItemList para posts de tipo lista
- [] Validar con Google Rich Results Test en 3 posts de cada tipo

### E-E-A-T:

- [] Página "Sobre el blog" publicada con criterio editorial
- [] Footer con datos de contacto y links legales
- [] Bloque de "Fuentes y Referencias" al final de cada post
- [] Fecha de publicación y modificación visible en cada post

### Imágenes:

- [] Agente renombra archivos antes de subir (formato definido)
- [] Agente rellena alt_text, title, caption y description en cada imagen
- [] Auditar imágenes de los 60 posts existentes y actualizar alt text vacíos

### Internal Linking:

- [] Reglas de ancla descriptiva configuradas en el agente
- [] Límite de 5 enlaces internos por post
- [] Workflow /update-internal-links para posts existentes
- [] Ejecutar en lotes de 10 posts/semana

### Agentready:

- [] Validar blog en isitagentready.com y anotar puntuación inicial
- [] Configurar validación de datos técnicos contra MobyGames o IGDB API
- [] Añadir nota de transparencia en página "Sobre el blog"