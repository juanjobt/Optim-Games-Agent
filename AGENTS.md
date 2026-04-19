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
memory/           # Base de datos SQLite (blog.db) y scripts de consulta
opencode.json     # Configuración del agente y MCP
.env              # Credenciales de API (nunca commitear)
```

## Comandos

| Comando | Descripción |
|---------|-------------|
| `/create-post` | Flujo completo: investigación → redacción → datos de publicación → imagen → publicación |
| `/generate-post-ideas` | Genera 10 prompts editoriales y los guarda en memoria |

## Skills

| Skill | Cuándo usarla |
|-------|---------------|
| `generate-post-review` | Redactar una review |
| `generate-post-history` | Redactar un post de historia |
| `generate-post-list` | Redactar un post de lista |
| `find-game-image` | Localizar imagen de portada (SerpApi → RAWG) |
| `upload-wordpress-image` | Subir imagen a la biblioteca de medios de WordPress |
| `publish-wordpress` | Publicar un post via MCP (gestiona categorías y tags) |
| `set-videogame-schema` | Inyectar schema VideoGame en un post publicado |
| `link-related-posts` | Gestionar internal links entre posts |
| `search-game-candidates` | Buscar juegos candidatos para nuevas ideas |

## Herramientas WordPress MCP

Disponibles via `wordpress-mcp-remote`:

| Herramienta | Uso |
|-------------|-----|
| `wp_add_post` | Crear nuevo post |
| `wp_update_post` | Actualizar post existente |
| `wp_upload_media` | Subir imágenes a la biblioteca de medios |
| `wp_list_categories` / `wp_list_tags` | Obtener IDs de taxonomías |
| `wp_add_category` / `wp_add_tag` | Crear si no existe |

### Slugs de categorías

| Tipo de post | Slug |
|--------------|------|
| Review | `reviews` |
| Historias | `historias` |
| Listas | `listas` |

## Sistema de memoria

`memory/blog.db` (SQLite) es la fuente de verdad. Schema definido en `memory/blog.dbml`.

Las ideas se gestionan mediante `memory/scripts/db_query.py`.

| Estado | Significado |
|--------|-------------|
| `pendiente` | Generada pero sin usar |
| `en_uso` | En proceso de creación |
| `publicado` | Publicado en WordPress |