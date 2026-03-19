# AGENTS.md — Optim Pixel Agent

Agente de IA para crear y publicar contenido sobre videojuegos retro en optimpixel.com.

## Descripción del proyecto

Proyecto basado en OpenCode — sin sistema de build ni tests. El agente genera posts sobre videojuegos clásicos y los publica en WordPress via MCP.

## Estructura

```
.opencode/
├── agents/       # Definición del agente (content-marketer)
├── commands/     # Comandos slash (/create-post, /generate-post-ideas)
├── rules/        # Reglas siempre activas (cargadas automáticamente via opencode.json)
└── skills/       # Capacidades bajo demanda (se cargan cuando se necesitan)
memory/           # Cola de ideas y estado de publicación
opencode.json     # Configuración del agente y MCP
.env              # Credenciales de API (nunca commitear)
```

## Comandos

| Comando | Descripción |
|---------|-------------|
| `/create-post` | Flujo completo: investigación → redacción → SEO → imagen → publicación |
| `/generate-post-ideas` | Genera 10 prompts editoriales y los guarda en memoria |

## Skills

| Skill | Cuándo usarla |
|-------|---------------|
| `generate-post-review` | Redactar una review |
| `generate-post-historia` | Redactar un post de historia y curiosidades |
| `generate-post-lista` | Redactar un post de lista y ranking |
| `find-game-image` | Localizar imagen de portada (RAWG → Wikimedia) |
| `upload-wordpress-image` | Subir imagen a la biblioteca de medios de WordPress |
| `publish-wordpress` | Publicar un post via MCP |
| `search-game-candidates` | Buscar juegos candidatos para nuevas ideas |

## Herramientas WordPress MCP

Disponibles via `wordpress-mcp-remote`:

| Herramienta | Uso |
|-------------|-----|
| `wp_create_post` | Crear nuevo post |
| `wp_update_post` | Actualizar post existente |
| `wp_upload_media` | Subir imágenes a la biblioteca de medios |
| `wp_get_categories` / `wp_get_tags` | Obtener IDs de taxonomías |
| `wp_create_category` / `wp_create_tag` | Crear si no existe |

### Slugs de categorías

| Tipo de post | Slug |
|--------------|------|
| Review | `reviews` |
| Historia y curiosidades | `historia-y-curiosidades` |
| Lista o ranking | `listas-y-rankings` |

## Sistema de memoria

`memory/post-ideas.md` registra todas las ideas de posts. Las reglas completas de gestión están en la rule `post-ideas-memory`.

| Estado | Significado |
|--------|-------------|
| `pendiente` | Generada pero sin usar |
| `en uso` | En proceso de creación |
| `publicado` | Publicado en WordPress |