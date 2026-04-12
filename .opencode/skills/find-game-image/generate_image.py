#!/usr/bin/env python3
"""
Genera una imagen de portada para un videojuego usando Hugging Face Spaces
(Gradio API). Usa black-forest-labs/FLUX.1-dev como modelo principal.

Uso:
    python3 generate_image.py "Sonic the Hedgehog 3" "Sega Genesis" [--output-dir /ruta/imagenes]

Devuelve por stdout la ruta del archivo generado, o "ERROR: <mensaje>" si falla.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests

ENV_PATH = Path(__file__).resolve().parent.parent.parent.parent / ".env"

SPACE_URL = "https://black-forest-labs-flux-1-dev.hf.space"
API_ENDPOINT = "/gradio_api/call/infer"

# FLUX.1-dev API parameters:
# [prompt, seed, randomize_seed, width, height, guidance_scale, steps]
PROMPT_INDEX = 0
SEED_INDEX = 1
RANDOMIZE_INDEX = 2
WIDTH_INDEX = 3
HEIGHT_INDEX = 4
GUIDANCE_INDEX = 5
STEPS_INDEX = 6

MAX_RETRIES = 3
RETRY_WAIT = 10
GENERATION_TIMEOUT = 300


def load_env():
    env = {}
    if not ENV_PATH.exists():
        return env
    with open(ENV_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                env[key.strip()] = value.strip()
    return env


def build_prompt(game_name: str, system: str) -> str:
    prompt = (
        f"retro video game cover art for {game_name}, {system} style, "
        f"vibrant colors, 16-bit aesthetic, box art illustration, "
        f"detailed character artwork, classic gaming era, "
        f"high quality, detailed, professional cover art, no text overlay, clean composition"
    )
    return prompt


def query_gradio_space(prompt: str, hf_token: str = None):
    headers = {"Content-Type": "application/json"}
    if hf_token:
        headers["Authorization"] = f"Bearer {hf_token}"

    payload = {
        "data": [
            prompt,
            0,
            True,
            768,
            1024,
            3.5,
            20,
        ]
    }

    for attempt in range(MAX_RETRIES):
        try:
            r = requests.post(
                f"{SPACE_URL}{API_ENDPOINT}",
                json=payload,
                headers=headers,
                timeout=60,
            )
        except requests.exceptions.RequestException as e:
            print(
                f"Error de conexion (intento {attempt + 1}/{MAX_RETRIES}): {e}",
                file=sys.stderr,
            )
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_WAIT)
            continue

        if r.status_code != 200:
            print(
                f"Error {r.status_code} al enviar trabajo (intento {attempt + 1}/{MAX_RETRIES}): {r.text[:200]}",
                file=sys.stderr,
            )
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_WAIT)
            continue

        try:
            event_id = r.json().get("event_id")
        except (json.JSONDecodeError, ValueError):
            print(f"Respuesta inesperada: {r.text[:200]}", file=sys.stderr)
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_WAIT)
            continue

        if not event_id:
            print("No se recibio event_id", file=sys.stderr)
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_WAIT)
            continue

        print(f"Trabajo enviado (event_id: {event_id}), esperando resultado...", file=sys.stderr)
        time.sleep(5)

        result = _stream_result(event_id, headers)
        if result is not None:
            return result

        print(
            f"La generacion fallo (intento {attempt + 1}/{MAX_RETRIES})",
            file=sys.stderr,
        )
        if attempt < MAX_RETRIES - 1:
            time.sleep(RETRY_WAIT)

    return None


def _stream_result(event_id: str, headers: dict):
    url = f"{SPACE_URL}/gradio_api/call/infer/{event_id}"
    try:
        r = requests.get(url, headers=headers, stream=True, timeout=GENERATION_TIMEOUT)
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener resultado: {e}", file=sys.stderr)
        return None

    if r.status_code != 200:
        print(f"Error {r.status_code} al obtener resultado: {r.text[:200]}", file=sys.stderr)
        return None

    current_event = None
    for line in r.iter_lines(decode_unicode=True):
        if line is None:
            continue
        if line.startswith("event:"):
            current_event = line.split(":", 1)[1].strip()
        elif line.startswith("data:"):
            data_str = line.split(":", 1)[1].strip()
            if current_event == "error":
                print(f"Error del Space: {data_str}", file=sys.stderr)
                return None
            if current_event == "complete":
                return _parse_gradio_result(data_str)

    return None


def _parse_gradio_result(data_str: str):
    try:
        result = json.loads(data_str)
    except (json.JSONDecodeError, ValueError):
        print(f"No se pudo parsear resultado: {data_str[:200]}", file=sys.stderr)
        return None

    if not isinstance(result, list) or len(result) == 0:
        print(f"Resultado vacio o inesperado: {str(result)[:200]}", file=sys.stderr)
        return None

    image_data = result[0]
    if isinstance(image_data, dict) and "url" in image_data:
        url = image_data["url"]
        if url.startswith("/file/"):
            url = SPACE_URL + url
        elif not url.startswith("http"):
            url = SPACE_URL + "/" + url.lstrip("/")
        return _download_image(url)
    elif isinstance(image_data, dict) and "path" in image_data:
        path = image_data["path"]
        url = f"{SPACE_URL}/file={path}"
        return _download_image(url)
    elif isinstance(image_data, str):
        if image_data.startswith("http"):
            return _download_image(image_data)
        elif image_data.startswith("/"):
            url = SPACE_URL + image_data
            return _download_image(url)

    print(f"Formato de resultado no reconocido: {str(image_data)[:200]}", file=sys.stderr)
    return None


def _download_image(url: str):
    try:
        r = requests.get(url, timeout=60)
        if r.status_code == 200 and len(r.content) > 1000:
            return r.content
        else:
            print(f"Error descargando imagen: {r.status_code}", file=sys.stderr)
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error descargando imagen: {e}", file=sys.stderr)
        return None


def generate_image(game_name: str, system: str, output_dir: str = None) -> str:
    env = load_env()
    hf_token = env.get("HF_TOKEN")

    if output_dir:
        out_path = Path(output_dir)
    else:
        out_path = Path(__file__).resolve().parent / "generated"
    out_path.mkdir(parents=True, exist_ok=True)

    safe_game = "".join(
        c if c.isalnum() or c in "- _" else "_" for c in game_name
    ).strip().replace(" ", "_")

    prompt = build_prompt(game_name, system)
    print(f"Prompt: {prompt}", file=sys.stderr)

    image_data = query_gradio_space(prompt, hf_token)

    if image_data is None:
        return "ERROR: No se pudo generar imagen. El Space de FLUX.1-dev puede estar saturado o temporalmente no disponible. Intenta generar la imagen manualmente en https://huggingface.co/spaces/black-forest-labs/FLUX.1-dev"

    if image_data[:4] == b"\x89PNG":
        ext = "png"
    elif image_data[:2] == b"\xff\xd8":
        ext = "jpg"
    elif image_data[:4] == b"RIFF" and image_data[8:12] == b"WEBP":
        ext = "webp"
    else:
        ext = "png"

    filename = f"{safe_game}_cover.{ext}"
    filepath = out_path / filename

    with open(filepath, "wb") as f:
        f.write(image_data)

    print(f"Imagen generada: {filepath}", file=sys.stderr)
    return str(filepath)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Genera imagen de portada con Hugging Face Spaces (FLUX.1-dev)"
    )
    parser.add_argument("game_name", help="Nombre del videojuego")
    parser.add_argument("system", help="Sistema/plataforma del juego")
    parser.add_argument(
        "--output-dir", default=None, help="Directorio de salida para la imagen"
    )

    args = parser.parse_args()
    result = generate_image(args.game_name, args.system, args.output_dir)
    print(result)