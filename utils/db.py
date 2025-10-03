import pyodbc
import streamlit as st
import pandas as pd

def get_connection():
    """Devuelve una conexión a Azure SQL Database usando los secrets."""
    try:
        conn = pyodbc.connect(
            f"DRIVER={{{st.secrets['azure_sql']['driver']}}};"
            f"SERVER={st.secrets['azure_sql']['server']};"
            f"DATABASE={st.secrets['azure_sql']['database']};"
            f"UID={st.secrets['azure_sql']['username']};"
            f"PWD={st.secrets['azure_sql']['password']}",
            timeout=30
        )
        return conn
    except pyodbc.Error:
        st.error("⚠️ No se pudo conectar con la base de datos. "
                 "Verifique credenciales, firewall o disponibilidad del servidor.")
        return None

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
        ORDER BY fecha_registro DESC
    """, (cliente_id,))
    row2 = cursor.fetchone()
    if row2:
        cols2 = [col[0] for col in cursor.description]
        datos["ventas_topdown"] = dict(zip(cols2, row2))

    # Ventas Bottom-up (ajustado)
    cursor.execute("""
        SELECT mes_referencia, unidad_clientes, clientes_valor, dias_abiertos, semanas_abiertas,
               ticket_promedio_colones, ventas_estimadas_colones, comentario, no_data
        FROM ventas_bottomup
        WHERE cliente_identificacion=?
    """, (cliente_id,))
    row3 = cursor.fetchone()
    if row3:
        cols3 = [col[0] for col in cursor.description]
        datos["ventas_bottomup"] = dict(zip(cols3, row3))

    # Ventas Paso 5 (ajustado)
    cursor.execute("""
        SELECT mes_referencia, modo, tiene_registros, compras_mes_colones, tipo_margen, margen_pct,
               facturacion_bruta_mes_colones, comision_pct, ventas_reportadas_mes_colones, costo_pct_sobre_ventas,
               costo_estimado_colones, ventas_estimadas_colones, comentario, no_data
        FROM ventas_p5
        WHERE cliente_identificacion=?
    """, (cliente_id,))
    row4 = cursor.fetchone()
    if row4:
        cols4 = [col[0] for col in cursor.description]
        datos["ventas_p5"] = dict(zip(cols4, row4))


    # Valoración asesor (ajustado)
    cursor.execute("""
        SELECT conocimiento_0a10, credibilidad_0a10, dudas_declaracion, clasificacion,
               evidencia, comentario, factor_asesor_0a1
        FROM valoracion_asesor
        WHERE cliente_identificacion=?
    """, (cliente_id,))
    row5 = cursor.fetchone()
    if row5:
        cols5 = [col[0] for col in cursor.description]
        datos["valoracion_asesor"] = dict(zip(cols5, row5))


    # Otros ingresos
    cursor.execute("""
        SELECT titular, relacion, fuente, periodicidad, monto_periodo,
               verificado, evidencia, meses_cont, prob_cont, comentario,
               ingreso_mensualizado, factor_confiabilidad, ingreso_ponderado
        FROM OtrosIngresos
        WHERE cliente_identificacion=?
    """, (cliente_id,))
    rows = cursor.fetchall()
    if rows:
        cols = [col[0] for col in cursor.description]
        df_oi = pd.DataFrame.from_records(rows, columns=cols)

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
            "comentario": "Comentario",
            "ingreso_mensualizado": "Ingreso mensualizado (₡)",
            "factor_confiabilidad": "Factor confiabilidad (0.2–1.0)",
            "ingreso_ponderado": "Ingreso ponderado (₡)"
        })

        datos["otros_ingresos"] = df_oi.to_dict(orient="records")



    # Deudas Activas (un solo balance por cliente)
    cursor.execute("""
        SELECT titular, acreedor, tipo_deuda, saldo_adeudado,
               cuota_periodo, periodicidad, verificado, evidencia,
               estado, dias_atraso, comentario, meses_restantes, plazo,
               cuota_mensualizada
        FROM DeudasActivas
        WHERE cliente_identificacion=? AND sin_deudas=0
    """, (cliente_id,))
    rows = cursor.fetchall()
    if rows:
        cols = [col[0] for col in cursor.description]
        df_deu = pd.DataFrame.from_records(rows, columns=cols)

        df_deu = df_deu.rename(columns={
            "titular": "Titular",
            "acreedor": "Acreedor/Entidad",
            "tipo_deuda": "Tipo de deuda",
            "saldo_adeudado": "Saldo adeudado (₡)",
            "cuota_periodo": "Cuota por período (₡)",
            "periodicidad": "Periodicidad de pago",
            "verificado": "Verificado por asesor",
            "evidencia": "Tipo de evidencia",
            "estado": "Estado",
            "dias_atraso": "Días de atraso",
            "comentario": "Comentario",
            "meses_restantes": "Meses restantes (opcional)",
            "plazo": "Plazo (clasificación)",
            "cuota_mensualizada": "Cuota mensualizada (₡)"
        })

        datos["deudas_activas"] = df_deu.to_dict(orient="records")





    
    # === Paso 10: Gastos operativos ===
    cursor.execute("""
        SELECT Rubro, Detalle, MontoPorPeriodo, Periodicidad,
               VerificadoAsesor, TipoEvidencia, Comentario, GastoMensualizado,
               total_gasto_operativo_mensualizado_colones,
               total_gasto_operativo_verificado_colones,
               registros_validos, sin_gastos
        FROM GastosOperativos
        WHERE cliente_identificacion=?
    """, (cliente_id,))
    rows = cursor.fetchall()
    if rows:
        cols = [col[0] for col in cursor.description]
        df_go = pd.DataFrame.from_records(rows, columns=cols)

        df_go = df_go.rename(columns={
            "Rubro": "Rubro",
            "Detalle": "Detalle",
            "MontoPorPeriodo": "Monto por período (₡)",
            "Periodicidad": "Periodicidad",
            "VerificadoAsesor": "Verificado por asesor",
            "TipoEvidencia": "Tipo de evidencia",
            "Comentario": "Comentario",
            "GastoMensualizado": "Gasto mensualizado (₡)"
        })

        if "Verificado por asesor" in df_go.columns:
            df_go["Verificado por asesor"] = df_go["Verificado por asesor"].astype(bool)

        # separar totales (solo tomamos la primera fila porque son iguales en todo el snapshot)
        totales = {
            "total_gasto_operativo_mensualizado_colones": int(df_go["total_gasto_operativo_mensualizado_colones"].iloc[0] or 0),
            "total_gasto_operativo_verificado_colones": int(df_go["total_gasto_operativo_verificado_colones"].iloc[0] or 0),
            "registros_validos": int(df_go["registros_validos"].iloc[0] or 0),
            "sin_gastos": bool(df_go["sin_gastos"].iloc[0])
        }

        # quitamos columnas de totales para que quede solo la tabla de gastos
        df_tabla = df_go.drop(columns=[
            "total_gasto_operativo_mensualizado_colones",
            "total_gasto_operativo_verificado_colones",
            "registros_validos",
            "sin_gastos"
        ], errors="ignore")

        datos["gastos_operativos"] = {
            "tabla": df_tabla.to_dict(orient="records"),
            "totales": totales
        }




    # === Paso 11: Gastos familiares (tabla + totales) ===
    cursor.execute("""
        SELECT id, cliente_identificacion, mes_iso,
               rubro, detalle, monto_periodo, periodicidad,
               verificado, tipo_evidencia, comentario, gasto_mensualizado,
               total_gastos_familiares_mensualizado_colones,
               total_gastos_familiares_verificado_colones,
               registros_validos, fecha_registro
        FROM GastosFamiliares
        WHERE cliente_identificacion=?
    """, (cliente_id,))
    rows = cursor.fetchall()
    if rows:
        cols = [col[0] for col in cursor.description]
        df_gf = pd.DataFrame.from_records(rows, columns=cols)

        # Totales (mismos en todas las filas → se toma el primero)
        totales = {
            "total_gastos_familiares_mensualizado_colones": int(df_gf["total_gastos_familiares_mensualizado_colones"].iloc[0] or 0),
            "total_gastos_familiares_verificado_colones": int(df_gf["total_gastos_familiares_verificado_colones"].iloc[0] or 0),
            "registros_validos": int(df_gf["registros_validos"].iloc[0] or 0),
        }

        # Preparar tabla para UI
        df_gf = df_gf.rename(columns={
            "rubro": "Rubro",
            "detalle": "Detalle",
            "monto_periodo": "Monto por período (₡)",
            "periodicidad": "Periodicidad",
            "verificado": "Verificado por asesor",
            "tipo_evidencia": "Tipo de evidencia",
            "comentario": "Comentario",
            "gasto_mensualizado": "Gasto mensualizado (₡)"
        })
        df_tabla = df_gf.drop(columns=[
            "id", "cliente_identificacion", "mes_iso", "fecha_registro",
            "total_gastos_familiares_mensualizado_colones",
            "total_gastos_familiares_verificado_colones",
            "registros_validos"
        ], errors="ignore")
        if "Verificado por asesor" in df_tabla.columns:
            df_tabla["Verificado por asesor"] = df_tabla["Verificado por asesor"].astype(bool)

        datos["gastos_familiares"] = {
            "tabla": df_tabla.to_dict(orient="records"),
            "totales": totales
        }





    # === Paso 13: Balance General (ajustado) ===
    # Totales
    cursor.execute("""
        SELECT activo_circulante, activo_fijo, total_activos,
               pasivo_circulante, pasivo_largo, total_pasivo,
               patrimonio, capital_trabajo, comentarios
        FROM BalanceGeneralTotales
        WHERE cliente_identificacion=?
    """, (cliente_id,))
    row_tot = cursor.fetchone()
    if row_tot:
        cols_tot = [col[0] for col in cursor.description]
        datos["balance_general"] = {
            "totales": dict(zip(cols_tot, row_tot))
        }

        # Detalles
        cursor.execute("""
            SELECT seccion, descripcion, monto, monto_secundario,
                   verificado, evidencia, comentario
            FROM BalanceGeneralDetalles
            WHERE cliente_identificacion=?
        """, (cliente_id,))
        rows_det = cursor.fetchall()
        if rows_det:
            cols_det = [col[0] for col in cursor.description]
            df_det = pd.DataFrame.from_records(rows_det, columns=cols_det)

            # Agrupar por sección y guardar como DataFrame directo
            for seccion in df_det["seccion"].unique():
                sub_df = df_det[df_det["seccion"] == seccion].copy()
                sub_df = sub_df.rename(columns={
                    "descripcion": "Descripción",
                    "monto": "Monto (₡)",
                    "monto_secundario": "Depreciación acum. (₡)",
                    "verificado": "Verificado por asesor",
                    "evidencia": "Tipo de evidencia",
                    "comentario": "Comentario"
                })
                if "Verificado por asesor" in sub_df.columns:
                    sub_df["Verificado por asesor"] = sub_df["Verificado por asesor"].astype(bool)
                datos["balance_general"][seccion] = sub_df

    
    conn.close()
    return datos










# ==========================================================
# GUARDAR PASO 3 – TOP-DOWN (sin mes_iso)
# ==========================================================
def save_ventas_topdown(cliente_id: str, data: dict) -> bool:
    """
    Guarda los datos de ventas top-down de un cliente.
    - Se elimina cualquier registro previo del cliente.
    - Se inserta siempre un snapshot único.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 🔄 Borrar registros previos del cliente
        cursor.execute("""
            DELETE FROM ventas_topdown
            WHERE cliente_identificacion=?
        """, (cliente_id,))

        # Insertar nuevo snapshot
        cursor.execute("""
            INSERT INTO ventas_topdown (
                cliente_identificacion, mes_referencia, monto_colones,
                tipicidad, fuente, confianza_cliente_0a10, comentario,
                fecha_registro
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, GETDATE())
        """, (
            cliente_id,
            data.get("mes_referencia"),
            float(data.get("monto_colones", 0) or 0),
            data.get("tipicidad", ""),
            data.get("fuente", ""),
            int(data.get("confianza_cliente_0a10", 0) or 0),
            data.get("comentario", "")
        ))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error guardando ventas_topdown: {e}")
        return False



# ==========================================================
# GUARDAR PASO 4 – BOTTOM-UP (ajustado)
# ==========================================================
def save_ventas_bottomup(cliente_id: str, data: dict) -> bool:
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 🔄 Borrar previos
        cursor.execute("DELETE FROM ventas_bottomup WHERE cliente_identificacion=?", (cliente_id,))

        # 🔽 Insertar snapshot
        cursor.execute("""
            INSERT INTO ventas_bottomup (
                cliente_identificacion, mes_referencia, unidad_clientes, clientes_valor, dias_abiertos, semanas_abiertos,
                ticket_promedio_colones, ventas_estimadas_colones, comentario, no_data, fecha_registro
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
        """, (
            cliente_id,
            data.get("mes_referencia"),
            data.get("unidad_clientes"),
            data.get("clientes_valor"),
            data.get("dias_abiertos"),
            data.get("semanas_abiertas"),
            data.get("ticket_promedio_colones"),
            data.get("ventas_estimadas_colones"),
            data.get("comentario"),
            data.get("no_data")
        ))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error guardando ventas_bottomup: {e}")
        return False



# ==========================================================
# GUARDAR PASO 5 – INSUMOS (ajustado)
# ==========================================================
def save_ventas_p5(cliente_id: str, data: dict) -> bool:
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 🔄 Borrar previos
        cursor.execute("DELETE FROM ventas_p5 WHERE cliente_identificacion=?", (cliente_id,))

        # 🔽 Insertar snapshot
        cursor.execute("""
            INSERT INTO ventas_p5 (
                cliente_identificacion, mes_referencia, modo, tiene_registros, compras_mes_colones,
                tipo_margen, margen_pct, facturacion_bruta_mes_colones, comision_pct,
                ventas_reportadas_mes_colones, costo_pct_sobre_ventas, costo_estimado_colones,
                ventas_estimadas_colones, comentario, no_data, fecha_registro
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
        """, (
            cliente_id,
            data.get("mes_referencia"),
            data.get("modo"),
            data.get("tiene_registros"),
            data.get("compras_mes_colones"),
            data.get("tipo_margen"),
            data.get("margen_pct"),
            data.get("facturacion_bruta_mes_colones"),
            data.get("comision_pct"),
            data.get("ventas_reportadas_mes_colones"),
            data.get("costo_pct_sobre_ventas"),
            data.get("costo_estimado_colones"),
            data.get("ventas_estimadas_colones"),
            data.get("comentario"),
            data.get("no_data")
        ))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error guardando ventas_p5: {e}")
        return False



# ==========================================================
# GUARDAR PASO 6 – VALORACIÓN ASESOR (ajustado)
# ==========================================================
def save_valoracion_asesor(cliente_id: str, data: dict) -> bool:
    """
    Guarda la valoración del asesor como snapshot único por cliente.
    Se elimina lo anterior y se inserta el nuevo registro.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 🔄 Borrar previos
        cursor.execute("""
            DELETE FROM valoracion_asesor
            WHERE cliente_identificacion=?
        """, (cliente_id,))

        # 🔽 Insertar el snapshot
        cursor.execute("""
            INSERT INTO valoracion_asesor (
                cliente_identificacion,
                conocimiento_0a10, credibilidad_0a10, dudas_declaracion, clasificacion,
                evidencia, comentario, factor_asesor_0a1, fecha_registro
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
        """, (
            cliente_id,
            data.get("conocimiento_0a10"),
            data.get("credibilidad_0a10"),
            data.get("dudas_declaracion"),
            data.get("clasificacion"),
            ",".join(data.get("evidencia", [])),
            data.get("comentario"),
            data.get("factor_asesor_0a1")
        ))

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        st.error(f"Error guardando valoracion_asesor: {e}")
        return False



# ==========================================================
# GUARDAR PASO 8 – OTROS INGRESOS (ajustado sin mes_iso)
# ==========================================================
def save_otros_ingresos(cliente_id: str, df) -> bool:
    """
    Inserta los registros de otros ingresos en la tabla OtrosIngresos.
    Se maneja como snapshot único por cliente (sin mes_iso).
    Antes de insertar, elimina los registros existentes del mismo cliente.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 🔄 Borrar registros previos del cliente
        cursor.execute("""
            DELETE FROM OtrosIngresos
            WHERE cliente_identificacion=?
        """, (cliente_id,))

        if df.empty:
            conn.commit()
            conn.close()
            return True  # nada más que guardar

        insert_sql = """
            INSERT INTO OtrosIngresos (
                cliente_identificacion,
                titular, relacion, fuente, periodicidad,
                monto_periodo, verificado, evidencia, meses_cont, prob_cont,
                ingreso_mensualizado, factor_confiabilidad, ingreso_ponderado,
                comentario, fecha_registro
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
        """

        for _, row in df.iterrows():
            cursor.execute(
                insert_sql,
                cliente_id,
                row.get("Titular (nombre)", ""),
                row.get("Relación", ""),
                row.get("Fuente de ingreso", ""),
                row.get("Periodicidad", ""),
                float(row.get("Monto por período (₡)", 0) or 0),
                1 if row.get("Verificado por asesor", False) else 0,
                row.get("Tipo de evidencia", ""),
                int(row.get("Meses de continuidad", 0) or 0),
                int(row.get("Prob. continuidad (0–10)", 0) or 0),
                float(row.get("Ingreso mensualizado (₡)", 0) or 0),
                float(row.get("Factor confiabilidad (0.2–1.0)", 0) or 0),
                float(row.get("Ingreso ponderado (₡)", 0) or 0),
                row.get("Comentario", "")
            )

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        st.error(f"Error guardando otros_ingresos: {e}")
        return False


# ==========================================================
# GUARDAR PASO 9 – DEUDAS ACTIVAS (un balance por cliente)
# ==========================================================
def save_deudas_activas(cliente_id: str, df, totales: dict, sin_deudas: bool) -> bool:
    """
    Guarda las deudas activas de un cliente en la tabla DeudasActivas.
    Si sin_deudas=True, solo guarda los totales con bandera sin_deudas=1.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 🔄 Borrar registros previos de este cliente
        cursor.execute("""
            DELETE FROM DeudasActivas
            WHERE cliente_identificacion = ?
        """, (cliente_id,))

        if not sin_deudas and not df.empty:
            insert_sql = """
                INSERT INTO DeudasActivas (
                    cliente_identificacion, 
                    titular, acreedor, tipo_deuda, saldo_adeudado,
                    cuota_periodo, periodicidad, verificado, evidencia,
                    estado, dias_atraso, comentario, meses_restantes,
                    plazo, cuota_mensualizada,
                    total_pago_mensual_colones, total_pago_mensual_verificado_colones,
                    total_adeudado_colones, total_adeudado_corto_plazo_colones,
                    total_adeudado_largo_plazo_colones, registros_validos, sin_deudas,
                    fecha_registro
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
            """
            for _, row in df.iterrows():
                cursor.execute(
                    insert_sql,
                    cliente_id,
                    row.get("Titular", ""),
                    row.get("Acreedor/Entidad", ""),
                    row.get("Tipo de deuda", ""),
                    float(row.get("Saldo adeudado (₡)", 0) or 0),
                    float(row.get("Cuota por período (₡)", 0) or 0),
                    row.get("Periodicidad de pago", ""),
                    1 if row.get("Verificado por asesor", False) else 0,
                    row.get("Tipo de evidencia", ""),
                    row.get("Estado", ""),
                    int(row.get("Días de atraso", 0) or 0),
                    row.get("Comentario", ""),
                    int(row.get("Meses restantes (opcional)", 0) or 0),
                    row.get("Plazo (clasificación)", ""),
                    float(row.get("Cuota mensualizada (₡)", 0) or 0),
                    float(totales.get("total_pago_mensual_colones", 0) or 0),
                    float(totales.get("total_pago_mensual_verificado_colones", 0) or 0),
                    float(totales.get("total_adeudado_colones", 0) or 0),
                    float(totales.get("total_adeudado_corto_plazo_colones", 0) or 0),
                    float(totales.get("total_adeudado_largo_plazo_colones", 0) or 0),
                    int(totales.get("registros_validos", 0) or 0),
                    0
                )
        else:
            # Guardar solo totales si sin_deudas=True
            cursor.execute("""
                INSERT INTO DeudasActivas (
                    cliente_identificacion,
                    total_pago_mensual_colones, total_pago_mensual_verificado_colones,
                    total_adeudado_colones, total_adeudado_corto_plazo_colones,
                    total_adeudado_largo_plazo_colones, registros_validos, sin_deudas,
                    fecha_registro
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, GETDATE())
            """, (
                cliente_id,
                float(totales.get("total_pago_mensual_colones", 0) or 0),
                float(totales.get("total_pago_mensual_verificado_colones", 0) or 0),
                float(totales.get("total_adeudado_colones", 0) or 0),
                float(totales.get("total_adeudado_corto_plazo_colones", 0) or 0),
                float(totales.get("total_adeudado_largo_plazo_colones", 0) or 0),
                int(totales.get("registros_validos", 0) or 0)
            ))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error guardando deudas_activas: {e}")
        return False


# ====================================
# GUARDAR PASO 10 – GASTOS OPERATIVOS
# ====================================
def save_gastos_operativos(cliente_id: str, df: pd.DataFrame, totales: dict, sin_gastos: bool) -> bool:
    """
    Guarda los gastos operativos en la tabla GastosOperativos.
    Si sin_gastos=True, solo guarda los totales con bandera sin_gastos=1.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 🔄 Borrar registros previos de este cliente
        cursor.execute("""
            DELETE FROM GastosOperativos
            WHERE cliente_identificacion = ?
        """, (cliente_id,))

        if not sin_gastos and not df.empty:
            insert_sql = """
                INSERT INTO GastosOperativos (
                    cliente_identificacion,
                    Rubro, Detalle, MontoPorPeriodo, Periodicidad,
                    VerificadoAsesor, TipoEvidencia, Comentario, GastoMensualizado,
                    total_gasto_operativo_mensualizado_colones,
                    total_gasto_operativo_verificado_colones,
                    registros_validos, sin_gastos, creado_en
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, GETDATE())
            """
            for _, row in df.iterrows():
                cursor.execute(
                    insert_sql,
                    cliente_id,
                    row.get("Rubro", ""),
                    row.get("Detalle", ""),
                    float(row.get("Monto por período (₡)", 0) or 0),
                    row.get("Periodicidad", ""),
                    1 if row.get("Verificado por asesor", False) else 0,
                    row.get("Tipo de evidencia", ""),
                    row.get("Comentario", ""),
                    float(row.get("Gasto mensualizado (₡)", 0) or 0),
                    float(totales.get("total_gasto_operativo_mensualizado_colones", 0) or 0),
                    float(totales.get("total_gasto_operativo_verificado_colones", 0) or 0),
                    int(totales.get("registros_validos", 0) or 0)
                )
        else:
            # ✅ Guardar solo snapshot vacío con bandera sin_gastos=1
            cursor.execute("""
                INSERT INTO GastosOperativos (
                    cliente_identificacion,
                    total_gasto_operativo_mensualizado_colones,
                    total_gasto_operativo_verificado_colones,
                    registros_validos, sin_gastos, creado_en
                )
                VALUES (?, ?, ?, ?, 1, GETDATE())
            """, (
                cliente_id,
                float(totales.get("total_gasto_operativo_mensualizado_colones", 0) or 0),
                float(totales.get("total_gasto_operativo_verificado_colones", 0) or 0),
                int(totales.get("registros_validos", 0) or 0)
            ))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error guardando gastos operativos: {e}")
        return False











# ==========================================================
# GUARDAR PASO 11 – GASTOS FAMILIARES (ajustado)
# ==========================================================
def save_gastos_familiares(cliente_id: str, df, totales: dict, sin_gastos: bool = False) -> bool:
    """
    Inserta los registros de gastos familiares en la tabla GastosFamiliares.
    Antes de insertar, elimina los registros existentes del mismo cliente.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 🔄 Borrar registros previos del cliente
        cursor.execute("""
            DELETE FROM GastosFamiliares
            WHERE cliente_identificacion=?
        """, (cliente_id,))

        # Si no hay registros válidos o se marcó "sin gastos", salir
        if df is None or df.empty or sin_gastos:
            conn.commit()
            conn.close()
            return True

        insert_sql = """
            INSERT INTO GastosFamiliares (
                cliente_identificacion,
                rubro, detalle, monto_periodo, periodicidad,
                verificado, tipo_evidencia, comentario, gasto_mensualizado,
                total_gastos_familiares_mensualizado_colones,
                total_gastos_familiares_verificado_colones,
                registros_validos,
                fecha_registro
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
        """

        for _, row in df.iterrows():
            cursor.execute(insert_sql, (
                cliente_id,
                row.get("Rubro", ""),
                row.get("Detalle", ""),
                float(row.get("Monto por período (₡)", 0) or 0),
                row.get("Periodicidad", ""),
                1 if row.get("Verificado por asesor", False) else 0,
                row.get("Tipo de evidencia", ""),
                row.get("Comentario", ""),
                float(row.get("Gasto mensualizado (₡)", 0) or 0),
                int(totales.get("total_gastos_familiares_mensualizado_colones", 0)),
                int(totales.get("total_gastos_familiares_verificado_colones", 0)),
                int(totales.get("registros_validos", 0))
            ))

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        print(f"❌ Error guardando gastos familiares: {e}")
        return False



# ==========================================================
# GUARDAR PASO 13 – BALANCE GENERAL (ajustado)
# ==========================================================
def save_balance_general(cliente_id: str, datos: dict) -> bool:
    """
    Guarda la información del Balance General por cliente.
    Se borra todo lo anterior y se inserta el nuevo snapshot.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 🔄 Borrar registros previos del cliente
        cursor.execute("""
            DELETE FROM BalanceGeneralTotales
            WHERE cliente_identificacion=?
        """, (cliente_id,))
        cursor.execute("""
            DELETE FROM BalanceGeneralDetalles
            WHERE cliente_identificacion=?
        """, (cliente_id,))

        # 🔽 Insertar totales
        tot = datos.get("totales", {})
        cursor.execute("""
            INSERT INTO BalanceGeneralTotales (
                cliente_identificacion,
                activo_circulante, activo_fijo, total_activos,
                pasivo_circulante, pasivo_largo, total_pasivo,
                patrimonio, capital_trabajo,
                comentarios, fecha_registro
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
        """, (
            cliente_id,
            float(tot.get("activo_circulante", 0) or 0),
            float(tot.get("activo_fijo", 0) or 0),
            float(tot.get("total_activos", 0) or 0),
            float(tot.get("pasivo_circulante", 0) or 0),
            float(tot.get("pasivo_largo", 0) or 0),
            float(tot.get("total_pasivo", 0) or 0),
            float(tot.get("patrimonio", 0) or 0),
            float(tot.get("capital_trabajo", 0) or 0),
            datos.get("comentarios", "")
        ))

        # 🔽 Insertar detalles por secciones
        insert_sql = """
            INSERT INTO BalanceGeneralDetalles (
                cliente_identificacion,
                seccion, descripcion, monto, monto_secundario,
                verificado, evidencia, comentario, fecha_registro
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
        """

        def insert_detalles(seccion: str, lista: list, desc_field: str, monto_field: str, monto2_field: str = None):
            for row in lista:
                cursor.execute(
                    insert_sql,
                    cliente_id,
                    seccion,
                    row.get(desc_field, ""),
                    float(row.get(monto_field, 0) or 0),
                    float(row.get(monto2_field, 0) or 0) if monto2_field else None,
                    1 if row.get("Verificado por asesor", False) else 0,
                    row.get("Tipo de evidencia", ""),
                    row.get("Comentario", "")
                )

        insert_detalles("caja_bancos", datos.get("caja_bancos", []), "Cuenta/Banco", "Saldo (₡)")
        insert_detalles("cxc_clientes", datos.get("cxc_clientes", []), "Cliente/Descripción", "Monto (₡)")
        insert_detalles("inv_mp", datos.get("inv_mp", []), "Detalle", "Valor (₡)")
        insert_detalles("inv_pp", datos.get("inv_pp", []), "Detalle", "Valor (₡)")
        insert_detalles("inv_pt", datos.get("inv_pt", []), "Detalle", "Valor (₡)")
        insert_detalles("activo_fijo", datos.get("activo_fijo", []), "Activo", "Valor bruto (₡)", "Depreciación acum. (₡)")
        insert_detalles("cpp", datos.get("cpp", []), "Proveedor", "Monto (₡)")
        insert_detalles("anticipos", datos.get("anticipos", []), "Cliente/Descripción", "Monto (₡)")

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        st.error(f"Error guardando balance_general: {e}")
        return False



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
