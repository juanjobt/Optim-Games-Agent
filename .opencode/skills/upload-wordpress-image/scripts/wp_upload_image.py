#!/usr/bin/env python3
"""
wp_upload_image.py
Descarga una imagen y la sube a WordPress como media.
Soporta portada (asigna featured_media), screenshot y concepto artístico
(solo sube a biblioteca de medios).

Uso:
    # Portada (asigna featured_media al post):
    python3 wp_upload_image.py \
        --url "https://example.com/imagen.jpg" \
        --post-id 123 \
        --game "Chrono Trigger" \
        --system "Super Nintendo" \
        --type portada

    # Screenshot (solo biblioteca de medios):
    python3 wp_upload_image.py \
        --url "https://example.com/screenshot.jpg" \
        --game "Chrono Trigger" \
        --type screenshot

    # Concepto artístico (solo biblioteca de medios):
    python3 wp_upload_image.py \
        --url "https://example.com/concept.jpg" \
        --game "Chrono Trigger" \
        --type concepto

Requiere en .env:
    WP_BASE_URL=https://optimpixel.com
    WP_USER=tu_usuario
    WP_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx
"""

import argparse
import base64
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


IMAGE_TYPES = ("portada", "screenshot", "concepto")

ALT_TEMPLATES = {
    "portada": "Portada de {game} para {system}",
    "portada_no_system": "Portada de {game}",
    "screenshot": "Captura de pantalla de {game}",
    "concepto": "{game} — concepto artistico",
}

CAPTION_TEMPLATES = {
    "portada": "Portada de {game}",
    "screenshot": "Captura de pantalla de {game}",
    "concepto": "{game} — concepto artistico",
}


def load_env(env_path=".env"):
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


def build_alt_text(image_type: str, game: str, system: str, custom_alt: str = None) -> str:
    if custom_alt:
        return custom_alt
    if image_type == "portada" and system:
        return ALT_TEMPLATES["portada"].format(game=game, system=system)
    if image_type == "portada":
        return ALT_TEMPLATES["portada_no_system"].format(game=game)
    return ALT_TEMPLATES.get(image_type, ALT_TEMPLATES["screenshot"]).format(game=game)


def build_caption(image_type: str, game: str) -> str:
    return CAPTION_TEMPLATES.get(image_type, CAPTION_TEMPLATES["screenshot"]).format(game=game)


def build_description(image_type: str, game: str) -> str:
    desc_map = {
        "portada": f"Portada de {game}",
        "screenshot": f"Captura de pantalla de {game}",
        "concepto": f"Concepto artistico de {game}",
    }
    return desc_map.get(image_type, game)


def download_image(url: str, dest_path: str) -> str:
    print(f"  Descargando imagen: {url}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            with open(dest_path, "wb") as f:
                f.write(response.read())
    except urllib.error.URLError as e:
        print(f"  ERROR descargando imagen: {e}")
        sys.exit(1)

    size = os.path.getsize(dest_path)
    if size < 1024:
        print(f"  ERROR: archivo descargado demasiado pequeno ({size} bytes). URL invalida.")
        sys.exit(1)

    print(f"  OK — {size / 1024:.1f} KB descargados")
    return dest_path


def upload_to_wordpress(
    image_path: str,
    wp_base_url: str,
    auth_header: str,
    post_id: int,
    game: str,
    image_type: str,
    alt_text: str,
    caption: str,
    description: str,
) -> int:
    api_url = f"{wp_base_url.rstrip('/')}/wp-json/wp/v2/media"

    mime_type, _ = mimetypes.guess_type(image_path)
    if not mime_type:
        mime_type = "image/jpeg"

    filename = Path(image_path).name

    print(f"  Subiendo a WordPress: {api_url}")

    with open(image_path, "rb") as f:
        image_data = f.read()

    boundary = "----WPUploadBoundary"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: {mime_type}\r\n\r\n"
    ).encode("utf-8") + image_data + f"\r\n--{boundary}--\r\n".encode("utf-8")

    headers = {
        "Authorization": auth_header,
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Content-Disposition": f'attachment; filename="{filename}"',
    }

    req = urllib.request.Request(api_url, data=body, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        print(f"  ERROR HTTP {e.code}: {error_body}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"  ERROR de red: {e}")
        sys.exit(1)

    media_id = result.get("id")
    if not media_id:
        print(f"  ERROR: respuesta inesperada de WordPress: {result}")
        sys.exit(1)

    print(f"  OK — media_id: {media_id}")

    source_url = result.get("source_url", "")

    patch_url = f"{wp_base_url.rstrip('/')}/wp-json/wp/v2/media/{media_id}"
    patch_data = json.dumps({
        "alt_text": alt_text,
        "caption": caption,
        "description": description,
    }).encode("utf-8")

    patch_req = urllib.request.Request(
        patch_url,
        data=patch_data,
        headers={"Authorization": auth_header, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(patch_req, timeout=30):
            pass
        print(f"  OK — metadatos actualizados")
    except Exception as e:
        print(f"  AVISO: no se pudieron actualizar metadatos ({e}), pero la imagen si se subio")

    return media_id, source_url


def set_featured_image(wp_base_url: str, auth_header: str, post_id: int, media_id: int):
    api_url = f"{wp_base_url.rstrip('/')}/wp-json/wp/v2/posts/{post_id}"

    data = json.dumps({"featured_media": media_id}).encode("utf-8")
    headers = {
        "Authorization": auth_header,
        "Content-Type": "application/json",
    }

    req = urllib.request.Request(api_url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        print(f"  ERROR asignando featured image HTTP {e.code}: {error_body}")
        sys.exit(1)

    assigned = result.get("featured_media")
    if assigned != media_id:
        print(f"  AVISO: featured_media devuelto ({assigned}) no coincide con media_id ({media_id})")
    else:
        print(f"  OK — featured_media asignado: {assigned}")


def main():
    parser = argparse.ArgumentParser(description="Sube imagen a WordPress (portada, screenshot o concepto)")
    parser.add_argument("--url", required=True, help="URL publica de la imagen")
    parser.add_argument("--post-id", type=int, default=None, help="ID del post destino (obligatorio para portada)")
    parser.add_argument("--game", required=True, help="Nombre del juego")
    parser.add_argument("--system", default="", help="Sistema (ej: Super Nintendo)")
    parser.add_argument("--type", required=True, choices=IMAGE_TYPES, help="Tipo de imagen: portada, screenshot o concepto")
    parser.add_argument("--alt-text", default=None, help="Texto alternativo personalizado (sobreescribe el por defecto)")
    parser.add_argument("--env", default=".env", help="Ruta al archivo .env")
    args = parser.parse_args()

    if args.type == "portada" and args.post_id is None:
        print("ERROR: --post-id es obligatorio para tipo 'portada'")
        sys.exit(1)

    env = load_env(args.env)
    wp_base_url = env.get("WP_BASE_URL") or os.environ.get("WP_BASE_URL")
    wp_user = env.get("WP_USER") or os.environ.get("WP_USER")
    wp_app_password = env.get("WP_APP_PASSWORD") or os.environ.get("WP_APP_PASSWORD")

    if not wp_base_url or not wp_user or not wp_app_password:
        print("ERROR: WP_BASE_URL, WP_USER y WP_APP_PASSWORD son obligatorios en .env")
        sys.exit(1)

    auth_header = make_basic_auth(wp_user, wp_app_password)

    alt_text = build_alt_text(args.type, args.game, args.system, args.alt_text)
    caption = build_caption(args.type, args.game)
    description = build_description(args.type, args.game)

    print(f"\n=== wp_upload_image ===")
    print(f"  Tipo      : {args.type}")
    print(f"  Juego     : {args.game}")
    print(f"  Sistema   : {args.system or '(no especificado)'}")
    if args.post_id:
        print(f"  Post ID   : {args.post_id}")
    else:
        print(f"  Post ID   : (sin asignar — solo biblioteca de medios)")
    print(f"  Alt text  : {alt_text}")
    print(f"  Usuario WP: {wp_user}")

    ext = Path(args.url.split("?")[0]).suffix or ".jpg"
    safe_name = args.game.lower().replace(" ", "_").replace("/", "_")
    prefix = args.type
    tmp_path = f"/tmp/{prefix}_{safe_name}{ext}"

    download_image(args.url, tmp_path)

    media_id, source_url = upload_to_wordpress(
        tmp_path, wp_base_url, auth_header,
        args.post_id or 0, args.game, args.type,
        alt_text, caption, description,
    )

    if args.type == "portada" and args.post_id:
        set_featured_image(wp_base_url, auth_header, args.post_id, media_id)

    os.remove(tmp_path)
    print(f"  Archivo temporal eliminado")

    if args.type == "portada" and args.post_id:
        print(f"\n✓ Imagen subida y asignada correctamente")
        print(f"  media_id   : {media_id}")
        print(f"  post_id    : {args.post_id}")
        print(f"  type       : {args.type}")
        print(f"  featured   : yes")
        print(f"  source_url : {source_url}")
    else:
        print(f"\n✓ Imagen subida a la biblioteca de medios")
        print(f"  media_id   : {media_id}")
        print(f"  type       : {args.type}")
        print(f"  featured   : no")
        print(f"  source_url : {source_url}")


if __name__ == "__main__":
    main()