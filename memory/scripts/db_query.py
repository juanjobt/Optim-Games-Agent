#!/usr/bin/env python3
"""
db_query.py — Interfaz de consultas para la base de datos del blog Optim Pixel.

Subcomandos:

  # Post Ideas
  db_query.py get-pending-ideas [--limit N] [--tipo Review|Historias|Listas]
  db_query.py get-idea --id N
  db_query.py get-idea --title "Título exacto"
  db_query.py add-idea --title "..." --sistema "..." --tipo Review --angulo "..." [--modo editorial] [--justificacion "..."] [--keyword "..."] [--factor "..."] [--genero "..."] [--epoca "..."]
  db_query.py update-idea-state --id N --state pendiente|en_uso|publicado [--wp-id N]

  # Tags
  db_query.py get-tags-by-group --group <group_slug>
  db_query.py get-tag --name "Nombre exacto"
  db_query.py get-tag --wp-id N
  db_query.py get-or-create-tag --name "Nombre exacto" --group <group_slug> [--wp-id N]
  db_query.py add-tag --name "..." --slug "..." --group <group_slug> --wp-id N

  # Posts
  db_query.py get-post --wp-id N
  db_query.py get-post --slug "slug-del-post"
  db_query.py add-post --wp-id N --title "..." --slug "..." --category-slug reviews [--published-at "2026-04-18"]
  db_query.py add-post-tags --wp-id N --tag-ids 12,34,56
  db_query.py update-post --wp-id N [--title "..."] [--slug "..."] [--category-slug "..."] [--status "..."]
  db_query.py list-posts [--category reviews|historias|listas] [--limit 20] [--search "keyword"]

  # Internal Links
  db_query.py get-links --wp-id N
  db_query.py add-link --from N --to N --score N
  db_query.py link-stats

  # General
  db_query.py search "keyword"
  db_query.py stats

Todos los comandos devuelven JSON.
"""

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
DB_PATH = PROJECT_ROOT / "memory" / "blog.db"

VALID_TYPES = ("Review", "Historias", "Listas")
VALID_STATES = ("pendiente", "en_uso", "publicado")
VALID_MODES = ("editorial", "seo_master")
VALID_CATEGORIES = ("reviews", "historias", "listas")


def get_conn():
    if not DB_PATH.exists():
        print(json.dumps({"ok": False, "error": f"Base de datos no encontrada: {DB_PATH}. Ejecuta db_init.py init primero."}), file=sys.stderr)
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


# ============================================================
# POST IDEAS
# ============================================================

def cmd_get_pending_ideas(args):
    conn = get_conn()
    try:
        query = "SELECT * FROM post_ideas WHERE estado = ?"
        params = ["pendiente"]
        if args.tipo:
            query += " AND tipo = ?"
            params.append(args.tipo)
        query += " ORDER BY created_at ASC"
        if args.limit:
            query += f" LIMIT {int(args.limit)}"
        rows = conn.execute(query, params).fetchall()
        out({"ok": True, "ideas": rows_to_list(rows), "count": len(rows)})
    except Exception as e:
        out({"ok": False, "error": str(e)})
    finally:
        conn.close()


def cmd_get_idea(args):
    conn = get_conn()
    try:
        if args.id:
            row = conn.execute("SELECT * FROM post_ideas WHERE id = ?", (int(args.id),)).fetchone()
        elif args.title:
            row = conn.execute("SELECT * FROM post_ideas WHERE title = ?", (args.title,)).fetchone()
        else:
            out({"ok": False, "error": "Se requiere --id o --title"})
            return
        if row:
            out({"ok": True, "idea": row_to_dict(row)})
        else:
            out({"ok": False, "error": "Idea no encontrada"})
    except Exception as e:
        out({"ok": False, "error": str(e)})
    finally:
        conn.close()


def cmd_add_idea(args):
    conn = get_conn()
    try:
        if args.tipo not in VALID_TYPES:
            out({"ok": False, "error": f"Tipo invalido: {args.tipo}. Validos: {VALID_TYPES}"})
            return
        if args.modo and args.modo not in VALID_MODES:
            out({"ok": False, "error": f"Modo invalido: {args.modo}. Validos: {VALID_MODES}"})
            return

        existing = conn.execute("SELECT id FROM post_ideas WHERE title = ?", (args.title,)).fetchone()
        if existing:
            out({"ok": False, "error": f"Ya existe una idea con el titulo '{args.title}' (id={existing['id']})"})
            return

        now = datetime.now(timezone.utc).isoformat()
        cursor = conn.execute(
            """INSERT INTO post_ideas (title, sistema, tipo, estado, modo, angulo_editorial, justificacion, keyword_sugerida, factor_oportunidad, genero, epoca, created_at, updated_at)
               VALUES (?, ?, ?, 'pendiente', ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                args.title,
                args.sistema,
                args.tipo,
                args.modo or "editorial",
                args.angulo or "",
                args.justificacion or None,
                args.keyword or None,
                args.factor or None,
                args.genero or None,
                args.epoca or None,
                now,
                now,
            ),
        )
        conn.commit()
        idea_id = cursor.lastrowid
        row = conn.execute("SELECT * FROM post_ideas WHERE id = ?", (idea_id,)).fetchone()
        out({"ok": True, "idea": row_to_dict(row)})
    except Exception as e:
        conn.rollback()
        out({"ok": False, "error": str(e)})
    finally:
        conn.close()


def cmd_update_idea_state(args):
    conn = get_conn()
    try:
        if args.state not in VALID_STATES:
            out({"ok": False, "error": f"Estado invalido: {args.state}. Validos: {VALID_STATES}"})
            return

        now = datetime.now(timezone.utc).isoformat()
        sets = ["estado = ?", "updated_at = ?"]
        params = [args.state, now]

        if args.wp_id is not None:
            sets.append("post_wp_id = ?")
            params.append(int(args.wp_id))

        if args.state == "publicado" and args.wp_id is None:
            row = conn.execute("SELECT post_wp_id FROM post_ideas WHERE id = ?", (int(args.id),)).fetchone()
            if row and row["post_wp_id"] is None:
                out({"ok": False, "error": "Se requiere --wp-id para cambiar estado a 'publicado'"})
                return

        params.append(int(args.id))
        conn.execute(f"UPDATE post_ideas SET {', '.join(sets)} WHERE id = ?", params)
        conn.commit()
        row = conn.execute("SELECT * FROM post_ideas WHERE id = ?", (int(args.id),)).fetchone()
        if row:
            out({"ok": True, "idea": row_to_dict(row)})
        else:
            out({"ok": False, "error": f"Idea {args.id} no encontrada"})
    except Exception as e:
        conn.rollback()
        out({"ok": False, "error": str(e)})
    finally:
        conn.close()


# ============================================================
# TAGS
# ============================================================

def cmd_get_tags_by_group(args):
    conn = get_conn()
    try:
        group_row = conn.execute("SELECT id, slug, name FROM tag_groups WHERE slug = ?", (args.group,)).fetchone()
        if not group_row:
            out({"ok": False, "error": f"Grupo '{args.group}' no encontrado. Grupos disponibles: consulta sin --group para ver todos."})
            return
        rows = conn.execute(
            "SELECT t.wp_id, t.name, t.slug, t.group_id, tg.slug as group_slug, tg.name as group_name FROM tags t JOIN tag_groups tg ON t.group_id = tg.id WHERE t.group_id = ? ORDER BY t.name",
            (group_row["id"],),
        ).fetchall()
        out({"ok": True, "group": row_to_dict(group_row), "tags": rows_to_list(rows), "count": len(rows)})
    except Exception as e:
        out({"ok": False, "error": str(e)})
    finally:
        conn.close()


def cmd_get_tag(args):
    conn = get_conn()
    try:
        if args.name:
            row = conn.execute("SELECT t.wp_id, t.name, t.slug, t.group_id, tg.slug as group_slug, tg.name as group_name FROM tags t JOIN tag_groups tg ON t.group_id = tg.id WHERE t.name = ?", (args.name,)).fetchone()
        elif args.wp_id is not None:
            row = conn.execute("SELECT t.wp_id, t.name, t.slug, t.group_id, tg.slug as group_slug, tg.name as group_name FROM tags t JOIN tag_groups tg ON t.group_id = tg.id WHERE t.wp_id = ?", (int(args.wp_id),)).fetchone()
        else:
            out({"ok": False, "error": "Se requiere --name o --wp-id"})
            return
        if row:
            out({"ok": True, "tag": row_to_dict(row)})
        else:
            out({"ok": False, "error": "Tag no encontrado"})
    except Exception as e:
        out({"ok": False, "error": str(e)})
    finally:
        conn.close()


def cmd_add_tag(args):
    conn = get_conn()
    try:
        group_row = conn.execute("SELECT id FROM tag_groups WHERE slug = ?", (args.group,)).fetchone()
        if not group_row:
            out({"ok": False, "error": f"Grupo '{args.group}' no encontrado"})
            return

        existing = conn.execute("SELECT wp_id FROM tags WHERE name = ?", (args.name,)).fetchone()
        if existing:
            out({"ok": False, "error": f"Tag '{args.name}' ya existe con wp_id={existing['wp_id']}"})
            return

        now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        conn.execute(
            "INSERT INTO tags (wp_id, name, slug, group_id, created_at) VALUES (?, ?, ?, ?, ?)",
            (args.wp_id, args.name, args.slug, group_row["id"], now),
        )
        conn.commit()
        row = conn.execute("SELECT t.wp_id, t.name, t.slug, t.group_id, tg.slug as group_slug FROM tags t JOIN tag_groups tg ON t.group_id = tg.id WHERE t.name = ?", (args.name,)).fetchone()
        out({"ok": True, "tag": row_to_dict(row)})
    except Exception as e:
        conn.rollback()
        out({"ok": False, "error": str(e)})
    finally:
        conn.close()


def cmd_get_or_create_tag(args):
    conn = get_conn()
    try:
        group_row = conn.execute("SELECT id FROM tag_groups WHERE slug = ?", (args.group,)).fetchone()
        if not group_row:
            out({"ok": False, "error": f"Grupo '{args.group}' no encontrado"})
            return

        row = conn.execute("SELECT t.wp_id, t.name, t.slug, t.group_id, tg.slug as group_slug, tg.name as group_name FROM tags t JOIN tag_groups tg ON t.group_id = tg.id WHERE t.name = ?", (args.name,)).fetchone()
        if row:
            out({"ok": True, "tag": row_to_dict(row), "created": False})
            return

        slug = args.slug or args.name.lower().replace(" ", "-")
        wp_id = args.wp_id
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        cursor = conn.execute(
            "INSERT INTO tags (wp_id, name, slug, group_id, created_at) VALUES (?, ?, ?, ?, ?)",
            (wp_id, args.name, slug, group_row["id"], now),
        )
        conn.commit()
        new_row = conn.execute("SELECT t.wp_id, t.name, t.slug, t.group_id, tg.slug as group_slug, tg.name as group_name FROM tags t JOIN tag_groups tg ON t.group_id = tg.id WHERE t.name = ?", (args.name,)).fetchone()
        out({"ok": True, "tag": row_to_dict(new_row), "created": True})
    except Exception as e:
        conn.rollback()
        out({"ok": False, "error": str(e)})
    finally:
        conn.close()


# ============================================================
# POSTS
# ============================================================

def cmd_get_post(args):
    conn = get_conn()
    try:
        if args.wp_id is not None:
            row = conn.execute("SELECT * FROM posts WHERE wp_id = ?", (int(args.wp_id),)).fetchone()
        elif args.slug:
            row = conn.execute("SELECT * FROM posts WHERE slug = ?", (args.slug,)).fetchone()
        else:
            out({"ok": False, "error": "Se requiere --wp-id o --slug"})
            return
        if row:
            out({"ok": True, "post": row_to_dict(row)})
        else:
            out({"ok": False, "error": "Post no encontrado"})
    except Exception as e:
        out({"ok": False, "error": str(e)})
    finally:
        conn.close()


def cmd_add_post(args):
    conn = get_conn()
    try:
        if args.category_slug not in VALID_CATEGORIES:
            out({"ok": False, "error": f"Categoria invalida: {args.category_slug}. Validas: {VALID_CATEGORIES}"})
            return

        existing = conn.execute("SELECT wp_id FROM posts WHERE wp_id = ?", (int(args.wp_id),)).fetchone()
        if existing:
            out({"ok": False, "error": f"Post con wp_id={args.wp_id} ya existe"})
            return

        existing_slug = conn.execute("SELECT wp_id FROM posts WHERE slug = ?", (args.slug,)).fetchone()
        if existing_slug:
            out({"ok": False, "error": f"Post con slug '{args.slug}' ya existe (wp_id={existing_slug['wp_id']})"})
            return

        now = datetime.now(timezone.utc).isoformat()
        cursor = conn.execute(
            """INSERT INTO posts (wp_id, title, slug, category_slug, status, published_at, created_at, updated_at)
               VALUES (?, ?, ?, ?, 'publish', ?, ?, ?)""",
            (int(args.wp_id), args.title, args.slug, args.category_slug, args.published_at or now, now, now),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM posts WHERE wp_id = ?", (int(args.wp_id),)).fetchone()
        out({"ok": True, "post": row_to_dict(row)})
    except Exception as e:
        conn.rollback()
        out({"ok": False, "error": str(e)})
    finally:
        conn.close()


def cmd_add_post_tags(args):
    conn = get_conn()
    try:
        post_wp_id = int(args.wp_id)
        tag_ids = [int(t.strip()) for t in args.tag_ids.split(",") if t.strip()]

        if not tag_ids:
            out({"ok": False, "error": "No se proporcionaron tag_ids. Usa formato: 12,34,56"})
            return

        post_exists = conn.execute("SELECT wp_id FROM posts WHERE wp_id = ?", (post_wp_id,)).fetchone()
        if not post_exists:
            out({"ok": False, "error": f"Post con wp_id={post_wp_id} no encontrado en la DB"})
            return

        inserted = 0
        skipped = 0
        not_found = []
        for tag_wp_id in tag_ids:
            tag_exists = conn.execute("SELECT wp_id FROM tags WHERE wp_id = ?", (tag_wp_id,)).fetchone()
            if not tag_exists:
                not_found.append(tag_wp_id)
                continue
            try:
                conn.execute(
                    "INSERT INTO post_tags (post_wp_id, tag_wp_id) VALUES (?, ?)",
                    (post_wp_id, tag_wp_id),
                )
                inserted += 1
            except sqlite3.IntegrityError:
                skipped += 1

        conn.commit()
        result = {"ok": True, "post_wp_id": post_wp_id, "inserted": inserted, "skipped_duplicates": skipped}
        if not_found:
            result["warning"] = f"Tags no encontrados en la DB: {not_found}"
        out(result)
    except Exception as e:
        conn.rollback()
        out({"ok": False, "error": str(e)})
    finally:
        conn.close()


def cmd_update_post(args):
    conn = get_conn()
    try:
        sets = []
        params = []
        for field, arg_name in [("title", "title"), ("slug", "slug"), ("category_slug", "category_slug"), ("status", "status")]:
            val = getattr(args, arg_name, None)
            if val is not None:
                sets.append(f"{field} = ?")
                params.append(val)
        if not sets:
            out({"ok": False, "error": "No hay campos para actualizar. Usa --title, --slug, --category-slug o --status"})
            return
        sets.append("updated_at = ?")
        params.append(datetime.now(timezone.utc).isoformat())
        params.append(int(args.wp_id))
        conn.execute(f"UPDATE posts SET {', '.join(sets)} WHERE wp_id = ?", params)
        conn.commit()
        row = conn.execute("SELECT * FROM posts WHERE wp_id = ?", (int(args.wp_id),)).fetchone()
        if row:
            out({"ok": True, "post": row_to_dict(row)})
        else:
            out({"ok": False, "error": f"Post wp_id={args.wp_id} no encontrado"})
    except Exception as e:
        conn.rollback()
        out({"ok": False, "error": str(e)})
    finally:
        conn.close()


def cmd_list_posts(args):
    conn = get_conn()
    try:
        query = "SELECT * FROM posts WHERE 1=1"
        params = []
        if args.category:
            if args.category not in VALID_CATEGORIES:
                out({"ok": False, "error": f"Categoria invalida: {args.category}. Validas: {VALID_CATEGORIES}"})
                return
            query += " AND category_slug = ?"
            params.append(args.category)
        if args.search:
            query += " AND (title LIKE ? OR slug LIKE ?)"
            params.extend([f"%{args.search}%", f"%{args.search}%"])
        query += " ORDER BY published_at DESC"
        if args.limit:
            query += f" LIMIT {int(args.limit)}"
        rows = conn.execute(query, params).fetchall()
        out({"ok": True, "posts": rows_to_list(rows), "count": len(rows)})
    except Exception as e:
        out({"ok": False, "error": str(e)})
    finally:
        conn.close()


# ============================================================
# INTERNAL LINKS
# ============================================================

def cmd_get_links(args):
    conn = get_conn()
    try:
        outgoing = conn.execute(
            "SELECT * FROM internal_links WHERE from_wp_id = ? ORDER BY created_at DESC",
            (int(args.wp_id),),
        ).fetchall()
        incoming = conn.execute(
            "SELECT * FROM internal_links WHERE to_wp_id = ? ORDER BY created_at DESC",
            (int(args.wp_id),),
        ).fetchall()
        out({
            "ok": True,
            "wp_id": int(args.wp_id),
            "outgoing": rows_to_list(outgoing),
            "incoming": rows_to_list(incoming),
            "outgoing_count": len(outgoing),
            "incoming_count": len(incoming),
        })
    except Exception as e:
        out({"ok": False, "error": str(e)})
    finally:
        conn.close()


def cmd_add_link(args):
    conn = get_conn()
    try:
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            """INSERT INTO internal_links (from_wp_id, to_wp_id, score, created_at)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(from_wp_id, to_wp_id) DO UPDATE SET score=excluded.score, created_at=excluded.created_at""",
            (int(args.from_wp_id), int(args.to_wp_id), int(args.score), now),
        )
        conn.commit()
        out({"ok": True, "from_wp_id": int(args.from_wp_id), "to_wp_id": int(args.to_wp_id), "score": int(args.score)})
    except Exception as e:
        conn.rollback()
        out({"ok": False, "error": str(e)})
    finally:
        conn.close()


def cmd_link_stats(args):
    conn = get_conn()
    try:
        total_links = conn.execute("SELECT COUNT(*) FROM internal_links").fetchone()[0]
        distinct_from = conn.execute("SELECT COUNT(DISTINCT from_wp_id) FROM internal_links").fetchone()[0]
        distinct_to = conn.execute("SELECT COUNT(DISTINCT to_wp_id) FROM internal_links").fetchone()[0]
        total_posts = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
        posts_with_links = conn.execute("SELECT DISTINCT from_wp_id FROM internal_links").fetchall()
        posts_with_links_count = len(posts_with_links)
        posts_without_links = total_posts - posts_with_links_count if total_posts > 0 else 0

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
                "distinct_from": distinct_from,
                "distinct_to": distinct_to,
                "posts_with_outgoing_links": posts_with_links_count,
                "posts_without_outgoing_links": posts_without_links,
                "posts_with_one_link": one_link,
                "posts_with_multiple_links": multiple_links,
            },
        })
    except Exception as e:
        out({"ok": False, "error": str(e)})
    finally:
        conn.close()


# ============================================================
# GENERAL
# ============================================================

def cmd_search(args):
    conn = get_conn()
    try:
        term = f"%{args.keyword}%"
        tags = conn.execute(
            "SELECT t.wp_id, t.name, t.slug, tg.slug as group_slug, tg.name as group_name FROM tags t JOIN tag_groups tg ON t.group_id = tg.id WHERE t.name LIKE ? OR t.slug LIKE ?",
            (term, term),
        ).fetchall()
        posts = conn.execute(
            "SELECT * FROM posts WHERE title LIKE ? OR slug LIKE ?",
            (term, term),
        ).fetchall()
        ideas = conn.execute(
            "SELECT * FROM post_ideas WHERE title LIKE ? OR angulo_editorial LIKE ? OR justificacion LIKE ?",
            (term, term, term),
        ).fetchall()
        out({
            "ok": True,
            "search": args.keyword,
            "tags": rows_to_list(tags),
            "tags_count": len(tags),
            "posts": rows_to_list(posts),
            "posts_count": len(posts),
            "ideas": rows_to_list(ideas),
            "ideas_count": len(ideas),
        })
    except Exception as e:
        out({"ok": False, "error": str(e)})
    finally:
        conn.close()


def cmd_stats(args):
    conn = get_conn()
    try:
        counts = {}
        for table in ["tag_groups", "tags", "posts", "post_tags", "post_ideas", "internal_links"]:
            counts[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

        ideas_by_state = {}
        for row in conn.execute("SELECT estado, COUNT(*) as cnt FROM post_ideas GROUP BY estado").fetchall():
            ideas_by_state[row["estado"]] = row["cnt"]

        ideas_by_tipo = {}
        for row in conn.execute("SELECT tipo, COUNT(*) as cnt FROM post_ideas GROUP BY tipo").fetchall():
            ideas_by_tipo[row["tipo"]] = row["cnt"]

        posts_by_category = {}
        for row in conn.execute("SELECT category_slug, COUNT(*) as cnt FROM posts GROUP BY category_slug").fetchall():
            posts_by_category[row["category_slug"]] = row["cnt"]

        tags_by_group = {}
        for row in conn.execute("SELECT tg.name as group_name, tg.slug as group_slug, COUNT(t.wp_id) as cnt FROM tag_groups tg LEFT JOIN tags t ON tg.id = t.group_id GROUP BY tg.id ORDER BY tg.id").fetchall():
            tags_by_group[row["group_slug"]] = {"name": row["group_name"], "count": row["cnt"]}

        out({
            "ok": True,
            "counts": counts,
            "ideas_by_state": ideas_by_state,
            "ideas_by_tipo": ideas_by_tipo,
            "posts_by_category": posts_by_category,
            "tags_by_group": tags_by_group,
        })
    except Exception as e:
        out({"ok": False, "error": str(e)})
    finally:
        conn.close()


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Consultas sobre la base de datos del blog Optim Pixel")
    sub = parser.add_subparsers(dest="command", required=True)

    # -- Post Ideas --
    p_pending = sub.add_parser("get-pending-ideas", help="Lista ideas en estado pendiente")
    p_pending.add_argument("--limit", type=int, default=None)
    p_pending.add_argument("--tipo", choices=list(VALID_TYPES), default=None)

    p_get_idea = sub.add_parser("get-idea", help="Obtiene una idea por ID o titulo")
    p_get_idea.add_argument("--id", type=int, default=None)
    p_get_idea.add_argument("--title", type=str, default=None)

    p_add_idea = sub.add_parser("add-idea", help="Crea una nueva idea")
    p_add_idea.add_argument("--title", type=str, required=True)
    p_add_idea.add_argument("--sistema", type=str, required=True)
    p_add_idea.add_argument("--tipo", type=str, required=True, choices=list(VALID_TYPES))
    p_add_idea.add_argument("--modo", type=str, default=None, choices=list(VALID_MODES))
    p_add_idea.add_argument("--angulo", type=str, default=None)
    p_add_idea.add_argument("--justificacion", type=str, default=None)
    p_add_idea.add_argument("--keyword", type=str, default=None)
    p_add_idea.add_argument("--factor", type=str, default=None)
    p_add_idea.add_argument("--genero", type=str, default=None)
    p_add_idea.add_argument("--epoca", type=str, default=None)

    p_update_idea = sub.add_parser("update-idea-state", help="Actualiza el estado de una idea")
    p_update_idea.add_argument("--id", type=int, required=True)
    p_update_idea.add_argument("--state", type=str, required=True, choices=list(VALID_STATES))
    p_update_idea.add_argument("--wp-id", type=int, default=None)

    # -- Tags --
    p_tags_group = sub.add_parser("get-tags-by-group", help="Lista tags de un grupo")
    p_tags_group.add_argument("--group", type=str, required=True)

    p_get_tag = sub.add_parser("get-tag", help="Obtiene un tag por nombre o wp_id")
    p_get_tag.add_argument("--name", type=str, default=None)
    p_get_tag.add_argument("--wp-id", type=int, default=None)

    p_add_tag = sub.add_parser("add-tag", help="Crea un nuevo tag")
    p_add_tag.add_argument("--name", type=str, required=True)
    p_add_tag.add_argument("--slug", type=str, required=True)
    p_add_tag.add_argument("--group", type=str, required=True)
    p_add_tag.add_argument("--wp-id", type=int, required=True)

    p_get_or_create = sub.add_parser("get-or-create-tag", help="Obtiene un tag o lo crea si no existe")
    p_get_or_create.add_argument("--name", type=str, required=True)
    p_get_or_create.add_argument("--group", type=str, required=True)
    p_get_or_create.add_argument("--wp-id", type=int, default=None)
    p_get_or_create.add_argument("--slug", type=str, default=None)

    # -- Posts --
    p_get_post = sub.add_parser("get-post", help="Obtiene un post por wp_id o slug")
    p_get_post.add_argument("--wp-id", type=int, default=None)
    p_get_post.add_argument("--slug", type=str, default=None)

    p_add_post = sub.add_parser("add-post", help="Registra un post publicado")
    p_add_post.add_argument("--wp-id", type=int, required=True)
    p_add_post.add_argument("--title", type=str, required=True)
    p_add_post.add_argument("--slug", type=str, required=True)
    p_add_post.add_argument("--category-slug", type=str, required=True, choices=list(VALID_CATEGORIES))
    p_add_post.add_argument("--published-at", type=str, default=None)

    p_add_post_tags = sub.add_parser("add-post-tags", help="Registra relaciones post-tags en lotes")
    p_add_post_tags.add_argument("--wp-id", type=int, required=True, help="wp_id del post")
    p_add_post_tags.add_argument("--tag-ids", type=str, required=True, help="IDs de tags separados por coma (ej: 12,34,56)")

    p_update_post = sub.add_parser("update-post", help="Actualiza campos de un post")
    p_update_post.add_argument("--wp-id", type=int, required=True)
    p_update_post.add_argument("--title", type=str, default=None)
    p_update_post.add_argument("--slug", type=str, default=None)
    p_update_post.add_argument("--category-slug", type=str, default=None, choices=list(VALID_CATEGORIES))
    p_update_post.add_argument("--status", type=str, default=None)

    p_list_posts = sub.add_parser("list-posts", help="Lista posts con filtros opcionales")
    p_list_posts.add_argument("--category", type=str, default=None, choices=list(VALID_CATEGORIES))
    p_list_posts.add_argument("--limit", type=int, default=20)
    p_list_posts.add_argument("--search", type=str, default=None)

    # -- Internal Links --
    p_links = sub.add_parser("get-links", help="Obtiene enlaces salientes y entrantes de un post")
    p_links.add_argument("--wp-id", type=int, required=True)

    p_add_link = sub.add_parser("add-link", help="Registra un internal link")
    p_add_link.add_argument("--from", dest="from_wp_id", type=int, required=True)
    p_add_link.add_argument("--to", dest="to_wp_id", type=int, required=True)
    p_add_link.add_argument("--score", type=int, required=True)

    sub.add_parser("link-stats", help="Estadisticas de internal linking")

    # -- General --
    p_search = sub.add_parser("search", help="Busca en tags, posts e ideas")
    p_search.add_argument("keyword", type=str)

    sub.add_parser("stats", help="Estadisticas generales de la base de datos")

    args = parser.parse_args()

    commands = {
        "get-pending-ideas": cmd_get_pending_ideas,
        "get-idea": cmd_get_idea,
        "add-idea": cmd_add_idea,
        "update-idea-state": cmd_update_idea_state,
        "get-tags-by-group": cmd_get_tags_by_group,
        "get-tag": cmd_get_tag,
        "add-tag": cmd_add_tag,
        "get-or-create-tag": cmd_get_or_create_tag,
        "get-post": cmd_get_post,
        "add-post": cmd_add_post,
        "add-post-tags": cmd_add_post_tags,
        "update-post": cmd_update_post,
        "list-posts": cmd_list_posts,
        "get-links": cmd_get_links,
        "add-link": cmd_add_link,
        "link-stats": cmd_link_stats,
        "search": cmd_search,
        "stats": cmd_stats,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()