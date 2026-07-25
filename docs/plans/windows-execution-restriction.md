# Plan: Restricción de ejecución del agente a Linux/WSL

> **Estado:** aprobado · **Fecha:** 2026-07-24
> Originado por la investigación del post 1037 (Terranigma) con `post_content` vacío.

---

## 1. Problema y evidencia

Ejecuciones recientes del comando `/create-post` bajo **Windows PowerShell 5.1** producen posts en WordPress con el campo `post_content` **vacío (0 bytes)**, mientras que título, excerpt, tags, categoría e imagen destacada se asignan correctamente.

**Síntoma observable:**

- Post creado con status `publish`, ID válido, URL válida.
- `post_content` = `""` (0 bytes) en **todas las revisiones** del post.
- Excerpt llega con acentos corruptos: `acción` → `acci�n` (UTF-8 mal decodificado como cp1252/latin1).
- Tags, categoría, featured_media y título llegan correctos.

**Evidencia recogida:**

- Query `GET /wp-json/wp/v2/posts/1037?context=edit` → `content.raw.Length = 0`, `content.rendered.Length = 0`.
- Revisions 1041 y 1039 del post 1037 → ambas con `content_len = 0` (el contenido nunca se almacenó, no se vació después).
- Lista de posts recientes (`per_page=15`): los dos últimos (1037 y 1030) tienen `content_len = 0`; todos los anteriores (desde 1025 Jet Set Radio, con 5566 bytes) están correctos.

---

## 2. Posts afectados

| Post ID | Slug | Estado del contenido | Causa |
|---------|------|----------------------|------|
| **1037** | `review-terranigma-snes` | Vacío (0 bytes) | Creado hoy bajo Windows PowerShell |
| **1030** | `historia-super-mario-rpg-square` | Vacío (0 bytes) | Creado en ejecución anterior bajo Windows PowerShell |

Ambos requieren **reinyección del contenido** desde WSL/Linux una vez solucionado el mecanismo de publicación.

---

## 3. Causa raíz: PowerShell 5.1 vs WSL/Linux

**Factor discriminante:** las ejecuciones anteriores funcionaban porque se hacían bajo WSL/Linux; las fallidas ocurrieron al pasar a Windows PowerShell 5.1.

**Cadena de problemas en Windows PowerShell 5.1:**

1. **Bypass de la capa MCP.** `opencode.json` configura el MCP `wordpress-mcp-remote` (token JWT) que expone `wp_add_post`. En WSL/Linux el agente usaba esa herramienta MCP — el servidor MCP serializa el cuerpo JSON en UTF-8 limpio. En Windows, el agente hizo llamadas HTTP directas con `Invoke-RestMethod` contra `wp-json/wp/v2/posts` con Basic Auth. **Esa es la diferencia clave.**
2. **`ConvertTo-Json` de PS 5.1 escapa `<`/`>` como `\u003c`/`\u003e`** (JSON válido pero inusual), dejando los acentos non-ASCII sin escapar. El cuerpo resultante mezcla escapes ASCII con bytes UTF-8 brutos.
3. **`Invoke-RestMethod -Body $byteArray` es poco fiable en PS 5.1** con `Content-Type: application/json` — bug documentado que provoca truncado/mangle de cuerpos largos con mezcla de escapes + non-ASCII. El campo `content` (el más largo, lleno de HTML `<`/`>` escapados y acentos) es la víctima: llega vacío. Campos cortos ASCII (title, slug) y el excerpt (corto, sin HTML) sobreviven — el excerpt queda con acentos corruptos.
4. **Consola Windows cp1252.** Los acentos se corrompen ya en stdout (`acción` se muestra `acci�n`), demostrando la capa de encoding defectuosa que se propaga al body HTTP.

**Confirmaciones de descarte:**

- Localmente, el pipeline `Get-Content -Raw → hashtable → ConvertTo-Json → UTF8.GetBytes` **preserva el `content` correctamente** en tests de 491, 4911 y 5985 caracteres. El problema está en el envío HTTP real, no en la serialización local.
- `Get-Content -Raw -Encoding UTF8` lee correctamente archivos creados por la tool `write` (verificado con el fichero de logs de 5193 bytes).

---

## 4. Decisión: agente multiplataforma bloqueado en Windows

El agente `content-marketer`, las skills de publicación (`publish-wordpress`, `upload-wordpress-image`, `set-videogame-schema`, `find-game-image`) y el comando `/create-post` **solo deben ejecutarse bajo Linux/WSL**. En Windows PowerShell no se garantiza la integridad del `post_content`.

---

## 5. Cambios a realizar

### 5.1 — En `AGENTS.md` (regla siempre activa)

Añadir sección **"Requisito de entorno"** indicando:

- El agente debe ejecutarse exclusivamente en Linux/WSL.
- Intentar publicar contenido desde Windows PowerShell produce posts con `post_content` vacío.
- Los scripts que usan `Invoke-RestMethod` + `ConvertTo-Json` no son seguros para cuerpos JSON con HTML + non-ASCII.
- Ante detectar PowerShell/cmd de Windows, detenerse y pedir ejecutar en WSL.

### 5.2 — En `.opencode/agents/content-marketer.md`

Añadir nota al inicio: "Ejecutar únicamente en Linux/WSL. En Windows el flujo de publicación corrompe el contenido del post."

### 5.3 — En `docs/plans/windows-execution-restriction.md`

Documentar el plan completo (este documento).

---

## 6. Mitigación: checklist de verificación post-publicación

Añadir un paso al comando `/create-post` (Paso 7, justo tras crear el post) y a la skill `publish-wordpress` (Paso 6, reporte final):

**Verificación obligatoria tras `wp_add_post`:**

```
GET /wp-json/wp/v2/posts/{id}?context=edit
Comprobar content.raw.Length > 0
```

- Si `content.raw.Length = 0` → el paso se marca como **error**, se revierte el estado de la idea a `pendiente` (si venía de la cola) y se informa al usuario. **No se continúa** con schema ni registro en DB local como "publicado".
- Si `content.raw.Length > 0` → continuar el flujo normalmente.

Esto detectaría el bug incluso si se escapara el bloqueo de OS, evitando dejar posts vacíos marcados como publicados.

---

## 7. Pendientes (trabajo futuro desde WSL/Linux)

- [ ] **Reinyectar contenido del post 1037** (Terranigma): reconstruir el HTML (disponible en el log de ejecución `memory/execution-logs/2026-07-24.md` y en el historial de la sesión) y hacer `wp_update_post` con el `content` completo desde WSL. Re-aplicar Paso 7.5 (schema ya inyectado, no necesario) y verificar `content_len > 0`.
- [ ] **Reinyectar contenido del post 1030** (Historia Super Mario RPG): recuperar el contenido de su log de ejecución correspondiente en `memory/execution-logs/` y re-publicar vía `wp_update_post` desde WSL.
- [ ] Implementar el **checklist de mitigación** del apartado 6 en la skill `publish-wordpress` y en el comando `/create-post`.
- [ ] Añadir la nota de bloqueo OS en `AGENTS.md` y en `.opencode/agents/content-marketer.md`.