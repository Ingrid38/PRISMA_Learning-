import textstat

# Configurar idioma español para cálculos métricos
try:
    textstat.set_lang('es')
except Exception:
    pass

def calcular_legibilidad(texto: str) -> dict:
    """
    Calcula el Índice Fernández-Huerta (adaptación de Flesch para el idioma español).
    Escala estándar de Fernández-Huerta:
      90 - 100: Muy fácil (Lectura fácil accesible para primaria)
      80 - 90:  Fácil
      70 - 80:  Bastante fácil
      60 - 70:  Normal
      50 - 60:  Algo difícil
      0 - 50:   Muy difícil / Universitario / Requiere adaptación DUA
    """
    if not texto or len(texto.strip()) < 10:
        return {"score": 0.0, "nivel": "Texto insuficiente", "apto_lectura_facil": False}
    
    score = round(textstat.fernandez_huerta(texto), 2)
    
    if score >= 80:
        nivel = "Muy fácil / Lectura Fácil (DUA Aprobado)"
        apto = True
    elif score >= 60:
        nivel = "Dificultad Media / Comprensión estándar"
        apto = False
    else:
        nivel = "Dificultad Elevada / Requiere adaptación urgente"
        apto = False
        
    return {
        "score": score,
        "nivel": nivel,
        "apto_lectura_facil": apto
    }
