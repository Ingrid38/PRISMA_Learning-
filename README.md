# PRISMA — Motor de Refracción Pedagógica DUA
> **Reto 03 · Un contenido, muchas formas de aprender (Premio ProFuturo)**  
> VII Edición Hack4Edu 2026 — Sede Internacional

PRISMA convierte cualquier recurso escolar convencional (PDF, presentación PPT, imagen, audio o video) en un espectro completo de formatos accesibles bajo el marco del Diseño Universal para el Aprendizaje (DUA).

---

## Estructura del Proyecto
- `app.py`: Servidor web Flask con endpoints REST.
- `schema.sql`: Script de base de datos relacional para Supabase (PostgreSQL).
- `legibilidad.py`: Motor de auditoría cuantitativa del Índice Fernández-Huerta (`textstat`).
- `Procfile`: Configuración de despliegue para Render.com (`gunicorn app:app`).
- `requirements.txt`: Dependencias del sistema (100% de código abierto y sin coste).

---

## Configuración Rápida
1. Clona el repositorio e instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
2. Configura tus variables de entorno copiando `.env.example` a `.env`:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `GEMINI_API_KEY`
3. Ejecuta el servidor localmente:
   ```bash
   python app.py
   ```
4. Despliega en Render.com vinculando tu repositorio de GitHub.
