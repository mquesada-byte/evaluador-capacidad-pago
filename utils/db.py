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

    # Ventas Paso 5 (último registro)
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

    # Valoración asesor (último registro)
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


def save_ventas_bottomup(cliente_id: str, data: dict) -> bool:
    """UPSERT en la tabla ventas_bottomup."""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        if data.get("no_data") == 1:
            unidad_clientes = None
            clientes_valor = None
            dias_abiertos = None
            semanas_abiertas = None
            ticket_promedio_colones = None
            ventas_estimadas_colones = None
            comentario = data.get("comentario")
        else:
            unidad_clientes = data.get("unidad_clientes")
            clientes_valor = data.get("clientes_valor")
            dias_abiertos = data.get("dias_abiertos")
            semanas_abiertas = data.get("semanas_abiertas")
            ticket_promedio_colones = data.get("ticket_promedio_colones")
            ventas_estimadas_colones = data.get("ventas_estimadas_colones")
            comentario = data.get("comentario")

        cursor.execute("""
            UPDATE ventas_bottomup
            SET mes_referencia=?, unidad_clientes=?, clientes_valor=?, dias_abiertos=?, semanas_abiertas=?,
                ticket_promedio_colones=?, ventas_estimadas_colones=?, comentario=?, no_data=?, fecha_registro=GETDATE()
            WHERE cliente_identificacion=? AND mes_iso=?
        """, (
            data.get("mes_referencia"), unidad_clientes, clientes_valor, dias_abiertos, semanas_abiertas,
            ticket_promedio_colones, ventas_estimadas_colones, comentario, data.get("no_data"),
            cliente_id, data.get("mes_iso"),
        ))

        if cursor.rowcount == 0:
            cursor.execute("""
                INSERT INTO ventas_bottomup (
                    cliente_identificacion, mes_referencia, mes_iso, unidad_clientes,
                    clientes_valor, dias_abiertos, semanas_abiertas,
                    ticket_promedio_colones, ventas_estimadas_colones,
                    comentario, no_data
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cliente_id, data.get("mes_referencia"), data.get("mes_iso"), unidad_clientes,
                clientes_valor, dias_abiertos, semanas_abiertas,
                ticket_promedio_colones, ventas_estimadas_colones,
                comentario, data.get("no_data"),
            ))

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        st.error(f"Error guardando ventas_bottomup: {e}")
        return False


def save_ventas_p5(cliente_id: str, data: dict) -> bool:
    """UPSERT en la tabla ventas_p5."""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        if data.get("no_data") == 1:
            modo = None
            tiene_registros = None
            compras_mes_colones = None
            tipo_margen = None
            margen_pct = None
            facturacion_bruta_mes_colones = None
            comision_pct = None
            ventas_reportadas_mes_colones = None
            costo_pct_sobre_ventas = None
            costo_estimado_colones = None
            ventas_estimadas_colones = None
            comentario = data.get("comentario")
        else:
            modo = data.get("modo")
            tiene_registros = data.get("tiene_registros")
            compras_mes_colones = data.get("compras_mes_colones")
            tipo_margen = data.get("tipo_margen")
            margen_pct = data.get("margen_pct")
            facturacion_bruta_mes_colones = data.get("facturacion_bruta_mes_colones")
            comision_pct = data.get("comision_pct")
            ventas_reportadas_mes_colones = data.get("ventas_reportadas_mes_colones")
            costo_pct_sobre_ventas = data.get("costo_pct_sobre_ventas")
            costo_estimado_colones = data.get("costo_estimado_colones")
            ventas_estimadas_colones = data.get("ventas_estimadas_colones")
            comentario = data.get("comentario")

        cursor.execute("""
            UPDATE ventas_p5
            SET mes_referencia=?, modo=?, tiene_registros=?, compras_mes_colones=?, tipo_margen=?, margen_pct=?,
                facturacion_bruta_mes_colones=?, comision_pct=?, ventas_reportadas_mes_colones=?, costo_pct_sobre_ventas=?,
                costo_estimado_colones=?, ventas_estimadas_colones=?, comentario=?, no_data=?, fecha_registro=GETDATE()
            WHERE cliente_identificacion=? AND mes_iso=?
        """, (
            data.get("mes_referencia"), modo, tiene_registros, compras_mes_colones, tipo_margen, margen_pct,
            facturacion_bruta_mes_colones, comision_pct, ventas_reportadas_mes_colones, costo_pct_sobre_ventas,
            costo_estimado_colones, ventas_estimadas_colones, comentario, data.get("no_data"),
            cliente_id, data.get("mes_iso"),
        ))

        if cursor.rowcount == 0:
            cursor.execute("""
                INSERT INTO ventas_p5 (
                    cliente_identificacion, mes_referencia, mes_iso, modo,
                    tiene_registros, compras_mes_colones, tipo_margen, margen_pct,
                    facturacion_bruta_mes_colones, comision_pct,
                    ventas_reportadas_mes_colones, costo_pct_sobre_ventas,
                    costo_estimado_colones, ventas_estimadas_colones,
                    comentario, no_data
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cliente_id, data.get("mes_referencia"), data.get("mes_iso"), modo,
                tiene_registros, compras_mes_colones, tipo_margen, margen_pct,
                facturacion_bruta_mes_colones, comision_pct,
                ventas_reportadas_mes_colones, costo_pct_sobre_ventas,
                costo_estimado_colones, ventas_estimadas_colones,
                comentario, data.get("no_data"),
            ))

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        st.error(f"Error guardando ventas_p5: {e}")
        return False


def save_valoracion_asesor(cliente_id: str, data: dict) -> bool:
    """UPSERT en la tabla valoracion_asesor."""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE valoracion_asesor
            SET conocimiento_0a10=?, credibilidad_0a10=?, dudas_declaracion=?, clasificacion=?,
                evidencia=?, comentario=?, factor_asesor_0a1=?, fecha_registro=GETDATE()
            WHERE cliente_identificacion=? AND mes_iso=?
        """, (
            data.get("conocimiento_0a10"), data.get("credibilidad_0a10"),
            data.get("dudas_declaracion"), data.get("clasificacion"),
            ",".join(data.get("evidencia", [])),
            data.get("comentario"), data.get("factor_asesor_0a1"),
            cliente_id, data.get("mes_iso")
        ))

        if cursor.rowcount == 0:
            cursor.execute("""
                INSERT INTO valoracion_asesor (
                    cliente_identificacion, mes_iso, conocimiento_0a10, credibilidad_0a10,
                    dudas_declaracion, clasificacion, evidencia, comentario, factor_asesor_0a1
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cliente_id, data.get("mes_iso"),
                data.get("conocimiento_0a10"), data.get("credibilidad_0a10"),
                data.get("dudas_declaracion"), data.get("clasificacion"),
                ",".join(data.get("evidencia", [])),
                data.get("comentario"), data.get("factor_asesor_0a1")
            ))

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        st.error(f"Error guardando valoracion_asesor: {e}")
        return False




