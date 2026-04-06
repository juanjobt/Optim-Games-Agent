#!/usr/bin/env python3
"""
manage-internal-links.py
Gestiona la base de datos de internal linking para Optim Pixel.

Uso:
  python manage-internal-links.py init
  python manage-internal-links.py register --wp-id 42 --title "Título" --url "https://..." --tipo "Historias" --plataforma "Super Nintendo" --genero "RPG" --saga "Final Fantasy" --desarrolladora "Square" --epoca "Años 90" --tags "tag1,tag2,tag3"
  python manage-internal-links.py find-related --wp-id 42 --plataforma "Super Nintendo" --genero "RPG" --saga "Final Fantasy" --tags "tag1,tag2,tag3" --limit 5
  python manage-internal-links.py log-link --from-wp-id 42 --to-wp-id 17 --score 7
  python manage-internal-links.py needs-links --limit 10
  python manage-internal-links.py stats

Requiere en .env:
  WP_BASE_URL=https://games.optimbyte.com
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


def wp_post(endpoint, data, wp_base_url, auth_header):
    """POST a la WP REST API. Devuelve el JSON parseado."""
    url = f"{wp_base_url}/wp-json/wp/v2/{endpoint}"
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        url, data=body,
        headers={"Authorization": auth_header, "Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
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
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS posts (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            wp_post_id     TEXT    NOT NULL UNIQUE,
            title          TEXT    NOT NULL,
            url            TEXT    NOT NULL,
            tipo           TEXT,
            plataforma     TEXT,
            genero         TEXT,
            saga           TEXT,
            desarrolladora TEXT,
            epoca          TEXT,
            created_at     TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS tags (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre  TEXT    NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS post_tags (
            post_id  INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
            tag_id   INTEGER NOT NULL REFERENCES tags(id)  ON DELETE CASCADE,
            PRIMARY KEY (post_id, tag_id)
        );

        CREATE TABLE IF NOT EXISTS internal_links (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            from_post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
            to_post_id   INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
            score        INTEGER NOT NULL DEFAULT 0,
            created_at   TEXT    NOT NULL,
            UNIQUE (from_post_id, to_post_id)
        );

        CREATE INDEX IF NOT EXISTS idx_posts_wp_id      ON posts(wp_post_id);
        CREATE INDEX IF NOT EXISTS idx_posts_saga       ON posts(saga);
        CREATE INDEX IF NOT EXISTS idx_posts_plataforma ON posts(plataforma);
        CREATE INDEX IF NOT EXISTS idx_posts_genero     ON posts(genero);
        CREATE INDEX IF NOT EXISTS idx_post_tags_post   ON post_tags(post_id);
        CREATE INDEX IF NOT EXISTS idx_post_tags_tag    ON post_tags(tag_id);
    """)
    conn.commit()
    conn.close()
    print(json.dumps({"ok": True, "message": "Base de datos inicializada correctamente", "path": str(DB_PATH)}))


def cmd_register(args):
    conn = get_conn()
    now = datetime.now(timezone.utc).isoformat()

    try:
        cur = conn.execute(
            """
            INSERT INTO posts (wp_post_id, title, url, tipo, plataforma, genero, saga, desarrolladora, epoca, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(wp_post_id) DO UPDATE SET
                title=excluded.title, url=excluded.url, tipo=excluded.tipo,
                plataforma=excluded.plataforma, genero=excluded.genero,
                saga=excluded.saga, desarrolladora=excluded.desarrolladora,
                epoca=excluded.epoca
            """,
            (args.wp_id, args.title, args.url, args.tipo,
             args.plataforma, args.genero, args.saga,
             args.desarrolladora, args.epoca, now)
        )
        post_id = cur.lastrowid
        if post_id == 0:
            row = conn.execute("SELECT id FROM posts WHERE wp_post_id = ?", (args.wp_id,)).fetchone()
            post_id = row["id"]

        if args.tags:
            raw_tags = [t.strip() for t in args.tags.split(",") if t.strip()]
            for tag_nombre in raw_tags:
                conn.execute("INSERT OR IGNORE INTO tags (nombre) VALUES (?)", (tag_nombre,))
                tag_row = conn.execute("SELECT id FROM tags WHERE nombre = ?", (tag_nombre,)).fetchone()
                conn.execute(
                    "INSERT OR IGNORE INTO post_tags (post_id, tag_id) VALUES (?, ?)",
                    (post_id, tag_row["id"])
                )

        conn.commit()
        print(json.dumps({"ok": True, "post_id": post_id, "wp_post_id": args.wp_id, "title": args.title}))

    except Exception as e:
        conn.rollback()
        print(json.dumps({"ok": False, "error": str(e)}), file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()


def cmd_find_related(args):
    conn = get_conn()

    current_row = conn.execute("SELECT id FROM posts WHERE wp_post_id = ?", (str(args.wp_id),)).fetchone()
    if not current_row:
        print(json.dumps({"ok": False, "error": f"Post con wp_post_id={args.wp_id} no encontrado en la base de datos"}), file=sys.stderr)
        sys.exit(1)

    current_id = current_row["id"]
    input_tags = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else []

    tag_ids = []
    for tag_nombre in input_tags:
        row = conn.execute("SELECT id FROM tags WHERE nombre = ?", (tag_nombre,)).fetchone()
        if row:
            tag_ids.append(row["id"])

    tag_ids_placeholder = ",".join("?" * len(tag_ids)) if tag_ids else "NULL"
    tag_filter = f"AND pt2.tag_id IN ({tag_ids_placeholder})" if tag_ids else "AND 1=0"

    query = f"""
        SELECT
            p.id, p.wp_post_id, p.title, p.url,
            p.tipo, p.plataforma, p.genero, p.saga, p.desarrolladora, p.epoca,
            (
                CASE WHEN p.saga IS NOT NULL AND p.saga != '' AND p.saga = ? THEN 3 ELSE 0 END +
                CASE WHEN p.plataforma IS NOT NULL AND p.plataforma = ? THEN 2 ELSE 0 END +
                CASE WHEN p.genero IS NOT NULL AND p.genero = ? THEN 1 ELSE 0 END +
                CASE WHEN p.desarrolladora IS NOT NULL AND p.desarrolladora = ? THEN 1 ELSE 0 END +
                CASE WHEN p.epoca IS NOT NULL AND p.epoca = ? THEN 1 ELSE 0 END +
                COALESCE((
                    SELECT COUNT(DISTINCT pt2.tag_id)
                    FROM post_tags pt2
                    WHERE pt2.post_id = p.id {tag_filter}
                ), 0)
            ) AS score
        FROM posts p
        WHERE p.id != ?
        ORDER BY score DESC, p.created_at DESC
        LIMIT ?
    """

    params = [args.saga or "", args.plataforma or "", args.genero or "",
              args.desarrolladora or "", args.epoca or ""]
    if tag_ids:
        params.extend(tag_ids)
    params.extend([current_id, args.limit])

    rows = conn.execute(query, params).fetchall()
    conn.close()

    print(json.dumps({"ok": True, "related": [dict(r) for r in rows]}, ensure_ascii=False))


def cmd_log_link(args):
    conn = get_conn()
    now = datetime.now(timezone.utc).isoformat()

    try:
        from_row = conn.execute("SELECT id FROM posts WHERE wp_post_id = ?", (str(args.from_wp_id),)).fetchone()
        to_row   = conn.execute("SELECT id FROM posts WHERE wp_post_id = ?", (str(args.to_wp_id),)).fetchone()

        if not from_row:
            raise ValueError(f"Post origen no encontrado: wp_post_id={args.from_wp_id}")
        if not to_row:
            raise ValueError(f"Post destino no encontrado: wp_post_id={args.to_wp_id}")

        conn.execute(
            """
            INSERT INTO internal_links (from_post_id, to_post_id, score, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(from_post_id, to_post_id) DO UPDATE SET
                score=excluded.score, created_at=excluded.created_at
            """,
            (from_row["id"], to_row["id"], args.score, now)
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
    conn = get_conn()
    rows = conn.execute("""
        SELECT
            p.wp_post_id, p.title, p.url,
            p.tipo, p.plataforma, p.genero, p.saga, p.epoca,
            COUNT(il.id) AS outgoing_links
        FROM posts p
        LEFT JOIN internal_links il ON il.from_post_id = p.id
        GROUP BY p.id
        HAVING outgoing_links < 2
        ORDER BY p.created_at ASC
        LIMIT ?
    """, (args.limit,)).fetchall()
    conn.close()
    results = [dict(r) for r in rows]
    print(json.dumps({"ok": True, "posts_needing_links": results, "count": len(results)}, ensure_ascii=False))


def cmd_stats(args):
    conn = get_conn()
    total_posts       = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    total_tags        = conn.execute("SELECT COUNT(*) FROM tags").fetchone()[0]
    total_links       = conn.execute("SELECT COUNT(*) FROM internal_links").fetchone()[0]
    posts_sin_links   = conn.execute("""
        SELECT COUNT(*) FROM posts p
        LEFT JOIN internal_links il ON il.from_post_id = p.id
        WHERE il.id IS NULL
    """).fetchone()[0]
    posts_con_un_link = conn.execute("""
        SELECT COUNT(*) FROM (
            SELECT p.id FROM posts p
            JOIN internal_links il ON il.from_post_id = p.id
            GROUP BY p.id HAVING COUNT(il.id) = 1
        )
    """).fetchone()[0]
    conn.close()
    print(json.dumps({
        "ok": True,
        "stats": {
            "total_posts": total_posts,
            "total_tags": total_tags,
            "total_internal_links": total_links,
            "posts_sin_ningun_link": posts_sin_links,
            "posts_con_un_solo_link": posts_con_un_link,
            "posts_correctamente_enlazados": total_posts - posts_sin_links - posts_con_un_link,
        }
    }))


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

    p_reg = sub.add_parser("register", help="Registra un post publicado")
    p_reg.add_argument("--wp-id",          type=int, required=True)
    p_reg.add_argument("--title",          required=True)
    p_reg.add_argument("--url",            required=True)
    p_reg.add_argument("--tipo",           default="")
    p_reg.add_argument("--plataforma",     default="")
    p_reg.add_argument("--genero",         default="")
    p_reg.add_argument("--saga",           default="")
    p_reg.add_argument("--desarrolladora", default="")
    p_reg.add_argument("--epoca",          default="")
    p_reg.add_argument("--tags",           default="", help="Tags separados por comas")

    p_find = sub.add_parser("find-related", help="Busca posts relacionados por score")
    p_find.add_argument("--wp-id",          type=int, required=True)
    p_find.add_argument("--plataforma",     default="")
    p_find.add_argument("--genero",         default="")
    p_find.add_argument("--saga",           default="")
    p_find.add_argument("--desarrolladora", default="")
    p_find.add_argument("--epoca",          default="")
    p_find.add_argument("--tags",           default="")
    p_find.add_argument("--limit",          type=int, default=5)

    p_log = sub.add_parser("log-link", help="Registra un internal link creado")
    p_log.add_argument("--from-wp-id", type=int, required=True)
    p_log.add_argument("--to-wp-id",   type=int, required=True)
    p_log.add_argument("--score",      type=int, default=0)

    p_needs = sub.add_parser("needs-links", help="Lista posts con menos de 2 outgoing links")
    p_needs.add_argument("--limit", type=int, default=20)

    p_get = sub.add_parser("get-post-content", help="Obtiene el contenido HTML de un post")
    p_get.add_argument("--wp-id", type=int, required=True, help="ID de WordPress del post")

    sub.add_parser("stats", help="Estadísticas generales de la base de datos")

    args = parser.parse_args()
    {
        "init":            cmd_init,
        "register":        cmd_register,
        "find-related":    cmd_find_related,
        "log-link":        cmd_log_link,
        "needs-links":     cmd_needs_links,
        "get-post-content": cmd_get_post_content,
        "stats":           cmd_stats,
    }[args.command](args)


if __name__ == "__main__":
    main()