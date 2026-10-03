import os
import json
import base64
import time
import requests
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # Soporte preparado para Groq

# Modelos en cascada por orden de prioridad (Lite primero por velocidad y menor saturación)
GEMINI_MODELS = [
    "gemini-flash-lite-latest",  # Ultrarrápido, menor latencia y alta disponibilidad
    "gemini-flash-latest"        # Modelo de respaldo
]

def invocar_groq(prompt: str) -> dict:
    """
    [PREPARADO PARA EL FUTURO]
    Llamada a Groq Cloud con Llama-3.3-70b-versatile.
    Se activará automáticamente cuando configures GROQ_API_KEY en tu .env.
    Velocidad promedio: >300 tokens/segundo.
    """
    if not GROQ_API_KEY:
        return None

    endpoint = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {
                "role": "system",
                "content": "Eres PRISMA, copiloto DUA. Responde siempre y exclusivamente en formato JSON válido."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.2
    }

    try:
        resp = requests.post(endpoint, headers=headers, json=payload, timeout=15)
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"]
            return json.loads(content)
    except Exception as e:
        print(f"[Aviso Groq] Falló llamada a Groq: {e}, conmutando a Gemini...")
    
    return None


def invocar_gemini_multimodal(prompt: str, base64_image: str = None, mime_type: str = "image/jpeg") -> dict:
    """
    Invoca Gemini con cascada automática entre modelos (Lite -> Flash)
    y timeouts rápidos de 20s para evitar bloqueos del navegador.
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY no está configurada en .env")

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

    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": GEMINI_API_KEY
    }

    errores = []

    # Cascada inteligente: prueba primero Lite, si falla prueba Flash
    for model_name in GEMINI_MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
        
        # 2 intentos rápidos por modelo con timeout corto de 25s
        for intento in range(1, 3):
            try:
                # print(f"[IA] Probando {model_name} (intento {intento})...")
                resp = requests.post(url, headers=headers, json=payload, timeout=25)

                if resp.status_code == 200:
                    data = resp.json()
                    raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                    clean = raw_text.strip()
                    if clean.startswith("```json"):
                        clean = clean[7:]
                    if clean.endswith("```"):
                        clean = clean[:-3]
                    return json.loads(clean.strip())

                elif resp.status_code in [503, 429, 500]:
                    print(f"[Aviso] {model_name} respondió {resp.status_code}. Reintentando o conmutando...")
                    time.sleep(1)
                else:
                    errores.append(f"{model_name}: {resp.status_code} - {resp.text[:100]}")
                    break  # Si es error 400 u otro, pasar de inmediato al siguiente modelo
            except requests.exceptions.Timeout:
                print(f"[Aviso] Timeout de 25s alcanzado en {model_name}. Conmutando de inmediato...")
                errores.append(f"{model_name}: Timeout 25s")
                break  # En timeout no insistir en el mismo modelo saturado; conmutar al siguiente
            except Exception as e:
                errores.append(f"{model_name}: {str(e)}")
                time.sleep(1)

    raise RuntimeError(f"Error tras cascada de modelos Gemini: {'; '.join(errores)}")


def adaptar_recurso_dua(texto_o_tema: str, base64_image: str = None, mime_type: str = "image/jpeg", barreras_dua: list = None) -> dict:
    """
    Motor de Refracción Pedagógica DUA:
    Transforma el contenido a Lectura Fácil, genera glosario contextual,
    descripción accesible (alt-text) y pautas didácticas adaptadas
    a las barreras observables seleccionadas por el docente.
    """
    enfoque_barreras = ""
    if barreras_dua and len(barreras_dua) > 0:
        mapeo_barreras = {
            "vocabulario": "- DUA Representación: Ampliar glosario contextual y sustituir términos abstractos por analogías cotidianas.",
            "atencion": "- DUA Implicación: Párrafos extra breves (máximo 3 líneas), uso de viñetas y conceptos clave resaltados.",
            "visual": "- DUA Percepción: Descripción visual ultra detallada paso a paso pensada para audiodescripción.",
            "segunda_lengua": "- DUA Lingüístico: Sintaxis directa en español neutro universal, sin modismos ni metáforas confusas.",
            "comprension_lenta": "- DUA Andamiaje: Estructura de ideas paso a paso (primero causa, luego efecto)."
        }
        instrucciones_especificas = "\n".join([mapeo_barreras[b] for b in barreras_dua if b in mapeo_barreras])
        if instrucciones_especificas:
            enfoque_barreras = f"""
PRIORIDADES PEDAGÓGICAS DUA SELECCIONADAS POR EL DOCENTE PARA ESTE GRUPO:
{instrucciones_especificas}
"""

    prompt = f"""
Eres PRISMA, el copiloto pedagógico de diseño universal para el aprendizaje (DUA) para el Reto 03 de ProFuturo.
Tu misión es transformar el material educativo brindado por el docente en un recurso accesible de LECTURA FÁCIL en español.
{enfoque_barreras}
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
    # 1. Si no hay imagen y Groq está configurado, intentar Groq primero (súper veloz)
    if not base64_image and GROQ_API_KEY:
        res_groq = invocar_groq(prompt)
        if res_groq:
            return res_groq

    # 2. Cascada multimodal rápida con Gemini (Lite -> Flash)
    return invocar_gemini_multimodal(prompt, base64_image, mime_type)
