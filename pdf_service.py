import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)

def generar_ficha_pdf(
    titulo: str,
    lectura_facil: str,
    glosario: list,
    descripcion_visual: str = None,
    score_original: float = None,
    score_adaptado: float = None,
    pautas_docente: str = None
) -> bytes:
    """
    Genera una ficha educativa en PDF accesible y lista para imprimir.
    Optimizado para lectura fácil (tipografía limpia, espaciado generoso, bajo consumo de tinta).
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    # Estilos accesibles con alto contraste
    style_header_brand = ParagraphStyle(
        'HeaderBrand',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=colors.HexColor('#0284c7'), # Cyan/Azul ProFuturo
        spaceAfter=2
    )

    style_title = ParagraphStyle(
        'AccessibleTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=8
    )

    style_student_bar = ParagraphStyle(
        'StudentBar',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#475569'),
        spaceAfter=12
    )

    style_section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#0369a1'),
        spaceBefore=10,
        spaceAfter=6
    )

    style_body_accessible = ParagraphStyle(
        'BodyAccessible',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=18, # Interlineado 1.5 para accesibilidad y dislexia
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=10
    )

    style_glossary_term = ParagraphStyle(
        'GlossaryTerm',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        textColor=colors.HexColor('#0f172a')
    )

    style_glossary_def = ParagraphStyle(
        'GlossaryDef',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor('#334155')
    )

    style_small_note = ParagraphStyle(
        'SmallNote',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#64748b')
    )

    elementos = []

    # 1. Encabezado institucional y marca del proyecto
    elementos.append(Paragraph("PRISMA · Motor de Refracción Pedagógica DUA | #hack4edu 2026", style_header_brand))
    elementos.append(Paragraph(f"{titulo}", style_title))
    
    # Barra de datos para el alumno en el aula física
    datos_alumno = "Estudiante: ____________________________________   Grado/Aula: ___________   Fecha: ____________"
    elementos.append(Paragraph(datos_alumno, style_student_bar))
    elementos.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cbd5e1'), spaceBefore=2, spaceAfter=10))

    # 2. Resumen Métrico de DUA (Auditoría Fernández-Huerta)
    if score_adaptado is not None:
        texto_metrica = f"<b>Auditoría DUA (Índice Fernández-Huerta):</b> Adaptado a Lectura Fácil con <b>{score_adaptado:.1f}/100</b> (Comprensión accesible)"
        if score_original is not None:
            texto_metrica += f" | Texto original: {score_original:.1f}/100"
        elementos.append(Paragraph(texto_metrica, style_small_note))
        elementos.append(Spacer(1, 8))

    # 3. Contenido en Lectura Fácil
    elementos.append(Paragraph("📖 Lectura Adaptada (Lectura Fácil)", style_section_heading))
    
    # Dividir el texto en párrafos limpios
    parrafos = lectura_facil.split("\n")
    for p in parrafos:
        p_clean = p.strip()
        if p_clean:
            elementos.append(Paragraph(p_clean, style_body_accessible))
    
    elementos.append(Spacer(1, 10))

    # 4. Glosario de Apoyo
    if glosario and len(glosario) > 0:
        elementos.append(Paragraph("📚 Glosario de Palabras Clave", style_section_heading))
        tabla_datos = []
        for item in glosario:
            termino = item.get("termino", "")
            definicion = item.get("significado_simple", "")
            p_term = Paragraph(f"• <b>{termino}</b>", style_glossary_term)
            p_def = Paragraph(definicion, style_glossary_def)
            tabla_datos.append([p_term, p_def])

        t_glosario = Table(tabla_datos, colWidths=[130, 400])
        t_glosario.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
            ('BOX', (0, 0), (-1, -1), 0.8, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#e2e8f0')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elementos.append(t_glosario)
        elementos.append(Spacer(1, 12))

    # 5. Descripción Visual (si aplica)
    if descripcion_visual and descripcion_visual.strip() and "sin elementos visuales" not in descripcion_visual.lower():
        elementos.append(Paragraph("👁️ Apoyo Visual y Esquema Explicativo", style_section_heading))
        elementos.append(Paragraph(descripcion_visual, style_body_accessible))
        elementos.append(Spacer(1, 8))

    # 6. Pauta DUA para el Docente
    if pautas_docente and pautas_docente.strip():
        elementos.append(Spacer(1, 6))
        pauta_box = [
            [Paragraph("<b>Orientación DUA para el docente:</b> " + pautas_docente, style_small_note)]
        ]
        t_pauta = Table(pauta_box, colWidths=[530])
        t_pauta.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f9ff')),
            ('BOX', (0, 0), (-1, -1), 0.8, colors.HexColor('#bae6fd')),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        elementos.append(KeepTogether(t_pauta))

    # Pie de página
    elementos.append(Spacer(1, 14))
    elementos.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#94a3b8'), spaceBefore=2, spaceAfter=4))
    elementos.append(Paragraph("Material generado con PRISMA · Diseño Universal para el Aprendizaje · Licencia Libre Educativa", style_small_note))

    # Construir documento PDF
    doc.build(elementos)
    return buffer.getvalue()
