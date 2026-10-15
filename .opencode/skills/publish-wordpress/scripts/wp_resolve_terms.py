#!/usr/bin/env python3
"""
wp_resolve_terms.py — Resuelve/crea categorías y tags en WordPress (REST).

Fallback REST equivalente a las operaciones MCP de taxonomías
(`wp_list_categories`, `wp_add_category`, `wp_list_tags`, `wp_add_tag`).
Para cada tag: primero consulta la base local (memory/blog.db) vía
db_query.py; si no está, lo busca/crea en WordPress, lo registra en la DB
local y le asigna el term meta `tag_group` (catálogo).

Subcomandos:
    # Categoría a partir del tipo de post:
    wp_resolve_terms.py category --type review|historia|lista

    # Tags (repetir --term grupo=nombre):
    wp_resolve_terms.py tags \
        --term "sistema=PC" --term "genero=RPG" --term "epoca=Años 90" \
        --term "ano=1991" --term "desarrolladora=New World Computing" \
        --term "saga=Saga Might and Magic"

    [--env .env]

Salida: JSON por stdout.
Exit code: 0 si todos los términos se resuelven, 1 si alguno falla.
"""

import argparse
import base64
import html
import json
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent.parent
DB_QUERY = PROJECT_ROOT / "memory" / "scripts" / "db_query.py"
SYNC_TAG_GROUPS = SCRIPT_DIR / "sync_tag_groups.py"

CATEGORY_MAP = {
    "review": ("Reviews", "reviews"),
    "historia": ("Historias", "historias"),
    "lista": ("Listas", "listas"),
}


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


class WP:
    def __init__(self, base, user, pwd):
        self.base = base.rstrip("/")
        self.auth = base64.b64encode(f"{user}:{pwd}".encode()).decode()

    def req(self, method, endpoint, data=None):
        url = f"{self.base}/wp-json/wp/v2/{endpoint}"
        body = json.dumps(data).encode("utf-8") if data is not None else None
        r = urllib.request.Request(url, data=body, method=method,
                                   headers={"Authorization": f"Basic {self.auth}",
                                            "Content-Type": "application/json; charset=utf-8"})
        with urllib.request.urlopen(r, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def find_term(self, taxonomy, name):
        q = urllib.parse.quote(name)
        items = self.req("GET", f"{taxonomy}?search={q}&per_page=100")
        target = name.strip().casefold()
        for it in items:
            if html.unescape(it.get("name", "")).strip().casefold() == target:
                return it
        return None


def db_get_tag(name):
    """Devuelve el wp_id del tag en la DB local, o None."""
    try:
        r = subprocess.run([sys.executable, str(DB_QUERY), "get-tag", "--name", name],
                           capture_output=True, text=True, timeout=30)
        d = json.loads(r.stdout.strip().splitlines()[-1])
        if d.get("ok") and d.get("tag") and d["tag"].get("wp_id", 0) > 0:
            return d["tag"]
    except Exception:
        pass
    return None


def db_add_tag(name, slug, group, wp_id):
    subprocess.run([sys.executable, str(DB_QUERY), "add-tag", "--name", name,
                    "--slug", slug, "--group", group, "--wp-id", str(wp_id)],
                   capture_output=True, text=True, timeout=30)


def sync_tag_group(wp_id, group):
    subprocess.run([sys.executable, str(SYNC_TAG_GROUPS), "--single",
                    "--wp-id", str(wp_id), "--group", group],
                   capture_output=True, text=True, timeout=30)


def resolve_category(wp, ptype):
    name, slug = CATEGORY_MAP[ptype]
    items = wp.req("GET", f"categories?slug={slug}")
    if items:
        return {"ok": True, "category_id": items[0]["id"], "slug": slug, "name": name, "origin": "existing"}
    created = wp.req("POST", "categories", {"name": name, "slug": slug})
    return {"ok": True, "category_id": created["id"], "slug": slug, "name": name, "origin": "created"}


def resolve_tag(wp, name, group):
    local = db_get_tag(name)
    if local:
        return {"name": name, "group": group, "slug": local.get("slug"),
                "wp_id": local["wp_id"], "origin": "db"}

    found = wp.find_term("tags", name)
    if found:
        wp_id, slug, origin = found["id"], found["slug"], "wp"
    else:
        created = wp.req("POST", "tags", {"name": name})
        wp_id, slug, origin = created["id"], created["slug"], "created"

    db_add_tag(name, slug, group, wp_id)
    sync_tag_group(wp_id, group)
    return {"name": name, "group": group, "slug": slug, "wp_id": wp_id, "origin": origin}


def main():
    parser = argparse.ArgumentParser(description="Resuelve/crea categorías y tags (REST)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("category", help="Resuelve la categoría del tipo de post")
    c.add_argument("--type", required=True, choices=list(CATEGORY_MAP))

    t = sub.add_parser("tags", help="Resuelve/crea tags (--term grupo=nombre, repetible)")
    t.add_argument("--term", action="append", required=True, help="Formato: grupo=nombre")

    parser.add_argument("--env", default=str(PROJECT_ROOT / ".env"))
    args = parser.parse_args()

    env = load_env(args.env)
    base = (env.get("WP_BASE_URL") or "").rstrip("/")
    user = env.get("WP_USER")
    pwd = env.get("WP_APP_PASSWORD")
    if not base or not user or not pwd:
        print(json.dumps({"ok": False, "error": "Faltan WP_BASE_URL/WP_USER/WP_APP_PASSWORD en .env"}))
        return 1

    wp = WP(base, user, pwd)
    try:
        if args.cmd == "category":
            print(json.dumps(resolve_category(wp, args.type), ensure_ascii=False))
            return 0

        results, errors = [], []
        for term in args.term:
            if "=" not in term:
                errors.append({"term": term, "error": "formato inválido, se espera grupo=nombre"})
                continue
            group, name = term.split("=", 1)
            try:
                results.append(resolve_tag(wp, name.strip(), group.strip()))
            except urllib.error.HTTPError as e:
                errors.append({"term": term, "error": f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:200]}"})
            except Exception as e:
                errors.append({"term": term, "error": f"{type(e).__name__}: {e}"})
        print(json.dumps({"ok": not errors, "tags": results, "errors": errors}, ensure_ascii=False))
        return 0 if not errors else 1
    except urllib.error.HTTPError as e:
        print(json.dumps({"ok": False, "error": f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:300]}"}))
        return 1
    except Exception as e:
        print(json.dumps({"ok": False, "error": f"{type(e).__name__}: {e}"}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
