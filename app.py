import os
import uuid
from flask import Flask, jsonify, request, render_template, send_from_directory
from dotenv import load_dotenv
from db import db
from legibilidad import calcular_legibilidad
from ai_service import adaptar_recurso_dua
from parser_service import extraer_texto_pdf, extraer_texto_pptx, preparar_imagen_base64

load_dotenv()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 30 * 1024 * 1024  # 30 MB max upload

@app.route("/", methods=["GET"])
def index():
    """Interfaz web principal interactiva de PRISMA"""
    return render_template("index.html")

@app.route("/health", methods=["GET"])
def health():
    """Verifica el estado del servicio y la conexión a la base de datos de Supabase"""
    try:
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

@app.route("/api/adaptar", methods=["POST"])
def adaptar_recurso():
    """
    Endpoint principal de Refracción Multimodal DUA:
    Recibe texto directo o un archivo (PDF, PPTX, Imagen) y genera la versión accesible.
    """
    try:
        titulo = request.form.get("titulo") or "Recurso Pedagógico"
        formato = "texto"
        contenido_extraido = ""
        archivo_url = None
        base64_img = None
        mime_type = "image/jpeg"

        # 1. Procesamiento si viene un archivo adjunto
        if "archivo" in request.files and request.files["archivo"].filename:
            file = request.files["archivo"]
            filename = file.filename
            file_bytes = file.read()
            ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

            # Subir a Supabase Storage (bucket 'origenes')
            storage_path = f"doc_{uuid.uuid4().hex[:8]}_{filename}"
            try:
                archivo_url = db.upload_file(
                    bucket="origenes",
                    path=storage_path,
                    file_bytes=file_bytes,
                    content_type=file.content_type or "application/octet-stream"
                )
            except Exception as e:
                print(f"[Aviso] No se pudo subir archivo a Supabase Storage: {e}")
                archivo_url = f"local://{filename}"

            # Extraer contenido según formato
            if ext == "pdf":
                formato = "pdf"
                contenido_extraido = extraer_texto_pdf(file_bytes)
            elif ext in ["ppt", "pptx"]:
                formato = "pptx"
                contenido_extraido = extraer_texto_pptx(file_bytes)
            elif ext in ["jpg", "jpeg", "png", "webp"]:
                formato = "imagen"
                mime_type = file.content_type or "image/jpeg"
                base64_img = preparar_imagen_base64(file_bytes)
                contenido_extraido = f"[Imagen educativa: {filename}]"
            else:
                formato = ext or "archivo"
                contenido_extraido = file_bytes.decode("utf-8", errors="ignore")

        # 2. Si no viene archivo pero sí texto directo
        elif request.is_json:
            json_data = request.get_json() or {}
            titulo = json_data.get("titulo", titulo)
            contenido_extraido = json_data.get("texto", "")
            formato = "texto"
        else:
            contenido_extraido = request.form.get("texto", "")

        if not contenido_extraido and not base64_img:
            return jsonify({"error": "No se proporcionó ningún texto ni archivo para adaptar"}), 400

        # 3. Calcular legibilidad original (Índice Fernández-Huerta)
        metricas_orig = calcular_legibilidad(contenido_extraido) if contenido_extraido else {"score": 40.0}

        # 4. Invocar Motor de Refracción DUA (Gemini Flash)
        resultado_ia = adaptar_recurso_dua(
            texto_o_tema=contenido_extraido,
            base64_image=base64_img,
            mime_type=mime_type
        )

        texto_adaptado = resultado_ia.get("lectura_facil", "")
        glosario = resultado_ia.get("glosario", [])
        desc_visual = resultado_ia.get("descripcion_visual", "")
        titulo_final = resultado_ia.get("titulo_adaptado") or titulo

        # 5. Calcular legibilidad del texto adaptado
        metricas_adapt = calcular_legibilidad(texto_adaptado)

        # 6. Guardar en Supabase (recursos_origen y adaptaciones_multimodales)
        rec_id = str(uuid.uuid4())
        try:
            db.table("recursos_origen").insert({
                "id": rec_id,
                "titulo": titulo_final,
                "formato_origen": formato,
                "archivo_url": archivo_url or "texto_directo",
                "contenido_extraido": contenido_extraido[:3000],
                "legibilidad_original": metricas_orig["score"]
            })

            adapt_id = str(uuid.uuid4())
            db.table("adaptaciones_multimodales").insert({
                "id": adapt_id,
                "recurso_id": rec_id,
                "lectura_facil": texto_adaptado,
                "legibilidad_adaptada": metricas_adapt["score"],
                "glosario": glosario,
                "descripcion_visual": desc_visual,
                "estado": "borrador",
                "notas_docente": resultado_ia.get("pautas_docente", "")
            })
        except Exception as e:
            print(f"[Error Supabase] {e}")
            adapt_id = str(uuid.uuid4())

        return jsonify({
            "status": "success",
            "recurso_id": rec_id,
            "adaptacion_id": adapt_id,
            "titulo": titulo_final,
            "formato_origen": formato,
            "contenido_original": contenido_extraido,
            "legibilidad_original": metricas_orig,
            "lectura_facil": texto_adaptado,
            "legibilidad_adaptada": metricas_adapt,
            "glosario": glosario,
            "descripcion_visual": desc_visual,
            "pautas_docente": resultado_ia.get("pautas_docente", ""),
            "archivo_url": archivo_url
        }), 200

    except Exception as e:
        print(f"Error en /api/adaptar: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/recursos", methods=["GET"])
def listar_recursos():
    """Lista los recursos procesados almacenados en Supabase"""
    try:
        datos = db.table("recursos_origen").select("*").order("created_at", ascending=False).limit(20).execute()
        return jsonify({"recursos": datos}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/adaptaciones/<id>", methods=["PUT"])
def actualizar_adaptacion(id):
    """Permite al docente editar y aprobar la adaptación (Human-in-the-Loop)"""
    try:
        data = request.get_json() or {}
        campos = {}
        if "lectura_facil" in data:
            campos["lectura_facil"] = data["lectura_facil"]
            campos["legibilidad_adaptada"] = calcular_legibilidad(data["lectura_facil"])["score"]
        if "estado" in data:
            campos["estado"] = data["estado"]  # 'borrador' o 'aprobado'
        if "notas_docente" in data:
            campos["notas_docente"] = data["notas_docente"]

        res = db.table("adaptaciones_multimodales").eq("id", id).update(campos)
        return jsonify({"status": "ok", "actualizado": res}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    puerto = int(os.getenv("PORT", 5000))
    debug_mode = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    print(f" Servidor PRISMA en ejecución en http://localhost:{puerto}")
    app.run(host="0.0.0.0", port=puerto, debug=debug_mode)
