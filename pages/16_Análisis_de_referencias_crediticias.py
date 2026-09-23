# ==========================================
# Página 16 — Carga de referencias crediticias
# ==========================================

import streamlit as st
import pyodbc
import fitz
from openai import OpenAI

st.set_page_config(
    page_title="Paso 16: Carga de referencias crediticias",
    page_icon="📄"
)

st.title("📄 Paso 16 — Carga de referencias crediticias")

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
# CLIENTE ACTIVO
# ==============================

cliente_id = st.session_state.get("cliente", {}).get("identificacion")

if not cliente_id:
    st.warning("Cargá un cliente antes de gestionar sus reportes crediticios.")
    st.stop()

usuario = (
    st.session_state.get("asesor", {}).get("nombre")
    or "Aplicacion"
)
numero_operacion = None

# ==============================
# 3️⃣ CARGA DOCUMENTOS
# ==============================

st.subheader("Carga de reportes")

if st.session_state.pop("reporte_pdf_guardado", False):
    st.success("Documento actualizado correctamente")

tipo_documento = st.selectbox(
    "Tipo de reporte",
    ["EQUIFAX", "CIC", "CREDID"]
)

uploaded_file = st.file_uploader(
    "Subir archivo PDF",
    type=["pdf"],
    key=f"reporte_pdf_{cliente_id}_{st.session_state.get('reporte_pdf_version', 0)}",
)

# Advertir sobre reemplazo solo si se seleccionó un nuevo PDF
if uploaded_file is not None:
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT TOP 1 NombreArchivo
            FROM dbo.DocumentosReferenciasCrediticias
            WHERE ClienteId = ? AND TipoDocumento = ?
            ORDER BY FechaCarga DESC
        """, cliente_id, tipo_documento)

        ex = cursor.fetchone()
        conn.close()

        if ex:
            st.warning(
                f"⚠️ Ya existe un reporte {tipo_documento}: "
                f"{ex.NombreArchivo}. Se reemplazará."
            )
    except Exception as e:
        st.error(f"No fue posible consultar el reporte existente: {e}")


# Guardar o reemplazar el reporte
if st.button("Guardar documento"):
    if uploaded_file is None:
        st.error("Seleccioná un archivo PDF antes de guardar.")
    else:
        try:
            file_bytes = uploaded_file.getvalue()
            file_size_kb = int(len(file_bytes) / 1024)
            file_name = uploaded_file.name

            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE dbo.DocumentosReferenciasCrediticias
                SET NumeroOperacion = NULL,
                    NombreArchivo = ?,
                    ArchivoPDF = ?,
                    PesoArchivoKB = ?,
                    FechaCarga = GETDATE(),
                    UsuarioCarga = ?,
                    VersionDocumento = VersionDocumento + 1
                WHERE ClienteId = ?
                  AND TipoDocumento = ?
            """,
                file_name, file_bytes, file_size_kb,
                usuario, cliente_id, tipo_documento
            )

            if cursor.rowcount == 0:
                cursor.execute("""
                    INSERT INTO dbo.DocumentosReferenciasCrediticias
                        (ClienteId, NumeroOperacion, TipoDocumento,
                         NombreArchivo, ArchivoPDF, PesoArchivoKB,
                         UsuarioCarga, VersionDocumento)
                    VALUES (?, NULL, ?, ?, ?, ?, ?, 1)
                """,
                    cliente_id, tipo_documento, file_name,
                    file_bytes, file_size_kb, usuario
                )

            conn.commit()
            conn.close()

            # Cambiar la clave del selector lo deja vacío tras guardar
            st.session_state["reporte_pdf_version"] = (
                st.session_state.get("reporte_pdf_version", 0) + 1
            )
            st.session_state["reporte_pdf_guardado"] = True
            st.rerun()

        except Exception as e:
            st.error(f"Error al guardar: {e}")

# ==============================
# DOCUMENTOS DEL CLIENTE
# Ver, descargar y eliminar
# ==============================

try:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT IdDocumento, TipoDocumento, NombreArchivo, ArchivoPDF,
               VersionDocumento, FechaCarga, UsuarioCarga, PesoArchivoKB
        FROM dbo.DocumentosReferenciasCrediticias
        WHERE ClienteId = ?
        ORDER BY FechaCarga DESC
    """, cliente_id)
    documentos = cursor.fetchall()
    conn.close()

    if documentos:
        st.subheader("📂 Documentos cargados")

        for doc in documentos:
            doc_id = int(doc.IdDocumento)
            pdf_bytes = bytes(doc.ArchivoPDF)
            documento_actual = (cliente_id, doc_id)

            st.markdown(
                f"**{doc.TipoDocumento}** — {doc.NombreArchivo}  \n"
                f"Versión: {doc.VersionDocumento} · "
                f"Fecha: {doc.FechaCarga:%d/%m/%Y %H:%M} · "
                f"Tamaño: {doc.PesoArchivoKB} KB"
            )

            col_ver, col_descargar, col_eliminar = st.columns(3)

            with col_ver:
                if st.button(
                    "👁️ Ver",
                    key=f"ver_ref_{doc_id}",
                    use_container_width=True,
                ):
                    if st.session_state.get("ref_pdf_abierto") == documento_actual:
                        st.session_state.pop("ref_pdf_abierto", None)
                    else:
                        st.session_state["ref_pdf_abierto"] = documento_actual

            with col_descargar:
                st.download_button(
                    "⬇️ Descargar",
                    data=pdf_bytes,
                    file_name=doc.NombreArchivo,
                    mime="application/pdf",
                    key=f"descargar_ref_{doc_id}",
                    use_container_width=True,
                )

            with col_eliminar:
                if st.button(
                    "🗑️ Eliminar",
                    key=f"eliminar_ref_{doc_id}",
                    use_container_width=True,
                ):
                    st.session_state["ref_confirmar_eliminar"] = documento_actual

            if st.session_state.get("ref_confirmar_eliminar") == documento_actual:
                st.warning(f"¿Eliminar el reporte {doc.TipoDocumento}: {doc.NombreArchivo}?")
                col_confirmar, col_cancelar = st.columns(2)

                with col_confirmar:
                    if st.button(
                        "Sí, eliminar",
                        key=f"confirmar_ref_{doc_id}",
                        use_container_width=True,
                    ):
                        try:
                            conn = get_connection()
                            cursor = conn.cursor()
                            cursor.execute("""
                                DELETE FROM dbo.DocumentosReferenciasCrediticias
                                WHERE IdDocumento = ? AND ClienteId = ?
                            """, doc_id, cliente_id)
                            conn.commit()
                            conn.close()

                            st.session_state.pop("ref_confirmar_eliminar", None)
                            if st.session_state.get("ref_pdf_abierto") == documento_actual:
                                st.session_state.pop("ref_pdf_abierto", None)
                            st.rerun()
                        except Exception as e:
                            st.error(f"No se pudo eliminar el reporte: {e}")

                with col_cancelar:
                    if st.button(
                        "Cancelar",
                        key=f"cancelar_ref_{doc_id}",
                        use_container_width=True,
                    ):
                        st.session_state.pop("ref_confirmar_eliminar", None)
                        st.rerun()

            if st.session_state.get("ref_pdf_abierto") == documento_actual:
                try:
                    with fitz.open(stream=pdf_bytes, filetype="pdf") as pdf:
                        total_paginas = len(pdf)
                        clave_pagina = f"pagina_actual_ref_{cliente_id}_{doc_id}"
                        st.session_state.setdefault(clave_pagina, 1)

                        pagina = min(
                            max(st.session_state[clave_pagina], 1),
                            total_paginas,
                        )

                        col_anterior, col_numero, col_siguiente = st.columns([1, 2, 1])

                        with col_anterior:
                            if st.button(
                                "⬅️ Anterior",
                                key=f"anterior_ref_{doc_id}",
                                disabled=pagina <= 1,
                                use_container_width=True,
                            ):
                                pagina -= 1
                                st.session_state[clave_pagina] = pagina

                        with col_numero:
                            st.markdown(
                                f"<p style='text-align:center'>"
                                f"<b>Página {pagina} de {total_paginas}</b></p>",
                                unsafe_allow_html=True,
                            )

                        with col_siguiente:
                            if st.button(
                                "Siguiente ➡️",
                                key=f"siguiente_ref_{doc_id}",
                                disabled=pagina >= total_paginas,
                                use_container_width=True,
                            ):
                                pagina += 1
                                st.session_state[clave_pagina] = pagina

                        imagen = pdf[pagina - 1].get_pixmap(
                            matrix=fitz.Matrix(1.5, 1.5)
                        ).tobytes("png")
                        st.image(imagen, use_container_width=True)

                except Exception as e:
                    st.error(f"No se pudo visualizar el PDF: {e}")

            st.divider()
    else:
        st.info("Este cliente aún no tiene reportes cargados.")

except Exception as e:
    st.error(f"No fue posible consultar los documentos: {e}")

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
            SELECT TOP 1 TipoDocumento, ArchivoPDF
            FROM DocumentosReferenciasCrediticias
            WHERE ClienteId = ?
            ORDER BY FechaCarga DESC
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
        Actúas como ANALISTA SENIOR DE RIESGO EN MICROFINANZAS EN COSTA RICA.
        
        Tu función es evaluar el comportamiento crediticio del cliente para decidir
        si es recomendable otorgar un microcrédito productivo.
        
        Debes realizar un análisis profundo orientado a detectar probabilidad de NO PAGO,
        más allá del score tradicional del buró.
        
        ========================
        CRITERIO MICROFINANCIERO LOCAL
        ========================
        
        1. Evalúa principalmente deudas con:
        - financieras
        - bancos
        - cooperativas
        - casas comerciales
        - prestamistas
        - créditos personales o de consumo
        
        2. Si existen cobros judiciales relacionados con estas entidades,
        considerarlo como señal de ALTO RIESGO.
        
        3. Si los cobros judiciales corresponden a:
        - CCSS
        - servicios públicos (electricidad, agua, telecomunicaciones)
        - municipalidades
        - impuestos
        
        Debes mencionarlos solo como contexto socioeconómico,
        pero NO debes concluir sobre sobreendeudamiento financiero ni mala cultura de pago
        basándote en esos casos.
        
        ========================
        ANÁLISIS REQUERIDO
        ========================
        
        Debes estructurar tu análisis en las siguientes secciones:
        
        1️⃣ PERFIL CONDUCTUAL DE PAGO
        
        Describe cómo se comporta el cliente financieramente:
        
        - ordenado / desordenado
        - reactivo / preventivo
        - dependiente de crédito
        - uso intensivo de financiamiento
        - tendencia a atrasos
        - cultura de cancelación puntual
        - señales de estrés financiero
        - posible fragilidad económica
        
        2️⃣ NIVEL DE ENDEUDAMIENTO REAL
        
        Analiza:
        
        - saldo total
        - cuota mensual estimada
        - cantidad de créditos activos
        - concentración de deuda
        - posible sobreapalancamiento
        
        3️⃣ MOROSIDAD HISTÓRICA
        
        Determina:
        
        - existencia de atrasos recurrentes
        - duración de la mora
        - refinanciamientos
        - cancelaciones tardías
        - castigos o cuentas incobrables
        
        4️⃣ CONSULTAS RECIENTES
        
        Evalúa si el cliente:
        
        - está buscando financiamiento activamente
        - presenta incremento acelerado de consultas
        - muestra señales de necesidad urgente de liquidez
        
        5️⃣ SEÑALES TEMPRANAS DE POSIBLE NO PAGO
        
        Debes identificar pistas como:
        
        - aumento reciente del endeudamiento
        - comportamiento irregular de pago
        - múltiples créditos de consumo
        - cobros judiciales financieros
        - saldos elevados para su perfil
        - presión financiera acumulada
        - dependencia del crédito para sostener su flujo
        
        6️⃣ CLASIFICACIÓN FINAL DE RIESGO
        
        Clasifica el cliente como:
        
        BAJO  
        MEDIO  
        ALTO  
        
        7️⃣ RECOMENDACIÓN MICROFINANCIERA
        
        Indica:
        
        - si se puede otorgar crédito o no
        - si requiere monto reducido
        - si requiere plazo corto
        - si requiere garantía o seguimiento
        - si se debe esperar antes de aprobar
        
        Tu análisis debe ser claro, técnico y práctico,
        como si fueras el jefe de crédito de una institución microfinanciera.
        
        Texto de los reportes:
        
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
