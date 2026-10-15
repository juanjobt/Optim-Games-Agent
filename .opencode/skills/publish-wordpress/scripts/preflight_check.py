#!/usr/bin/env python3
"""
preflight_check.py — Verificación de entorno previa a /create-post.

Comprueba, SIN publicar nada, que el entorno está listo para crear un post:

  1. Que existe el `.env` y están las credenciales obligatorias.
  2. Que el JWT de WordPress MCP configurado en `opencode.json` es válido
     (no ha caducado). Los tools `wp_*` solo se cargan si el JWT es válido.
  3. Que WordPress responde por REST con la Application Password.
  4. Qué claves de API opcionales faltan (RAWG, SerpApi, HF).

Recomienda un modo de publicación:
  - "mcp"  → MCP disponible (JWT válido) → usar tools `wp_*` (camino principal).
  - "rest" → MCP no disponible → usar los scripts REST wp_*.py (fallback).

Uso:
    python3 .opencode/skills/publish-wordpress/scripts/preflight_check.py [--env .env]

Salida: JSON por stdout.
Exit code: 0 si WP REST responde y no falta ninguna credencial obligatoria;
           1 en caso contrario (o si no existe el .env).
"""

import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent.parent
OPENCODE_JSON = PROJECT_ROOT / "opencode.json"

REQUIRED_ENV = ("WP_BASE_URL", "WP_USER", "WP_APP_PASSWORD")
OPTIONAL_ENV = ("WP_VIDEOGAME_SCHEMA_ID", "SERPAPI_KEY", "RAWG_API_KEY", "HF_TOKEN")


def load_env(path):
    env = {}
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    return env


def decode_jwt(token):
    """Decodifica la parte payload de un JWT (sin verificar firma)."""
    parts = token.split(".")
    if len(parts) < 2:
        return None
    payload = parts[1]
    payload += "=" * (-len(payload) % 4)
    try:
        return json.loads(base64.urlsafe_b64decode(payload))
    except Exception:
        return None


def check_jwt():
    result = {"present": False, "valid": False, "iat": None, "exp": None,
              "days_left": None, "reason": "no encontrado"}
    if not OPENCODE_JSON.exists():
        result["reason"] = f"opencode.json no encontrado en {OPENCODE_JSON}"
        return result
    try:
        cfg = json.loads(OPENCODE_JSON.read_text(encoding="utf-8"))
    except Exception as e:
        result["reason"] = f"opencode.json ilegible: {e}"
        return result

    mcp = (cfg.get("mcp") or {}).get("wordpress-mcp-remote") or {}
    headers = mcp.get("headers") or {}
    auth = headers.get("Authorization", "")
    if not auth.lower().startswith("bearer "):
        result["reason"] = "no hay Authorization Bearer en mcp.wordpress-mcp-remote"
        return result

    token = auth.split(None, 1)[1].strip()
    payload = decode_jwt(token)
    if not payload:
        result["reason"] = "JWT no decodificable"
        return result

    result["present"] = True
    result["iat"] = payload.get("iat")
    result["exp"] = payload.get("exp")
    now = int(time.time())
    if result["exp"] is None:
        result["reason"] = "JWT sin campo exp"
        return result
    result["days_left"] = round((result["exp"] - now) / 86400, 2)
    if result["exp"] < now:
        result["valid"] = False
        result["reason"] = "JWT CADUCADO"
    else:
        result["valid"] = True
        result["reason"] = "OK"
    return result


def check_wp_rest(base_url, user, password):
    url = f"{base_url.rstrip('/')}/wp-json/wp/v2/users/me"
    creds = base64.b64encode(f"{user}:{password}".encode()).decode()
    req = urllib.request.Request(url, headers={"Authorization": f"Basic {creds}"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return {"ok": True, "status": 200, "user": data.get("name") or data.get("slug"), "error": None}
    except urllib.error.HTTPError as e:
        return {"ok": False, "status": e.code, "user": None,
                "error": f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:150]}"}
    except Exception as e:
        return {"ok": False, "status": None, "user": None, "error": f"{type(e).__name__}: {e}"}


def main():
    parser = argparse.ArgumentParser(description="Preflight de entorno para /create-post")
    parser.add_argument("--env", default=str(PROJECT_ROOT / ".env"), help="Ruta al .env")
    args = parser.parse_args()

    env_path = Path(args.env)
    out = {
        "ok": False,
        "env_file": str(env_path),
        "env_found": env_path.exists(),
        "missing_required": [],
        "missing_optional": [],
        "jwt": check_jwt(),
        "wp_rest": {"ok": False, "status": None, "user": None, "error": "no evaluado"},
        "recommended_mode": None,
        "notes": [],
    }

    env = load_env(env_path)
    out["missing_required"] = [k for k in REQUIRED_ENV if not env.get(k)]
    out["missing_optional"] = [k for k in OPTIONAL_ENV if not env.get(k)]

    if out["env_found"] and not out["missing_required"]:
        out["wp_rest"] = check_wp_rest(env["WP_BASE_URL"], env["WP_USER"], env["WP_APP_PASSWORD"])

    jwt_ok = bool(out["jwt"].get("valid"))
    rest_ok = bool(out["wp_rest"].get("ok"))
    out["recommended_mode"] = "mcp" if jwt_ok else ("rest" if rest_ok else None)

    if not out["env_found"]:
        out["notes"].append(f"No existe {env_path}")
    if out["missing_required"]:
        out["notes"].append("Faltan credenciales obligatorias en .env: " + ", ".join(out["missing_required"]))
    if not jwt_ok and out["jwt"].get("present"):
        dl = out["jwt"].get("days_left")
        out["notes"].append(f"JWT MCP no válido ({out['jwt'].get('reason')}"
                            + (f", days_left={dl}" if dl is not None else "") + "). "
                            "Renovar en WP → Ajustes → WordPress MCP → Authentication Tokens y actualizar opencode.json.")
    if not jwt_ok and rest_ok:
        out["notes"].append("MCP no disponible: usar el fallback REST (wp_create_post.py / wp_update_post.py / wp_resolve_terms.py).")
    if out["missing_optional"]:
        out["notes"].append("Variables opcionales ausentes: " + ", ".join(out["missing_optional"]))

    out["ok"] = bool(out["env_found"] and not out["missing_required"] and rest_ok)

    print(json.dumps(out, ensure_ascii=False, default=str, indent=2))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
