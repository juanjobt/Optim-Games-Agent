#!/usr/bin/env python3
"""
sync_tag_groups.py — Sincroniza los tag_group desde la base de datos local
a los term meta de WordPress.

Modos de uso:
    Sincronización completa (todos los tags):
        python3 .opencode/skills/publish-wordpress/scripts/sync_tag_groups.py [--dry-run]

    Tag individual (para cuando se crea un tag nuevo durante la publicación):
        python3 .opencode/skills/publish-wordpress/scripts/sync_tag_groups.py --single --wp-id ID --group GRUPO

El meta "tag_group" permite que el shortcode [opcat_section] de la página
"El Catálogo" (/el-catalogo) agrupe los tags dinámicamente por sección.
"""

import argparse
import base64
import json
import sqlite3
import urllib.error
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent.parent
DB_PATH = PROJECT_ROOT / "memory" / "blog.db"
ENV_PATH = PROJECT_ROOT / ".env"


def load_env():
    env = {}
    with open(ENV_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                key, _, value = line.partition("=")
                env[key.strip()] = value.strip()
    return env


def assign_tag_group(base_url, creds, wp_id, group_slug):
    """Asigna el term meta 'tag_group' a un tag de WordPress via REST API.

    Devuelve True si tuvo éxito, False en caso contrario.
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {creds}",
    }
    payload = json.dumps({"meta": {"tag_group": group_slug}}).encode("utf-8")

    req = urllib.request.Request(
        f"{base_url}/wp-json/wp/v2/tags/{wp_id}",
        data=payload,
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            returned_group = result.get("meta", {}).get("tag_group", "")
            if returned_group == group_slug:
                return True
            else:
                print(f"  WARN: Tag {wp_id} → devolvió tag_group='{returned_group}' (esperado '{group_slug}')")
                return False
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"  ERROR: Tag {wp_id} → HTTP {e.code}: {body[:200]}")
        return False
    except Exception as e:
        print(f"  ERROR: Tag {wp_id} → {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Sincroniza tag_group entre DB local y WordPress")
    parser.add_argument("--dry-run", action="store_true", help="Simula sin hacer cambios")
    parser.add_argument("--single", action="store_true", help="Asigna tag_group a un solo tag")
    parser.add_argument("--wp-id", type=int, help="ID del tag en WordPress (para --single)")
    parser.add_argument("--group", type=str, help="Slug del grupo (para --single, ej: sistema, genero, saga)")
    args = parser.parse_args()

    env = load_env()
    base_url = env.get("WP_BASE_URL", "").rstrip("/")
    wp_user = env.get("WP_USER", "")
    wp_app_password = env.get("WP_APP_PASSWORD", "")

    if not base_url or not wp_user or not wp_app_password:
        print("ERROR: WP_BASE_URL, WP_USER y WP_APP_PASSWORD deben estar en .env")
        return

    creds = base64.b64encode(f"{wp_user}:{wp_app_password}".encode()).decode()

    # Modo single: asignar tag_group a un tag individual
    if args.single:
        if not args.wp_id or not args.group:
            print("ERROR: --single requiere --wp-id y --group")
            return

        print(f"Asignando tag_group='{args.group}' al tag {args.wp_id}...")
        if args.dry_run:
            print(f"  [DRY] Tag {args.wp_id} → tag_group='{args.group}'")
        else:
            ok = assign_tag_group(base_url, creds, args.wp_id, args.group)
            if ok:
                print(f"  OK: Tag {args.wp_id} → tag_group='{args.group}'")
            else:
                print(f"  FALLO: Tag {args.wp_id} → tag_group='{args.group}'")
        return

    # Modo completo: sincronizar todos los tags desde la DB
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    rows = cur.execute("""
        SELECT t.wp_id, t.name, t.slug, tg.slug as group_slug
        FROM tags t
        JOIN tag_groups tg ON t.group_id = tg.id
        ORDER BY tg.slug, t.name
    """).fetchall()

    conn.close()

    print(f"Sincronizando {len(rows)} tags con tag_group en WordPress...")
    if args.dry_run:
        print("DRY RUN — No se realizarán cambios.")

    success = 0
    errors = 0
    skipped = 0

    for wp_id, name, slug, group_slug in rows:
        if args.dry_run:
            print(f"  [DRY] Tag {wp_id} '{name}' → tag_group='{group_slug}'")
            skipped += 1
            continue

        ok = assign_tag_group(base_url, creds, wp_id, group_slug)
        if ok:
            success += 1
        else:
            errors += 1

    print()
    if args.dry_run:
        print(f"DRY RUN: {skipped} tags serían sincronizados.")
    else:
        print(f"Resultado: {success} OK, {errors} errores de {len(rows)} tags")
        if success + errors != len(rows):
            print(f"  (Procesados: {success + errors}, Total: {len(rows)})")


if __name__ == "__main__":
    main()