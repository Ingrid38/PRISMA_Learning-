import io
import base64
from pypdf import PdfReader
from pptx import Presentation

def extraer_texto_pdf(file_bytes: bytes) -> str:
    """Extrae todo el texto legible de un archivo PDF en memoria."""
    pdf_file = io.BytesIO(file_bytes)
    reader = PdfReader(pdf_file)
    texto = []
    for page in reader.pages:
        t = page.extract_text()
        if t:
            texto.append(t)
    return "\n\n".join(texto).strip()

def extraer_texto_pptx(file_bytes: bytes) -> str:
    """Extrae el contenido textual y notas de una presentación PowerPoint."""
    ppt_file = io.BytesIO(file_bytes)
    prs = Presentation(ppt_file)
    diapositivas_texto = []
    
    for i, slide in enumerate(prs.slides, 1):
        lineas = [f"--- Diapositiva {i} ---"]
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text:
                lineas.append(shape.text.strip())
        diapositivas_texto.append("\n".join(lineas))
        
    return "\n\n".join(diapositivas_texto).strip()

def preparar_imagen_base64(file_bytes: bytes) -> str:
    """Convierte los bytes de una imagen en cadena base64 para Gemini Vision."""
    return base64.b64encode(file_bytes).decode("utf-8")
