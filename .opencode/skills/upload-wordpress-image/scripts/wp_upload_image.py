#!/usr/bin/env python3
"""
wp_upload_image.py
Descarga una imagen y la sube a WordPress como media.
Devuelve el media_id para asignarlo como featured image.

Uso:
    python3 wp_upload_image.py \
        --url "https://example.com/imagen.jpg" \
        --post-id 123 \
        --game "Chrono Trigger" \
        --platform "Super Nintendo"

Requiere en .env:
    WP_BASE_URL=https://optimpixel.com
    WP_USER=tu_usuario
    WP_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx
"""

import argparse
import base64
import os
import sys
import urllib.request
import urllib.error
import json
import mimetypes
from pathlib import Path


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
    """Genera el header Authorization para Basic Auth."""
    credentials = base64.b64encode(f"{user}:{app_password}".encode()).decode()
    return f"Basic {credentials}"


def download_image(url: str, dest_path: str) -> str:
    """Descarga la imagen y devuelve la ruta local."""
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
        print(f"  ERROR: archivo descargado demasiado pequeño ({size} bytes). URL inválida.")
        sys.exit(1)

    print(f"  OK — {size / 1024:.1f} KB descargados")
    return dest_path


def upload_to_wordpress(
    image_path: str,
    wp_base_url: str,
    auth_header: str,
    post_id: int,
    game: str,
    platform: str,
) -> int:
    """Sube la imagen a WordPress via REST API. Devuelve el media_id."""

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

    # Actualizar alt_text, caption y description
    patch_url = f"{wp_base_url.rstrip('/')}/wp-json/wp/v2/media/{media_id}"
    patch_data = json.dumps({
        "alt_text": f"Portada de {game} para {platform}",
        "caption": f"Portada de {game}",
        "description": f"Portada de {game}",
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
        print(f"  AVISO: no se pudieron actualizar metadatos ({e}), pero la imagen sí se subió")

    return media_id


def set_featured_image(wp_base_url: str, auth_header: str, post_id: int, media_id: int):
    """Asigna el media como featured image del post."""
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
    parser = argparse.ArgumentParser(description="Sube imagen de portada a WordPress")
    parser.add_argument("--url", required=True, help="URL pública de la imagen")
    parser.add_argument("--post-id", required=True, type=int, help="ID del post destino")
    parser.add_argument("--game", required=True, help="Nombre del juego")
    parser.add_argument("--platform", default="", help="Plataforma (ej: Super Nintendo)")
    parser.add_argument("--env", default=".env", help="Ruta al archivo .env")
    args = parser.parse_args()

    # Cargar credenciales
    env = load_env(args.env)
    wp_base_url = env.get("WP_BASE_URL") or os.environ.get("WP_BASE_URL")
    wp_user = env.get("WP_USER") or os.environ.get("WP_USER")
    wp_app_password = env.get("WP_APP_PASSWORD") or os.environ.get("WP_APP_PASSWORD")

    if not wp_base_url or not wp_user or not wp_app_password:
        print("ERROR: WP_BASE_URL, WP_USER y WP_APP_PASSWORD son obligatorios en .env")
        sys.exit(1)

    auth_header = make_basic_auth(wp_user, wp_app_password)

    print(f"\n=== wp_upload_image ===")
    print(f"  Post ID   : {args.post_id}")
    print(f"  Juego     : {args.game}")
    print(f"  Plataforma: {args.platform}")
    print(f"  Usuario WP: {wp_user}")

    # Descargar imagen a /tmp
    ext = Path(args.url.split("?")[0]).suffix or ".jpg"
    safe_name = args.game.lower().replace(" ", "_").replace("/", "_")
    tmp_path = f"/tmp/portada_{safe_name}{ext}"

    download_image(args.url, tmp_path)

    # Subir a WordPress
    media_id = upload_to_wordpress(
        tmp_path, wp_base_url, auth_header, args.post_id, args.game, args.platform
    )

    # Asignar como featured image
    set_featured_image(wp_base_url, auth_header, args.post_id, media_id)

    # Limpiar tmp
    os.remove(tmp_path)
    print(f"  Archivo temporal eliminado")

    print(f"\n✓ Imagen subida y asignada correctamente")
    print(f"  media_id: {media_id}")
    print(f"  post_id : {args.post_id}")


if __name__ == "__main__":
    main()