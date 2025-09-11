import pyodbc
import streamlit as st

def get_connection():
    """Devuelve una conexión a Azure SQL Database usando los secrets."""
    conn = pyodbc.connect(
        f"DRIVER={{{st.secrets['azure_sql']['driver']}}};"
        f"SERVER={st.secrets['azure_sql']['server']};"
        f"DATABASE={st.secrets['azure_sql']['database']};"
        f"UID={st.secrets['azure_sql']['username']};"
        f"PWD={st.secrets['azure_sql']['password']}",
        timeout=30
    )
    return conn


def load_visita(cliente_identificacion: str):
    """Carga un registro de visitas_credito por cédula. 
       Devuelve un dict con las columnas, o None si no existe."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM visitas_credito WHERE cliente_identificacion = ?", (cliente_identificacion,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    columns = [col[0] for col in cursor.description]
    data = dict(zip(columns, row))
    conn.close()
    return data
