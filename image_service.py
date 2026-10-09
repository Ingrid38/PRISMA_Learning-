import base64
import os
import re

import requests
from dotenv import load_dotenv

load_dotenv()

CLOUDFLARE_ACCOUNT_ID = (os.getenv("CLOUDFLARE_ACCOUNT_ID") or "").strip()
CLOUDFLARE_API_TOKEN = (os.getenv("CLOUDFLARE_API_TOKEN") or "").strip()
MODELO_IMAGEN = "@cf/black-forest-labs/flux-1-schnell"


def generar_imagen_referencial(titulo: str, texto_apoyo: str = "") -> bytes:
    """
    Genera una ilustración escolar sencilla del tema con Cloudflare Workers AI.
    Devuelve los bytes JPEG/PNG de la imagen.
    """
    if not CLOUDFLARE_ACCOUNT_ID or not CLOUDFLARE_API_TOKEN:
        raise ValueError("Faltan CLOUDFLARE_ACCOUNT_ID o CLOUDFLARE_API_TOKEN")

    idea = _resumir_tema(titulo, texto_apoyo)
    prompt = (
        "Simple educational classroom diagram for children about this topic: "
        f"{idea}. "
        "Flat illustration, white background, few clear objects, bright colors, "
        "high contrast, no text, no letters, no numbers, no watermark, no logo."
    )

    url = (
        "https://api.cloudflare.com/client/v4/accounts/"
        f"{CLOUDFLARE_ACCOUNT_ID}/ai/run/{MODELO_IMAGEN}"
    )
    resp = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
            "Content-Type": "application/json",
        },
        json={"prompt": prompt[:1800], "steps": 4},
        timeout=60,
    )
    if not resp.ok:
        raise RuntimeError(f"Cloudflare imagen {resp.status_code}: {resp.text[:240]}")

    content_type = (resp.headers.get("Content-Type") or "").lower()
    if content_type.startswith("image/"):
        return resp.content

    data = resp.json()
    imagen = (data.get("result") or {}).get("image") if isinstance(data, dict) else None
    if not imagen and isinstance(data, dict):
        imagen = data.get("image")
    if not imagen:
        raise RuntimeError("Cloudflare no devolvió una imagen")

    if isinstance(imagen, str) and imagen.startswith("data:"):
        imagen = imagen.split(",", 1)[-1]
    return base64.b64decode(imagen)


def _resumir_tema(titulo: str, texto_apoyo: str) -> str:
    base = (titulo or "tema escolar").strip()
    apoyo = re.sub(r"\s+", " ", (texto_apoyo or "")).strip()
    if apoyo:
        base = f"{base}. {apoyo[:280]}"
    return base[:400]
