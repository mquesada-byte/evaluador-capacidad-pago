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
