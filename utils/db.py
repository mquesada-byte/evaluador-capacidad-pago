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


def load_visita(cliente_id: str) -> dict | None:
    conn = get_connection()
    cursor = conn.cursor()

    # Cliente/negocio/asesor
    cursor.execute("SELECT * FROM visitas_credito WHERE cliente_identificacion=?", (cliente_id,))
    row1 = cursor.fetchone()

    if not row1:
        conn.close()
        return None

    datos = dict(zip([col[0] for col in cursor.description], row1))

    # Ventas Top-down (último registro)
    cursor.execute("""
        SELECT TOP 1 *
        FROM ventas_topdown
        WHERE cliente_identificacion=?
        ORDER BY mes_iso DESC
    """, (cliente_id,))
    row2 = cursor.fetchone()

    if row2:
        cols2 = [col[0] for col in cursor.description]
        datos["ventas_topdown"] = dict(zip(cols2, row2))

    conn.close()
    return datos
