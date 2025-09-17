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

    # Otros ingresos 👇 (ajustado: tomar último mes_iso de la tabla OtrosIngresos)
    cursor.execute("""
        SELECT TOP 1 mes_iso 
        FROM OtrosIngresos
        WHERE cliente_identificacion=?
        ORDER BY mes_iso DESC
    """, (cliente_id,))
    mes_row = cursor.fetchone()
    mes_iso = mes_row[0] if mes_row else None

    if mes_iso:
        cursor.execute("""
            SELECT titular, relacion, fuente, periodicidad, monto_periodo,
                   verificado, evidencia, meses_cont, prob_cont, comentario
            FROM OtrosIngresos

 # Deudas Activas 👇
 cursor.execute("""
     SELECT TOP 1 mes_iso
     FROM DeudasActivas
     WHERE cliente_identificacion=?
     ORDER BY mes_iso DESC
 """, (cliente_id,))
 mes_row = cursor.fetchone()
 mes_iso = mes_row[0] if mes_row else None

    if mes_iso:
        cursor.execute("""
            SELECT titular, relacion, fuente, periodicidad, monto_periodo,
                   verificado, evidencia, meses_cont, prob_cont, comentario
            FROM OtrosIngresos
            WHERE cliente_identificacion=? AND mes_iso=?
        """, (cliente_id, mes_iso))
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
                "comentario": "Comentario"
            })

            datos["otros_ingresos"] = df_oi.to_dict(orient="records")

    # Deudas Activas 👇
    cursor.execute("""
        SELECT TOP 1 mes_iso
        FROM DeudasActivas
        WHERE cliente_identificacion=?
        ORDER BY mes_iso DESC
    """, (cliente_id,))
    mes_row = cursor.fetchone()
    mes_iso = mes_row[0] if mes_row else None

    if mes_iso:
        cursor.execute("""
            SELECT titular, acreedor, tipo_deuda, saldo_adeudado,
                   cuota_periodo, periodicidad, verificado, evidencia,
                   estado, dias_atraso, comentario, meses_restantes, plazo,
                   cuota_mensualizada
            FROM DeudasActivas
            WHERE cliente_identificacion=? AND mes_iso=? AND sin_deudas=0
        """, (cliente_id, mes_iso))
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

    conn.close()
    return datos



# ==========================================================
# GUARDAR PASO 3 – TOP-DOWN
# ==========================================================
def save_ventas_topdown(cliente_id: str, data: dict) -> bool:
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE ventas_topdown
            SET mes_referencia=?, monto_colones=?, tipicidad=?, fuente=?,
                confianza_cliente_0a10=?, comentario=?, fecha_registro=GETDATE()
            WHERE cliente_identificacion=? AND mes_iso=?
        """, (
            data.get("mes_referencia"), data.get("monto_colones"),
            data.get("tipicidad"), data.get("fuente"),
            data.get("confianza_cliente_0a10"), data.get("comentario"),
            cliente_id, data.get("mes_iso")
        ))

        if cursor.rowcount == 0:
            cursor.execute("""
                INSERT INTO ventas_topdown (
                    cliente_identificacion, mes_referencia, mes_iso,
                    monto_colones, tipicidad, fuente,
                    confianza_cliente_0a10, comentario
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cliente_id, data.get("mes_referencia"), data.get("mes_iso"),
                data.get("monto_colones"), data.get("tipicidad"),
                data.get("fuente"), data.get("confianza_cliente_0a10"),
                data.get("comentario")
            ))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error guardando ventas_topdown: {e}")
        return False


# ==========================================================
# GUARDAR PASO 4 – BOTTOM-UP
# ==========================================================
def save_ventas_bottomup(cliente_id: str, data: dict) -> bool:
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
            data.get("mes_referencia"), unidad_clientes, clientes_valor,
            dias_abiertos, semanas_abiertas, ticket_promedio_colones,
            ventas_estimadas_colones, comentario, data.get("no_data"),
            cliente_id, data.get("mes_iso")
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
                cliente_id, data.get("mes_referencia"), data.get("mes_iso"),
                unidad_clientes, clientes_valor, dias_abiertos,
                semanas_abiertas, ticket_promedio_colones,
                ventas_estimadas_colones, comentario, data.get("no_data")
            ))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error guardando ventas_bottomup: {e}")
        return False


# ==========================================================
# GUARDAR PASO 5 – INSUMOS
# ==========================================================
def save_ventas_p5(cliente_id: str, data: dict) -> bool:
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
            data.get("mes_referencia"), modo, tiene_registros, compras_mes_colones,
            tipo_margen, margen_pct, facturacion_bruta_mes_colones, comision_pct,
            ventas_reportadas_mes_colones, costo_pct_sobre_ventas, costo_estimado_colones,
            ventas_estimadas_colones, comentario, data.get("no_data"),
            cliente_id, data.get("mes_iso")
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
                cliente_id, data.get("mes_referencia"), data.get("mes_iso"),
                modo, tiene_registros, compras_mes_colones, tipo_margen,
                margen_pct, facturacion_bruta_mes_colones, comision_pct,
                ventas_reportadas_mes_colones, costo_pct_sobre_ventas,
                costo_estimado_colones, ventas_estimadas_colones,
                comentario, data.get("no_data")
            ))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error guardando ventas_p5: {e}")
        return False


# ==========================================================
# GUARDAR PASO 6 – VALORACIÓN ASESOR
# ==========================================================
def save_valoracion_asesor(cliente_id: str, data: dict) -> bool:
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
                ",".join(data.get("evidencia", [])), data.get("comentario"),
                data.get("factor_asesor_0a1")
            ))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error guardando valoracion_asesor: {e}")
        return False


# ==========================================================
# GUARDAR PASO 8 – OTROS INGRESOS
# ==========================================================
def save_otros_ingresos(cliente_id: str, mes_iso: str, df) -> bool:
    """
    Inserta los registros de otros ingresos en la tabla OtrosIngresos.
    Antes de insertar, elimina los registros existentes del mismo cliente y mes_iso.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 🔄 Borrar registros previos del cliente y mes
        cursor.execute("""
            DELETE FROM OtrosIngresos
            WHERE cliente_identificacion=? AND mes_iso=?
        """, (cliente_id, mes_iso))

        if df.empty:
            conn.commit()
            conn.close()
            return True  # nada más que guardar

        insert_sql = """
            INSERT INTO OtrosIngresos (
                cliente_identificacion, mes_iso,
                titular, relacion, fuente, periodicidad,
                monto_periodo, verificado, evidencia, meses_cont, prob_cont,
                ingreso_mensualizado, factor_confiabilidad, ingreso_ponderado,
                comentario, fecha_registro
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
        """

        for _, row in df.iterrows():
            cursor.execute(
                insert_sql,
                cliente_id,
                mes_iso,
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
# GUARDAR PASO 9 – DEUDAS ACTIVAS
# ==========================================================
def save_deudas_activas(cliente_id: str, mes_iso: str, df, totales: dict, sin_deudas: bool) -> bool:
    """
    Guarda las deudas activas de un cliente en la tabla DeudasActivas.
    Si sin_deudas=True, solo guarda los totales con bandera sin_deudas=1.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 🔄 Borrar registros previos
        cursor.execute("""
            DELETE FROM DeudasActivas
            WHERE cliente_identificacion=? AND mes_iso=?
        """, (cliente_id, mes_iso))

        if not sin_deudas and not df.empty:
            insert_sql = """
                INSERT INTO DeudasActivas (
                    cliente_identificacion, mes_iso,
                    titular, acreedor, tipo_deuda, saldo_adeudado,
                    cuota_periodo, periodicidad, verificado, evidencia,
                    estado, dias_atraso, comentario, meses_restantes,
                    plazo, cuota_mensualizada,
                    total_pago_mensual_colones, total_pago_mensual_verificado_colones,
                    total_adeudado_colones, total_adeudado_corto_plazo_colones,
                    total_adeudado_largo_plazo_colones, registros_validos, sin_deudas
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            for _, row in df.iterrows():
                cursor.execute(
                    insert_sql,
                    cliente_id,
                    mes_iso,
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
                    cliente_identificacion, mes_iso,
                    total_pago_mensual_colones, total_pago_mensual_verificado_colones,
                    total_adeudado_colones, total_adeudado_corto_plazo_colones,
                    total_adeudado_largo_plazo_colones, registros_validos, sin_deudas
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                cliente_id, mes_iso,
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
# Guardar Gastos Operativos
# ====================================
def save_gastos_operativos(cliente_id: str, mes_iso: str, df: pd.DataFrame, totales: dict, sin_gastos: bool = False) -> bool:
    """
    Guarda los gastos operativos en la tabla GastosOperativos.
    Si ya existen registros para cliente_id + mes_iso, se eliminan y se insertan de nuevo.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Eliminar registros previos (para evitar duplicados)
        cursor.execute("""
            DELETE FROM GastosOperativos 
            WHERE cliente_identificacion=? AND mes_iso=?
        """, (cliente_id, mes_iso))

        if not sin_gastos and not df.empty:
            for _, row in df.iterrows():
                cursor.execute("""
                    INSERT INTO GastosOperativos (
                        cliente_identificacion, mes_iso,
                        Rubro, Detalle, MontoPorPeriodo, Periodicidad,
                        VerificadoAsesor, TipoEvidencia, Comentario, GastoMensualizado,
                        total_gasto_operativo_mensualizado_colones,
                        total_gasto_operativo_verificado_colones,
                        registros_validos
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    cliente_id,
                    mes_iso,
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
                ))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[save_gastos_operativos] Error: {e}")
        return False

# ==========================================================
# GUARDAR PASO 11 – GASTOS FAMILIARES
# ==========================================================
def save_gastos_familiares(cliente_id: str, mes_iso: str, df, totales: dict, sin_gastos: bool = False) -> bool:
    """
    Inserta los registros de gastos familiares en la tabla GastosFamiliares.
    Antes de insertar, elimina los registros existentes del mismo cliente y mes_iso.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 🔄 Borrar registros previos del cliente y mes
        cursor.execute("""
            DELETE FROM GastosFamiliares
            WHERE cliente_identificacion=? AND mes_iso=?
        """, (cliente_id, mes_iso))

        # Si no hay registros válidos o se marcó "sin gastos", salir
        if df is None or df.empty or sin_gastos:
            conn.commit()
            conn.close()
            return True

        insert_sql = """
            INSERT INTO GastosFamiliares (
                cliente_identificacion, mes_iso,
                rubro, detalle, monto_periodo, periodicidad,
                verificado, tipo_evidencia, comentario, gasto_mensualizado,
                total_gastos_familiares_mensualizado_colones,
                total_gastos_familiares_verificado_colones,
                registros_validos,
                fecha_registro
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
        """

        for _, row in df.iterrows():
            cursor.execute(insert_sql, (
                cliente_id,
                mes_iso,
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
# GUARDAR PASO 13 – BALANCE GENERAL
# ==========================================================
def save_balance_general(cliente_id: str, mes_iso: str, datos: dict) -> bool:
    """
    Guarda la información del Balance General.
    - datos["totales"]: diccionario con los totales
    - datos["comentarios"]: string
    - datos["caja_bancos"], datos["cxc_clientes"], datos["inv_mp"], datos["inv_pp"],
      datos["inv_pt"], datos["activo_fijo"], datos["cpp"], datos["anticipos"]: listas de dicts
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 🔄 1) Borrar registros previos
        cursor.execute("""
            DELETE FROM BalanceGeneralTotales
            WHERE cliente_identificacion=? AND mes_iso=?
        """, (cliente_id, mes_iso))
        cursor.execute("""
            DELETE FROM BalanceGeneralDetalles
            WHERE cliente_identificacion=? AND mes_iso=?
        """, (cliente_id, mes_iso))

        # 🔽 2) Insertar totales
        tot = datos.get("totales", {})
        cursor.execute("""
            INSERT INTO BalanceGeneralTotales (
                cliente_identificacion, mes_iso,
                activo_circulante, activo_fijo, total_activos,
                pasivo_circulante, pasivo_largo, total_pasivo,
                patrimonio, capital_trabajo,
                comentarios
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cliente_id, mes_iso,
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

        # 🔽 3) Insertar detalles por secciones
        insert_sql = """
            INSERT INTO BalanceGeneralDetalles (
                cliente_identificacion, mes_iso,
                seccion, descripcion, monto, monto_secundario,
                verificado, evidencia, comentario
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        def insert_detalles(seccion: str, lista: list, desc_field: str, monto_field: str, monto2_field: str = None):
            for row in lista:
                cursor.execute(
                    insert_sql,
                    cliente_id, mes_iso,
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

        # ✅ Guardar cambios
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
