#!/usr/bin/env python3
"""
db_init.py — Inicialización y migración de la base de datos del blog Optim Pixel.

Subcomandos:
    python3 memory/scripts/db_init.py init            # Crear tablas y seed de tag_groups
    python3 memory/scripts/db_init.py migrate-tags   # Migrar tags desde tags-usables.md (resuelve wp_ids via WP API)
    python3 memory/scripts/db_init.py migrate-ideas  # Migrar post ideas desde post-ideas.md
    python3 memory/scripts/db_init.py sync-tags-wp    # Sincronizar wp_ids de tags con WordPress
    python3 memory/scripts/db_init.py sync-posts-wp   # Poblar posts y post_tags desde WordPress
"""

import argparse
import base64
import json
import os
import re
import sqlite3
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
DB_PATH = PROJECT_ROOT / "memory" / "blog.db"
TAGS_FILE = PROJECT_ROOT / "memory" / "tags-usables.md"
IDEAS_FILE = PROJECT_ROOT / "memory" / "post-ideas.md"
ENV_PATH = PROJECT_ROOT / ".env"

TAG_GROUPS_SEED = [
    (1, "sistema", "Sistema", 3, "Plataformas y sistemas de juego"),
    (2, "genero", "Género", 2, "Tipos de juego"),
    (3, "epoca", "Época", 1, "Décadas genéricas"),
    (4, "ano", "Año", 1, "Años específicos"),
    (5, "desarrolladora", "Desarrolladora", 1, "Compañías desarrolladoras"),
    (6, "creador", "Creador", 1, "Directores y diseñadores clave"),
    (7, "saga", "Saga", 4, "Series de juegos"),
    (8, "pais", "País", 1, "Origen geográfico"),
    (9, "tecnica", "Técnica", 1, "Tecnologías y motores"),
    (10, "personaje", "Personaje", 1, "Personajes icónicos"),
    (11, "compositor", "Compositor", 1, "Compositores de música"),
]

GROUP_NAME_TO_SLUG = {
    "Sistema": "sistema",
    "Género": "genero",
    "Época": "epoca",
    "Año": "ano",
    "Desarrolladora": "desarrolladora",
    "Creador": "creador",
    "Saga": "saga",
    "País": "pais",
    "Técnica": "tecnica",
    "Personaje": "personaje",
    "Compositor": "compositor",
}

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS tag_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL UNIQUE,
    score_weight INTEGER NOT NULL DEFAULT 1,
    description TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS tags (
    wp_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    slug TEXT NOT NULL UNIQUE,
    group_id INTEGER NOT NULL REFERENCES tag_groups(id),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS posts (
    wp_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    category_slug TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'publish',
    published_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS post_tags (
    post_wp_id INTEGER NOT NULL REFERENCES posts(wp_id),
    tag_wp_id INTEGER NOT NULL REFERENCES tags(wp_id),
    UNIQUE (post_wp_id, tag_wp_id)
);

CREATE TABLE IF NOT EXISTS post_ideas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL UNIQUE,
    sistema TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('Review', 'Historias', 'Listas')),
    estado TEXT NOT NULL DEFAULT 'pendiente' CHECK (estado IN ('pendiente', 'en_uso', 'publicado')),
    modo TEXT NOT NULL DEFAULT 'editorial' CHECK (modo IN ('editorial', 'seo_master')),
    angulo_editorial TEXT NOT NULL,
    justificacion TEXT,
    keyword_sugerida TEXT,
    factor_oportunidad TEXT,
    genero TEXT,
    epoca TEXT,
    post_wp_id INTEGER REFERENCES posts(wp_id),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_tags_group_id ON tags(group_id);
CREATE INDEX IF NOT EXISTS idx_posts_category ON posts(category_slug);
CREATE INDEX IF NOT EXISTS idx_post_ideas_tipo ON post_ideas(tipo);
CREATE INDEX IF NOT EXISTS idx_post_ideas_estado ON post_ideas(estado);

CREATE TABLE IF NOT EXISTS internal_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_wp_id INTEGER NOT NULL REFERENCES posts(wp_id),
    to_wp_id INTEGER NOT NULL REFERENCES posts(wp_id),
    score INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (from_wp_id, to_wp_id)
);

CREATE INDEX IF NOT EXISTS idx_from_wp_id ON internal_links(from_wp_id);
CREATE INDEX IF NOT EXISTS idx_to_wp_id ON internal_links(to_wp_id);
"""


def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def load_env(env_path=None):
    env = {}
    p = Path(env_path) if env_path else ENV_PATH
    try:
        with open(p) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    env[key.strip()] = value.strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    return env


def get_wp_config():
    env = load_env()
    wp_base_url = env.get("WP_BASE_URL") or os.environ.get("WP_BASE_URL")
    wp_user = env.get("WP_USER") or os.environ.get("WP_USER")
    wp_app_password = env.get("WP_APP_PASSWORD") or os.environ.get("WP_APP_PASSWORD")
    if not wp_base_url or not wp_user or not wp_app_password:
        return None, None
    credentials = base64.b64encode(f"{wp_user}:{wp_app_password}".encode()).decode()
    return wp_base_url.rstrip("/"), f"Basic {credentials}"


def wp_api_get(endpoint, wp_base_url, auth_header, params=None):
    query = ""
    if params:
        query = "&".join(f"{k}={v}" for k, v in params.items())
        query = f"?{query}"
    url = f"{wp_base_url}/wp-json/wp/v2/{endpoint}{query}"
    req = urllib.request.Request(url, headers={"Authorization": auth_header})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        raise RuntimeError(f"HTTP {e.code}: {error_body}")


def wp_api_get_all(endpoint, wp_base_url, auth_header, params=None):
    all_items = []
    page = 1
    params = dict(params) if params else {}
    params["per_page"] = "100"
    while True:
        params["page"] = str(page)
        items = wp_api_get(endpoint, wp_base_url, auth_header, params)
        if not items:
            break
        all_items.extend(items)
        if len(items) < 100:
            break
        page += 1
    return all_items


def wp_api_post(endpoint, wp_base_url, auth_header, data=None):
    url = f"{wp_base_url}/wp-json/wp/v2/{endpoint}"
    body = json.dumps(data).encode("utf-8") if data else b"{}"
    req = urllib.request.Request(url, data=body, headers={
        "Authorization": auth_header,
        "Content-Type": "application/json",
    }, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        raise RuntimeError(f"HTTP {e.code}: {error_body}")


def slugify(name):
    slug = name.lower().strip()
    slug = re.sub(r'[áàäâ]', 'a', slug)
    slug = re.sub(r'[éèëê]', 'e', slug)
    slug = re.sub(r'[íìïî]', 'i', slug)
    slug = re.sub(r'[óòöô]', 'o', slug)
    slug = re.sub(r'[úùüû]', 'u', slug)
    slug = re.sub(r'[ñ]', 'n', slug)
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = slug.strip('-')
    return slug


# ============================================================
# INIT
# ============================================================

def cmd_init(args):
    print("Inicializando base de datos...")
    conn = get_conn()

    old_links = []
    try:
        rows = conn.execute("SELECT from_wp_id, to_wp_id, score, created_at FROM internal_links").fetchall()
        old_links = [(r[0], r[1], r[2], r[3] if r[3] else datetime.now(timezone.utc).isoformat()) for r in rows]
        print(f"  Preservando {len(old_links)} registros de internal_links")
    except sqlite3.OperationalError:
        print("  No hay tabla internal_links previa — se creará nueva")

    conn.execute("PRAGMA foreign_keys = OFF")

    conn.executescript("DROP TABLE IF EXISTS tag_groups; DROP TABLE IF EXISTS tags; DROP TABLE IF EXISTS posts; DROP TABLE IF EXISTS post_tags; DROP TABLE IF EXISTS post_ideas; DROP TABLE IF EXISTS internal_links;")

    conn.executescript(SCHEMA_SQL)

    conn.execute("PRAGMA foreign_keys = ON")

    for seed in TAG_GROUPS_SEED:
        conn.execute(
            "INSERT OR IGNORE INTO tag_groups (id, slug, name, score_weight, description, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (*seed, "2026-04-11"),
        )
    print(f"  Insertados {len(TAG_GROUPS_SEED)} grupos de tags")

    if old_links:
        conn.execute("PRAGMA foreign_keys = OFF")
        for from_id, to_id, score, created_at in old_links:
            conn.execute(
                "INSERT OR IGNORE INTO internal_links (from_wp_id, to_wp_id, score, created_at) VALUES (?, ?, ?, ?)",
                (from_id, to_id, score, created_at),
            )
        conn.execute("PRAGMA foreign_keys = ON")
        print(f"  Restaurados {len(old_links)} registros de internal_links")

    conn.commit()
    conn.close()

    counts = {}
    conn = get_conn()
    for table in ["tag_groups", "tags", "posts", "post_tags", "post_ideas", "internal_links"]:
        counts[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    conn.close()

    print(json.dumps({"ok": True, "message": "Base de datos inicializada", "path": str(DB_PATH), "counts": counts}, ensure_ascii=False))


# ============================================================
# PARSE TAGS-USABLES.MD
# ============================================================

def parse_tags_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    groups = {}
    tags = []

    in_groups = False
    in_tags = False

    for line in content.split("\n"):
        line = line.strip()
        if "## Grupos de Tags" in line:
            in_groups = True
            in_tags = False
            continue
        if "## Lista de Tags" in line:
            in_groups = False
            in_tags = True
            continue
        if line.startswith("## ") and "Grupos" not in line and "Lista" not in line:
            in_groups = False
            in_tags = False
            continue

        if in_groups and line.startswith("|"):
            parts = [p.strip() for p in line.split("|")]
            parts = [p for p in parts if p]
            if len(parts) >= 2 and parts[0] not in ("Grupo", "#"):
                group_name = parts[0]
                group_desc = parts[1] if len(parts) > 1 else ""
                groups[group_name] = group_desc

        if in_tags and line.startswith("|"):
            parts = [p.strip() for p in line.split("|")]
            parts = [p for p in parts if p]
            if len(parts) >= 3 and parts[0] not in ("#", "—"):
                try:
                    num = int(parts[0])
                except ValueError:
                    continue
                tag_name = parts[1]
                group_name = parts[2]
                date_added = parts[3] if len(parts) > 3 else "2026-04-11"
                date_added = date_added.split()[0].strip()
                tags.append({
                    "num": num,
                    "name": tag_name,
                    "group_name": group_name,
                    "date_added": date_added,
                })

    return groups, tags


# ============================================================
# MIGRATE TAGS
# ============================================================

def cmd_migrate_tags(args):
    print("Migrando tags desde tags-usables.md...")
    groups, tags = parse_tags_file(TAGS_FILE)
    print(f"  Encontrados {len(tags)} tags en {len(groups)} grupos")

    wp_base_url, auth_header = get_wp_config()
    if not wp_base_url:
        print(json.dumps({"ok": False, "error": "No se pudieron leer las credenciales de WordPress desde .env"}), file=sys.stderr)
        sys.exit(1)

    print("  Descargando tags de WordPress...")
    wp_tags = wp_api_get_all("tags", wp_base_url, auth_header, {"fields": "id,name,slug,count"})
    wp_tags_by_name = {}
    for t in wp_tags:
        wp_tags_by_name[t["name"]] = t
        wp_tags_by_name[t["name"].lower()] = t
        wp_tags_by_name[t["slug"]] = t
    print(f"  Obtenidos {len(wp_tags)} tags de WordPress")

    conn = get_conn()
    group_lookup = {}
    for row in conn.execute("SELECT id, name, slug FROM tag_groups").fetchall():
        group_lookup[row["name"]] = row["id"]
        group_lookup[row["slug"]] = row["id"]

    inserted = 0
    created_in_wp = 0
    errors = []

    for tag_data in tags:
        tag_name = tag_data["name"]
        group_name = tag_data["group_name"]
        group_id = group_lookup.get(group_name)
        if not group_id:
            slug = GROUP_NAME_TO_SLUG.get(group_name, group_name.lower())
            group_id = group_lookup.get(slug)
            if not group_id:
                errors.append(f"Grupo no encontrado: {group_name} para tag {tag_name}")
                continue

        wp_tag = wp_tags_by_name.get(tag_name) or wp_tags_by_name.get(tag_name.lower())
        wp_id = None
        tag_slug = None

        if wp_tag:
            wp_id = wp_tag["id"]
            tag_slug = wp_tag["slug"]
        else:
            tag_slug = slugify(tag_name)
            try:
                new_tag = wp_api_post("tags", wp_base_url, auth_header, {"name": tag_name, "slug": tag_slug})
                wp_id = new_tag["id"]
                tag_slug = new_tag.get("slug", tag_slug)
                created_in_wp += 1
                print(f"    Creado tag en WordPress: {tag_name} (ID: {wp_id})")
            except Exception as e:
                errors.append(f"No se pudo crear tag '{tag_name}' en WordPress: {e}")
                continue

        try:
            conn.execute(
                "INSERT OR IGNORE INTO tags (wp_id, name, slug, group_id, created_at) VALUES (?, ?, ?, ?, ?)",
                (wp_id, tag_name, tag_slug, group_id, tag_data["date_added"]),
            )
            inserted += 1
        except Exception as e:
            errors.append(f"Error insertando tag '{tag_name}': {e}")

    conn.commit()
    conn.close()

    print(f"  Insertados {inserted} tags en la base de datos")
    if created_in_wp:
        print(f"  Creados {created_in_wp} tags nuevos en WordPress")
    if errors:
        print(f"  {len(errors)} errores:")
        for err in errors:
            print(f"    - {err}")

    result = {"ok": True, "inserted": inserted, "created_in_wp": created_in_wp, "errors": errors}
    print(json.dumps(result, ensure_ascii=False))


# ============================================================
# PARSE POST-IDEAS.MD
# ============================================================

def parse_prompt(prompt_text):
    fields = {}
    text = prompt_text.strip()

    prefixes = [
        "Ejecuta el comando /create-post con los siguientes datos:",
        "Ejecuta el comando /create-post con los siguientes datos:",
    ]
    for prefix in prefixes:
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
            break

    text = text.lstrip("-").strip()
    text = text.replace("\n", " ").strip()

    field_patterns = [
        (r'(?:Título|Juego)\s*:\s*', 'title'),
        (r'Modo\s+aplicado\s*:\s*', 'modo'),
        (r'Tipo\s+de\s+post\s*:\s*', 'tipo'),
        (r'sistema\s*:\s*', 'sistema'),
        (r'genero\s*:\s*', 'genero'),
        (r'epoca\s*:\s*', 'epoca'),
        (r'Ángulo\s+Editorial\s*:\s*', 'angulo_editorial'),
        (r'Justificación\s*:\s*', 'justificacion'),
        (r'Keyword\s+Sugerida\s*:\s*', 'keyword_sugerida'),
        (r'Factor\s+de\s+Oportunidad\s*:\s*', 'factor_oportunidad'),
    ]

    markers = []
    for pattern, key in field_patterns:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            markers.append((m.end(), key, m.start()))
    markers.sort(key=lambda x: x[0])

    for i, (end_pos, key, start_pos) in enumerate(markers):
        value_end = markers[i + 1][2] if i + 1 < len(markers) else len(text)
        value = text[end_pos:value_end].strip().rstrip('-').strip()
        if value.endswith('|'):
            value = value[:-1].strip()
        fields[key] = value

    return fields


def cmd_migrate_ideas(args):
    print("Migrando post ideas desde post-ideas.md...")
    with open(IDEAS_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    ideas = []
    in_table = False

    for line in content.split("\n"):
        line = line.strip()
        if "| # | Título" in line:
            in_table = True
            continue
        if in_table and line.startswith("|"):
            parts = [p.strip() for p in line.split("|")]
            parts = [p for p in parts if p]
            if len(parts) >= 7 and parts[0] not in ("#", "—"):
                try:
                    num = int(parts[0])
                except ValueError:
                    continue
                title = parts[1].strip()
                sistema = parts[2].strip()
                tipo = parts[3].strip()
                estado = parts[4].strip()
                updated_at = parts[5].strip()
                prompt = parts[6].strip() if len(parts) > 6 else ""

                if estado == "en uso":
                    estado = "en_uso"

                parsed = parse_prompt(prompt)

                idea = {
                    "num": num,
                    "title": title,
                    "sistema": sistema,
                    "tipo": tipo,
                    "estado": estado,
                    "updated_at": updated_at,
                    "prompt": prompt,
                    "modo": parsed.get("modo", "editorial"),
                    "genero": parsed.get("genero", ""),
                    "epoca": parsed.get("epoca", ""),
                    "angulo_editorial": parsed.get("angulo_editorial", ""),
                    "justificacion": parsed.get("justificacion", ""),
                    "keyword_sugerida": parsed.get("keyword_sugerida"),
                    "factor_oportunidad": parsed.get("factor_oportunidad"),
                }
                ideas.append(idea)
        elif in_table and not line.startswith("|") and line and not line.startswith("##") and not line.startswith("---"):
            continue

    print(f"  Encontradas {len(ideas)} ideas")

    conn = get_conn()
    inserted = 0
    errors = []

    valid_tipos = ("Review", "Historias", "Listas")
    valid_estados = ("pendiente", "en_uso", "publicado")
    valid_modos = ("editorial", "seo_master")

    for idea in ideas:
        tipo = idea["tipo"]
        if tipo not in valid_tipos:
            closest = {"Histogram": "Historias"}.get(tipo, tipo)
            if closest in valid_tipos:
                tipo = closest
            else:
                errors.append(f"Idea #{idea['num']}: tipo inválido '{tipo}'")
                continue

        estado = idea["estado"]
        if estado not in valid_estados:
            errors.append(f"Idea #{idea['num']}: estado inválido '{estado}'")
            continue

        modo = idea["modo"].lower()
        if modo not in valid_modos:
            modo = "editorial"

        angulo = idea["angulo_editorial"] or f"Post sobre {idea['title']}"
        justificacion = idea["justificacion"] or None
        keyword = idea["keyword_sugerida"] or None
        factor = idea["factor_oportunidad"] or None
        genero = idea["genero"] or None
        epoca = idea["epoca"] or None

        try:
            conn.execute(
                """INSERT OR IGNORE INTO post_ideas
                   (title, sistema, tipo, estado, modo, angulo_editorial, justificacion,
                    keyword_sugerida, factor_oportunidad, genero, epoca, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (idea["title"], idea["sistema"], tipo, estado, modo, angulo,
                 justificacion, keyword, factor, genero, epoca,
                 idea["updated_at"], idea["updated_at"]),
            )
            inserted += 1
        except Exception as e:
            errors.append(f"Idea #{idea['num']} '{idea['title']}': {e}")

    conn.commit()
    conn.close()

    print(f"  Insertadas {inserted} ideas en la base de datos")
    if errors:
        print(f"  {len(errors)} errores:")
        for err in errors:
            print(f"    - {err}")

    result = {"ok": True, "inserted": inserted, "errors": errors}
    print(json.dumps(result, ensure_ascii=False))


# ============================================================
# SYNC TAGS WP
# ============================================================

def cmd_sync_tags_wp(args):
    print("Sincronizando wp_ids de tags con WordPress...")
    wp_base_url, auth_header = get_wp_config()
    if not wp_base_url:
        print(json.dumps({"ok": False, "error": "No se pudieron leer las credenciales de WordPress"}), file=sys.stderr)
        sys.exit(1)

    wp_tags = wp_api_get_all("tags", wp_base_url, auth_header, {"fields": "id,name,slug,count"})
    wp_by_name = {}
    for t in wp_tags:
        wp_by_name[t["name"]] = t
        wp_by_name[t["name"].lower()] = t
        wp_by_name[t["slug"]] = t

    conn = get_conn()
    local_tags = conn.execute("SELECT wp_id, name, slug, group_id FROM tags").fetchall()
    print(f"  {len(local_tags)} tags locales, {len(wp_tags)} tags en WordPress")

    updated = 0
    created = 0
    errors = []

    for tag in local_tags:
        wp_id = tag["wp_id"]
        name = tag["name"]

        wp_tag = wp_by_name.get(name) or wp_by_name.get(name.lower())
        if wp_tag and wp_tag["id"] == wp_id:
            continue

        if wp_tag:
            new_wp_id = wp_tag["id"]
            new_slug = wp_tag["slug"]
            try:
                conn.execute(
                    "UPDATE tags SET wp_id = ?, slug = ? WHERE name = ?",
                    (new_wp_id, new_slug, name),
                )
                updated += 1
            except Exception as e:
                errors.append(f"Error actualizando tag '{name}': {e}")
        else:
            tag_slug = slugify(name)
            try:
                new_tag = wp_api_post("tags", wp_base_url, auth_header, {"name": name, "slug": tag_slug})
                new_wp_id = new_tag["id"]
                new_slug = new_tag.get("slug", tag_slug)
                conn.execute(
                    "UPDATE tags SET wp_id = ?, slug = ? WHERE name = ?",
                    (new_wp_id, new_slug, name),
                )
                created += 1
                print(f"    Creado tag en WordPress: {name} (ID: {new_wp_id})")
            except Exception as e:
                errors.append(f"No se pudo crear tag '{name}' en WordPress: {e}")

    for wp_tag in wp_tags:
        exists = conn.execute("SELECT 1 FROM tags WHERE wp_id = ?", (wp_tag["id"],)).fetchone()
        if not exists:
            group = GROUP_NAME_TO_SLUG.get("Sistema")
            conn.execute(
                "INSERT OR IGNORE INTO tags (wp_id, name, slug, group_id, created_at) VALUES (?, ?, ?, (SELECT id FROM tag_groups WHERE slug = 'sistema'), ?)",
                (wp_tag["id"], wp_tag["name"], wp_tag["slug"], datetime.now(timezone.utc).strftime("%Y-%m-%d")),
            )

    conn.commit()
    conn.close()

    print(f"  Actualizados {updated} tags, creados {created} en WordPress")
    if errors:
        print(f"  {len(errors)} errores:")
        for err in errors:
            print(f"    - {err}")

    result = {"ok": True, "updated": updated, "created": created, "errors": errors}
    print(json.dumps(result, ensure_ascii=False))


# ============================================================
# SYNC POSTS WP
# ============================================================

def cmd_sync_posts_wp(args):
    print("Sincronizando posts desde WordPress...")
    wp_base_url, auth_header = get_wp_config()
    if not wp_base_url:
        print(json.dumps({"ok": False, "error": "No se pudieron leer las credenciales de WordPress"}), file=sys.stderr)
        sys.exit(1)

    categories = wp_api_get_all("categories", wp_base_url, auth_header, {"fields": "id,name,slug,count"})
    cat_by_id = {c["id"]: c for c in categories}

    wp_posts = wp_api_get_all("posts", wp_base_url, auth_header, {"status": "publish", "fields": "id,title,slug,categories,tags,date"})
    print(f"  Obtenidos {len(wp_posts)} posts de WordPress")

    conn = get_conn()
    inserted_posts = 0
    inserted_tags = 0
    errors = []

    for post in wp_posts:
        wp_id = post["id"]
        title = post.get("title", {}).get("rendered", "").strip()
        slug = post.get("slug", "")
        published_at = post.get("date", "")
        cat_ids = post.get("categories", [])
        tag_ids = post.get("tags", [])

        cat_slug = "reviews"
        if cat_ids:
            primary_cat = cat_ids[0]
            if primary_cat in cat_by_id:
                cat_slug = cat_by_id[primary_cat].get("slug", "reviews")

        try:
            conn.execute(
                """INSERT OR IGNORE INTO posts (wp_id, title, slug, category_slug, status, published_at, created_at, updated_at)
                   VALUES (?, ?, ?, ?, 'publish', ?, datetime('now'), datetime('now'))""",
                (wp_id, title, slug, cat_slug, published_at),
            )
            inserted_posts += 1
        except Exception as e:
            errors.append(f"Error insertando post {wp_id}: {e}")
            continue

        for tag_id in tag_ids:
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO post_tags (post_wp_id, tag_wp_id) VALUES (?, ?)",
                    (wp_id, tag_id),
                )
                inserted_tags += 1
            except Exception as e:
                errors.append(f"Error insertando post_tag ({wp_id}, {tag_id}): {e}")

    conn.commit()
    conn.close()

    print(f"  Insertados {inserted_posts} posts y {inserted_tags} relaciones post_tags")
    if errors:
        print(f"  {len(errors)} errores:")
        for err in errors:
            print(f"    - {err}")

    result = {"ok": True, "posts_inserted": inserted_posts, "post_tags_inserted": inserted_tags, "errors": errors}
    print(json.dumps(result, ensure_ascii=False))


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Inicialización y migración de la base de datos Optim Pixel")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Crear tablas y datos iniciales (tag_groups, preserva internal_links)")
    sub.add_parser("migrate-tags", help="Migrar tags desde tags-usables.md (resuelve wp_ids via WP API)")
    sub.add_parser("migrate-ideas", help="Migrar post ideas desde post-ideas.md")
    sub.add_parser("sync-tags-wp", help="Sincronizar wp_ids de tags con WordPress")
    sub.add_parser("sync-posts-wp", help="Poblar posts y post_tags desde WordPress")

    args = parser.parse_args()

    commands = {
        "init": cmd_init,
        "migrate-tags": cmd_migrate_tags,
        "migrate-ideas": cmd_migrate_ideas,
        "sync-tags-wp": cmd_sync_tags_wp,
        "sync-posts-wp": cmd_sync_posts_wp,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()