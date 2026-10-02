import os
import json
import base64
import time
import requests
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent"

def invocar_gemini(prompt: str, base64_image: str = None, mime_type: str = "image/jpeg", max_retries: int = 3) -> dict:
    """
    Envía prompt e imagen opcional a Gemini Flash con reintentos automáticos
    y espera una respuesta JSON estructurada.
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY no está configurada en .env")

    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": GEMINI_API_KEY
    }

    parts = []
    
    if base64_image:
        parts.append({
            "inline_data": {
                "mime_type": mime_type,
                "data": base64_image
            }
        })

    parts.append({"text": prompt})

    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json"
        }
    }

    last_error = None
    for intento in range(1, max_retries + 1):
        try:
            resp = requests.post(GEMINI_ENDPOINT, headers=headers, json=payload, timeout=60)
            if resp.status_code == 200:
                data = resp.json()
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                try:
                    return json.loads(raw_text)
                except Exception:
                    clean = raw_text.strip()
                    if clean.startswith("```json"):
                        clean = clean[7:]
                    if clean.endswith("```"):
                        clean = clean[:-3]
                    return json.loads(clean.strip())
            elif resp.status_code in [500, 503, 504, 429]:
                print(f"[Aviso] Reintento {intento}/{max_retries} por status {resp.status_code} de Google...")
                time.sleep(2 * intento)
            else:
                resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            last_error = e
            print(f"[Aviso] Reintento {intento}/{max_retries} tras error de conexión: {e}")
            time.sleep(2 * intento)

    raise RuntimeError(f"Error tras {max_retries} intentos con Gemini: {last_error}")


def adaptar_recurso_dua(texto_o_tema: str, base64_image: str = None, mime_type: str = "image/jpeg") -> dict:
    """
    Motor de Refracción Pedagógica DUA:
    Transforma el contenido a Lectura Fácil, genera glosario contextual,
    descripción accesible (alt-text) y pautas didácticas.
    """
    prompt = f"""
Eres PRISMA, el copiloto pedagógico de diseño universal para el aprendizaje (DUA) para el Reto 03 de ProFuturo.
Tu misión es transformar el material educativo brindado por el docente en un recurso accesible de LECTURA FÁCIL en español.

REGLAS OBLIGATORIAS DE ADAPTACIÓN (Norma Europea de Lectura Fácil / DUA):
1. Longitud de oraciones: Máximo 12 a 15 palabras por oración.
2. Estructura directa: Sujeto + Verbo + Predicado. Evita oraciones subordinadas complejas y voz pasiva.
3. Vocabulario claro: Sustituye tecnicismos difíciles por palabras cotidianas sin perder el concepto científico o histórico.
4. Organización: Divide en párrafos breves con ideas claras.
5. Inclusión: Respeta el rigor del tema para que el alumno aprenda el mismo objetivo de clase que sus compañeros.

RESPONDE EXCLUSIVAMENTE CON UN OBJETO JSON con esta estructura exacta:
{{
    "titulo_adaptado": "Título claro y motivador del tema",
    "contenido_extraido": "Texto original resumido o transcripción fiel del contenido/imagen",
    "lectura_facil": "El texto completamente adaptado a las reglas de Lectura Fácil",
    "glosario": [
        {{"termino": "Palabra clave 1", "significado_simple": "Explicación en una frase sencilla"}},
        {{"termino": "Palabra clave 2", "significado_simple": "Explicación en una frase sencilla"}}
    ],
    "descripcion_visual": "Descripción pedagógica clara y estructurada de cualquier imagen, esquema o pizarra presente (o texto descriptivo si es solo texto)",
    "pautas_docente": "Breve recomendación DUA para el docente en el aula (ej: usar preguntas guía, andamiaje visual)"
}}

CONTENIDO A TRANSFORMAR:
{texto_o_tema}
"""
    return invocar_gemini(prompt, base64_image, mime_type)
