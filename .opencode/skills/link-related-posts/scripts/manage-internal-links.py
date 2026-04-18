#!/usr/bin/env python3
"""
manage-internal-links.py
Gestiona los internal links para Optim Pixel usando SQLite como fuente de datos.

Uso:
  python manage-internal-links.py find-related --wp-id 42 [--tags "sistema:Super Nintendo,genero:RPG"] [--limit 5]
  python manage-internal-links.py log-link --from-wp-id 42 --to-wp-id 17 --score 7
  python manage-internal-links.py needs-links [--limit 10]
  python manage-internal-links.py stats
  python manage-internal-links.py get-post-content --wp-id 42
  python manage-internal-links.py get-links --wp-id 42

La base de datos se inicializa con db_init.py. Este script asume que las tablas
ya existen y contienen datos sincronizados (tags, posts, post_tags).
"""

import argparse
import base64
import json
import os
import sqlite3
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
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
    import os as _os
    env_path = PROJECT_ROOT / ".env"
    env = load_env(env_path)
    wp_base_url = env.get("WP_BASE_URL") or _os.environ.get("WP_BASE_URL")
    wp_user = env.get("WP_USER") or _os.environ.get("WP_USER")
    wp_app_password = env.get("WP_APP_PASSWORD") or _os.environ.get("WP_APP_PASSWORD")
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


def row_to_dict(row):
    if row is None:
        return None
    return dict(row)


def rows_to_list(rows):
    return [dict(r) for r in rows]


def out(data):
    print(json.dumps(data, ensure_ascii=False, default=str))


def get_score_weights(conn):
    rows = conn.execute("SELECT slug, score_weight FROM tag_groups").fetchall()
    weights = {row["slug"]: row["score_weight"] for row in rows}
    weights["tag_comun"] = 1
    return weights


def find_related_from_db(conn, wp_id, limit):
    tag_rows = conn.execute("""
        SELECT t.wp_id, t.name, t.slug, tg.slug as group_slug, tg.score_weight
        FROM post_tags pt
        JOIN tags t ON pt.tag_wp_id = t.wp_id
        JOIN tag_groups tg ON t.group_id = tg.id
        WHERE pt.post_wp_id = ?
    """, (wp_id,)).fetchall()

    if not tag_rows:
        out({"ok": False, "error": f"El post wp_id={wp_id} no tiene tags en la base de datos local. Usa --tags para especificarlos manualmente."})
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


def find_related_from_tags(conn, wp_id, tags_str, limit):
    weights = get_score_weights(conn)
    raw_tags = [t.strip() for t in tags_str.split(",") if t.strip()]

    tagged = []
    untyped = []
    for tag_str in raw_tags:
        if ":" in tag_str:
            parts = tag_str.split(":", 1)
            group_slug = parts[0].strip().lower()
            tag_value = parts[1].strip()
            weight = weights.get(group_slug, 1)
            tagged.append((group_slug, tag_value, weight))
        else:
            untyped.append(tag_str)

    scores = {}

    for group_slug, tag_value, weight in tagged:
        tag_row = conn.execute(
            "SELECT wp_id, name, slug FROM tags WHERE name = ? OR slug = ?",
            (tag_value, tag_value.lower().replace(" ", "-")),
        ).fetchone()

        if not tag_row:
            tag_row = conn.execute(
                "SELECT wp_id, name, slug FROM tags WHERE name LIKE ?",
                (f"%{tag_value}%",),
            ).fetchone()

        if not tag_row:
            continue

        matching_posts = conn.execute(
            "SELECT post_wp_id FROM post_tags WHERE tag_wp_id = ? AND post_wp_id != ?",
            (tag_row["wp_id"], wp_id),
        ).fetchall()

        for mp in matching_posts:
            cid = mp["post_wp_id"]
            if cid not in scores:
                scores[cid] = {"wp_id": cid, "score": 0, "shared_tags": []}
            scores[cid]["score"] += weight
            scores[cid]["shared_tags"].append({
                "name": tag_row["name"],
                "slug": tag_row["slug"],
                "group_slug": group_slug,
                "score_weight": weight,
            })

    for tag_value in untyped:
        weight = weights.get("tag_comun", 1)
        tag_row = conn.execute(
            "SELECT wp_id, name, slug FROM tags WHERE name = ? OR slug = ?",
            (tag_value, tag_value.lower().replace(" ", "-")),
        ).fetchone()

        if not tag_row:
            continue

        matching_posts = conn.execute(
            "SELECT post_wp_id FROM post_tags WHERE tag_wp_id = ? AND post_wp_id != ?",
            (tag_row["wp_id"], wp_id),
        ).fetchall()

        for mp in matching_posts:
            cid = mp["post_wp_id"]
            if cid not in scores:
                scores[cid] = {"wp_id": cid, "score": 0, "shared_tags": []}
            scores[cid]["score"] += weight
            scores[cid]["shared_tags"].append({
                "name": tag_row["name"],
                "slug": tag_row["slug"],
                "group_slug": "tag_comun",
                "score_weight": weight,
            })

    linked_to_ids = set()
    try:
        existing = conn.execute(
            "SELECT to_wp_id FROM internal_links WHERE from_wp_id = ?",
            (wp_id,),
        ).fetchall()
        linked_to_ids = {row["to_wp_id"] for row in existing}
    except Exception:
        pass

    candidate_ids = [cid for cid in scores if cid not in linked_to_ids]

    placeholders = ",".join("?" * len(candidate_ids)) if candidate_ids else "0"
    posts_rows = conn.execute(
        f"SELECT wp_id, title, slug, category_slug, published_at FROM posts WHERE wp_id IN ({placeholders})",
        candidate_ids if candidate_ids else [0],
    ).fetchall()
    posts_by_id = {row["wp_id"]: row for row in posts_rows}

    results = []
    for cid in candidate_ids:
        score_data = scores[cid]
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

    out({"ok": True, "related": results, "source_wp_id": wp_id, "count": len(results)})


def cmd_find_related(args):
    conn = get_conn()
    try:
        source_exists = conn.execute("SELECT 1 FROM posts WHERE wp_id = ?", (args.wp_id,)).fetchone()
        if args.tags:
            find_related_from_tags(conn, args.wp_id, args.tags, args.limit)
        else:
            if not source_exists:
                out({"ok": False, "error": f"El post wp_id={args.wp_id} no existe en la base de datos local. Usa --tags para especificar los tags manualmente."})
                return
            find_related_from_db(conn, args.wp_id, args.limit)
    except Exception as e:
        out({"ok": False, "error": str(e)})
    finally:
        conn.close()


def cmd_log_link(args):
    conn = get_conn()
    now = datetime.now(timezone.utc).isoformat()
    try:
        conn.execute(
            """
            INSERT INTO internal_links (from_wp_id, to_wp_id, score, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(from_wp_id, to_wp_id) DO UPDATE SET
                score=excluded.score, created_at=excluded.created_at
            """,
            (args.from_wp_id, args.to_wp_id, args.score, now),
        )
        conn.commit()
        out({"ok": True, "from_wp_id": args.from_wp_id, "to_wp_id": args.to_wp_id, "score": args.score})
    except Exception as e:
        conn.rollback()
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


def cmd_stats(args):
    conn = get_conn()
    try:
        total_posts = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
        total_links = conn.execute("SELECT COUNT(*) FROM internal_links").fetchone()[0]

        posts_with_links = conn.execute("SELECT DISTINCT from_wp_id FROM internal_links").fetchall()
        posts_with_links_count = len(posts_with_links)
        posts_without_links = total_posts - posts_with_links_count

        rows = conn.execute("""
            SELECT from_wp_id, COUNT(*) as cnt FROM internal_links
            GROUP BY from_wp_id
        """).fetchall()
        one_link = sum(1 for r in rows if r["cnt"] == 1)
        multiple_links = sum(1 for r in rows if r["cnt"] >= 2)

        out({
            "ok": True,
            "stats": {
                "total_posts": total_posts,
                "total_internal_links": total_links,
                "posts_sin_ningun_link": posts_without_links,
                "posts_con_un_solo_link": one_link,
                "posts_correctamente_enlazados": multiple_links,
            }
        })
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


def cmd_get_links(args):
    conn = get_conn()
    try:
        outgoing = conn.execute("""
            SELECT to_wp_id, score, created_at
            FROM internal_links
            WHERE from_wp_id = ?
            ORDER BY created_at DESC
        """, (args.wp_id,)).fetchall()

        incoming = conn.execute("""
            SELECT from_wp_id as wp_id, score, created_at
            FROM internal_links
            WHERE to_wp_id = ?
            ORDER BY created_at DESC
        """, (args.wp_id,)).fetchall()

        out({
            "ok": True,
            "wp_id": args.wp_id,
            "outgoing": rows_to_list(outgoing),
            "incoming": rows_to_list(incoming),
            "outgoing_count": len(outgoing),
            "incoming_count": len(incoming)
        })
    except Exception as e:
        out({"ok": False, "error": str(e)})
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Gestión de internal links para Optim Pixel")
    sub = parser.add_subparsers(dest="command", required=True)

    p_find = sub.add_parser("find-related", help="Busca posts relacionados usando la base de datos local")
    p_find.add_argument("--wp-id", type=int, required=True, help="ID de WordPress del post fuente")
    p_find.add_argument("--tags", type=str, default=None, help="Tags con tipo: 'sistema:Super Nintendo,genero:RPG' (opcional, si no se proporciona se usan los del post)")
    p_find.add_argument("--limit", type=int, default=5)

    p_log = sub.add_parser("log-link", help="Registra un internal link creado")
    p_log.add_argument("--from-wp-id", type=int, required=True)
    p_log.add_argument("--to-wp-id", type=int, required=True)
    p_log.add_argument("--score", type=int, default=0)

    p_needs = sub.add_parser("needs-links", help="Lista posts con menos de 2 outgoing links")
    p_needs.add_argument("--limit", type=int, default=20)

    p_get = sub.add_parser("get-post-content", help="Obtiene el contenido HTML de un post de WordPress")
    p_get.add_argument("--wp-id", type=int, required=True)

    p_links = sub.add_parser("get-links", help="Obtiene los enlaces salientes y entrantes de un post")
    p_links.add_argument("--wp-id", type=int, required=True)

    sub.add_parser("stats", help="Estadísticas generales de internal linking")

    args = parser.parse_args()
    {
        "find-related": cmd_find_related,
        "log-link": cmd_log_link,
        "needs-links": cmd_needs_links,
        "get-post-content": cmd_get_post_content,
        "get-links": cmd_get_links,
        "stats": cmd_stats,
    }[args.command](args)


if __name__ == "__main__":
    main()