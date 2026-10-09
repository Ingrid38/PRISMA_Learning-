# 🌈 PRISMA — Motor de Refracción Pedagógica DUA

> **VII Edición Internacional #hack4edu 2026** (Fundación ProFuturo, Telefónica y Universidad Pontificia de Salamanca)  
> **Reto 03 · *Un contenido, muchas formas de aprender*** (Especialidad Reto ProFuturo)  
> **Licencia:** MIT (Software Libre y de Código Abierto)

---

## 🎯 La Metáfora y el Propósito
En un aula diversa, los docentes se enfrentan al desafío de adaptar materiales diseñados para un "estudiante promedio" inexistente. 

Al igual que un **prisma óptico** toma un único haz de luz blanca y lo descompone en todo el espectro visible, **PRISMA** toma un único recurso rígido escolar (un documento denso, una ficha PDF, diapositivas PPTX o la foto de una pizarra) y lo **refracta en un espectro multimodal accesible** bajo el marco del **Diseño Universal para el Aprendizaje (DUA)**, permitiendo que todos los estudiantes aprendan en la misma clase sin estigmas ni segregación.

---

## 🚀 Características Principales

1. **Ingesta Multiformato (Entrada Universal):**
   - Textos planos y guías curriculares pegadas directamente.
   - Archivos PDF escolares (`pypdf`).
   - Presentaciones PowerPoint (`python-pptx`).
   - Imágenes e infografías de pizarras analizadas mediante visión artificial multirresolución (`Google Gemini Vision`).

2. **Refracción Pedagógica DUA (Salida Multimodal):**
   - **Lectura Fácil Adaptada:** Sintaxis directa (Sujeto + Verbo + Predicado), oraciones acotadas (12-15 palabras) y simplificación de sobrecarga cognitiva según normas europeas de inclusión.
   - **Locución Neuronal de Audio MP3 (Edge TTS):** Text-to-Speech de alta calidad con voz natural en español (`es-ES-AlvaroNeural`), alojado en Supabase Storage para estudiantes con baja visión o dificultades severas de decodificación lectora.
   - **Fichas Imprimibles en PDF (ReportLab):** Diseñadas bajo criterios de bajo consumo de tinta (B/N), tipografía de alta legibilidad, espaciado interlineal amplio y glosario tabular listo para entornos con conectividad limitada o nula.
   - **Glosario Contextual:** Explicación de términos abstractos con definiciones funcionales y ejemplos cotidianos.
   - **Descripción Visual Accesible (Alt-Text):** Explicación secuencial de esquemas, mapas conceptuales e infografías.
   - **Pautas de Mediación Docente:** Orientaciones didácticas inmediatas para dinamizar la sesión escolar.

3. **Auditoría Cuantitativa de Legibilidad:**
   - Medición matemática en tiempo real del **Índice Fernández-Huerta** (`textstat` en español).
   - Comprobación empírica en pantalla de cómo un texto escolar denso (score < 40, "Difícil") se transforma en lectura accesible (> 80-95, "Muy Fácil").

4. **Filtro Ético de Barreras Pedagógicas DUA:**
   - Selección de barreras pedagógicas observadas en el aula (vocabulario, sobrecarga atencional, baja visión, lengua originaria, ritmo gradual).
   - **Sin diagnósticos clínicos ni etiquetas estigmatizantes** de alumnos; registro ético y anónimo para mejora continua.

5. **Human-in-the-Loop y Biblioteca Docente:**
   - Editor interactivo en vivo que empodera al docente para ajustar el contenido antes de aprobarlo.
   - Botón de regeneración de audio al instante tras editar el texto.
   - Biblioteca de recursos sincronizada en Supabase con historial completo y descargas inmediatas.

---

## 🛠️ Arquitectura Técnica y Stack (Coste 0,00 €)

| Capa | Tecnología | Justificación |
|---|---|---|
| **Backend** | Python 3.11+, Flask 3.1.3, Gunicorn | Ligero, modular, estándar en producción y compatible con microservicios. |
| **Base de Datos & Storage** | **Supabase** (PostgreSQL + Buckets) | Almacenamiento relacional PostgREST con políticas de seguridad y CDN de audios. |
| **Motor de IA Multimodal** | **Google Gemini Flash Lite** / Groq LLaMA 3.3 | Inferencia ultra rápida (< 3 seg), gratuita en nivel tier y visión multimodal nativa. |
| **Text-to-Speech** | `edge-tts` (con fallback `gTTS`) | Voz neuronal de calidad humana en español sin requerir tarjeta de crédito ni API keys. |
| **Generación de Fichas** | `reportlab` | Renderizado vectorial de PDFs listos para imprimir a bajo coste de tinta. |
| **Auditoría de Texto** | `textstat` (Fernández-Huerta) | Evaluación algorítmica objetiva del nivel de accesibilidad lingüística. |
| **Frontend** | Tailwind CSS + Atkinson Hyperlegible | Interfaz moderna, responsiva, modo oscuro con contraste y tipografía accesible. |
| **Despliegue** | **Render.com** (Web Service gratuito) | Integración continua directa desde GitHub con `Procfile` y `render.yaml`. |

---

## 📁 Estructura del Repositorio

```text
PRISMA_LEARNING/
├── app.py                 # Servidor Flask principal y rutas REST de la API
├── ai_service.py          # Orquestador de inferencia multimodal y prompts DUA
├── audio_service.py       # Síntesis neuronal de voz y subida a Supabase Storage
├── pdf_service.py         # Maquetación de fichas imprimibles en PDF con ReportLab
├── parser_service.py      # Extracción de contenido en PDF, PPTX e imágenes
├── legibilidad.py         # Cálculo cuantitativo del Índice Fernández-Huerta
├── db.py                  # Cliente REST nativo para Supabase PostgREST & Storage
├── schema.sql             # Esquema DDL de tablas y políticas RLS para Supabase
├── Procfile               # Definición del proceso web de Gunicorn para Render
├── render.yaml            # Manifiesto de infraestructura como código (IaC) en Render
├── requirements.txt       # Dependencias de Python fijadas
├── templates/
│   └── index.html         # Interfaz web responsiva con editor DUA y biblioteca
├── LICENSE                # Licencia de código abierto MIT
└── README.md              # Documentación técnica del proyecto
```

---

## ⚙️ Instalación y Ejecución Local

### 1. Clonar el repositorio
```bash
git clone https://github.com/Ingrid38/PRISMA_Learning-.git
cd PRISMA_Learning-
```

### 2. Crear y activar entorno virtual
```bash
python -m venv venv
# En Windows:
venv\Scripts\activate
# En Linux / macOS:
source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno
Copia `.env.example` como `.env` y coloca tus claves gratuitas:
```env
SUPABASE_URL=https://TU_PROYECTO.supabase.co
SUPABASE_KEY=TU_SUPABASE_ANON_KEY
GEMINI_API_KEY=tu_clave_gratuita_de_google_ai_studio
PORT=5000
```

### 5. Iniciar la aplicación
```bash
python app.py
```
Abre tu navegador en `http://localhost:5000`.

---

## ☁️ Despliegue en Render.com

1. Sube este repositorio a tu cuenta de **GitHub**.
2. Ingresa a [Render.com](https://dashboard.render.com/) e inicia sesión.
3. Haz clic en **New +** ➔ **Web Service**.
4. Conecta tu repositorio de GitHub `PRISMA_LEARNING`.
5. Configura los siguientes campos:
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
6. En la pestaña **Environment Variables**, añade:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `GEMINI_API_KEY`
7. Haz clic en **Create Web Service**. ¡En 2 minutos tu servicio estará en línea con HTTPS gratuito!

---

## 👥 Equipo y Participación en #hack4edu 2026
* **Reto:** Reto 03 · *Un contenido, muchas formas de aprender* (Reto ProFuturo).
* **Entregables:** Repositorio en GitHub, Presentación Pitch de 5 diapositivas y Vídeo Demo de 3 minutos.
* **Licencia:** MIT License.
