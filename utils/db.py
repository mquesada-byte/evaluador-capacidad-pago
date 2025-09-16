import pyodbc
import streamlit as st
import pandas as pd

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

    # Ventas Top-down
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

    # Ventas Bottom-up
    cursor.execute("""
        SELECT TOP 1 *
        FROM ventas_bottomup
        WHERE cliente_identificacion=?
        ORDER BY mes_iso DESC
    """, (cliente_id,))
    row3 = cursor.fetchone()
    if row3:
        cols3 = [col[0] for col in cursor.description]
        datos["ventas_bottomup"] = dict(zip(cols3, row3))

    # Ventas Paso 5
    cursor.execute("""
        SELECT TOP 1 *
        FROM ventas_p5
        WHERE cliente_identificacion=?
        ORDER BY mes_iso DESC
    """, (cliente_id,))
    row4 = cursor.fetchone()
    if row4:
        cols4 = [col[0] for col in cursor.description]
        datos["ventas_p5"] = dict(zip(cols4, row4))

    # Valoración asesor
    cursor.execute("""
        SELECT TOP 1 *
        FROM valoracion_asesor
        WHERE cliente_identificacion=?
        ORDER BY mes_iso DESC
    """, (cliente_id,))
    row5 = cursor.fetchone()
    if row5:
        cols5 = [col[0] for col in cursor.description]
        datos["valoracion_asesor"] = dict(zip(cols5, row5))

    conn.close()
    return datos


# ==========================================================
# TEST DE CONEXIÓN
# ==========================================================
if __name__ == "__main__":
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT GETDATE()")
        fecha = cursor.fetchone()[0]
        print("🔎 Conexión exitosa. Fecha/hora en SQL Server:", fecha)
        conn.close()
    except Exception as e:
        print("❌ No se pudo conectar:", e)






