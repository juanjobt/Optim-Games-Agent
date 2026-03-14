# WordPress Image Upload Skill

## Descripción
Esta skill documenta el proceso completo para subir correctamente una imagen a un post de WordPress usando el MCP de WordPress disponible en opencode. Incluye todos los pasos necesarios, desde la verificación del post hasta la asignación de la imagen como imagen destacada.

## Prerrequisitos
1. **Conexión MCP de WordPress**: Configurada y funcionando en `opencode.json`
2. **Permisos de usuario**: El token debe tener permisos para subir medios y editar posts
3. **URL de imagen accesible**: La imagen debe estar disponible públicamente para descargar

## Flujo de Trabajo Paso a Paso

### Paso 1: Verificar el Post Destino
Antes de subir la imagen, verifica que el post existe y obtén su información actual.

**Herramienta a usar**: `wordpress-mcp-remote_wp_get_post`
```javascript
// Ejemplo: Obtener información del post #42
wordpress-mcp-remote_wp_get_post({
  id: 42,
  context: "edit"
})
```

**Propósito**:
- Confirmar que el post existe
- Verificar el estado actual (`featured_media`)
- Obtener información del autor y categorías

### Paso 2: Descargar la Imagen desde URL
Descarga la imagen desde la URL proporcionada al sistema de archivos local.

**Comando Bash**:
```bash
# Descargar la imagen a un archivo temporal
curl -s -o "/tmp/imagen_temporal.jpg" "https://ejemplo.com/imagen.jpg"

# Verificar que se descargó correctamente
ls -lh "/tmp/imagen_temporal.jpg"
```

**Parámetros importantes**:
- `-s`: Modo silencioso (sin output)
- `-o`: Especificar archivo de salida
- URL completa entre comillas

### Paso 3: Convertir la Imagen a Base64
WordPress MCP requiere que las imágenes se suban en formato base64.

**Comando Bash**:
```bash
# Convertir la imagen a base64 y guardar en archivo
base64 "/tmp/imagen_temporal.jpg" > "/tmp/imagen_base64.txt"

# Verificar que la conversión fue exitosa
head -c 100 "/tmp/imagen_base64.txt"
```

**Consideraciones**:
- El archivo base64 debe contener solo el contenido base64, sin encabezados
- No debe incluir `data:image/jpeg;base64,` al principio
- Debe ser una cadena base64 continua sin saltos de línea

### Paso 4: Leer el Contenido Base64
Lee el contenido base64 del archivo para pasarlo a la herramienta de WordPress.

**Herramienta a usar**: `read`
```javascript
// Leer el contenido base64 completo
read({
  filePath: "/tmp/imagen_base64.txt"
})
```

**Nota**: Guarda el contenido en una variable para usarlo en el siguiente paso.

### Paso 5: Subir la Imagen a WordPress
Usa la herramienta de WordPress para subir la imagen como medio.

**Herramienta a usar**: `wordpress-mcp-remote_wp_upload_media`

**Parámetros requeridos**:
- `file`: (string) Contenido base64 de la imagen
- `title`: (opcional) Título de la imagen
- `alt_text`: (opcional) Texto alternativo para accesibilidad
- `caption`: (opcional) Pie de foto
- `description`: (opcional) Descripción de la imagen

**Ejemplo completo**:
```javascript
wordpress-mcp-remote_wp_upload_media({
  title: "Portada de Phantasy Star IV para Sega Mega Drive",
  alt_text: "Portada de Phantasy Star IV para Sega Mega Drive",
  caption: "Portada de Phantasy Star IV para Sega Mega Drive",
  description: "Portada de Phantasy Star IV para Sega Mega Drive",
  file: "CONTENIDO_BASE64_AQUI"
})
```

**Respuesta exitosa**: Deberías recibir un objeto con `id` (ID del medio), `source_url` (URL de la imagen), y otros metadatos.

### Paso 6: Asignar la Imagen al Post como Imagen Destacada
Actualiza el post para asignar la imagen recién subida como imagen destacada.

**Herramienta a usar**: `wordpress-mcp-remote_wp_update_post`
```javascript
wordpress-mcp-remote_wp_update_post({
  id: 42, // ID del post
  featured_media: 44 // ID de la imagen subida
})
```

**Propósito**: Establece la imagen como imagen destacada del post, lo que hará que aparezca como miniatura en listas y como imagen principal.

## Ejemplo Completo

Aquí tienes un ejemplo completo que combina todos los pasos:

```javascript
// Paso 1: Verificar el post
const postInfo = await wordpress-mcp-remote_wp_get_post({
  id: 42,
  context: "edit"
});

// Paso 2: Descargar imagen (ejecutar en bash)
// curl -s -o "/tmp/imagen.jpg" "https://media.rawg.io/media/screenshots/6b6/6b6b8d9de805f0041457eb2cbc2102b2.jpg"

// Paso 3: Convertir a base64 (ejecutar en bash)
// base64 "/tmp/imagen.jpg" > "/tmp/imagen_base64.txt"

// Paso 4: Leer base64
const base64Content = await read({
  filePath: "/tmp/imagen_base64.txt"
});

// Paso 5: Subir imagen
const mediaResponse = await wordpress-mcp-remote_wp_upload_media({
  title: "Título de la imagen",
  alt_text: "Texto alternativo para accesibilidad",
  caption: "Pie de foto opcional",
  description: "Descripción de la imagen",
  file: base64Content
});

// Paso 6: Asignar al post
const updateResponse = await wordpress-mcp-remote_wp_update_post({
  id: 42,
  featured_media: mediaResponse.id
});
```

## Solución de Problemas

### Error: "Invalid input" al subir la imagen
**Causa**: Formato base64 incorrecto o parámetros faltantes.
**Solución**:
1. Verifica que el contenido base64 no tenga encabezados como `data:image/jpeg;base64,`
2. Asegúrate de que el parámetro `file` sea una cadena base64 válida
3. Verifica que todos los parámetros requeridos estén presentes

### Error: La imagen no se muestra en el post
**Causa**: El post no se actualizó correctamente o la imagen no se asignó como `featured_media`.
**Solución**:
1. Verifica que el `featured_media` en la respuesta del post sea el ID correcto
2. Revisa que la imagen se haya subido correctamente (verifica `mediaResponse.id`)
3. Limpia la caché de WordPress si es necesario

### Error: Tamaño de imagen muy pequeño
**Causa**: Algunas imágenes de APIs como RAWG pueden ser miniaturas.
**Solución**:
1. Busca una versión de mayor resolución de la imagen
2. Considera usar otras fuentes de imágenes si la calidad es importante
3. Avisa al usuario que la imagen puede ser de baja resolución

### Error: Permisos insuficientes
**Causa**: El token de autenticación no tiene permisos para subir medios.
**Solución**:
1. Verifica que el token en `opencode.json` sea válido
2. Asegúrate de que el usuario tenga rol de administrador o editor
3. Renueva el token si es necesario

## Consideraciones Importantes

### Formatos de imagen soportados
- JPEG/JPG (recomendado)
- PNG
- GIF
- WebP

### Tamaños recomendados
- **Imagen destacada**: Mínimo 1200x630 px para redes sociales
- **Imágenes en contenido**: Ancho máximo 1200 px
- **Miniaturas**: 150x150 px o 300x300 px

### Optimización de imágenes
1. **Compresión**: Usa herramientas como ImageOptim o TinyPNG antes de subir
2. **Formato**: JPEG para fotografías, PNG para gráficos con transparencia
3. **Tamaño**: Redimensiona imágenes grandes para reducir tiempo de carga

### Metadatos de imagen
- **Title**: Aparece en tooltips y atributos HTML
- **Alt Text**: Importante para accesibilidad (SEO y lectores de pantalla)
- **Caption**: Texto que aparece debajo de la imagen
- **Description**: Para uso interno, no visible públicamente

## Buenas Prácticas

1. **Nombres descriptivos**: Usa nombres de archivo descriptivos (ej: `phantasy-star-iv-portada.jpg`)
2. **Texto alternativo**: Siempre proporciona alt text descriptivo para accesibilidad
3. **Consistencia**: Mantén un estilo consistente en títulos y descripciones
4. **Backup**: Mantén copias locales de las imágenes subidas
5. **Verificación**: Siempre verifica que la imagen se muestre correctamente después de subirla

## Referencias

- [Documentación WordPress REST API](https://developer.wordpress.org/rest-api/reference/media/)
- [Guía de MCP WordPress](https://github.com/automattic/wordpress-mcp)
- [Mejores prácticas para imágenes en WordPress](https://wordpress.org/documentation/article/best-practices-for-images/)

---

*Esta skill fue creada basándose en la experiencia práctica de subir imágenes a WordPress usando el MCP de WordPress en opencode. Incluye soluciones a problemas comunes encontrados durante la implementación.*