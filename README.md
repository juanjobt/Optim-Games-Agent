# Optim Pixel Agent

Agente de IA para generar y publicar contenido sobre videojuegos retro en [optimpixel.com](https://optimpixel.com). Automatiza el flujo completo: desde la búsqueda de ideas hasta la publicación en WordPress con imagen de portada y metadatos SEO.

---

## Requisitos

- [OpenCode](https://opencode.ai) instalado y configurado
- Acceso al blog WordPress con el plugin `wordpress-mcp` activo
- Archivo `.env` en la raíz del proyecto con las credenciales (ver siguiente sección)

---

## Configuración inicial

Crea un archivo `.env` en la raíz del proyecto con estos valores:

```env
RAWG_API_KEY=tu_rawg_api_key
HF_TOKEN=tu_huggingface_token
WP_BASE_URL=https://optimpixel.com
WP_USER=tu_usuario_wordpress
WP_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx
```

> **Nota sobre autenticación dual:** El agente usa dos sistemas de autenticación:
> - Para las operaciones MCP (crear posts, categorías, tags) se utilizará auth por jwt
> - `WP_USER` + `WP_APP_PASSWORD` para conectar directamente con la api de wordpress cuando se usen scripts de Python

---

## Comandos disponibles

### `/create-post`

Genera y publica un post completo. El agente se encarga de investigar, redactar, preparar el SEO, buscar la imagen de portada y publicar en WordPress.

**Uso con datos concretos:**
```
/create-post

Juego: Chrono Trigger
Tipo de post: Historias
Sistema: Super Nintendo
Enfoque: El caos creativo detrás del desarrollo — cómo un equipo de lujo con agenda imposible acabó haciendo una obra maestra casi por accidente
```

**Uso con una idea de la cola:**
```
/create-post
```
Sin datos adicionales, el agente coge automáticamente la primera idea pendiente de `memory/post-ideas.md`.

**Tipos de post disponibles:**

| Tipo | Extensión | Estructura |
|------|-----------|------------|
| Review | 1000-1500 palabras | Gancho → Ficha técnica → Sinopsis → Gameplay → Envejecimiento → Veredicto |
| Historias | 800-1200 palabras | Gancho → Contexto → Narrativa → Datos curiosos → Conclusión |
| Listas | 600-900 palabras | Intro provocadora → Ítems → Número 1 destacado → Cierre debate |

---

### `/generate-post-ideas`

Genera prompts editoriales listos para usar con `/create-post` y los guarda en `memory/post-ideas.md` con estado `pendiente`.

**Uso libre** (el agente decide con criterio editorial):
```
/generate-post-ideas
```

**Uso con filtros:**
```
/generate-post-ideas

sistema: Mega Drive
genero: Plataformas
epoca: Años 90
tipo_post: Review
cantidad: 10
enfoque_tematico: que trate sobre sonic
modo_estrategia: editorial
```
---


## Sistema de memoria

El archivo `memory/post-ideas.md` es la cola editorial del blog. Registra todas las ideas generadas y su estado.

| Estado | Significado |
|--------|-------------|
| `pendiente` | Generada, lista para usar |
| `en uso` | Siendo procesada ahora mismo |
| `publicado` | Ya publicada en WordPress |

---

## Solución de problemas frecuentes

**La imagen no se sube correctamente**
Verifica que el archivo no supere 8MB y que el formato sea jpg, png o webp. Comprueba también que:
1. `WP_USER` y `WP_APP_PASSWORD` están correctos en `.env`
2. El usuario tiene rol de administrador o editor
3. La aplicación password tiene permisos de escritura

**Error "WP_BASE_URL, WP_USER y WP_APP_PASSWORD son obligatorios"**
El script `wp_upload_image.py` no encuentra las credenciales. Verifica que el archivo `.env` existe en la raíz del proyecto y contiene las tres variables.

**RAWG devuelve error de autenticación**
El agente está usando un valor incorrecto para `RAWG_API_KEY`. Verifica que el archivo `.env` existe y contiene el valor real.

**No se encuentran las categorías en WordPress**
Las categorías `reviews`, `historias` y `listas` deben existir en WordPress. Si no existen, el agente las crea automáticamente al publicar el primer post de cada tipo.

**El agente no sigue la voz del blog**
Revisa `blog-identity.md` — es la biblia editorial del blog. Si el tono no encaja, es el primer sitio donde mirar.