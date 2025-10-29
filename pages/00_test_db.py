import streamlit as st
import sys
from sqlalchemy import create_engine, text

st.title("🔍 Prueba de lectura en Azure SQL Database")

# Leer los secrets de Streamlit
server = st.secrets["azure_sql"]["server"]
database = st.secrets["azure_sql"]["database"]
username = st.secrets["azure_sql"]["username"]
password = st.secrets["azure_sql"]["password"]

def get_engine():
    if sys.platform == "win32":
        # Windows: usa ODBC Driver 18 + pyodbc
        conn_url = (
            "mssql+pyodbc://{USER}:{PWD}@{SERVER}:1433/{DB}"
            "?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no"
        ).format(
            USER=username,
            PWD=password,
            SERVER=server,
            DB=database,
        )
    else:
        # Linux (Streamlit Cloud): usa python-tds
        conn_url = (
            "mssql+pytds://{USER}:{PWD}@{SERVER}:1433/{DB}?encrypt=true"
        ).format(
            USER=username,
            PWD=password,
            SERVER=server,
            DB=database,
        )
    return create_engine(conn_url, pool_pre_ping=True)

try:
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("SELECT @@VERSION;"))
        version = result.scalar()

    st.success("✅ Conexión establecida")
    st.write("Versión de SQL Server:")
    st.code(version)

except Exception as e:
    st.error(f"❌ Error: {e}")
