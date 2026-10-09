-- ====================================================================
-- PROYECTO: PRISMA - Motor de Refracción Pedagógica DUA
-- RETO: Reto 03 · Un contenido, muchas formas de aprender (ProFuturo)
-- ====================================================================

-- 1. Habilitar extensión UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. Tabla de recursos originales subidos por el docente (cualquier formato)
CREATE TABLE IF NOT EXISTS recursos_origen (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    titulo TEXT NOT NULL,
    formato_origen TEXT NOT NULL, -- 'pdf', 'pptx', 'imagen', 'audio', 'video', 'texto'
    archivo_url TEXT,             -- URL pública o ruta en Supabase Storage
    contenido_extraido TEXT,       -- Texto base extraído / transcripción
    legibilidad_original NUMERIC(5,2), -- Índice Fernández-Huerta del original
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Tabla del espectro accesible generado por PRISMA
CREATE TABLE IF NOT EXISTS adaptaciones_multimodales (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recurso_id UUID REFERENCES recursos_origen(id) ON DELETE CASCADE,
    
    -- Salida 1: Lectura Fácil (Texto)
    lectura_facil TEXT,
    legibilidad_adaptada NUMERIC(5,2), -- Índice Fernández-Huerta adaptado (meta > 80)
    glosario JSONB DEFAULT '[]'::jsonb,
    
    -- Salida 2: Accesibilidad Auditiva (Audio)
    audio_mp3_url TEXT,

    -- Salida 2b: Ilustración referencial del tema (Cloudflare Workers AI)
    imagen_referencial_url TEXT,
    
    -- Salida 3: Accesibilidad Visual (Alt-Text pedagógico)
    descripcion_visual TEXT,
    
    -- Salida 4: Subtítulos
    subtitulos_vtt TEXT,
    
    -- Control docente (Human-in-the-Loop)
    estado TEXT DEFAULT 'borrador', -- 'borrador', 'editado', 'aprobado'
    notas_docente TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Tabla de sesiones de observación DUA (señales observables sin diagnóstico)
CREATE TABLE IF NOT EXISTS observaciones_dua (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    grupo_aula TEXT NOT NULL,         -- Ej: '3A_Primaria_Rural' (NUNCA datos personales)
    alias_alumno TEXT NOT NULL,       -- Ej: 'Estudiante 01'
    senales_observadas JSONB NOT NULL,-- Ej: ["fatiga_lectura", "atencion_breve"]
    estrategias_dua JSONB NOT NULL,   -- Estrategias pedagógicas recomendadas
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices de consulta rápida
CREATE INDEX IF NOT EXISTS idx_adaptaciones_recurso ON adaptaciones_multimodales(recurso_id);
CREATE INDEX IF NOT EXISTS idx_recursos_fecha ON recursos_origen(created_at DESC);
