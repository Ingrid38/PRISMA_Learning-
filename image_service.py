import base64
import os
import re

import requests
from dotenv import load_dotenv

load_dotenv()

CLOUDFLARE_ACCOUNT_ID = (os.getenv("CLOUDFLARE_ACCOUNT_ID") or "").strip()
CLOUDFLARE_API_TOKEN = (os.getenv("CLOUDFLARE_API_TOKEN") or "").strip()
MODELO_IMAGEN = "@cf/black-forest-labs/flux-1-schnell"


def generar_imagen_referencial(titulo: str = "", texto_apoyo: str = "", prompt_visual: str = "") -> bytes:
    """
    Genera una ilustración escolar sencilla del tema con Cloudflare Workers AI (Flux Schnell).
    Utiliza preferentemente un prompt visual en inglés generado por la IA para evitar
    texto deformado y asegurar calidad artística vectorial.
    Devuelve los bytes JPEG/PNG de la imagen.
    """
    if not CLOUDFLARE_ACCOUNT_ID or not CLOUDFLARE_API_TOKEN:
        raise ValueError("Faltan CLOUDFLARE_ACCOUNT_ID o CLOUDFLARE_API_TOKEN")

    if prompt_visual and len(prompt_visual.strip()) > 15:
        # Usar el prompt visual curado por Gemini/Groq
        prompt = (
            f"{prompt_visual.strip()}, "
            "clean modern educational vector illustration, vibrant flat colors, isolated on solid white background, "
            "minimalist textbook art, high quality, completely wordless, strictly no text, no letters, no words, no labels, no symbols"
        )
    else:
        idea = _resumir_tema(titulo, texto_apoyo)
        prompt = (
            f"Educational clean vector illustration of: {idea}. "
            "Minimalist flat cartoon style for school textbook, bright clear colors, solid white background, "
            "completely wordless, zero text, no letters, no characters, no words, no labels, no writing, no watermark"
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
