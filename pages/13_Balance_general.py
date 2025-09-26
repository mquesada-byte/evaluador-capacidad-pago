import pandas as pd
import streamlit as st
from utils.db import get_connection

st.set_page_config(page_title="Paso 13: Balance General", page_icon="📒")

# --- Título principal ---
st.title("📒 Paso 13: Balance General")
st.subheader("I. Activo Circulante")

# --- Placeholder de la UI ---
caja_placeholder = pd.DataFrame([{
    "Cuenta/Banco": "",
    "Saldo (₡)": 0,
    "Verificado por asesor": False,
    "Tipo de evidencia": "",
    "Comentario": ""
} for _ in range(3)])

# --- Cargar datos desde SQL si existen ---
cliente_id = st.session_state.get("cliente", {}).get("identificacion", "")
mes_iso = st.session_state.get("mes_iso", "")
caja_df = caja_placeholder.copy()

if cliente_id and mes_iso:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT descripcion, monto, verificado, evidencia, comentario
            FROM balancegeneraldetalles
            WHERE cliente_identificacion = ? AND mes_iso = ? AND seccion = 'caja_bancos'
        """, (cliente_id, mes_iso))
        rows = cursor.fetchall()
        conn.close()

        if rows:
            caja_df = pd.DataFrame.from_records(
                rows,
                columns=[
                    "Cuenta/Banco", "Saldo (₡)", "Verificado por asesor",
                    "Tipo de evidencia", "Comentario"
                ]
            )
            caja_df["Saldo (₡)"] = pd.to_numeric(caja_df["Saldo (₡)"], errors="coerce").fillna(0).astype(int)
            caja_df["Verificado por asesor"] = caja_df["Verificado por asesor"].map({1: True, 0: False}).fillna(False).astype(bool)

    except Exception as e:
        st.warning(f"No se pudieron cargar los datos guardados: {e}")

# --- Sección Caja y Bancos ---
st.markdown("### 1) Caja y Bancos")

caja_df = st.data_editor(
    caja_df,
    use_container_width=True,
    num_rows="dynamic",
    hide_index=True,
    key="bg_caja_bancos",
    column_config={
        "Cuenta/Banco": st.column_config.TextColumn("Cuenta/Banco"),
        "Saldo (₡)": st.column_config.NumberColumn("Saldo (₡)", min_value=0, step=10000, format="₡ %d"),
        "Verificado por asesor": st.column_config.CheckboxColumn("Verificado por asesor"),
        "Tipo de evidencia": st.column_config.SelectboxColumn("Tipo de evidencia", options=[
            "Los tiene en caja", "Estado de cuenta", "Movimientos/SINPE", "Factura/Recibo",
            "Contrato", "Inventario físico", "Fotos/Video", "Otro", "No aplica"
        ]),
        "Comentario": st.column_config.TextColumn("Comentario"),
    },
)

caja_total = int(pd.to_numeric(caja_df["Saldo (₡)"], errors="coerce").fillna(0).sum())
st.metric("Subtotal Caja y Bancos", f"₡{caja_total:,.0f}")
st.markdown("---")

# --- Guardar en la base de datos ---
if st.button("💾 Guardar Caja y Bancos"):
    if not cliente_id or not mes_iso:
        st.error("⚠️ Falta cliente o mes para guardar.")
        st.stop()

    # limpiar y transformar
    registros = []
    for r in caja_df.to_dict(orient="records"):
        if not any(r.values()):
            continue
        registros.append({
            "cliente_identificacion": cliente_id,
            "mes_iso": mes_iso,
            "seccion": "caja_bancos",
            "descripcion": r.get("Cuenta/Banco", "") or "",
            "monto": int(pd.to_numeric(r.get("Saldo (₡)", 0), errors="coerce") or 0),
            "verificado": 1 if r.get("Verificado por asesor") else 0,
            "evidencia": r.get("Tipo de evidencia", "") or "",
            "comentario": r.get("Comentario", "") or "",
        })

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # eliminar registros previos del cliente/mes/sección
        cursor.execute("""
            DELETE FROM balancegeneraldetalles
            WHERE cliente_identificacion = ? AND mes_iso = ? AND seccion = 'caja_bancos'
        """, (cliente_id, mes_iso))

        # insertar nuevos
        for reg in registros:
            cursor.execute("""
                INSERT INTO balancegeneraldetalles
                (cliente_identificacion, mes_iso, seccion, descripcion, monto, verificado, evidencia, comentario, fecha_registro)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
            """, (
                reg["cliente_identificacion"], reg["mes_iso"], reg["seccion"],
                reg["descripcion"], reg["monto"], reg["verificado"],
                reg["evidencia"], reg["comentario"]
            ))

        conn.commit()
        conn.close()
        st.success("✅ Datos de Caja y Bancos guardados correctamente.")

    except Exception as e:
        st.error(f"❌ Error al guardar: {e}")

# --- Navegación ---
col1, col2 = st.columns([1, 1])

with col1:
    if st.button("⬅️ Volver a 10 – Gastos operativos", use_container_width=True):
        for prev in [
            "pages/10_Gastos_operativos.py",
            "pages/10_gastos_operativos.py",
            "pages/10_Gastos.py",
        ]:
            try:
                st.switch_page(prev)
                break
            except Exception:
                continue

with col2:
    if st.button("Guardar y continuar ➡️", use_container_width=True):
        if not cliente_id or not mes_iso:
            st.error("⚠️ Falta cliente o mes para guardar.")
            st.stop()

        # limpiar y transformar
        registros = []
        for r in caja_df.to_dict(orient="records"):
            if not any(r.values()):
                continue
            registros.append({
                "cliente_identificacion": cliente_id,
                "mes_iso": mes_iso,
                "seccion": "caja_bancos",
                "descripcion": r.get("Cuenta/Banco", "") or "",
                "monto": int(pd.to_numeric(r.get("Saldo (₡)", 0), errors="coerce") or 0),
                "verificado": 1 if r.get("Verificado por asesor") else 0,
                "evidencia": r.get("Tipo de evidencia", "") or "",
                "comentario": r.get("Comentario", "") or "",
            })

        try:
            conn = get_connection()
            cursor = conn.cursor()

            # eliminar registros previos del cliente/mes/sección
            cursor.execute("""
                DELETE FROM balancegeneraldetalles
                WHERE cliente_identificacion = ? AND mes_iso = ? AND seccion = 'caja_bancos'
            """, (cliente_id, mes_iso))

            # insertar nuevos
            for reg in registros:
                cursor.execute("""
                    INSERT INTO balancegeneraldetalles
                    (cliente_identificacion, mes_iso, seccion, descripcion, monto, verificado, evidencia, comentario, fecha_registro)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
                """, (
                    reg["cliente_identificacion"], reg["mes_iso"], reg["seccion"],
                    reg["descripcion"], reg["monto"], reg["verificado"],
                    reg["evidencia"], reg["comentario"]
                ))

            conn.commit()
            conn.close()
            st.success("✅ Datos de Caja y Bancos guardados correctamente.")

            # avanzar al siguiente paso
            for nxt in [
                "pages/14_Informe_final.py",
                "pages/14_informe_final.py",
                "pages/14_Informe.py",
            ]:
                try:
                    st.switch_page(nxt)
                    break
                except Exception:
                    continue

        except Exception as e:
            st.error(f"❌ Error al guardar: {e}")


