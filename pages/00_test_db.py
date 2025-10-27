import streamlit as st

# ⛔️ Parche mínimo para evitar error si no existe pyodbc (como en Streamlit Cloud)
try:
    import pyodbc
except Exception:
    pyodbc = None

st.title("🔍 Prueba de lectura en Azure SQL Database")

# Si pyodbc no está disponible, mostrar aviso y detener esta página
if pyodbc is None:
    st.warning("⚠️ El módulo 'pyodbc' no está disponible en esta instancia (Streamlit Cloud). "
               "Esta página de prueba de conexión se ejecutará solo en modo local.")
    st.stop()

# Leer los secrets de Streamlit
server = st.secrets["azure_sql"]["server"]
database = st.secrets["azure_sql"]["database"]
username = st.secrets["azure_sql"]["username"]
password = st.secrets["azure_sql"]["password"]
driver = st.secrets["azure_sql"]["driver"]

try:
    conn = pyodbc.connect(
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password}",
        timeout=60
    )

    st.success("✅ Conexión establecida")

    cursor = conn.cursor()
    cursor.execute("SELECT @@VERSION;")
    version = cursor.fetchone()[0]

    st.write("Versión de SQL Server:")
    st.code(version)

    conn.close()

except Exception as e:
    st.error(f"❌ Error al conectar con Azure SQL: {e}")


