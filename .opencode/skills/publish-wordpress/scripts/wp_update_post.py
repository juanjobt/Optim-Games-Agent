#!/usr/bin/env python3
"""
wp_update_post.py — Actualiza un post en WordPress por REST.

Fallback REST equivalente a `wp_update_post` del MCP. Solo envía los campos
indicados. Serializa el cuerpo JSON en UTF-8 limpio.

Uso:
    # Cambiar estado:
    python3 .opencode/skills/publish-wordpress/scripts/wp_update_post.py --id 1141 --status publish

    # Actualizar contenido (p. ej. tras insertar internal links):
    python3 .opencode/skills/publish-wordpress/scripts/wp_update_post.py --id 1141 --content-file /tmp/post.html

    # Varios campos a la vez:
    python3 .opencode/skills/publish-wordpress/scripts/wp_update_post.py --id 1141 --title "..." --excerpt "..."
    [--env .env]

Salida: JSON por stdout con {id, status, slug, link}.
Exit code: 0 si el post se actualiza, 1 en caso contrario.
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
    parser = argparse.ArgumentParser(description="Actualiza un post en WordPress (REST)")
    parser.add_argument("--id", type=int, required=True)
    parser.add_argument("--status", default=None, choices=["draft", "publish", "pending", "private"])
    parser.add_argument("--content-file", default=None, help="Ruta al fichero HTML del contenido")
    parser.add_argument("--title", default=None)
    parser.add_argument("--excerpt", default=None)
    parser.add_argument("--env", default=str(PROJECT_ROOT / ".env"))
    args = parser.parse_args()

    env = load_env(args.env)
    base = (env.get("WP_BASE_URL") or "").rstrip("/")
    user = env.get("WP_USER")
    pwd = env.get("WP_APP_PASSWORD")
    if not base or not user or not pwd:
        print(json.dumps({"ok": False, "error": "Faltan WP_BASE_URL/WP_USER/WP_APP_PASSWORD en .env"}))
        return 1

    data = {}
    if args.status:
        data["status"] = args.status
    if args.title:
        data["title"] = args.title
    if args.excerpt:
        data["excerpt"] = args.excerpt
    if args.content_file:
        content = Path(args.content_file).read_text(encoding="utf-8")
        if not content.strip():
            print(json.dumps({"ok": False, "error": f"El fichero de contenido está vacío: {args.content_file}"}))
            return 1
        data["content"] = content

    if not data:
        print(json.dumps({"ok": False, "error": "Nada que actualizar (usa --status/--title/--excerpt/--content-file)"}))
        return 1

    auth = base64.b64encode(f"{user}:{pwd}".encode()).decode()
    req = urllib.request.Request(
        f"{base}/wp-json/wp/v2/posts/{args.id}",
        data=json.dumps(data).encode("utf-8"),
        headers={"Authorization": f"Basic {auth}", "Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            d = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(json.dumps({"ok": False, "id": args.id, "error": f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:400]}"}))
        return 1
    except Exception as e:
        print(json.dumps({"ok": False, "id": args.id, "error": f"{type(e).__name__}: {e}"}))
        return 1

    print(json.dumps({"ok": True, "id": d.get("id"), "status": d.get("status"),
                      "slug": d.get("slug"), "link": d.get("link")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
