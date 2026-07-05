#!/usr/bin/env python3
"""
validate_image_urls.py — Validación HTTP previa de URLs de imágenes.

Filtra URLs de imágenes antes de pasarlas a `upload-wordpress-image` para
evitar descargas que van a romper en el Paso 5.5 (URL anti-hotlink, 404,
Content-Type incorrecto, magic bytes inválidos, etc.).

Implementa la Mejora #4 del análisis de logs de ejecución:
- Caso FantasyAnime (log 2026-06-26): URL que pasa todos los filtros
  declarados (extensión, tamaño declarado) pero rompe al descargar.
- Caso YouTube/TikTok/Instagram (log 2026-05-11): filtros manuales ad-hoc
  del LLM; ahora deterministas via blacklist.

Uso:
    python3 validate_image_urls.py --urls "url1,url2,url3"
    python3 validate_image_urls.py --input-json results.json
    python3 validate_image_urls.py --urls "url1" --referer "https://example.com/page"

Salida (JSON por stdout): lista de objetos con el plano de validación
extendido, lista para que el LLM filtre o que upload-wordpress-image
pueda saltar re-validación.

    {
      "url": "https://media.rawg.io/...jpg",
      "original_url": "https://media.rawg.io/...jpg",
      "ok": true,
      "http_status": 200,
      "content_type": "image/jpeg",
      "content_length": 145632,
      "magic_bytes": "FFD8",
      "format": "jpg",
      "validated_at": "2026-07-05T10:30:00+02:00",
      "checks": {
        "head": true,
        "magic_bytes_ok": true,
        "anti_hotlink_ok": true,
        "domain_whitelisted": true
      },
      "warnings": []
    }

Opciones:
    --dry-syntax-only    Solo valida sintaxis de URL, no hace HTTP calls
    --no-head            Skip HEAD request, va directo a GET Range
    --referer REFERER    Referer a usar en ambos GETs (anti-hotlink check)
    --no-anti-hotlink    Skip anti-hotlink check (solo un GET)
    --timeout TIMEOUT    Timeout HTTP en segundos (default: 10)
    --max-retries N      Reintentos por URL (default: 3)
    --backoff N          Backoff base en segundos (default: 2)
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


# ============================================================
# Whitelist / Blacklist de dominios
# ============================================================

DOMAIN_WHITELIST = {
    # Fuentes conocidas estables (rawg, archive.org, mobygames, principales publishers)
    "media.rawg.io": "rawg_media",
    "api.rawg.io": "rawg_api",
    "archive.org": "archive_org",
    "web.archive.org": "archive_org",
    "ia801708.us.archive.org": "archive_org",
    "ia802708.us.archive.org": "archive_org",
    "www.mobygames.com": "mobygames",
    "mobygames.com": "mobygames",
    "imagebin.mobygames.com": "mobygames",
    "www.nintendo.com": "nintendo",
    "nintendo.com": "nintendo",
    "www.playstation.com": "playstation",
    "playstation.com": "playstation",
    "cdn.cloudflare.steamstatic.com": "steamstatic",
    "steamcdn-a.akamaihd.net": "steamstatic",
    "shared.cdn.queniupc.com": "queniupc",
    # GameFAQs / GameSpot son generalmente estables
    "gamefaqs.gamespot.com": "gamespot",
    "www.gamespot.com": "gamespot",
    "static.wikia.nocookie.net": "wikia",
    "vignette.wikia.nocookie.net": "wikia",
    "www.smwcentral.net": "smwcentral",
    "m1.sharedvestige.com": "sharedvestige",
}

DOMAIN_BLACKLIST = {
    # Redes sociales: nunca imágenes directas
    "youtube.com",
    "www.youtube.com",
    "img.youtube.com",
    "ytimg.com",
    "i.ytimg.com",
    "i1.ytimg.com",
    "i2.ytimg.com",
    "i3.ytimg.com",
    "tiktok.com",
    "www.tiktok.com",
    "instagram.com",
    "www.instagram.com",
    "scontent.cdninstagram.com",
    "scontent-iad3-1.cdninstagram.com",
    "facebook.com",
    "www.facebook.com",
    "scontent.fbcdn.net",
    "fbcdn.net",
    "x.com",
    "twitter.com",
    "www.twitter.com",
    "pbs.twimg.com",
    "pinimg.com",
    "i.pinimg.com",
    "pinterest.com",
    "www.pinterest.com",
    # Fansites con anti-hotlink conocido (de log 2026-06-26):
    "fantasyanime.com",
    "www.fantasyanime.com",
}

# Magic bytes conocidos para imagenes
MAGIC_BYTES = [
    (b"\xff\xd8\xff", "jpg"),
    (b"\x89PNG\r\n\x1a\n", "png"),
    (b"RIFF", "webp"),  # companion check: bytes [8:12] == b"WEBP"
    (b"GIF87a", "gif"),
    (b"GIF89a", "gif"),
]

WEBP_MAGIC_OFFSET = (8, b"WEBP")

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


def validate_magic_bytes(prefix):
    """Devuelve (format, ok) a partir de los primeros bytes de una imagen.

    Estricta: si los bytes no coinciden con ninguno de los formatos
    conocidos (jpg, png, webp, gif) devuelve (None, False). Esto es lo que
    nos protege de URLs con Content-Type 'image/jpeg' que en realidad
    devuelven HTML (página de anti-hotlink, 404 con body HTML, etc.).
    """
    if not prefix or len(prefix) < 6:
        return (None, False)
    if prefix[:4] == b"RIFF" and prefix[8:12] == b"WEBP":
        return ("webp", True)
    for magic, fmt in MAGIC_BYTES:
        if fmt == "webp":
            continue
        if prefix.startswith(magic):
            return (fmt, True)
    return (None, False)


def normalize_url(url):
    """Normaliza URL: urlsplit + quote solo de path/query (no de ://)."""
    try:
        parts = urllib.parse.urlsplit(url.strip())
    except Exception:
        return None
    if not parts.scheme or not parts.netloc:
        return None
    # Forzar scheme https si es http (mismo resultado en fetch, mejor practica)
    scheme = parts.scheme.lower()
    if scheme not in ("http", "https"):
        return None
    # Re-codificar path/query conservando /, ?, &, =, % ya codificados
    path = parts.path
    query = parts.query
    try:
        if path and not path.startswith("/"):
            path = "/" + path
        # quote solo caracteres no-ASCII y espacios; respeta %XX existente
        encoded_path = urllib.parse.quote(path, safe="/%")
        encoded_query = urllib.parse.quote(query, safe="=&%+")
        normalized = urllib.parse.urlunsplit((
            scheme,
            parts.netloc.lower(),
            encoded_path,
            encoded_query,
            parts.fragment,
        ))
        return normalized
    except Exception:
        return None


def get_domain(url):
    try:
        return urllib.parse.urlsplit(url).netloc.lower()
    except Exception:
        return ""


def domain_status(domain):
    """Devuelve (status, key) donde status es 'whitelist' | 'blacklist' |
    'unknown'."""
    if domain in DOMAIN_WHITELIST:
        return ("whitelist", DOMAIN_WHITELIST[domain])
    if domain in DOMAIN_BLACKLIST:
        return ("blacklist", domain)
    parent = ".".join(domain.split(".")[-2:]) if "." in domain else domain
    if parent in DOMAIN_WHITELIST or any(domain.endswith("." + k) for k in DOMAIN_WHITELIST):
        return ("whitelist", parent)
    if parent in DOMAIN_BLACKLIST or any(domain.endswith("." + k) for k in DOMAIN_BLACKLIST):
        return ("blacklist", parent)
    return ("unknown", None)


def head_request(url, timeout, headers, max_retries, backoff):
    """HEAD request con retries. Devuelve dict {status, headers} o None."""
    last_exc = None
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, method="HEAD", headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return {"status": r.status, "headers": dict(r.headers)}
        except urllib.error.HTTPError as e:
            # 4xx o 5xx — no reintenta salvo 429/503
            if e.code in (429, 503) and attempt < max_retries - 1:
                last_exc = e
                time.sleep(backoff * (attempt + 1))
                continue
            return {"status": e.code, "headers": dict(e.headers or {})}
        except urllib.error.URLError as e:
            last_exc = e
            if attempt < max_retries - 1:
                time.sleep(backoff * (attempt + 1))
                continue
            return None
        except Exception as e:
            last_exc = e
            if attempt < max_retries - 1:
                time.sleep(backoff * (attempt + 1))
                continue
            return None
    if last_exc:
        return None
    return None


def get_range_request(url, timeout, headers, max_retries, backoff, range_bytes=2048):
    """GET con Range: bytes=0-{range_bytes-1}. Devuelve dict {status, headers,
    content} o None.
    """

    rh = dict(headers)
    rh["Range"] = f"bytes=0-{range_bytes - 1}"
    rh["Accept"] = "image/*"

    last_exc = None
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers=rh, method="GET")
            with urllib.request.urlopen(req, timeout=timeout) as r:
                content = r.read()
                return {"status": r.status, "headers": dict(r.headers), "content": content}
        except urllib.error.HTTPError as e:
            if e.code in (429, 503, 500, 502, 504) and attempt < max_retries - 1:
                last_exc = e
                time.sleep(backoff * (attempt + 1))
                continue
            if e.code == 416:  # Range Not Satisfiable — server doesn't support Range, get full
                try:
                    req2 = urllib.request.Request(url, headers=headers, method="GET")
                    with urllib.request.urlopen(req2, timeout=timeout) as r:
                        content = r.read()
                        return {"status": r.status, "headers": dict(r.headers), "content": content}
                except Exception:
                    return None
            return {"status": e.code, "headers": dict(e.headers or {}), "content": b""}
        except urllib.error.URLError as e:
            last_exc = e
            if attempt < max_retries - 1:
                time.sleep(backoff * (attempt + 1))
                continue
            return None
        except Exception as e:
            last_exc = e
            if attempt < max_retries - 1:
                time.sleep(backoff * (attempt + 1))
                continue
            return None
    return None


def check_anti_hotlink(url, timeout, headers, max_retries, backoff):
    """Compara el HEAD con y sin Referer. Si el tamano cambia drásticamente
    (>30% de diferencia), el dominio usa anti-hotlink.
    Devuelve (is_anti_hotlink, evidence)."""
    headers_with_ref = dict(headers)  # ya tiene Referer si se paso
    headers_no_ref = {k: v for k, v in headers.items() if k.lower() != "referer"}

    h1 = head_request(url, timeout, headers_with_ref, max_retries, backoff)
    h2 = head_request(url, timeout, headers_no_ref, max_retries, backoff)

    if not h1 or not h2:
        return (None, {"with_referer": h1, "without_referer": h2})

    cl1 = h1["headers"].get("Content-Length") or h1["headers"].get("content-length")
    cl2 = h2["headers"].get("Content-Length") or h2["headers"].get("content-length")
    s1 = h1["status"]
    s2 = h2["status"]

    # Si sin referer devuelve 403/401 → anti-hotlink claro
    if s2 in (401, 403) and s1 == 200:
        return (True, {"reason": f"sin Referer HTTP {s2}, con Referer HTTP {s1}"})

    # Si Content-Length difiere >30%, sospechoso
    if cl1 and cl2:
        try:
            n1 = int(cl1)
            n2 = int(cl2)
            if n2 > 0 and n1 > 0:
                ratio = abs(n1 - n2) / max(n1, n2)
                if ratio > 0.30:
                    return (True, {
                        "reason": f"Content-Length con Referer={n1} vs sin Referer={n2} (diff {ratio:.0%})"
                    })
        except ValueError:
            pass

    return (False, {"with_referer_status": s1, "without_referer_status": s2})


def validate_one(url, args):
    """Valida una URL. Devuelve dict con el resultado completo."""
    result = {
        "url": url,
        "original_url": url,
        "ok": False,
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "checks": {
            "syntax": False,
            "head": False,
            "magic_bytes_ok": False,
            "anti_hotlink_ok": False,
            "domain_whitelisted": False,
        },
        "warnings": [],
    }

    normalized = normalize_url(url)
    if not normalized:
        result["error"] = "URL inválida o no normalizable"
        return result
    result["url"] = normalized
    result["checks"]["syntax"] = True

    domain = get_domain(normalized)
    result["domain"] = domain
    status, key = domain_status(domain)
    result["domain_status"] = status
    if status == "blacklist":
        result["error"] = f"Dominio '{domain}' en blacklist (no es imagen pública directa)"
        result["checks"]["domain_whitelisted"] = False
        return result
    if status == "whitelist":
        result["checks"]["domain_whitelisted"] = True
        result["domain_key"] = key
    elif status == "unknown":
        result["warnings"].append(f"Dominio '{domain}' no en whitelist; considerando OK provisional")

    if args.dry_syntax_only:
        result["ok"] = True
        result["checks"]["head"] = False
        result["checks"]["magic_bytes_ok"] = False
        return result

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "image/*",
    }
    if args.referer:
        headers["Referer"] = args.referer

    # HEAD request opcional
    if not args.no_head:
        head = head_request(normalized, args.timeout, headers, args.max_retries, args.backoff)
        if not head:
            result["error"] = "HEAD request: sin respuesta tras reintentos"
            return result
        result["http_status"] = head["status"]
        result["checks"]["head"] = True
        if head["status"] != 200:
            result["error"] = f"HEAD HTTP {head['status']}"
            return result
        ctype = head["headers"].get("Content-Type") or head["headers"].get("content-type")
        result["content_type"] = ctype
        if ctype and not ctype.lower().startswith("image/"):
            result["warnings"].append(f"Content-Type no es imagen: '{ctype}'")
        clen = head["headers"].get("Content-Length") or head["headers"].get("content-length")
        try:
            result["content_length"] = int(clen) if clen else None
        except (TypeError, ValueError):
            result["content_length"] = None

    # GET Range para inspectar magic bytes
    rg = get_range_request(normalized, args.timeout, headers, args.max_retries, args.backoff)
    if not rg:
        result["error"] = "GET Range: sin respuesta tras reintentos"
        return result
    if "status" in rg and "http_status" not in result:
        result["http_status"] = rg["status"]
    if rg.get("content"):
        prefix = rg["content"]
        result["magic_bytes"] = prefix[:8].hex().upper()
        fmt, ok = validate_magic_bytes(prefix)
        result["format"] = fmt
        result["checks"]["magic_bytes_ok"] = ok
        if not ok:
            result["warnings"].append(
                f"Magic bytes no reconocidos como imagen (primeros 8: {prefix[:8].hex()!r})"
            )
        # Anti-hotlink check (solo si GET funcionó)
        if not args.no_anti_hotlink:
            ah, evidence = check_anti_hotlink(
                normalized, args.timeout, headers, args.max_retries, args.backoff
            )
            result["anti_hotlink_detection"] = evidence
            if ah is True:
                result["checks"]["anti_hotlink_ok"] = False
                result["error"] = (
                    f"Dominio '{domain}' usa anti-hotlink "
                    f"(evidencia: {evidence.get('reason', 'desconocida')})"
                )
                return result
            elif ah is False:
                result["checks"]["anti_hotlink_ok"] = True
            else:
                result["warnings"].append("No se pudo verificar anti-hotlink")
    else:
        result["warnings"].append("GET Range devolvió contenido vacío")

    # Veredicto final
    is_ok = (
        result["checks"]["syntax"]
        and (result["checks"]["head"] or args.no_head)
        and (result["http_status"] == 200)
        and result["checks"]["magic_bytes_ok"]
        and (result["checks"]["anti_hotlink_ok"] or args.no_anti_hotlink)
        and result["domain_status"] != "blacklist"
    )
    result["ok"] = is_ok
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Validación HTTP previa de URLs de imágenes para find-game-image"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--urls", type=str, help="URLs separadas por coma")
    group.add_argument(
        "--input-json",
        type=str,
        help="Ruta a archivo JSON con array de URLs (o objetos {url, ...})",
    )
    parser.add_argument("--referer", type=str, default=None, help="Referer HTTP a usar")
    parser.add_argument(
        "--dry-syntax-only",
        action="store_true",
        help="Solo valida sintaxis de URL (sin HTTP calls)",
    )
    parser.add_argument("--no-head", action="store_true", help="Skip HEAD, va directo a GET Range")
    parser.add_argument(
        "--no-anti-hotlink", action="store_true", help="Skip segundo GET anti-hotlink check"
    )
    parser.add_argument("--timeout", type=int, default=10, help="Timeout HTTP (s)")
    parser.add_argument("--max-retries", type=int, default=3, help="Reintentos por URL")
    parser.add_argument("--backoff", type=float, default=2.0, help="Backoff base (s)")

    args = parser.parse_args()

    urls = []
    if args.urls:
        urls = [u.strip() for u in args.urls.split(",") if u.strip()]
    else:
        with open(args.input_json, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            for item in data:
                if isinstance(item, str):
                    urls.append(item)
                elif isinstance(item, dict) and "url" in item:
                    urls.append(item["url"])
        elif isinstance(data, dict) and "urls" in data:
            for item in data["urls"]:
                if isinstance(item, str):
                    urls.append(item)
                elif isinstance(item, dict) and "url" in item:
                    urls.append(item["url"])

    if not urls:
        print(json.dumps({"ok": False, "error": "No se proporcionaron URLs"}))
        sys.exit(1)

    results = []
    for u in urls:
        try:
            r = validate_one(u, args)
            results.append(r)
        except Exception as e:
            results.append({
                "url": u,
                "original_url": u,
                "ok": False,
                "error": f"Excepción: {e}",
                "validated_at": datetime.now(timezone.utc).isoformat(),
            })

    valid = [r for r in results if r.get("ok")]
    print(json.dumps({
        "ok": True,
        "total": len(results),
        "valid_count": len(valid),
        "invalid_count": len(results) - len(valid),
        "results": results,
        "valid_urls": [r["url"] for r in valid],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()