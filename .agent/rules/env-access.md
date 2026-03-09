---
trigger: always_on
---

# Regla: Acceso a Variables de Entorno

## Activación

Always On — Esta regla se aplica a TODO el contenido generado y todas las acciones del agente.

---

## Requisito Obligatorio

Antes de realizar **cualquier llamada a una API externa** (RAWG, Hugging Face, WordPress MCP, etc.), el agente DEBE:

1. **Leer el archivo `.env`** ubicado en la raíz del proyecto (`/mnt/g/PROJECTS/_OPTIMBYTE/optim-games-agent/.env`)
2. **Extraer los valores necesarios** del archivo:
   - `RAWG_API_KEY` → para búsquedas de portadas de juegos
   - `HF_TOKEN` → para generación de imágenes con IA
   - `WP_BASE_URL` → URL del blog

## Errores a Evitar

| ❌ Error | ✅ Correcto |
|----------|-------------|
| Usar "demo" como API key | Usar el valor real de `RAWG_API_KEY` del `.env` |
| Usar `key=RAWG_API_KEY` en la URL | Usar `key=744844ef430840ea86411672483d72a6` (valor real) |
| Continuar sin saber el valor | Detenerse y leer el `.env` primero |
| Asumir que la key no existe | Verificar el archivo antes de concluir |

## Flujo Correcto

```
1. Necesito hacer una llamada a RAWG API
2. → Leo el archivo .env
3. → Extraigo RAWG_API_KEY=744844ef430840ea86411672483d72a6
4. → Construyo la URL con la key real
5. → Realizo la llamada
```

## Ubicación del Archivo

```
/mnt/g/PROJECTS/_OPTIMBYTE/optim-games-agent/.env
```

Este archivo contiene las credenciales reales del proyecto. El agente debe tratarlo como la fuente de verdad para cualquier autenticación.

---

**Nota:** Esta regla existe porque en una ocasión el agente usó "demo" como key en lugar de leer el valor real del `.env`, causando que la búsqueda de imágenes fallara.