import streamlit as st
import pyodbc

st.title("🔍 Prueba de lectura en Azure SQL Database")

# Leer los secrets de Streamlit
server = st.secrets["azure_sql"]["server"]
database = st.secrets["azure_sql"]["database"]
username = st.secrets["azure_sql"]["username"]
password = st.secrets["azure_sql"]["password"]
driver = st.secrets["azure_sql"]["driver"]

# ----------------------------------------------------------------------------------------
# Mantener la conexión a SQL Server en memoria.
# Streamlit reutiliza esta conexión entre ejecuciones para evitar abrir
# una nueva conexión en cada consulta y así mejorar el rendimiento.

@st.cache_resource
def get_connection():
    return pyodbc.connect(
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password}",
        timeout=60
    )

# ----------------------------------------------------------------------------------------

try:
    conn = get_connection()
    # conn = pyodbc.connect(
        # f"DRIVER={{{driver}}};"
        # f"SERVER={server};"
        # f"DATABASE={database};"
        # f"UID={username};"
        # f"PWD={password}",
        # timeout=60
    # )

    st.success("✅ Conexión establecida")

    cursor = conn.cursor()
    cursor.execute("SELECT @@VERSION;")
    version = cursor.fetchone()[0]

    st.write("Versión de SQL Server:")
    st.code(version)

    # conn.close()

except Exception as e:
    st.error(f"❌ Error: {e}")
