# ==========================================
# Página 18 — Estados de cuenta financieros
# ==========================================

import streamlit as st
import pyodbc

st.set_page_config(
    page_title="Paso 18: Estados de cuenta financieros",
    page_icon="🏦"
)

st.title("🏦 Paso 18 — Estados de cuenta financieros")

# ==============================
# FUNCIÓN CONEXIÓN SQL
# ==============================

def get_connection():
    return pyodbc.connect(
        f"DRIVER={{{st.secrets['azure_sql']['driver']}}};"
        f"SERVER={st.secrets['azure_sql']['server']};"
        f"DATABASE={st.secrets['azure_sql']['database']};"
        f"UID={st.secrets['azure_sql']['username']};"
        f"PWD={st.secrets['azure_sql']['password']};"
        "TrustServerCertificate=yes;"
    )

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
        name="CustomBody18",
        fontName=font_name,
        fontSize=10.5,
        leading=14,
        textColor=colors.black
    )

    title_style = ParagraphStyle(
        name="CustomTitle18",
        fontName=font_name,
        fontSize=15,
        leading=19,
        spaceAfter=12,
        textColor=colors.black
    )

    story = []
    story.append(Paragraph("Informe IA de comportamiento financiero", title_style))
    story.append(Paragraph(f"Cliente: {escape(str(cliente_id))}", body_style))
    story.append(Paragraph(dt.datetime.now().strftime("%d/%m/%Y %H:%M"), body_style))
    story.append(Spacer(1, 10))

    for raw in md_text.split("\n"):
        line = raw.strip()

        if not line:
            story.append(Spacer(1, 6))
            continue

        line = (
            line.replace("**", "")
                .replace("__", "")
                .replace("### ", "")
                .replace("## ", "")
                .replace("# ", "")
        )

        line = escape(line)

        story.append(Paragraph(line, body_style))

    doc.build(story)

    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes





# ==============================
# 1️⃣ DETECTAR ASESOR
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

# ==============================
# 3️⃣ CARGA ESTADOS DE CUENTA
# ==============================

st.subheader("Carga de estados de cuenta")

tipo_documento = st.selectbox(
    "Tipo de estado",
    ["BANCARIO", "TARJETA"]
)

uploaded_file = st.file_uploader(
    "Subir estado de cuenta PDF",
    type=["pdf"]
)

if st.button("Guardar estado de cuenta"):

    if not usuario or not cliente_id or uploaded_file is None:
        st.error("Complete los datos requeridos")
        st.stop()

    try:

        file_bytes = uploaded_file.read()
        file_name = uploaded_file.name

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO DocumentosFinancierosCliente
            (CedulaCliente, TipoDocumento, NombreArchivo,
             ArchivoPDF, UsuarioCarga, Asesor)
            VALUES (?,?,?,?,?,?)
        """,
        cliente_id,
        tipo_documento,
        file_name,
        file_bytes,
        usuario,
        usuario
        )

        conn.commit()
        conn.close()

        st.success("Estado de cuenta guardado correctamente")
        st.rerun()

    except Exception as e:
        st.error(f"Error al guardar: {e}")

# ==============================
# 4️⃣ LISTADO + VER + DESCARGAR + ELIMINAR
# ==============================

if cliente_id:

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT IdDocumento, TipoDocumento,
                   NombreArchivo, FechaCarga, UsuarioCarga
            FROM DocumentosFinancierosCliente
            WHERE CedulaCliente = ?
            AND Activo = 1
            ORDER BY FechaCarga DESC
        """, cliente_id)

        rows = cursor.fetchall()
        conn.close()

        if rows:

            st.subheader("📂 Estados de cuenta cargados")

            for r in rows:

                col1, col2, col3, col4 = st.columns([5,1,1,1])

                col1.markdown(f"""
**{r.TipoDocumento}**  
Archivo: {r.NombreArchivo}  
Fecha: {r.FechaCarga}  
Asesor: {r.UsuarioCarga}
""")

                # 👁️ VER
                if col2.button("👁️", key=f"ver_{r.IdDocumento}"):

                    conn = get_connection()
                    cursor = conn.cursor()

                    cursor.execute("""
                        SELECT ArchivoPDF
                        FROM DocumentosFinancierosCliente
                        WHERE IdDocumento = ?
                    """, r.IdDocumento)

                    pdf = cursor.fetchone()
                    conn.close()

                    if pdf:
                        st.download_button(
                            label="Abrir PDF",
                            data=pdf.ArchivoPDF,
                            file_name=r.NombreArchivo,
                            mime="application/pdf",
                            key=f"open_{r.IdDocumento}"
                        )

                # ⬇️ DESCARGAR
                if col3.button("⬇️", key=f"down_{r.IdDocumento}"):

                    conn = get_connection()
                    cursor = conn.cursor()

                    cursor.execute("""
                        SELECT ArchivoPDF
                        FROM DocumentosFinancierosCliente
                        WHERE IdDocumento = ?
                    """, r.IdDocumento)

                    pdf = cursor.fetchone()
                    conn.close()

                    if pdf:
                        st.download_button(
                            label="Descargar",
                            data=pdf.ArchivoPDF,
                            file_name=r.NombreArchivo,
                            mime="application/pdf",
                            key=f"download_{r.IdDocumento}"
                        )

                # 🗑️ ELIMINAR
                if col4.button("🗑️", key=f"del_{r.IdDocumento}"):

                    conn = get_connection()
                    cursor = conn.cursor()

                    cursor.execute("""
                        UPDATE DocumentosFinancierosCliente
                        SET Activo = 0
                        WHERE IdDocumento = ?
                    """, r.IdDocumento)

                    conn.commit()
                    conn.close()

                    st.success("Documento eliminado")
                    st.rerun()

        else:
            st.info("Este cliente no tiene estados de cuenta cargados.")

    except Exception as e:
        st.error(e)

# ==============================
# 5️⃣ ANÁLISIS IA FINANCIERO
# ==============================

import fitz
from openai import OpenAI

st.divider()
st.subheader("🧠 Análisis automático de comportamiento financiero")

if st.button("Analizar movimientos financieros con IA"):

    if not cliente_id:
        st.error("Debe indicar la cédula del cliente")
        st.stop()

    try:

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT TipoDocumento, ArchivoPDF
            FROM DocumentosFinancierosCliente
            WHERE CedulaCliente = ?
            AND Activo = 1
            ORDER BY FechaCarga
        """, cliente_id)

        docs = cursor.fetchall()
        conn.close()

        if not docs:
            st.warning("No hay estados de cuenta para analizar.")
            st.stop()

        texto_total = ""

        with st.spinner("Extrayendo movimientos financieros..."):

            for d in docs:
                tipo = d.TipoDocumento
                pdf_bytes = d.ArchivoPDF

                with fitz.open(stream=pdf_bytes, filetype="pdf") as pdf:
                    for page in pdf:
                        texto_total += f"\n\n--- ESTADO {tipo} ---\n"
                        texto_total += page.get_text()

        if len(texto_total.strip()) < 100:
            st.warning("No se pudo extraer texto útil de los estados.")
            st.stop()

        st.success("Texto financiero consolidado correctamente")

        # 🔎 Control interno opcional
        st.text_area(
            "Texto consolidado (control interno)",
            texto_total[:4000],
            height=250
        )

        # ==============================
        # 🧠 ENVÍO A IA
        # ==============================

        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

        prompt = f"""
Actúas como ANALISTA SENIOR DE RIESGO MICROFINANCIERO especializado en
interpretación forense de estados de cuenta bancarios.

Tu objetivo es determinar la verdadera capacidad de pago del cliente,
su rol operativo en el negocio y su nivel de riesgo financiero.

========================
ANÁLISIS REQUERIDO
========================

1️⃣ INGRESO REAL
- Estimar ingreso promedio mensual
- Evaluar estabilidad del ingreso
- Detectar dependencia de pocos clientes

2️⃣ ROL FINANCIERO DEL CLIENTE
Determinar si:
- administra el negocio
- es solo receptor de pagos
- traslada dinero a terceros
- hay retiros inmediatos tras ingresos

3️⃣ EGRESOS
Separar:
Gastos negocio:
- combustible
- compras inventario
- pagos operativos
Gastos personales:
- consumo familiar
- supermercados
- tiendas
- transferencias personales

4️⃣ CARGA FINANCIERA
- Detectar pagos tipo cuota
- Estimar acreedores
- Evaluar sobreendeudamiento

5️⃣ ESTRÉS FINANCIERO
- descapitalización rápida
- saldos bajos recurrentes
- dependencia del ingreso diario

6️⃣ FLUJO DE CAJA
- estimar flujo neto mensual
- capacidad potencial de pago

7️⃣ CLASIFICACIÓN FINAL
BAJO / MEDIO / ALTO

8️⃣ RECOMENDACIÓN CREDITICIA

Texto financiero:

{texto_total[:18000]}
"""

        with st.spinner("Analizando comportamiento financiero..."):

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Eres experto en análisis financiero microempresarial."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )

        analisis = response.choices[0].message.content

        st.success("Informe IA generado correctamente")
        st.markdown(analisis)

        # ==============================
        # 📄 GENERAR PDF DEL ANÁLISIS
        # ==============================

        pdf_bytes = generar_pdf_analisis(analisis, cliente_id)

        st.download_button(
            label="📄 Descargar informe financiero en PDF",
            data=pdf_bytes,
            file_name=f"Informe_financiero_{cliente_id}.pdf",
            mime="application/pdf"
        )

    except Exception as e:
        st.error(f"Error en análisis financiero IA: {e}")
