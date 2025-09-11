import streamlit as st
import pyodbc

st.title("🔌 Prueba de conexión a Azure SQL Database")

# Leer los secrets de Streamlit
server = st.secrets["azure_sql"]["server"]
database = st.secrets["azure_sql"]["database"]
username = st.secrets["azure_sql"]["username"]
password = st.secrets["azure_sql"]["password"]
driver = st.secrets["azure_sql"]["driver"]

st.write("Intentando conectar a la base de datos...")

try:
    # Conectar
    conn = pyodbc.connect(
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password}"
    )

    st.success("✅ Conexión exitosa a Azure SQL Database")

    # Ejecutar consulta de prueba: listar tablas
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sys.tables")
    tablas = [row[0] for row in cursor.fetchall()]

    if tablas:
        st.write("Tablas encontradas en la base de datos:")
        st.table(tablas)
    else:
        st.info("No se encontraron tablas en la base de datos.")

    conn.close()

except Exception as e:
    st.error(f"❌ Error de conexión: {e}")
