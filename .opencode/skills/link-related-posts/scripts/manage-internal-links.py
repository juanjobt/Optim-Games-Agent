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


def find_related(conn, wp_id, limit):
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
            "url": f"https://optimpixel.com/{post['slug']}",
            "date": post["published_at"],
            "score": score_data["score"],
            "shared_tags": score_data["shared_tags"],
        })

    results.sort(key=lambda x: (-x["score"], x.get("date") or ""))
    results = results[:limit]

    tag_summary = [{"name": r["name"], "group_slug": r["group_slug"], "score_weight": r["score_weight"]} for r in tag_rows]

    out({"ok": True, "related": results, "source_wp_id": wp_id, "source_tags": tag_summary, "count": len(results)})


def cmd_find_related(args):
    conn = get_conn()
    try:
        source_exists = conn.execute("SELECT 1 FROM posts WHERE wp_id = ?", (args.wp_id,)).fetchone()
        if not source_exists:
            out({"ok": False, "error": f"El post wp_id={args.wp_id} no existe en la base de datos local. Sincroniza con db_init.py sync-posts-wp primero."})
            return
        find_related(conn, args.wp_id, args.limit)
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
                "url": f"https://optimpixel.com/{row['slug']}",
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