import streamlit as st
import pyodbc

st.title("🔍 Prueba de lectura en SQL Server DataHub_OnPremise")

# =========================
# Leer configuración
# =========================

server = st.secrets["azure_sql"]["server"]
database = st.secrets["azure_sql"]["database"]
username = st.secrets["azure_sql"]["username"]
password = st.secrets["azure_sql"]["password"]
driver = st.secrets["azure_sql"]["driver"]

# =========================
# Conexión cacheada (rápida)
# =========================

@st.cache_resource
def create_connection():
    return pyodbc.connect(
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password}",
        timeout=60
    )

# =========================
# Conexión resiliente
# =========================

def get_connection():
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        return conn
    except:
        create_connection.clear()
        return create_connection()

# =========================
# Prueba de conexión
# =========================

try:
    conn = get_connection()

    st.success("✅ Conexión establecida")

    cursor = conn.cursor()
    cursor.execute("SELECT @@VERSION;")
    version = cursor.fetchone()[0]

    st.write("Versión de SQL Server:")
    st.code(version)

except Exception as e:
    st.error(f"❌ Error: {e}")
