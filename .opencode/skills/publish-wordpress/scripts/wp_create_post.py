#!/usr/bin/env python3
"""
wp_create_post.py — Crea un post en WordPress por REST.

Fallback REST equivalente a `wp_add_post` del MCP. Serializa el cuerpo JSON
en UTF-8 limpio (a diferencia de PowerShell + Invoke-RestMethod), por lo que
es seguro para HTML con acentos y entidades.

Uso:
    python3 .opencode/skills/publish-wordpress/scripts/wp_create_post.py \
        --title "Título" \
        --slug "slug-del-post" \
        --content-file /tmp/post.html \
        --excerpt "Descripción de 150-160 caracteres" \
        --status draft \
        --categories 2 \
        --tags 41,6,9,70 \
        [--env .env]

Salida: JSON por stdout con {id, status, slug, link}.
Exit code: 0 si el post se crea, 1 en caso contrario.
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
    parser = argparse.ArgumentParser(description="Crea un post en WordPress (REST)")
    parser.add_argument("--title", required=True)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--content-file", required=True, help="Ruta al fichero HTML del contenido")
    parser.add_argument("--excerpt", required=True)
    parser.add_argument("--status", default="draft", choices=["draft", "publish", "pending", "private"])
    parser.add_argument("--categories", default="", help="IDs de categoría separados por coma")
    parser.add_argument("--tags", default="", help="IDs de tag separados por coma")
    parser.add_argument("--env", default=str(PROJECT_ROOT / ".env"))
    args = parser.parse_args()

    env = load_env(args.env)
    base = (env.get("WP_BASE_URL") or "").rstrip("/")
    user = env.get("WP_USER")
    pwd = env.get("WP_APP_PASSWORD")
    if not base or not user or not pwd:
        print(json.dumps({"ok": False, "error": "Faltan WP_BASE_URL/WP_USER/WP_APP_PASSWORD en .env"}))
        return 1

    content = Path(args.content_file).read_text(encoding="utf-8")
    if not content.strip():
        print(json.dumps({"ok": False, "error": f"El fichero de contenido está vacío: {args.content_file}"}))
        return 1

    data = {
        "title": args.title,
        "slug": args.slug,
        "content": content,
        "excerpt": args.excerpt,
        "status": args.status,
        "categories": [int(x) for x in args.categories.split(",") if x.strip()],
        "tags": [int(x) for x in args.tags.split(",") if x.strip()],
    }

    auth = base64.b64encode(f"{user}:{pwd}".encode()).decode()
    req = urllib.request.Request(
        f"{base}/wp-json/wp/v2/posts",
        data=json.dumps(data).encode("utf-8"),
        headers={"Authorization": f"Basic {auth}", "Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            d = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(json.dumps({"ok": False, "error": f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:400]}"}))
        return 1
    except Exception as e:
        print(json.dumps({"ok": False, "error": f"{type(e).__name__}: {e}"}))
        return 1

    print(json.dumps({"ok": True, "id": d.get("id"), "status": d.get("status"),
                      "slug": d.get("slug"), "link": d.get("link")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
