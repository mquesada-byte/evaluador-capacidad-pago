import streamlit as st
import pyodbc

st.title("🔍 Prueba de lectura en Azure SQL Database")

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
    err_msg = str(e)
    if "40613" in err_msg or "not currently available" in err_msg:
        st.warning("⚠️ No se ha podido conectar a la base de datos. Intente nuevamente en unos minutos.")
    else:
        st.error(f"❌ Error inesperado: {err_msg}")



