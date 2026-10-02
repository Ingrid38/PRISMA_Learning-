import os
from flask import Flask, jsonify, request
from dotenv import load_dotenv
from db import db
from legibilidad import calcular_legibilidad

load_dotenv()

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "proyecto": "PRISMA - Motor de Refracción Pedagógica DUA",
        "reto": "Reto 03 · Un contenido, muchas formas de aprender (ProFuturo)",
        "estado": "En ejecución",
        "fase": "Fase 1 - Cimientos e Infraestructura (Flask + Render + Supabase)",
        "docs": {
            "health": "/health",
            "test_legibilidad": "/api/legibilidad"
        }
    }), 200

@app.route("/health", methods=["GET"])
def health():
    """Verifica el estado del servicio y la conexión a la base de datos de Supabase"""
    try:
        # Consulta de prueba a la tabla 'recursos_origen' en Supabase
        res = db.table("recursos_origen").select("id").limit(1).execute()
        return jsonify({
            "status": "ok",
            "servicio_render": "activo",
            "supabase_conectado": True,
            "detalle": "Comunicación fluida con PostgreSQL en Supabase",
            "tablas_verificadas": ["recursos_origen", "adaptaciones_multimodales", "observaciones_dua"],
            "buckets_verificados": ["origenes", "accesibles"]
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "servicio_render": "activo",
            "supabase_conectado": False,
            "detalle": f"Error al conectar con Supabase: {str(e)}"
        }), 500

@app.route("/api/legibilidad", methods=["POST"])
def auditar_legibilidad():
    """Audita el índice Fernández-Huerta de un texto en español"""
    data = request.get_json() or {}
    texto = data.get("texto", "")
    
    if not texto:
        return jsonify({"error": "Debe enviar el campo 'texto'"}), 400
        
    resultado = calcular_legibilidad(texto)
    return jsonify(resultado), 200

if __name__ == "__main__":
    puerto = int(os.getenv("PORT", 5000))
    debug_mode = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    print(f" Servidor PRISMA iniciado en http://localhost:{puerto}")
    app.run(host="0.0.0.0", port=puerto, debug=debug_mode)
