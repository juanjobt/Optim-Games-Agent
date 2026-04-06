#!/usr/bin/env python3
"""
manage-internal-links.py
Gestiona los internal links para Optim Pixel usando WordPress como fuente de datos.

Uso:
  python manage-internal-links.py init
  python manage-internal-links.py find-related --wp-id 42 --limit 5
  python manage-internal-links.py log-link --from-wp-id 42 --to-wp-id 17 --score 7
  python manage-internal-links.py needs-links --limit 10
  python manage-internal-links.py stats
  python manage-internal-links.py get-post-content --wp-id 42

Requiere en .env:
  WP_BASE_URL=https://optimpixel.com
  WP_USER=tu_usuario
  WP_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx
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
    """Carga variables del .env sin dependencias externas."""
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


def get_wp_config(env_path=None):
    """Devuelve (wp_base_url, auth_header) leyendo el .env."""
    if env_path is None:
        env_path = PROJECT_ROOT / ".env"
    env = load_env(env_path)
    wp_base_url     = env.get("WP_BASE_URL")     or os.environ.get("WP_BASE_URL")
    wp_user         = env.get("WP_USER")         or os.environ.get("WP_USER")
    wp_app_password = env.get("WP_APP_PASSWORD") or os.environ.get("WP_APP_PASSWORD")

    if not wp_base_url or not wp_user or not wp_app_password:
        print(json.dumps({
            "ok": False,
            "error": "WP_BASE_URL, WP_USER y WP_APP_PASSWORD son obligatorios en .env"
        }), file=sys.stderr)
        sys.exit(1)

    credentials = base64.b64encode(f"{wp_user}:{wp_app_password}".encode()).decode()
    auth_header = f"Basic {credentials}"
    return wp_base_url.rstrip("/"), auth_header


def wp_get(endpoint, wp_base_url, auth_header):
    """GET a la WP REST API. Devuelve el JSON parseado."""
    url = f"{wp_base_url}/wp-json/wp/v2/{endpoint}"
    req = urllib.request.Request(url, headers={"Authorization": auth_header})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        raise RuntimeError(f"HTTP {e.code}: {error_body}")


def wp_get_with_headers(endpoint, wp_base_url, auth_header):
    """GET a la WP REST API. Devuelve (json, headers) para obtener total de posts."""
    url = f"{wp_base_url}/wp-json/wp/v2/{endpoint}"
    req = urllib.request.Request(url, headers={"Authorization": auth_header})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            headers = dict(response.headers)
            return json.loads(response.read().decode("utf-8")), headers
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        raise RuntimeError(f"HTTP {e.code}: {error_body}")


def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def cmd_init(args):
    """Inicializa la base de datos con solo la tabla internal_links."""
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS internal_links (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            from_wp_id   INTEGER NOT NULL,
            to_wp_id     INTEGER NOT NULL,
            score        INTEGER NOT NULL DEFAULT 0,
            created_at   TEXT    NOT NULL,
            UNIQUE (from_wp_id, to_wp_id)
        );

        CREATE INDEX IF NOT EXISTS idx_internal_links_from ON internal_links(from_wp_id);
        CREATE INDEX IF NOT EXISTS idx_internal_links_to   ON internal_links(to_wp_id);
    """)
    conn.commit()
    conn.close()
    print(json.dumps({"ok": True, "message": "Base de datos inicializada correctamente", "path": str(DB_PATH)}))


def get_post_metadata(wp_id, wp_base_url, auth_header):
    """Obtiene metadatos de un post desde la WP REST API."""
    post = wp_get(f"posts/{wp_id}?context=edit", wp_base_url, auth_header)

    meta = post.get("meta", {})

    return {
        "id": post.get("id"),
        "title": post.get("title", {}).get("rendered", ""),
        "url": post.get("link", ""),
        "date": post.get("date", ""),
        "tags": post.get("tags", []),
        "categories": post.get("categories", []),
        "plataforma": meta.get("plataforma", ""),
        "genero": meta.get("genero", ""),
        "saga": meta.get("saga", ""),
        "desarrolladora": meta.get("desarrolladora", ""),
        "epoca": meta.get("epoca", ""),
    }

TYPE_SCORES = {
    "saga": 3,
    "plataforma": 2,
    "genero": 1,
    "desarrolladora": 1,
    "epoca": 1,
    "tag_comun": 1,
}

def parse_tag_with_type(tag_str):
    """Parsea un tag con formato 'tipo:valor' o devuelve (None, tag_str)."""
    tag_str = tag_str.strip()
    if ":" in tag_str:
        parts = tag_str.split(":", 1)
        return parts[0].strip().lower(), parts[1].strip()
    return None, tag_str


def search_posts_by_tag(tag_name, wp_base_url, auth_header, exclude_wp_id, per_page=50):
    """Busca posts que contengan un tag específico."""
    tags = wp_get(f"tags?search={urllib.parse.quote(tag_name)}&per_page=10", wp_base_url, auth_header)
    if not tags:
        return []
    
    tag_ids = [t["id"] for t in tags if t["name"].lower() == tag_name.lower()]
    if not tag_ids:
        return []
    
    candidates = wp_get(
        f"posts?tags={','.join(map(str, tag_ids))}&exclude={exclude_wp_id}&per_page={per_page}&status=publish",
        wp_base_url,
        auth_header
    )
    return candidates


def calculate_score(candidate, current):
    """Calcula el score de similitud entre el post actual y un candidato."""
    score = 0

    if candidate.get("saga") and current.get("saga"):
        if candidate["saga"].lower() == current["saga"].lower():
            score += 3

    if candidate.get("plataforma") and current.get("plataforma"):
        if candidate["plataforma"].lower() == current["plataforma"].lower():
            score += 2

    if candidate.get("genero") and current.get("genero"):
        if candidate["genero"].lower() == current["genero"].lower():
            score += 1

    if candidate.get("desarrolladora") and current.get("desarrolladora"):
        if candidate["desarrolladora"].lower() == current["desarrolladora"].lower():
            score += 1

    if candidate.get("epoca") and current.get("epoca"):
        if candidate["epoca"].lower() == current["epoca"].lower():
            score += 1

    current_tags = set(current.get("tags", []))
    candidate_tags = set(candidate.get("tags", []))
    shared_tags = current_tags & candidate_tags
    score += len(shared_tags)

    return score


def cmd_find_related(args):
    """Busca posts relacionados usando la WP REST API con tags tipados."""
    env_path = PROJECT_ROOT / ".env"
    wp_base_url, auth_header = get_wp_config(str(env_path))

    try:
        if not args.tags:
            print(json.dumps({"ok": False, "error": "Se requiere --tags con formato 'tipo:valor'"}), file=sys.stderr)
            sys.exit(1)

        raw_tags = [t.strip() for t in args.tags.split(",") if t.strip()]
        parsed_tags = []
        for tag_str in raw_tags:
            tag_type, tag_value = parse_tag_with_type(tag_str)
            if tag_type and tag_type in TYPE_SCORES:
                parsed_tags.append((tag_type, tag_value, TYPE_SCORES[tag_type]))
            else:
                parsed_tags.append(("tag_comun", tag_str, TYPE_SCORES["tag_comun"]))

        posts_scores = {}

        for tag_type, tag_value, base_score in parsed_tags:
            candidates = search_posts_by_tag(tag_value, wp_base_url, auth_header, args.wp_id)
            
            for cand in candidates:
                wp_id = cand.get("id")
                if wp_id not in posts_scores:
                    posts_scores[wp_id] = {
                        "wp_id": wp_id,
                        "title": cand.get("title", {}).get("rendered", ""),
                        "url": cand.get("link", ""),
                        "date": cand.get("date", ""),
                        "score": 0,
                        "tags": cand.get("tags", []),
                        "categories": cand.get("categories", []),
                    }
                posts_scores[wp_id]["score"] += base_score

        scored = list(posts_scores.values())
        scored.sort(key=lambda x: (-x["score"], x["date"]))
        results = scored[:args.limit]

        print(json.dumps({"ok": True, "related": results}, ensure_ascii=False))

    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}), file=sys.stderr)
        sys.exit(1)


def cmd_log_link(args):
    """Registra un internal link creado."""
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
            (args.from_wp_id, args.to_wp_id, args.score, now)
        )
        conn.commit()
        print(json.dumps({"ok": True, "from_wp_id": args.from_wp_id, "to_wp_id": args.to_wp_id, "score": args.score}))

    except Exception as e:
        conn.rollback()
        print(json.dumps({"ok": False, "error": str(e)}), file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()


def cmd_needs_links(args):
    """Lista posts que necesitan más outgoing links."""
    env_path = PROJECT_ROOT / ".env"
    wp_base_url, auth_header = get_wp_config(str(env_path))
    conn = get_conn()

    try:
        all_posts = []
        page = 1
        while True:
            posts, headers = wp_get_with_headers(
                f"posts?per_page=100&page={page}&status=publish",
                wp_base_url,
                auth_header
            )
            if not posts:
                break
            all_posts.extend(posts)
            total_pages = int(headers.get("X-WP-TotalPages", 1))
            if page >= total_pages:
                break
            page += 1

        linked_posts = conn.execute("""
            SELECT DISTINCT from_wp_id FROM internal_links
        """).fetchall()
        linked_from = {row["from_wp_id"] for row in linked_posts}

        links_per_post = {}
        rows = conn.execute("""
            SELECT from_wp_id, COUNT(*) as cnt FROM internal_links
            GROUP BY from_wp_id
        """).fetchall()
        for row in rows:
            links_per_post[row["from_wp_id"]] = row["cnt"]

        needs_links = []
        for post in all_posts:
            wp_id = post["id"]
            outgoing = links_per_post.get(wp_id, 0)
            if outgoing < 2:
                needs_links.append({
                    "wp_id": wp_id,
                    "title": post["title"]["rendered"],
                    "url": post["link"],
                    "date": post["date"],
                    "outgoing_links": outgoing,
                })

        needs_links.sort(key=lambda x: (x["outgoing_links"], x["date"]))
        results = needs_links[:args.limit]

        print(json.dumps({"ok": True, "posts_needing_links": results, "count": len(results)}, ensure_ascii=False))

    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}), file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()


def cmd_stats(args):
    """Estadísticas generales de internal linking."""
    env_path = PROJECT_ROOT / ".env"
    wp_base_url, auth_header = get_wp_config(str(env_path))
    conn = get_conn()

    try:
        _, headers = wp_get_with_headers("posts?per_page=1&status=publish", wp_base_url, auth_header)
        total_posts = int(headers.get("X-WP-Total", 0))

        total_links = conn.execute("SELECT COUNT(*) FROM internal_links").fetchone()[0]

        linked_posts = conn.execute("""
            SELECT DISTINCT from_wp_id FROM internal_links
        """).fetchall()
        linked_from = {row["from_wp_id"] for row in linked_posts}

        posts_sin_links = total_posts - len(linked_from)

        rows = conn.execute("""
            SELECT from_wp_id, COUNT(*) as cnt FROM internal_links
            GROUP BY from_wp_id
        """).fetchall()
        posts_con_un_link = sum(1 for r in rows if r["cnt"] == 1)
        posts_con_multiple_links = sum(1 for r in rows if r["cnt"] >= 2)

        print(json.dumps({
            "ok": True,
            "stats": {
                "total_posts": total_posts,
                "total_internal_links": total_links,
                "posts_sin_ningun_link": posts_sin_links,
                "posts_con_un_solo_link": posts_con_un_link,
                "posts_correctamente_enlazados": posts_con_multiple_links,
            }
        }))

    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}), file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()


def cmd_get_post_content(args):
    """Obtiene el contenido HTML de un post de WordPress."""
    env_path = PROJECT_ROOT / ".env"
    wp_base_url, auth_header = get_wp_config(str(env_path))
    try:
        post = wp_get(f"posts/{args.wp_id}?context=edit", wp_base_url, auth_header)
        content = post.get("content", {}).get("raw", "")
        title = post.get("title", {}).get("rendered", "")
        print(json.dumps({
            "ok": True,
            "wp_id": str(args.wp_id),
            "title": title,
            "content": content
        }, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}), file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Gestión de internal links para Optim Pixel")
    parser.add_argument("--env", default=".env", help="Ruta al archivo .env")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Inicializa la base de datos")

    p_find = sub.add_parser("find-related", help="Busca posts relacionados por scoring de similitud")
    p_find.add_argument("--wp-id", type=int, required=True)
    p_find.add_argument("--tags", type=str, required=True, help="Tags con tipo: 'plataforma:Nintendo,genero:RPG,saga:Final Fantasy'")
    p_find.add_argument("--limit", type=int, default=5)

    p_log = sub.add_parser("log-link", help="Registra un internal link creado")
    p_log.add_argument("--from-wp-id", type=int, required=True)
    p_log.add_argument("--to-wp-id", type=int, required=True)
    p_log.add_argument("--score", type=int, default=0)

    p_needs = sub.add_parser("needs-links", help="Lista posts con menos de 2 outgoing links")
    p_needs.add_argument("--limit", type=int, default=20)

    p_get = sub.add_parser("get-post-content", help="Obtiene el contenido HTML de un post")
    p_get.add_argument("--wp-id", type=int, required=True, help="ID de WordPress del post")

    sub.add_parser("stats", help="Estadísticas generales de internal linking")

    args = parser.parse_args()
    {
        "init":            cmd_init,
        "find-related":    cmd_find_related,
        "log-link":        cmd_log_link,
        "needs-links":     cmd_needs_links,
        "get-post-content": cmd_get_post_content,
        "stats":           cmd_stats,
    }[args.command](args)


if __name__ == "__main__":
    main()
