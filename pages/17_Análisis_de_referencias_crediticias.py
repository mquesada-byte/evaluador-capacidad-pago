# ==========================================
# Página 17 — Análisis de referencias crediticias
# ==========================================

import streamlit as st
import pyodbc
import fitz
from openai import OpenAI

st.set_page_config(
    page_title="Paso 17: Análisis de referencias crediticias",
    page_icon="📄"
)

st.title("📄 Paso 17 — Análisis de referencias crediticias")

# ==============================
# FUNCIÓN CONEXIÓN SQL
# ==============================

def get_connection():
    import streamlit as st
    import pyodbc

    return pyodbc.connect(
        f"DRIVER={{{st.secrets['azure_sql']['driver']}}};"
        f"SERVER={st.secrets['azure_sql']['server']};"
        f"DATABASE={st.secrets['azure_sql']['database']};"
        f"UID={st.secrets['azure_sql']['username']};"
        f"PWD={st.secrets['azure_sql']['password']};"
        "TrustServerCertificate=yes;"
    )

# ==============================
# FUNCIÓN PDF DEL ANÁLISIS
# ==============================

def generar_pdf_analisis(md_text: str, cliente_id: str) -> bytes:
    import io
    import datetime as dt
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.pagesizes import LETTER
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib import colors
    from xml.sax.saxutils import escape

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        leftMargin=40,
        rightMargin=40,
        topMargin=48,
        bottomMargin=36
    )

    try:
        pdfmetrics.registerFont(TTFont("DejaVu", "DejaVuSans.ttf"))
        font_name = "DejaVu"
    except Exception:
        font_name = "Helvetica"

    styles = getSampleStyleSheet()

    body_style = ParagraphStyle(
        name="CustomBody17",
        fontName=font_name,
        fontSize=10.5,
        leading=14,
        textColor=colors.black
    )

    title_style = ParagraphStyle(
        name="CustomTitle17",
        fontName=font_name,
        fontSize=15,
        leading=19,
        spaceAfter=12,
        textColor=colors.black
    )

    story = []
    story.append(Paragraph("Análisis de referencias crediticias", title_style))
    story.append(Paragraph(f"Cliente: {escape(str(cliente_id))}", body_style))
    story.append(Paragraph(dt.datetime.now().strftime("%d/%m/%Y %H:%M"), body_style))
    story.append(Spacer(1, 10))

    for raw in md_text.split("\n"):
        line = raw.strip()

        if not line:
            story.append(Spacer(1, 6))
            continue

        # Limpieza mínima de markdown para PDF
        line = (
            line.replace("**", "")
                .replace("__", "")
                .replace("### ", "")
                .replace("## ", "")
                .replace("# ", "")
        )

        # Escapar caracteres especiales HTML/XML
        line = escape(line)

        story.append(Paragraph(line, body_style))

    doc.build(story)

    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

# ==============================
# 1️⃣ DETECTAR ASESOR AUTOMÁTICO
# ==============================

usuario = None

if "asesor" in st.session_state and st.session_state.asesor.get("nombre"):
    usuario = st.session_state.asesor["nombre"]
    st.success(f"Asesor detectado: {usuario}")
else:
    usuario = st.text_input("Nombre del asesor *")

# ==============================
# 2️⃣ IDENTIFICACIÓN CLIENTE
# ==============================

cliente_id = st.text_input("Número de cédula cliente (sin guiones) *")
numero_operacion = st.text_input("Número de operación (solo recrédito)")

# ==============================
# 3️⃣ CARGA DOCUMENTOS
# ==============================

st.subheader("Carga de reportes")

tipo_documento = st.selectbox(
    "Tipo de reporte",
    ["EQUIFAX", "CIC", "CREDID"]
)

uploaded_file = st.file_uploader("Subir archivo PDF", type=["pdf"])

if st.button("Guardar documento"):

    if not usuario:
        st.error("Debe indicar el nombre del asesor")
        st.stop()

    if not cliente_id:
        st.error("Debe indicar la cédula del cliente")
        st.stop()

    if uploaded_file is None:
        st.error("Debe cargar un archivo PDF")
        st.stop()

    try:
        file_bytes = uploaded_file.read()
        file_size_kb = int(len(file_bytes) / 1024)
        file_name = uploaded_file.name

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT ISNULL(MAX(VersionDocumento),0)+1
            FROM DocumentosReferenciasCrediticias
            WHERE ClienteId = ?
            AND TipoDocumento = ?
        """, cliente_id, tipo_documento)

        version = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO DocumentosReferenciasCrediticias
            (ClienteId, NumeroOperacion, TipoDocumento,
             NombreArchivo, ArchivoPDF, PesoArchivoKB,
             UsuarioCarga, VersionDocumento)
            VALUES (?,?,?,?,?,?,?,?)
        """,
        cliente_id,
        numero_operacion if numero_operacion != "" else None,
        tipo_documento,
        file_name,
        file_bytes,
        file_size_kb,
        usuario,
        version
        )

        conn.commit()
        conn.close()

        st.success(f"Documento cargado correctamente. Versión {version}")

    except Exception as e:
        st.error(f"Error al guardar: {e}")

# ==============================
# 4️⃣ MOSTRAR DOCUMENTOS EXISTENTES
# ==============================

if cliente_id:

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT TipoDocumento,
                   NombreArchivo,
                   VersionDocumento,
                   FechaCarga,
                   UsuarioCarga,
                   PesoArchivoKB
            FROM DocumentosReferenciasCrediticias
            WHERE ClienteId = ?
            ORDER BY TipoDocumento, VersionDocumento DESC
        """, cliente_id)

        rows = cursor.fetchall()
        conn.close()

        if rows:
            st.subheader("📂 Documentos cargados")

            for r in rows:
                st.markdown(
                    f"""
                    **{r.TipoDocumento}**  
                    Archivo: {r.NombreArchivo}  
                    Versión: {r.VersionDocumento}  
                    Fecha: {r.FechaCarga}  
                    Asesor: {r.UsuarioCarga}  
                    Tamaño: {r.PesoArchivoKB} KB
                    """
                )
                st.divider()
        else:
            st.info("Este cliente aún no tiene reportes cargados.")

    except Exception as e:
        st.error(f"No fue posible consultar documentos: {e}")


# ==============================
# 5️⃣ ANÁLISIS IA AUTOMÁTICO
# ==============================

st.divider()
st.subheader("🧠 Análisis automático de referencias")

if st.button("Generar análisis IA"):

    if not cliente_id:
        st.error("Debe indicar la cédula del cliente")
        st.stop()

    try:

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT TipoDocumento, ArchivoPDF
            FROM DocumentosReferenciasCrediticias A
            WHERE ClienteId = ?
            AND VersionDocumento = (
                SELECT MAX(VersionDocumento)
                FROM DocumentosReferenciasCrediticias
                WHERE ClienteId = A.ClienteId
                AND TipoDocumento = A.TipoDocumento
            )
        """, cliente_id)

        docs = cursor.fetchall()
        conn.close()

        if not docs:
            st.warning("No hay reportes para analizar.")
            st.stop()

        texto_total = ""

        for d in docs:
            tipo = d.TipoDocumento
            pdf_bytes = d.ArchivoPDF

            with fitz.open(stream=pdf_bytes, filetype="pdf") as pdf:
                for page in pdf:
                    texto_total += f"\n\n--- REPORTE {tipo} ---\n"
                    texto_total += page.get_text()

        if len(texto_total.strip()) < 50:
            st.warning("No se pudo extraer texto útil del PDF.")
            st.stop()

        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

        prompt = f"""
        Analiza el siguiente historial de referencias crediticias.

        Objetivo:
        Determinar riesgo de crédito para microcrédito.

        Evalúa:

        - nivel de endeudamiento
        - morosidad histórica
        - comportamiento de pago
        - consultas recientes
        - concentración de deuda
        - señales de sobreendeudamiento
        - riesgo global (BAJO / MEDIO / ALTO)

        Texto reportes:

        {texto_total[:15000]}
        """

        with st.spinner("Analizando referencias crediticias..."):
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Eres analista experto en riesgo microfinanciero."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )

        analisis = response.choices[0].message.content

        st.success("Análisis generado correctamente")
        st.markdown(analisis)

        # ==============================
        # 📄 GENERAR PDF DEL ANÁLISIS
        # ==============================

        pdf_bytes = generar_pdf_analisis(analisis, cliente_id)

        st.download_button(
            label="📄 Descargar análisis en PDF",
            data=pdf_bytes,
            file_name=f"Analisis_crediticio_{cliente_id}.pdf",
            mime="application/pdf"
        )

    except Exception as e:
        st.error(f"Error en análisis IA: {e}")
