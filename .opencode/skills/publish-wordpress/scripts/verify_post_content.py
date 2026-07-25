#!/usr/bin/env python3
"""
verify_post_content.py
Verifica que un post de WordPress tiene el contenido realmente almacenado
(post_content no vacío). Mitigación del bug documentado en
docs/plans/windows-execution-restriction.md, donde ejecuciones bajo
Windows PowerShell creaban posts con content.raw de 0 bytes.

Uso:
    python3 verify_post_content.py --post-id 123 [--env .env]

Salida JSON por stdout:
    {"ok": true,  "post_id": 123, "content_len": 5812, "status": "publish"}
    {"ok": false, "post_id": 123, "content_len": 0, "status": "publish",
     "error": "post_content vacío"}

Exit code:
    0 → content_len > 0 (verificación superada)
    1 → contenido vacío o error de conexión/autenticación
"""

import argparse
import base64
import json
import os
import sys
import urllib.request
import urllib.error

# Forzar stdout/stderr a UTF-8 (consolas con codepages legacy, ej: cp1252).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


def load_env(path: str) -> dict:
    env = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def main() -> int:
    parser = argparse.ArgumentParser(description="Verifica que un post de WP tiene post_content no vacío.")
    parser.add_argument("--post-id", type=int, required=True, help="ID del post en WordPress")
    parser.add_argument("--env", default=".env", help="Ruta al archivo .env (por defecto: .env)")
    args = parser.parse_args()

    if not os.path.exists(args.env):
        print(json.dumps({"ok": False, "post_id": args.post_id, "error": f"Archivo .env no encontrado: {args.env}"}))
        return 1

    env = load_env(args.env)
    try:
        base = env["WP_BASE_URL"].rstrip("/")
        user = env["WP_USER"]
        password = env["WP_APP_PASSWORD"]
    except KeyError as e:
        print(json.dumps({"ok": False, "post_id": args.post_id, "error": f"Falta variable en .env: {e}"}))
        return 1

    auth = base64.b64encode(f"{user}:{password}".encode()).decode()
    url = f"{base}/wp-json/wp/v2/posts/{args.post_id}?context=edit"
    req = urllib.request.Request(url, headers={"Authorization": f"Basic {auth}"})

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as e:
        print(json.dumps({"ok": False, "post_id": args.post_id, "error": f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:200]}"}))
        return 1
    except Exception as e:
        print(json.dumps({"ok": False, "post_id": args.post_id, "error": f"Error de conexión: {e}"}))
        return 1

    content_len = len(data.get("content", {}).get("raw", "") or "")
    status = data.get("status", "unknown")

    if content_len > 0:
        print(json.dumps({"ok": True, "post_id": args.post_id, "content_len": content_len, "status": status}))
        return 0

    print(json.dumps({"ok": False, "post_id": args.post_id, "content_len": 0, "status": status,
                      "error": "post_content vacío (0 bytes). Posible corrupción en el envío. Ver docs/plans/windows-execution-restriction.md"}))
    return 1


if __name__ == "__main__":
    sys.exit(main())
