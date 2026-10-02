import io
import base64
from pypdf import PdfReader
from pptx import Presentation

def extraer_texto_pdf(file_bytes: bytes, max_paginas: int = 15, max_chars: int = 12000) -> str:
    """
    Extrae el texto pedagógico de las páginas del PDF.
    Limita inteligentemente a las primeras páginas representativas (hasta 12.000 caracteres)
    para evitar saturación de tokens y tiempos de espera prolongados en la red.
    """
    pdf_file = io.BytesIO(file_bytes)
    reader = PdfReader(pdf_file)
    texto = []
    
    for i, page in enumerate(reader.pages):
        if i >= max_paginas:
            break
        t = page.extract_text()
        if t:
            texto.append(t.strip())
            
    resultado = "\n\n".join(texto).strip()
    if len(resultado) > max_chars:
        resultado = resultado[:max_chars]
        
    return resultado

def extraer_texto_pptx(file_bytes: bytes, max_diapos: int = 20, max_chars: int = 12000) -> str:
    """
    Extrae el contenido textual y notas de una presentación PowerPoint.
    """
    ppt_file = io.BytesIO(file_bytes)
    prs = Presentation(ppt_file)
    diapositivas_texto = []
    
    for i, slide in enumerate(prs.slides, 1):
        if i > max_diapos:
            break
        lineas = [f"--- Diapositiva {i} ---"]
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text:
                lineas.append(shape.text.strip())
        diapositivas_texto.append("\n".join(lineas))
        
    resultado = "\n\n".join(diapositivas_texto).strip()
    if len(resultado) > max_chars:
        resultado = resultado[:max_chars]
        
    return resultado

def preparar_imagen_base64(file_bytes: bytes) -> str:
    """Convierte los bytes de una imagen en cadena base64 para Gemini Vision."""
    return base64.b64encode(file_bytes).decode("utf-8")
