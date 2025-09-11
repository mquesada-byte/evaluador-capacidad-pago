import streamlit as st
import pyodbc
import time

st.title("🔌 Prueba de conexión a Azure SQL Database")

# Leer los secrets de Streamlit
server = st.secrets["azure_sql"]["server"]
database = st.secrets["azure_sql"]["database"]
username = st.secrets["azure_sql"]["username"]
password = st.secrets["azure_sql"]["password"]
driver = st.secrets["azure_sql"]["driver"]

st.write("Intentando conectar a la base de datos...")

# Intentos con reintento automático
max_retries = 3
connected = False
conn = None

for intento in range(1, max_retries + 1):
    try:
        conn = pyodbc.connect(
            f"DRIVER={{{driver}}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password}",
            timeout=60  # ⏳ esperar hasta 60 segundos
        )

        st.success(f"✅ Conexión exitosa a Azure SQL Database (intento {intento})")
        connected = True
        break

    except Exception as e:
        st.warning(f"⚠️ Intento {intento} fallido: {e}")
        time.sleep(10)  # esperar 10 segundos antes del siguiente intento

if connected and conn:
    try:
        # Ejecutar consulta de prueba: listar tablas
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sys.tables")
        tablas = [row[0] for row in cursor.fetchall()]

        if tablas:
            st.write("📂 Tablas encontradas en la base de datos:")
            st.table(tablas)
        else:
            st.info("No se encontraron tablas en la base de datos.")

        conn.close()

    except Exception as e:
        st.error(f"❌ Error al ejecutar consulta: {e}")
else:
    st.error("❌ No se pudo establecer conexión después de varios intentos.")

