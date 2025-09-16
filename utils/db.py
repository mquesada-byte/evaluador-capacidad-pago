def load_visita(cliente_id: str) -> dict | None:
    conn = get_connection()
    cursor = conn.cursor()

# ==========================================================
# TEST DE CONEXIÓN (se ejecuta solo si corres este archivo directamente)
# ==========================================================
if __name__ == "__main__":
    import streamlit as st
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT GETDATE()")
        fecha = cursor.fetchone()[0]
        st.title("🔎 Prueba de lectura en Azure SQL Database")
        st.success(f"Conexión exitosa. Fecha/hora en SQL Server: {fecha}")
        conn.close()
    except Exception as e:
        st.title("🔎 Prueba de lectura en Azure SQL Database")
        st.error(f"No se pudo conectar: {e}")


    
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

    # Otros ingresos 👇 (agregado pero aún no cargaba)
    cursor.execute("""
        SELECT titular, relacion, fuente, periodicidad, monto_periodo,
               verificado, evidencia, meses_cont, prob_cont, comentario
        FROM OtrosIngresos
        WHERE cliente_identificacion=? AND mes_iso=?
    """, (cliente_id, st.session_state.get("mes_iso", "")))
    rows = cursor.fetchall()
    if rows:
        cols = [col[0] for col in cursor.description]
        df_oi = pd.DataFrame.from_records(rows, columns=cols)

        # Mapear columnas de SQL -> columnas de UI (Paso 8)
        df_oi = df_oi.rename(columns={
            "titular": "Titular (nombre)",
            "relacion": "Relación",
            "fuente": "Fuente de ingreso",
            "periodicidad": "Periodicidad",
            "monto_periodo": "Monto por período (₡)",
            "verificado": "Verificado por asesor",
            "evidencia": "Tipo de evidencia",
            "meses_cont": "Meses de continuidad",
            "prob_cont": "Prob. continuidad (0–10)",
            "comentario": "Comentario"
        })

        datos["otros_ingresos"] = df_oi.to_dict(orient="records")

    conn.close()
    return datos




