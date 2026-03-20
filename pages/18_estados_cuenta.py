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
# 5️⃣ BOTÓN FUTURO IA
# ==============================

st.divider()

st.button("Analizar movimientos financieros con IA (próximamente)")
