# ==========================================
# Página 17 — Análisis de referencias crediticias
# ==========================================

import streamlit as st
import pyodbc

st.set_page_config(
    page_title="Paso 17: Análisis de referencias crediticias",
    page_icon="📄"
)

st.title("📄 Paso 17 — Análisis de referencias crediticias")

# ==============================
# FUNCIÓN CONEXIÓN SQL
# ==============================

def get_connection():
    return pyodbc.connect(
        "DRIVER={SQL Server};"
        "SERVER=TU_SERVIDOR;"
        "DATABASE=DataHub_OnPremise;"
        "Trusted_Connection=yes;"
    )

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
