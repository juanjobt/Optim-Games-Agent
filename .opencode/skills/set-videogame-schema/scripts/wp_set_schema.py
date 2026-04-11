#!/usr/bin/env python3
"""
wp_set_schema.py
Inyecta los metadatos del schema VideoGame en un post de WordPress.
Compatible con el plugin "Schema & Structured Data for WP & AMP".

Uso:
    python3 wp_set_schema.py \
        --post-id 123 \
        --name "Resident Evil" \
        --system "PlayStation, PC, Sega Saturn" \
        --genre "Survival Horror, Aventura" \
        --author-name "Capcom" \
        --description "El inicio de la saga survival horror de Capcom." \
        --image "https://optimpixel.com/wp-content/uploads/imagen.jpg" \
        --url "https://optimpixel.com/review-resident-evil"

Requiere en .env:
    WP_BASE_URL=https://optimpixel.com
    WP_USER=tu_usuario
    WP_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx
    WP_VIDEOGAME_SCHEMA_ID=118
"""

import argparse
import base64
import json
import os
import sys
import urllib.request
import urllib.error


# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

DEFAULT_SCHEMA_ID = "118"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_env(env_path=".env"):
    """Carga variables del .env sin dependencias externas."""
    env = {}
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


def make_basic_auth(user: str, app_password: str) -> str:
    credentials = base64.b64encode(f"{user}:{app_password}".encode()).decode()
    return f"Basic {credentials}"


def wp_request(url: str, auth_header: str, data: dict = None, method: str = "GET") -> dict:
    """Realiza una petición a la REST API de WordPress."""
    body = json.dumps(data).encode("utf-8") if data else None
    headers = {
        "Authorization": auth_header,
        "Content-Type": "application/json",
    }
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        print(f"  ERROR HTTP {e.code} en {url}: {error_body}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"  ERROR de red: {e}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Lógica principal
# ---------------------------------------------------------------------------

def build_meta_payload(schema_id: str, args: argparse.Namespace) -> dict:
    """
    Construye el dict de meta fields para el schema VideoGame.
    Solo incluye campos con valor — los vacíos los dejamos sin tocar.
    """
    # Helper para construir la key
    def key(field: str) -> str:
        return f"saswp_vg_schema_{field}_{schema_id}"

    meta = {}

    # Campos que siempre establecemos
    meta[f"saswp_modify_this_schema_{schema_id}"] = "1"
    meta[key("id")] = "VideoGame"
    meta[key("application_category")] = "Games"

    # Campos opcionales — solo si se pasaron como argumento
    field_map = {
        "name":               args.name,
        "description":        args.description,
        "game_platform":      args.system,
        "operating_system":   args.system,   # mismo valor: sistema = OS para retro
        "genre":              args.genre,
        "author_name":        args.author_name,
        "author_type":        args.author_type,
        "publisher":          args.publisher,
        "url":                args.url,
        "image":              args.image,
        "rating":             args.rating,
    }

    for field, value in field_map.items():
        if value:
            meta[key(field)] = value

    return meta


def set_schema(
    wp_base_url: str,
    auth_header: str,
    post_id: int,
    schema_id: str,
    args: argparse.Namespace,
):
    """Actualiza los meta fields del schema en el post."""
    meta = build_meta_payload(schema_id, args)

    print(f"\n  Meta fields a actualizar:")
    for k, v in meta.items():
        print(f"    {k} = {v}")

    url = f"{wp_base_url}/wp-json/wp/v2/posts/{post_id}"
    result = wp_request(url, auth_header, data={"meta": meta}, method="POST")

    # Verificación
    updated_meta = result.get("meta", {})
    name_key = f"saswp_vg_schema_name_{schema_id}"
    if updated_meta.get(name_key) == args.name:
        print(f"\n  ✓ Schema VideoGame actualizado correctamente")
    else:
        print(f"\n  ⚠ No se pudo verificar la actualización. Comprueba manualmente el post {post_id}")

    return result


# ---------------------------------------------------------------------------
# Entrada
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Inyecta schema VideoGame en un post de WordPress"
    )
    parser.add_argument("--post-id",     required=True,  type=int, help="ID del post en WordPress")
    parser.add_argument("--name",        required=True,            help="Nombre del videojuego")
    parser.add_argument("--description", default="",               help="Descripción breve del juego")
    parser.add_argument("--system",      default="",               help="Sistemas separados por coma (ej: 'PlayStation, PC')")
    parser.add_argument("--genre",       default="",              help="Géneros separados por coma (ej: 'RPG, Aventura')")
    parser.add_argument("--author-name", default="",               help="Desarrolladora del juego")
    parser.add_argument("--author-type", default="Organization",   help="Tipo de autor: Organization o Person")
    parser.add_argument("--publisher",   default="",               help="Distribuidora del juego")
    parser.add_argument("--image",       default="",               help="URL de la imagen de portada")
    parser.add_argument("--url",         default="",               help="URL canónica del post")
    parser.add_argument("--rating",      default="",               help="Puntuación (ej: '8.5'). Solo para reviews")
    parser.add_argument("--env",         default=".env",          help="Ruta al archivo .env")
    args = parser.parse_args()

    # Credenciales
    env = load_env(args.env)
    wp_base_url    = (env.get("WP_BASE_URL")    or os.environ.get("WP_BASE_URL", "")).rstrip("/")
    wp_user        = env.get("WP_USER")         or os.environ.get("WP_USER")
    wp_app_password = env.get("WP_APP_PASSWORD") or os.environ.get("WP_APP_PASSWORD")
    schema_id      = env.get("WP_VIDEOGAME_SCHEMA_ID")    or os.environ.get("WP_VIDEOGAME_SCHEMA_ID", DEFAULT_SCHEMA_ID)

    if not wp_base_url or not wp_user or not wp_app_password:
        print("ERROR: WP_BASE_URL, WP_USER y WP_APP_PASSWORD son obligatorios en .env")
        sys.exit(1)

    auth_header = make_basic_auth(wp_user, wp_app_password)

    print(f"\n=== wp_set_schema ===")
    print(f"  Post ID : {args.post_id}")
    print(f"  Juego   : {args.name}")
    print(f"  Sistema : {args.system}")

    # Actualizar schema
    set_schema(wp_base_url, auth_header, args.post_id, schema_id, args)

    print(f"\n✓ Proceso completado")
    print(f"  post_id   : {args.post_id}")
    print(f"  schema_id : {schema_id}")
    print(f"  juego     : {args.name}")


if __name__ == "__main__":
    main()