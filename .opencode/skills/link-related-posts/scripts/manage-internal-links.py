#!/usr/bin/env python3
"""
manage-internal-links.py
Busca posts relacionados y gestiona datos de internal linking para Optim Pixel.

Uso:
  python manage-internal-links.py find-related --wp-id 42 [--limit 5]
  python manage-internal-links.py needs-links [--limit 10]
  python manage-internal-links.py get-post-content --wp-id 42

Los comandos add-link, get-links y link-stats se han movido a db_query.py.
"""

import argparse
import base64
import json
import os
import sqlite3
import sys
import urllib.error
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent.parent
DB_PATH = PROJECT_ROOT / "memory" / "blog.db"


def load_env(env_path):
    env = {}
    env_path = Path(env_path) if isinstance(env_path, str) else env_path
    try:
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    env[key.strip()] = value.strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    return env


def get_wp_config():
    env_path = PROJECT_ROOT / ".env"
    env = load_env(env_path)
    wp_base_url = env.get("WP_BASE_URL") or os.environ.get("WP_BASE_URL")
    wp_user = env.get("WP_USER") or os.environ.get("WP_USER")
    wp_app_password = env.get("WP_APP_PASSWORD") or os.environ.get("WP_APP_PASSWORD")
    if not wp_base_url or not wp_user or not wp_app_password:
        print(json.dumps({
            "ok": False,
            "error": "WP_BASE_URL, WP_USER y WP_APP_PASSWORD son obligatorios en .env"
        }), file=sys.stderr)
        sys.exit(1)
    credentials = base64.b64encode(f"{wp_user}:{wp_app_password}".encode()).decode()
    return wp_base_url.rstrip("/"), f"Basic {credentials}"


def wp_get(endpoint, wp_base_url, auth_header):
    url = f"{wp_base_url}/wp-json/wp/v2/{endpoint}"
    req = urllib.request.Request(url, headers={"Authorization": auth_header})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        raise RuntimeError(f"HTTP {e.code}: {error_body}")


def _fetch_all_wp_tags(wp_base_url, auth_header):
    """Descarga todos los tags de WP normalizando HTML entities del name."""
    import html
    all_tags = []
    page = 1
    while True:
        url = f"{wp_base_url}/wp-json/wp/v2/tags?fields=id,name,slug,count&per_page=100&page={page}"
        req = urllib.request.Request(url, headers={"Authorization": auth_header})
        with urllib.request.urlopen(req, timeout=30) as response:
            items = json.loads(response.read().decode("utf-8"))
        if not items:
            break
        for t in items:
            if isinstance(t.get("name"), str):
                t["name"] = html.unescape(t["name"])
        all_tags.extend(items)
        if len(items) < 100:
            break
        page += 1
    return all_tags


def _fetch_wp_post(wp_id, wp_base_url, auth_header):
    url = f"{wp_base_url}/wp-json/wp/v2/posts/{wp_id}?_fields=id,title,slug,tags"
    req = urllib.request.Request(url, headers={"Authorization": auth_header})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def get_conn():
    if not DB_PATH.exists():
        print(json.dumps({
            "ok": False,
            "error": f"Base de datos no encontrada: {DB_PATH}. Ejecuta db_init.py init primero."
        }), file=sys.stderr)
        sys.exit(1)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def out(data):
    print(json.dumps(data, ensure_ascii=False, default=str))


def _validate_post_tags(conn, wp_id, wp_base_url, auth_header):
    """Compara post_tags locales contra WordPress para el post wp_id.

    Devuelve dict con:
      - is_valid: bool
      - in_wp_not_in_db: lista de tag_wp_id en WP ausentes en DB local
      - in_db_not_in_wp: lista de tag_wp_id en DB local ausentes en WP
      - name_mismatches: lista de wp_id presente en ambos pero name divergente
      - message: mensaje humano con el resumen
    No lanza — captura errores de red. En caso de fallo de WP devuelve
    is_valid=True y un warning (no bloqueamos la operacion principal).
    """
    try:
        wp_tags = _fetch_all_wp_tags(wp_base_url, auth_header)
    except Exception as e:
        return {
            "is_valid": True,
            "warning": f"No se pudo validar contra WordPress: {e}",
        }
    wp_tags_by_id = {t["id"]: t for t in wp_tags}

    try:
        wp_post = _fetch_wp_post(wp_id, wp_base_url, auth_header)
    except Exception as e:
        return {
            "is_valid": True,
            "warning": f"No se pudo obtener post {wp_id} de WP: {e}",
        }

    wp_tag_ids = set(wp_post.get("tags") or [])
    local_rows = conn.execute(
        "SELECT tag_wp_id FROM post_tags WHERE post_wp_id = ?", (wp_id,)
    ).fetchall()
    local_tag_ids = {r["tag_wp_id"] for r in local_rows}

    in_wp_not_in_db = sorted(wp_tag_ids - local_tag_ids)
    in_db_not_in_wp = sorted(local_tag_ids - wp_tag_ids)

    name_mismatches = []
    for tid in sorted(wp_tag_ids & local_tag_ids):
        local_name_row = conn.execute(
            "SELECT name FROM tags WHERE wp_id = ?", (tid,)
        ).fetchone()
        wp = wp_tags_by_id.get(tid)
        if local_name_row is None:
            name_mismatches.append({"tag_wp_id": tid, "issue": "tag no en tabla tags local"})
        elif wp is None:
            name_mismatches.append({
                "tag_wp_id": tid,
                "local_name": local_name_row["name"],
                "issue": "wp_id no existe en WordPress",
            })
        elif wp["name"] != local_name_row["name"]:
            name_mismatches.append({
                "tag_wp_id": tid,
                "local_name": local_name_row["name"],
                "wp_name": wp["name"],
            })

    is_valid = not (in_wp_not_in_db or in_db_not_in_wp or name_mismatches)
    parts = []
    if in_wp_not_in_db:
        parts.append(f"{len(in_wp_not_in_db)} tags en WP ausentes en DB local")
    if in_db_not_in_wp:
        parts.append(f"{len(in_db_not_in_wp)} tags en DB local ausentes en WP")
    if name_mismatches:
        parts.append(f"{len(name_mismatches)} name mismatches (posible stale tag)")
    message = "OK" if is_valid else "Divergencia: " + "; ".join(parts)
    return {
        "is_valid": is_valid,
        "in_wp_not_in_db": in_wp_not_in_db,
        "in_db_not_in_wp": in_db_not_in_wp,
        "name_mismatches": name_mismatches,
        "message": message,
    }


def find_related(conn, wp_id, limit, validate=False, wp_config=None):
    tag_rows = conn.execute("""
        SELECT t.wp_id, t.name, t.slug, tg.slug as group_slug, tg.score_weight
        FROM post_tags pt
        JOIN tags t ON pt.tag_wp_id = t.wp_id
        JOIN tag_groups tg ON t.group_id = tg.id
        WHERE pt.post_wp_id = ?
    """, (wp_id,)).fetchall()

    if not tag_rows:
        out({"ok": False, "error": f"El post wp_id={wp_id} no tiene tags en la base de datos local. Sincroniza los tags con db_init.py sync-tags-wp primero."})
        return

    validation = None
    if validate:
        if not wp_config:
            out({"ok": False, "error": "--validate requiere credenciales WP en .env"})
            return
        validation = _validate_post_tags(conn, wp_id, wp_config[0], wp_config[1])

    linked_to_ids = set()
    try:
        existing = conn.execute(
            "SELECT to_wp_id FROM internal_links WHERE from_wp_id = ?",
            (wp_id,),
        ).fetchall()
        linked_to_ids = {row["to_wp_id"] for row in existing}
    except Exception:
        pass

    scores = {}

    for tag_row in tag_rows:
        tag_wp_id = tag_row["wp_id"]
        group_slug = tag_row["group_slug"]
        score_weight = tag_row["score_weight"]

        matching_posts = conn.execute("""
            SELECT pt.post_wp_id
            FROM post_tags pt
            WHERE pt.tag_wp_id = ? AND pt.post_wp_id != ?
        """, (tag_wp_id, wp_id)).fetchall()

        for mp in matching_posts:
            candidate_id = mp["post_wp_id"]
            if candidate_id in linked_to_ids:
                continue
            if candidate_id not in scores:
                scores[candidate_id] = {"wp_id": candidate_id, "score": 0, "shared_tags": []}
            scores[candidate_id]["score"] += score_weight
            scores[candidate_id]["shared_tags"].append({
                "name": tag_row["name"],
                "slug": tag_row["slug"],
                "group_slug": group_slug,
                "score_weight": score_weight,
            })

    if not scores:
        out({"ok": True, "related": [], "source_wp_id": wp_id, "count": 0})
        return

    candidate_ids = list(scores.keys())
    placeholders = ",".join("?" * len(candidate_ids))
    posts_rows = conn.execute(
        f"SELECT wp_id, title, slug, category_slug, published_at FROM posts WHERE wp_id IN ({placeholders})",
        candidate_ids,
    ).fetchall()
    posts_by_id = {row["wp_id"]: row for row in posts_rows}

    results = []
    for cid, score_data in scores.items():
        post = posts_by_id.get(cid)
        if not post:
            continue
        results.append({
            "wp_id": cid,
            "title": post["title"],
            "slug": post["slug"],
            "category_slug": post["category_slug"],
            "url": f"https://optimpixel.com/{post['slug']}/",
            "date": post["published_at"],
            "score": score_data["score"],
            "shared_tags": score_data["shared_tags"],
        })

    results.sort(key=lambda x: (-x["score"], x.get("date") or ""))
    results = results[:limit]

    tag_summary = [{"name": r["name"], "group_slug": r["group_slug"], "score_weight": r["score_weight"]} for r in tag_rows]

    payload = {"ok": True, "related": results, "source_wp_id": wp_id, "source_tags": tag_summary, "count": len(results)}
    if validation is not None:
        payload["validation"] = validation
    out(payload)


def cmd_find_related(args):
    conn = get_conn()
    try:
        source_exists = conn.execute("SELECT 1 FROM posts WHERE wp_id = ?", (args.wp_id,)).fetchone()
        if not source_exists:
            out({"ok": False, "error": f"El post wp_id={args.wp_id} no existe en la base de datos local. Sincroniza con db_init.py sync-posts-wp primero."})
            return
        wp_config = None
        if args.validate:
            wp_config = get_wp_config()
        find_related(conn, args.wp_id, args.limit, validate=args.validate, wp_config=wp_config)
    except Exception as e:
        out({"ok": False, "error": str(e)})
    finally:
        conn.close()


def cmd_needs_links(args):
    conn = get_conn()
    try:
        rows = conn.execute("""
            SELECT p.wp_id, p.title, p.slug, p.category_slug, p.published_at,
                   COUNT(il.id) as outgoing_count
            FROM posts p
            LEFT JOIN internal_links il ON p.wp_id = il.from_wp_id
            GROUP BY p.wp_id
            HAVING outgoing_count < 2
            ORDER BY p.published_at ASC
            LIMIT ?
        """, (args.limit,)).fetchall()

        results = []
        for row in rows:
            results.append({
                "wp_id": row["wp_id"],
                "title": row["title"],
                "slug": row["slug"],
                "category_slug": row["category_slug"],
                "url": f"https://optimpixel.com/{row['slug']}/",
                "date": row["published_at"],
                "outgoing_links": row["outgoing_count"],
            })

        out({"ok": True, "posts_needing_links": results, "count": len(results)})
    except Exception as e:
        out({"ok": False, "error": str(e)})
    finally:
        conn.close()


def cmd_get_post_content(args):
    wp_base_url, auth_header = get_wp_config()
    try:
        post = wp_get(f"posts/{args.wp_id}?context=edit", wp_base_url, auth_header)
        content = post.get("content", {}).get("raw", "")
        title = post.get("title", {}).get("rendered", "")
        out({
            "ok": True,
            "wp_id": str(args.wp_id),
            "title": title,
            "content": content
        })
    except Exception as e:
        out({"ok": False, "error": str(e)})


def main():
    parser = argparse.ArgumentParser(description="Busqueda de posts relacionados y contenido para internal linking")
    sub = parser.add_subparsers(dest="command", required=True)

    p_find = sub.add_parser("find-related", help="Busca posts relacionados usando tags de la base de datos local")
    p_find.add_argument("--wp-id", type=int, required=True, help="ID de WordPress del post fuente")
    p_find.add_argument("--limit", type=int, default=5)
    p_find.add_argument("--validate", action="store_true", help="Valida contra WordPress que los post_tags locales del post fuente cuadran con la realidad. No bloquea la operacion, solo anade un bloque 'validation' al output.")

    p_needs = sub.add_parser("needs-links", help="Lista posts con menos de 2 outgoing links")
    p_needs.add_argument("--limit", type=int, default=20)

    p_get = sub.add_parser("get-post-content", help="Obtiene el contenido HTML de un post de WordPress")
    p_get.add_argument("--wp-id", type=int, required=True)

    args = parser.parse_args()
    {
        "find-related": cmd_find_related,
        "needs-links": cmd_needs_links,
        "get-post-content": cmd_get_post_content,
    }[args.command](args)


if __name__ == "__main__":
    main()