#!/usr/bin/env python3
"""
wp_get_post.py — Lee un post de WordPress por REST (context=edit).

Fallback REST equivalente a `wp_get_post` del MCP. Sirve para verificar
estado, featured_media, tags y longitud del contenido tras crear/actualizar.

Uso:
    python3 .opencode/skills/publish-wordpress/scripts/wp_get_post.py --id 1141 [--env .env]

Salida: JSON por stdout.
Exit code: 0 si el post se lee correctamente, 1 en caso contrario.
"""

import argparse
import base64
import json
import sys
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


def main():
    parser = argparse.ArgumentParser(description="Lee un post de WordPress (REST)")
    parser.add_argument("--id", type=int, required=True, help="ID del post en WordPress")
    parser.add_argument("--env", default=str(PROJECT_ROOT / ".env"))
    args = parser.parse_args()

    env = load_env(args.env)
    base = (env.get("WP_BASE_URL") or "").rstrip("/")
    user = env.get("WP_USER")
    pwd = env.get("WP_APP_PASSWORD")
    if not base or not user or not pwd:
        print(json.dumps({"ok": False, "id": args.id, "error": "Faltan WP_BASE_URL/WP_USER/WP_APP_PASSWORD en .env"}))
        return 1

    auth = base64.b64encode(f"{user}:{pwd}".encode()).decode()
    url = f"{base}/wp-json/wp/v2/posts/{args.id}?context=edit"
    req = urllib.request.Request(url, headers={"Authorization": f"Basic {auth}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            d = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(json.dumps({"ok": False, "id": args.id, "error": f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:200]}"}))
        return 1
    except Exception as e:
        print(json.dumps({"ok": False, "id": args.id, "error": f"{type(e).__name__}: {e}"}))
        return 1

    print(json.dumps({
        "ok": True,
        "id": d.get("id"),
        "status": d.get("status"),
        "slug": d.get("slug"),
        "link": d.get("link"),
        "title": (d.get("title") or {}).get("raw") or (d.get("title") or {}).get("rendered"),
        "featured_media": d.get("featured_media"),
        "categories": d.get("categories"),
        "tags": d.get("tags"),
        "content_len": len((d.get("content") or {}).get("raw", "") or ""),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
