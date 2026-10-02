import os
import io
import asyncio
import edge_tts
from gtts import gTTS

# Voz en español neutro de alta calidad
VOZ_PREDETERMINADA = "es-ES-AlvaroNeural"  # Alternativa: "es-MX-DaliaNeural"

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

    # Limitar longitud si el texto es demasiado largo para una cápsula auditiva
    texto_procesado = texto.strip()[:4000]

    try:
        # Intentar con edge-tts (asíncrono adaptado a síncrono)
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            # Si corre dentro de un event loop existente
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                audio_bytes = pool.submit(asyncio.run, _sintetizar_edge_tts(texto_procesado)).result()
        else:
            audio_bytes = loop.run_until_complete(_sintetizar_edge_tts(texto_procesado))

        if audio_bytes and len(audio_bytes) > 100:
            return audio_bytes
    except Exception as e:
        print(f"[Aviso TTS] edge-tts falló: {e}. Conmutando a gTTS...")

    # Fallback con gTTS
    tts = gTTS(text=texto_procesado, lang='es', slow=False)
    buffer = io.BytesIO()
    tts.write_to_fp(buffer)
    return buffer.getvalue()
