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

    # Ventas Bottom-up (último registro)
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

    conn.close()
    return datos


def save_ventas_bottomup(cliente_id: str, data: dict) -> bool:
    """
    Inserta o actualiza un registro en la tabla ventas_bottomup
    según cliente_id + mes_iso.
    - Si no_data=1 -> se limpian todos los valores y se guarda el flag.
    - Nunca borra registros.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Verificar si ya existe un registro para este cliente y mes
        cursor.execute("""
            SELECT COUNT(*)
            FROM ventas_bottomup
            WHERE cliente_identificacion=? AND mes_iso=?
        """, (cliente_id, data.get("mes_iso")))
        existe = cursor.fetchone()[0] > 0

        if data.get("no_data") == 1:
            # Sobrescribir a "sin datos"
            unidad_clientes = None
            clientes_valor = None
            dias_abiertos = None
            semanas_abiertas = None
            ticket_promedio_colones = None
            ventas_estimadas_colones = None
            comentario = data.get("comentario")
        else:
            # Guardar valores reales
            unidad_clientes = data.get("unidad_clientes")
            clientes_valor = data.get("clientes_valor")
            dias_abiertos = data.get("dias_abiertos")
            semanas_abiertas = data.get("semanas_abiertas")
            ticket_promedio_colones = data.get("ticket_promedio_colones")
            ventas_estimadas_colones = data.get("ventas_estimadas_colones")
            comentario = data.get("comentario")

        if existe:
            # UPDATE
            cursor.execute("""
                UPDATE ventas_bottomup
                SET mes_referencia=?,
                    unidad_clientes=?,
                    clientes_valor=?,
                    dias_abiertos=?,
                    semanas_abiertas=?,
                    ticket_promedio_colones=?,
                    ventas_estimadas_colones=?,
                    comentario=?,
                    no_data=?,
                    fecha_registro=GETDATE()
                WHERE cliente_identificacion=? AND mes_iso=?
            """, (
                data.get("mes_referencia"),
                unidad_clientes,
                clientes_valor,
                dias_abiertos,
                semanas_abiertas,
                ticket_promedio_colones,
                ventas_estimadas_colones,
                comentario,
                data.get("no_data"),
                cliente_id,
                data.get("mes_iso"),
            ))
        else:
            # INSERT
            cursor.execute("""
                INSERT INTO ventas_bottomup (
                    cliente_identificacion, mes_referencia, mes_iso, unidad_clientes,
                    clientes_valor, dias_abiertos, semanas_abiertas,
                    ticket_promedio_colones, ventas_estimadas_colones,
                    comentario, no_data
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cliente_id,
                data.get("mes_referencia"),
                data.get("mes_iso"),
                unidad_clientes,
                clientes_valor,
                dias_abiertos,
                semanas_abiertas,
                ticket_promedio_colones,
                ventas_estimadas_colones,
                comentario,
                data.get("no_data"),
            ))

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        st.error(f"Error guardando VentasBottomUp: {e}")
        return False


