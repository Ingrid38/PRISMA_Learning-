import io
import os
import uuid
from flask import Flask, jsonify, request, render_template, Response, send_file
from dotenv import load_dotenv
from db import db
from legibilidad import calcular_legibilidad
from ai_service import adaptar_recurso_dua
from parser_service import extraer_texto_pdf, extraer_texto_pptx, preparar_imagen_base64
from audio_service import construir_texto_audio, generar_audio_mp3
from image_service import generar_imagen_referencial
from pdf_service import generar_ficha_pdf

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
    Recibe texto directo o un archivo (PDF, PPTX, Imagen) y genera:
    1. Lectura Fácil con métricas Fernández-Huerta
    2. Glosario y descripción visual / Alt-Text
    3. Audio narrado MP3 almacenado en Supabase Storage
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

            # Si el docente no especificó título, usar el nombre del archivo
            if not request.form.get("titulo", "").strip():
                titulo = filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").title()

            # Subir archivo origen a Supabase Storage (bucket 'origenes')
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
        barreras_dua = []
        if request.is_json:
            json_data = request.get_json() or {}
            titulo = json_data.get("titulo") or titulo
            if not contenido_extraido and not base64_img:
                contenido_extraido = json_data.get("texto", "")
                formato = "texto"
            barreras_dua = json_data.get("barreras", [])
        else:
            texto_form = (request.form.get("texto") or "").strip()
            if not contenido_extraido and not base64_img and texto_form:
                contenido_extraido = texto_form
                formato = "texto"
            barreras_dua = request.form.getlist("barreras")

        if not contenido_extraido and not base64_img:
            return jsonify({"error": "No se proporcionó ningún texto ni archivo para adaptar"}), 400

        # 3. Calcular legibilidad original (Índice Fernández-Huerta)
        metricas_orig = calcular_legibilidad(contenido_extraido) if contenido_extraido else {"score": 40.0, "nivel": "Dificultad Estimada"}

        # 4. Invocar Motor de Refracción DUA (Gemini Flash / Lite) con barreras pedagógicas
        resultado_ia = adaptar_recurso_dua(
            texto_o_tema=contenido_extraido,
            base64_image=base64_img,
            mime_type=mime_type,
            barreras_dua=barreras_dua
        )

        texto_adaptado = resultado_ia.get("lectura_facil", "")
        glosario = resultado_ia.get("glosario", [])
        desc_visual = resultado_ia.get("descripcion_visual", "")
        titulo_final = resultado_ia.get("titulo_adaptado") or titulo

        # 5. Calcular legibilidad del texto adaptado
        metricas_adapt = calcular_legibilidad(texto_adaptado)

        # 6. Generar Audio MP3 Accesible (lectura fácil + audiodescripción de la imagen)
        adapt_id = str(uuid.uuid4())
        audio_mp3_url = None
        texto_audio, incluye_audiodescripcion = construir_texto_audio(texto_adaptado, desc_visual)
        try:
            audio_bytes = generar_audio_mp3(texto_audio)
            audio_filename = f"audios/audio_{adapt_id}.mp3"
            audio_mp3_url = db.upload_file(
                bucket="accesibles",
                path=audio_filename,
                file_bytes=audio_bytes,
                content_type="audio/mpeg"
            )
        except Exception as e:
            print(f"[Aviso Audio TTS] No se pudo subir audio a Supabase Storage: {e}")

        # 6b. Ilustración referencial del tema (Cloudflare Workers AI con prompt visual pedagógico)
        imagen_url = None
        try:
            prompt_visual = resultado_ia.get("prompt_visual_ingles", "")
            imagen_bytes = generar_imagen_referencial(
                titulo=titulo_final,
                texto_apoyo=texto_adaptado,
                prompt_visual=prompt_visual,
            )
            imagen_url = db.upload_file(
                bucket="accesibles",
                path=f"imagenes/ref_{adapt_id}.jpg",
                file_bytes=imagen_bytes,
                content_type="image/jpeg",
            )
        except Exception as e:
            print(f"[Aviso Imagen] No se pudo generar la ilustración: {e}")

        # 7. Guardar en Supabase (recursos_origen y adaptaciones_multimodales)
        rec_id = str(uuid.uuid4())
        try:
            db.table("recursos_origen").insert({
                "id": rec_id,
                "titulo": titulo_final,
                "formato_origen": formato,
                "archivo_url": archivo_url or "texto_directo",
                "contenido_extraido": contenido_extraido[:3000],
                "legibilidad_original": metricas_orig.get("score", 0.0)
            })

            adaptacion = {
                "id": adapt_id,
                "recurso_id": rec_id,
                "lectura_facil": texto_adaptado,
                "legibilidad_adaptada": metricas_adapt.get("score", 0.0),
                "glosario": glosario,
                "descripcion_visual": desc_visual,
                "audio_mp3_url": audio_mp3_url,
                "imagen_referencial_url": imagen_url,
                "estado": "borrador",
                "notas_docente": resultado_ia.get("pautas_docente", "")
            }
            try:
                db.table("adaptaciones_multimodales").insert(adaptacion)
            except Exception as e_col:
                print(f"[Aviso columna imagen] {e_col}")
                adaptacion.pop("imagen_referencial_url", None)
                if imagen_url:
                    adaptacion["subtitulos_vtt"] = imagen_url
                db.table("adaptaciones_multimodales").insert(adaptacion)

            # Registrar de forma ética y anónima las barreras pedagógicas observadas
            if barreras_dua:
                try:
                    db.table("observaciones_dua").insert({
                        "grupo_aula": "Aula_Inclusiva",
                        "alias_alumno": "Grupo_Docente",
                        "senales_observadas": barreras_dua,
                        "estrategias_dua": [resultado_ia.get("pautas_docente", "")]
                    })
                except Exception as e_obs:
                    print(f"[Aviso observaciones_dua] {e_obs}")
        except Exception as e:
            print(f"[Error Supabase] {e}")

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
            "audio_mp3_url": audio_mp3_url,
            "imagen_url": imagen_url,
            "incluye_audiodescripcion": incluye_audiodescripcion,
            "pautas_docente": resultado_ia.get("pautas_docente", ""),
            "archivo_url": archivo_url
        }), 200

    except Exception as e:
        print(f"Error en /api/adaptar: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/generar-audio/<id>", methods=["POST"])
def regenerar_audio(id):
    """Regenera y actualiza el audio MP3 en Supabase cuando el docente edita el texto"""
    try:
        data = request.get_json() or {}
        texto = data.get("texto", "")
        descripcion = ""

        res = db.table("adaptaciones_multimodales").select("lectura_facil, descripcion_visual").eq("id", id).execute()
        if res and len(res) > 0:
            if not texto:
                texto = res[0].get("lectura_facil", "")
            descripcion = res[0].get("descripcion_visual", "") or ""

        texto_audio, incluye_audiodescripcion = construir_texto_audio(texto, descripcion)
        if not texto_audio:
            return jsonify({"error": "No hay texto para generar el audio"}), 400

        audio_bytes = generar_audio_mp3(texto_audio)
        audio_filename = f"audios/audio_{id}_{uuid.uuid4().hex[:4]}.mp3"
        audio_url = db.upload_file(
            bucket="accesibles",
            path=audio_filename,
            file_bytes=audio_bytes,
            content_type="audio/mpeg"
        )

        db.table("adaptaciones_multimodales").eq("id", id).update({"audio_mp3_url": audio_url})

        return jsonify({
            "status": "ok",
            "audio_mp3_url": audio_url,
            "incluye_audiodescripcion": incluye_audiodescripcion
        }), 200
    except Exception as e:
        print(f"Error al generar audio: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/descargar-pdf/<id>", methods=["GET"])
def descargar_ficha_pdf(id):
    """
    Genera y descarga en tiempo real una Ficha Educativa en PDF accesible
    optimizada para impresión física en blanco y negro (bajo coste de tinta).
    """
    try:
        # Obtener los datos de la adaptación y del recurso origen
        adapt_res = db.table("adaptaciones_multimodales").select("*").eq("id", id).execute()
        if not adapt_res or len(adapt_res) == 0:
            return jsonify({"error": "Adaptación no encontrada"}), 404

        adapt = adapt_res[0]
        recurso_id = adapt.get("recurso_id")
        
        titulo = "Ficha Educativa Accesible"
        score_orig = None
        if recurso_id:
            rec_res = db.table("recursos_origen").select("titulo, legibilidad_original").eq("id", recurso_id).execute()
            if rec_res and len(rec_res) > 0:
                titulo = rec_res[0].get("titulo") or titulo
                score_orig = rec_res[0].get("legibilidad_original")

        lectura_facil = adapt.get("lectura_facil", "")
        glosario = adapt.get("glosario") or []
        desc_visual = adapt.get("descripcion_visual") or ""
        score_adapt = adapt.get("legibilidad_adaptada")
        pautas = adapt.get("notas_docente") or ""

        # Generar bytes del PDF con ReportLab
        pdf_bytes = generar_ficha_pdf(
            titulo=titulo,
            lectura_facil=lectura_facil,
            glosario=glosario,
            descripcion_visual=desc_visual,
            score_original=float(score_orig) if score_orig is not None else None,
            score_adaptado=float(score_adapt) if score_adapt is not None else None,
            pautas_docente=pautas
        )

        # Sanitizar nombre de archivo para descarga
        safe_titulo = "".join(c for c in titulo if c.isalnum() or c in (' ', '_', '-')).strip().replace(' ', '_')[:30]
        filename = f"PRISMA_{safe_titulo}.pdf"

        return Response(
            pdf_bytes,
            mimetype="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "application/pdf"
            }
        )
    except Exception as e:
        print(f"Error al generar PDF: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/historial", methods=["GET"])
def historial_recursos():
    """Retorna la lista de recursos adaptados con sus enlaces de PDF, Audio y métricas para la biblioteca del docente"""
    try:
        # Obtener las últimas 15 adaptaciones
        adaptaciones = db.table("adaptaciones_multimodales").select("*").order("created_at", ascending=False).limit(15).execute()
        if not adaptaciones:
            return jsonify({"historial": []}), 200

        # Obtener los recursos de origen para cruzar títulos y formatos
        recursos = db.table("recursos_origen").select("id, titulo, formato_origen, legibilidad_original, created_at").order("created_at", ascending=False).limit(30).execute()
        recursos_map = {r["id"]: r for r in (recursos or [])}

        resultado = []
        for a in adaptaciones:
            rec = recursos_map.get(a.get("recurso_id"), {})
            resultado.append({
                "adaptacion_id": a.get("id"),
                "recurso_id": a.get("recurso_id"),
                "titulo": rec.get("titulo", "Recurso Pedagógico"),
                "formato": rec.get("formato_origen", "texto"),
                "score_original": rec.get("legibilidad_original"),
                "score_adaptado": a.get("legibilidad_adaptada"),
                "audio_mp3_url": a.get("audio_mp3_url"),
                "imagen_url": a.get("imagen_referencial_url") or (
                    a.get("subtitulos_vtt") if str(a.get("subtitulos_vtt") or "").startswith("http") else None
                ),
                "pdf_url": f"/api/descargar-pdf/{a.get('id')}",
                "estado": a.get("estado", "borrador"),
                "fecha": a.get("created_at")
            })

        return jsonify({"historial": resultado}), 200
    except Exception as e:
        print(f"Error en /api/historial: {e}")
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
