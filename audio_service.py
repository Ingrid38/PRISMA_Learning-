import os
import io
import asyncio
import edge_tts
from gtts import gTTS

# Voz en español neutro de alta calidad
VOZ_PREDETERMINADA = "es-ES-AlvaroNeural"  # Alternativa: "es-MX-DaliaNeural"

_MARCADORES_SIN_IMAGEN = (
    "sin elementos visuales",
    "sin imagen",
    "no hay imagen",
    "no se observa imagen",
    "contenido adaptado sin elementos",
)


def descripcion_narrable(descripcion: str) -> str:
    """Devuelve la descripción solo si aporta una audiodescripción real de la imagen."""
    texto = (descripcion or "").strip()
    if len(texto) < 40:
        return ""
    bajo = texto.lower()
    if any(marca in bajo for marca in _MARCADORES_SIN_IMAGEN):
        return ""
    return texto


def construir_texto_audio(lectura: str, descripcion: str = "") -> tuple:
    """
    Arma el guion que se va a narrar.
    Si hay descripción de imagen, va primero para que el estudiante
    con discapacidad visual la escuche al pulsar reproducir.
    Devuelve (texto, incluye_audiodescripcion).
    """
    lectura = (lectura or "").strip()
    desc = descripcion_narrable(descripcion)

    if desc and lectura:
        if desc in lectura or lectura in desc:
            return (desc if len(desc) >= len(lectura) else lectura), True
        return (
            "Descripción de la imagen.\n"
            f"{desc}\n\n"
            "Lectura fácil.\n"
            f"{lectura}"
        ), True
    if desc:
        return f"Descripción de la imagen.\n{desc}", True
    return lectura, False

async def _sintetizar_edge_tts(texto: str, voz: str = VOZ_PREDETERMINADA) -> bytes:
    """Sintetiza audio con edge-tts en memoria."""
    communicate = edge_tts.Communicate(texto, voz)
    buffer = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buffer.write(chunk["data"])
    return buffer.getvalue()

def generar_audio_mp3(texto: str) -> bytes:
    """
    Convierte texto a archivo de audio MP3 en memoria.
    Prioridad 1: edge-tts (voz neuronal hiperrealista sin API key).
    Fallback: gTTS (Google Text-to-Speech estándar).
    """
    if not texto or not texto.strip():
        raise ValueError("El texto para generar audio no puede estar vacío.")

    # La descripción de la imagen va al inicio, así sobrevive si el texto se recorta
    texto_procesado = texto.strip()[:6000]

    try:
        audio_bytes = asyncio.run(
            asyncio.wait_for(_sintetizar_edge_tts(texto_procesado), timeout=25)
        )

        if audio_bytes and len(audio_bytes) > 100:
            return audio_bytes
    except Exception as e:
        print(f"[Aviso TTS] edge-tts falló: {e}. Conmutando a gTTS...")

    # Fallback con gTTS
    tts = gTTS(text=texto_procesado, lang='es', slow=False)
    buffer = io.BytesIO()
    tts.write_to_fp(buffer)
    return buffer.getvalue()
