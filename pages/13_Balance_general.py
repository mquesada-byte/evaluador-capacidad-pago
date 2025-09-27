import pandas as pd
import streamlit as st
from utils.db import get_connection, load_visita

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
            caja_df["Verificado por asesor"] = caja_df["Verificado por asesor"].apply(
                lambda v: True if str(v).strip() in ["1", "True", "true"] else False
            )

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


# --- Sección Cuentas por Cobrar ---
st.markdown("### 2) Cuentas por Cobrar a Clientes")

# --- Placeholder de la UI (Cuentas por Cobrar) ---
cxc_placeholder = pd.DataFrame([{
    "Cliente/Descripción": "",
    "Monto (₡)": 0,
    "Verificado por asesor": False,
    "Tipo de evidencia": "",
    "Comentario": ""
} for _ in range(3)])

cxc_df = cxc_placeholder.copy()

if cliente_id and mes_iso:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT descripcion, monto, verificado, evidencia, comentario
            FROM balancegeneraldetalles
            WHERE cliente_identificacion = ? AND mes_iso = ? AND seccion = 'cxc_clientes'
        """, (cliente_id, mes_iso))
        rows = cursor.fetchall()
        conn.close()

        if rows:
            cxc_df = pd.DataFrame.from_records(
                rows,
                columns=[
                    "Cliente/Descripción", "Monto (₡)", "Verificado por asesor",
                    "Tipo de evidencia", "Comentario"
                ]
            )
            # 🔧 Forzar tipos
            cxc_df["Monto (₡)"] = pd.to_numeric(cxc_df["Monto (₡)"], errors="coerce").fillna(0).astype(int)
            cxc_df["Verificado por asesor"] = cxc_df["Verificado por asesor"].apply(
                lambda v: True if str(v).strip() in ["1", "True", "true"] else False
            )

    except Exception as e:
        st.warning(f"No se pudieron cargar los datos de CxC: {e}")

cxc_df = st.data_editor(
    cxc_df,
    use_container_width=True,
    num_rows="dynamic",
    hide_index=True,
    key="bg_cxc_clientes",
    column_config={
        "Cliente/Descripción": st.column_config.TextColumn("Cliente/Descripción"),
        "Monto (₡)": st.column_config.NumberColumn("Monto (₡)", min_value=0, step=10000, format="₡ %d"),
        "Verificado por asesor": st.column_config.CheckboxColumn("Verificado por asesor"),
        "Tipo de evidencia": st.column_config.SelectboxColumn("Tipo de evidencia", options=[
            "Factura/Recibo", "Confirmación cliente", "Contrato", "Estado de cuenta",
            "Inventario físico", "Fotos/Video", "Otro", "No aplica"
        ]),
        "Comentario": st.column_config.TextColumn("Comentario"),
    },
)

cxc_total = int(pd.to_numeric(cxc_df["Monto (₡)"], errors="coerce").fillna(0).sum())
st.metric("Subtotal Cuentas por Cobrar", f"₡{cxc_total:,.0f}")
st.markdown("---")

# --- Sección Inventario ---
st.markdown("### 3) Inventario")

# --- Sub-sección: Materia Prima ---
st.markdown("#### a) Materia Prima")

# --- Placeholder de la UI (Materia Prima) ---
mp_placeholder = pd.DataFrame([{
    "Descripción": "",
    "Monto (₡)": 0,
    "Verificado por asesor": False,
    "Tipo de evidencia": "",
    "Comentario": ""
} for _ in range(3)])

mp_df = mp_placeholder.copy()

if cliente_id and mes_iso:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT descripcion, monto, verificado, evidencia, comentario
            FROM balancegeneraldetalles
            WHERE cliente_identificacion = ? AND mes_iso = ? AND seccion = 'inv_mp'
        """, (cliente_id, mes_iso))
        rows = cursor.fetchall()
        conn.close()

        if rows:
            mp_df = pd.DataFrame.from_records(
                rows,
                columns=[
                    "Descripción", "Monto (₡)", "Verificado por asesor",
                    "Tipo de evidencia", "Comentario"
                ]
            )
            mp_df["Monto (₡)"] = pd.to_numeric(mp_df["Monto (₡)"], errors="coerce").fillna(0).astype(int)
            mp_df["Verificado por asesor"] = mp_df["Verificado por asesor"].apply(
                lambda v: True if str(v).strip() in ["1", "True", "true"] else False
            )
    except Exception as e:
        st.warning(f"No se pudieron cargar los datos de Materia Prima: {e}")

mp_df = st.data_editor(
    mp_df,
    use_container_width=True,
    num_rows="dynamic",
    hide_index=True,
    key="bg_inv_materia_prima",  # misma lógica: key fija como en caja/cxc
    column_config={
        "Descripción": st.column_config.TextColumn("Descripción"),
        "Monto (₡)": st.column_config.NumberColumn("Monto (₡)", min_value=0, step=10000, format="₡ %d"),
        "Verificado por asesor": st.column_config.CheckboxColumn("Verificado por asesor"),
        "Tipo de evidencia": st.column_config.SelectboxColumn("Tipo de evidencia", options=[
            "Factura/Recibo", "Inventario físico", "Fotos/Video", "Contrato",
            "Otro", "No aplica"
        ]),
        "Comentario": st.column_config.TextColumn("Comentario"),
    },
)

mp_total = int(pd.to_numeric(mp_df["Monto (₡)"], errors="coerce").fillna(0).sum())
st.metric("Subtotal Materia Prima", f"₡{mp_total:,.0f}")
st.markdown("---")

# --- Sub-sección: Producto en Proceso ---
st.markdown("#### b) Producto en Proceso")

# Placeholder (igual formato que MP)
pp_placeholder = pd.DataFrame([{
    "Descripción": "",
    "Monto (₡)": 0,
    "Verificado por asesor": False,
    "Tipo de evidencia": "",
    "Comentario": ""
} for _ in range(3)])

pp_df = pp_placeholder.copy()

# Cargar desde SQL
if cliente_id and mes_iso:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT descripcion, monto, verificado, evidencia, comentario
            FROM balancegeneraldetalles
            WHERE cliente_identificacion = ? AND mes_iso = ? AND seccion = 'inv_pp'
        """, (cliente_id, mes_iso))
        rows = cursor.fetchall()
        conn.close()

        if rows:
            pp_df = pd.DataFrame.from_records(
                rows,
                columns=[
                    "Descripción", "Monto (₡)", "Verificado por asesor",
                    "Tipo de evidencia", "Comentario"
                ]
            )
            pp_df["Monto (₡)"] = pd.to_numeric(pp_df["Monto (₡)"], errors="coerce").fillna(0).astype(int)
            pp_df["Verificado por asesor"] = pp_df["Verificado por asesor"].apply(
                lambda v: True if str(v).strip() in ["1", "True", "true"] else False
            )
    except Exception as e:
        st.warning(f"No se pudieron cargar los datos de Producto en Proceso: {e}")

# Editor
pp_df = st.data_editor(
    pp_df,
    use_container_width=True,
    num_rows="dynamic",
    hide_index=True,
    key="bg_inv_producto_proceso",
    column_config={
        "Descripción": st.column_config.TextColumn("Descripción"),
        "Monto (₡)": st.column_config.NumberColumn("Monto (₡)", min_value=0, step=10000, format="₡ %d"),
        "Verificado por asesor": st.column_config.CheckboxColumn("Verificado por asesor"),
        "Tipo de evidencia": st.column_config.SelectboxColumn("Tipo de evidencia", options=[
            "Factura/Recibo", "Inventario físico", "Fotos/Video", "Contrato",
            "Otro", "No aplica"
        ]),
        "Comentario": st.column_config.TextColumn("Comentario"),
    },
)

# Subtotal
pp_total = int(pd.to_numeric(pp_df["Monto (₡)"], errors="coerce").fillna(0).sum())
st.metric("Subtotal Producto en Proceso", f"₡{pp_total:,.0f}")
st.markdown("---")

# --- Sub-sección: Producto Terminado ---
st.markdown("#### c) Producto Terminado")

# Placeholder (igual formato que MP/PP)
pt_placeholder = pd.DataFrame([{
    "Descripción": "",
    "Monto (₡)": 0,
    "Verificado por asesor": False,
    "Tipo de evidencia": "",
    "Comentario": ""
} for _ in range(3)])

pt_df = pt_placeholder.copy()

# Cargar desde SQL
if cliente_id and mes_iso:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT descripcion, monto, verificado, evidencia, comentario
            FROM balancegeneraldetalles
            WHERE cliente_identificacion = ? AND mes_iso = ? AND seccion = 'inv_pt'
        """, (cliente_id, mes_iso))
        rows = cursor.fetchall()
        conn.close()

        if rows:
            pt_df = pd.DataFrame.from_records(
                rows,
                columns=[
                    "Descripción", "Monto (₡)", "Verificado por asesor",
                    "Tipo de evidencia", "Comentario"
                ]
            )
            pt_df["Monto (₡)"] = pd.to_numeric(pt_df["Monto (₡)"], errors="coerce").fillna(0).astype(int)
            pt_df["Verificado por asesor"] = pt_df["Verificado por asesor"].apply(
                lambda v: True if str(v).strip() in ["1", "True", "true"] else False
            )
    except Exception as e:
        st.warning(f"No se pudieron cargar los datos de Producto Terminado: {e}")

# Editor
pt_df = st.data_editor(
    pt_df,
    use_container_width=True,
    num_rows="dynamic",
    hide_index=True,
    key="bg_inv_producto_terminado",
    column_config={
        "Descripción": st.column_config.TextColumn("Descripción"),
        "Monto (₡)": st.column_config.NumberColumn("Monto (₡)", min_value=0, step=10000, format="₡ %d"),
        "Verificado por asesor": st.column_config.CheckboxColumn("Verificado por asesor"),
        "Tipo de evidencia": st.column_config.SelectboxColumn("Tipo de evidencia", options=[
            "Factura/Recibo", "Inventario físico", "Fotos/Video", "Contrato",
            "Otro", "No aplica"
        ]),
        "Comentario": st.column_config.TextColumn("Comentario"),
    },
)

# Subtotal
pt_total = int(pd.to_numeric(pt_df["Monto (₡)"], errors="coerce").fillna(0).sum())
st.metric("Subtotal Producto Terminado", f"₡{pt_total:,.0f}")
st.markdown("---")


# --- Totales de Inventario y Activo Circulante ---
subtotal_mp = mp_total
subtotal_pp = pp_total
subtotal_pt = pt_total

total_inventarios = subtotal_mp + subtotal_pp + subtotal_pt
st.metric("**Total Inventarios**", f"₡{total_inventarios:,.0f}")
st.markdown("---")

activo_circulante = caja_total + cxc_total + total_inventarios
st.metric("💼 **Total Activo Circulante**", f"₡{activo_circulante:,.0f}")
st.divider()


# --- II. Activo No Circulante ---
st.subheader("II. Activo No Circulante")

# --- Sección: Activo Fijo ---
st.markdown("### 4) Activo Fijo")

# Placeholder (mismo formato)
af_placeholder = pd.DataFrame([{
    "Descripción": "",
    "Monto (₡)": 0,
    "Depreciación (₡)": 0,       # -> mapeado a monto_secundario
    "Verificado por asesor": False,
    "Tipo de evidencia": "",
    "Comentario": ""
} for _ in range(3)])

af_df = af_placeholder.copy()

# Cargar desde SQL
if cliente_id and mes_iso:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT descripcion, monto, monto_secundario, verificado, evidencia, comentario
            FROM balancegeneraldetalles
            WHERE cliente_identificacion = ? AND mes_iso = ? AND seccion = 'activo_fijo'
        """, (cliente_id, mes_iso))
        rows = cursor.fetchall()
        conn.close()

        if rows:
            af_df = pd.DataFrame.from_records(
                rows,
                columns=[
                    "Descripción", "Monto (₡)", "Depreciación (₡)",
                    "Verificado por asesor", "Tipo de evidencia", "Comentario"
                ]
            )
            af_df["Monto (₡)"] = pd.to_numeric(af_df["Monto (₡)"], errors="coerce").fillna(0).astype(int)
            af_df["Depreciación (₡)"] = pd.to_numeric(af_df["Depreciación (₡)"], errors="coerce").fillna(0).astype(int)
            af_df["Verificado por asesor"] = af_df["Verificado por asesor"].apply(
                lambda v: True if str(v).strip() in ["1","True","true"] else False
            )
    except Exception as e:
        st.warning(f"No se pudieron cargar los datos de Activo Fijo: {e}")

# Editor
af_df = st.data_editor(
    af_df,
    use_container_width=True,
    num_rows="dynamic",
    hide_index=True,
    key="bg_activo_fijo",
    column_config={
        "Descripción": st.column_config.TextColumn("Descripción"),
        "Monto (₡)": st.column_config.NumberColumn("Monto (₡)", min_value=0, step=10000, format="₡ %d"),
        "Depreciación (₡)": st.column_config.NumberColumn("Depreciación (₡)", min_value=0, step=10000, format="₡ %d"),
        "Verificado por asesor": st.column_config.CheckboxColumn("Verificado por asesor"),
        "Tipo de evidencia": st.column_config.SelectboxColumn("Tipo de evidencia", options=[
            "Factura/Recibo","Inventario físico","Fotos/Video","Contrato","Otro","No aplica"
        ]),
        "Comentario": st.column_config.TextColumn("Comentario"),
    },
)

# Subtotales y Neto
af_bruto_total = int(pd.to_numeric(af_df["Monto (₡)"], errors="coerce").fillna(0).sum())
af_deprec_total = int(pd.to_numeric(af_df["Depreciación (₡)"], errors="coerce").fillna(0).sum())
af_neto_total = af_bruto_total - af_deprec_total

# --- Totales Activo Fijo en una sola fila ---
col_bruto, col_depr, col_neto = st.columns(3, gap="large")
with col_bruto:
    st.metric("Subtotal Activo Fijo (Bruto)", f"₡{af_bruto_total:,.0f}")
with col_depr:
    st.metric("Depreciación acumulada", f"₡{af_deprec_total:,.0f}")
with col_neto:
    st.metric("Activo Fijo Neto", f"₡{af_neto_total:,.0f}")

st.markdown("---")

# Total Activos = Activo Circulante + Activo Fijo Neto
total_activos = int((caja_total + cxc_total) + (  # ya los traes
                    int(pd.to_numeric(mp_df["Monto (₡)"], errors="coerce").fillna(0).sum()) +
                    int(pd.to_numeric(pp_df["Monto (₡)"], errors="coerce").fillna(0).sum()) +
                    int(pd.to_numeric(pt_df["Monto (₡)"], errors="coerce").fillna(0).sum())
                ) + af_neto_total)

st.metric("📊 **Total Activos**", f"₡{total_activos:,.0f}")
st.divider()


# --- III. Pasivo ---
st.subheader("III. Pasivo")

# --- Sección: Pasivo Circulante ---
st.markdown("### 5) Cuentas por Pagar")

# Placeholder
cpp_placeholder = pd.DataFrame([{
    "Proveedor/Descripción": "",
    "Monto (₡)": 0,
    "Verificado por asesor": False,
    "Tipo de evidencia": "",
    "Comentario": ""
} for _ in range(3)])

cpp_df = cpp_placeholder.copy()

# Cargar desde SQL (seccion = 'cpp')
if cliente_id and mes_iso:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT descripcion, monto, verificado, evidencia, comentario
            FROM balancegeneraldetalles
            WHERE cliente_identificacion = ? AND mes_iso = ? AND seccion = 'cpp'
        """, (cliente_id, mes_iso))
        rows = cursor.fetchall()
        conn.close()

        if rows:
            cpp_df = pd.DataFrame.from_records(
                rows,
                columns=[
                    "Proveedor/Descripción", "Monto (₡)", "Verificado por asesor",
                    "Tipo de evidencia", "Comentario"
                ]
            )
            cpp_df["Monto (₡)"] = pd.to_numeric(cpp_df["Monto (₡)"], errors="coerce").fillna(0).astype(int)
            cpp_df["Verificado por asesor"] = cpp_df["Verificado por asesor"].apply(
                lambda v: True if str(v).strip() in ["1","True","true"] else False
            )
    except Exception as e:
        st.warning(f"No se pudieron cargar las Cuentas por Pagar: {e}")

# Editor
cpp_df = st.data_editor(
    cpp_df,
    use_container_width=True,
    num_rows="dynamic",
    hide_index=True,
    key="bg_cpp",
    column_config={
        "Proveedor/Descripción": st.column_config.TextColumn("Proveedor/Descripción"),
        "Monto (₡)": st.column_config.NumberColumn("Monto (₡)", min_value=0, step=10000, format="₡ %d"),
        "Verificado por asesor": st.column_config.CheckboxColumn("Verificado por asesor"),
        "Tipo de evidencia": st.column_config.SelectboxColumn("Tipo de evidencia", options=[
            "Factura de proveedor", "Estado de cuenta", "Confirmación proveedor",
            "Contrato", "Otro", "No aplica"
        ]),
        "Comentario": st.column_config.TextColumn("Comentario"),
    },
)

# Subtotal Pasivo Circulante - CxP
cpp_total = int(pd.to_numeric(cpp_df["Monto (₡)"], errors="coerce").fillna(0).sum())
st.metric("Subtotal Cuentas por Pagar", f"₡{cpp_total:,.0f}")
st.markdown("---")


# --- Deudas de Paso 9: Préstamos a Corto Plazo ---
st.markdown("*Cuentas por pagar a corto plazo (de Deudas Paso 9)*")

# 1) Primero desde session_state (como lo guarda Paso 9)
try:
    tot_corto = int(pd.to_numeric(
        st.session_state.get("reporte", {})
            .get("deudas_activas", {})
            .get("totales", {})
            .get("total_adeudado_corto_plazo_colones", 0)
    ) or 0)
except Exception:
    tot_corto = 0

# 2) Si no hay en sesión, intenta traerlo desde SQL (load_visita)
if (tot_corto == 0) and cliente_id:
    try:
        datos_09 = load_visita(cliente_id)
        if datos_09 and isinstance(datos_09.get("deudas_activas"), dict):
            tot_corto_sql = int(pd.to_numeric(
                datos_09["deudas_activas"]
                     .get("totales", {})
                     .get("total_adeudado_corto_plazo_colones", 0)
            ) or 0)
            if tot_corto_sql > 0:
                tot_corto = tot_corto_sql
    except Exception:
        pass

st.info(f"Total de corto plazo desde Deudas: **₡{tot_corto:,.0f}**")

# --- Total Pasivo Circulante (CxP + Préstamos CP Paso 9) ---
pasivo_circulante_total = cpp_total + tot_corto
st.metric("💳 **Total Pasivo Circulante**", f"₡{pasivo_circulante_total:,.0f}")
st.markdown("---")





# --- Pasivo a Largo Plazo (desde Paso 9) ---
st.markdown("*Pasivo a largo plazo (de Deudas Paso 9)*")

# 1) Intentar desde session_state (tal como lo guarda el Paso 9)
try:
    tot_largo = int(pd.to_numeric(
        st.session_state.get("reporte", {})
            .get("deudas_activas", {})
            .get("totales", {})
            .get("total_adeudado_largo_plazo_colones", 0)
    ) or 0)
except Exception:
    tot_largo = 0

# 2) Si no hay en sesión, intentar desde SQL (load_visita)
if (tot_largo == 0) and cliente_id:
    try:
        datos_09 = load_visita(cliente_id)
        if datos_09 and isinstance(datos_09.get("deudas_activas"), dict):
            tot_largo_sql = int(pd.to_numeric(
                datos_09["deudas_activas"]
                      .get("totales", {})
                      .get("total_adeudado_largo_plazo_colones", 0)
            ) or 0)
            if tot_largo_sql > 0:
                tot_largo = tot_largo_sql
    except Exception:
        pass

st.info(f"Total de largo plazo desde Deudas: **₡{tot_largo:,.0f}**")






# --- Total Pasivo (Circulante + Largo Plazo) ---
pasivo_circulante_total = int(cpp_total + tot_corto)   # CxP + préstamos CP (Paso 9)
pasivo_total = int(pasivo_circulante_total + tot_largo)

c1, c2, c3 = st.columns(3, gap="large")
with c1:
    st.metric("Pasivo Circulante", f"₡{pasivo_circulante_total:,.0f}")
with c2:
    st.metric("Pasivo Largo Plazo", f"₡{tot_largo:,.0f}")
with c3:
    st.metric("**Total Pasivo**", f"₡{pasivo_total:,.0f}")

st.markdown("---")




# --- Navegación ---
col1, col2 = st.columns([1, 1])

with col2:
    if st.button("Guardar y continuar ➡️", use_container_width=True):
        if not cliente_id or not mes_iso:
            st.error("⚠️ Falta cliente o mes para guardar.")
            st.stop()

        registros = []

        # --- Caja y Bancos ---
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

        # --- Cuentas por Cobrar ---
        for r in cxc_df.to_dict(orient="records"):
            if not any(r.values()):
                continue
            registros.append({
                "cliente_identificacion": cliente_id,
                "mes_iso": mes_iso,
                "seccion": "cxc_clientes",
                "descripcion": r.get("Cliente/Descripción", "") or "",
                "monto": int(pd.to_numeric(r.get("Monto (₡)", 0), errors="coerce") or 0),
                "verificado": 1 if r.get("Verificado por asesor") else 0,
                "evidencia": r.get("Tipo de evidencia", "") or "",
                "comentario": r.get("Comentario", "") or "",
            })

        # --- Inventario: Materia Prima ---
        for r in mp_df.to_dict(orient="records"):
            if not any(r.values()):
                continue
            registros.append({
                "cliente_identificacion": cliente_id,
                "mes_iso": mes_iso,
                "seccion": "inv_mp",
                "descripcion": r.get("Descripción", "") or "",
                "monto": int(pd.to_numeric(r.get("Monto (₡)", 0), errors="coerce") or 0),
                "verificado": 1 if r.get("Verificado por asesor") else 0,
                "evidencia": r.get("Tipo de evidencia", "") or "",
                "comentario": r.get("Comentario", "") or "",
            })

        # --- Inventario: Producto en Proceso ---
        for r in pp_df.to_dict(orient="records"):
            if not any(r.values()):
                continue
            registros.append({
                "cliente_identificacion": cliente_id,
                "mes_iso": mes_iso,
                "seccion": "inv_pp",
                "descripcion": r.get("Descripción", "") or "",
                "monto": int(pd.to_numeric(r.get("Monto (₡)", 0), errors="coerce") or 0),
                "verificado": 1 if r.get("Verificado por asesor") else 0,
                "evidencia": r.get("Tipo de evidencia", "") or "",
                "comentario": r.get("Comentario", "") or "",
            })

        # --- Inventario: Producto Terminado ---
        for r in pt_df.to_dict(orient="records"):
            if not any(r.values()):
                continue
            registros.append({
                "cliente_identificacion": cliente_id,
                "mes_iso": mes_iso,
                "seccion": "inv_pt",
                "descripcion": r.get("Descripción", "") or "",
                "monto": int(pd.to_numeric(r.get("Monto (₡)", 0), errors="coerce") or 0),
                "verificado": 1 if r.get("Verificado por asesor") else 0,
                "evidencia": r.get("Tipo de evidencia", "") or "",
                "comentario": r.get("Comentario", "") or "",
            })


        # --- Activo Fijo ---
        for r in af_df.to_dict(orient="records"):
            if not any(r.values()):
                continue
            registros.append({
                "cliente_identificacion": cliente_id,
                "mes_iso": mes_iso,
                "seccion": "activo_fijo",
                "descripcion": r.get("Descripción", "") or "",
                "monto": int(pd.to_numeric(r.get("Monto (₡)", 0), errors="coerce") or 0),
                "monto_secundario": int(pd.to_numeric(r.get("Depreciación (₡)", 0), errors="coerce") or 0),
                "verificado": 1 if r.get("Verificado por asesor") else 0,
                "evidencia": r.get("Tipo de evidencia", "") or "",
                "comentario": r.get("Comentario", "") or "",
            })


        


        # --- Pasivo Circulante: Cuentas por Pagar ---
        for r in cpp_df.to_dict(orient="records"):
            if not any(r.values()):
                continue
            registros.append({
                "cliente_identificacion": cliente_id,
                "mes_iso": mes_iso,
                "seccion": "cpp",
                "descripcion": r.get("Proveedor/Descripción", "") or "",
                "monto": int(pd.to_numeric(r.get("Monto (₡)", 0), errors="coerce") or 0),
                # monto_secundario no aplica aquí
                "verificado": 1 if r.get("Verificado por asesor") else 0,
                "evidencia": r.get("Tipo de evidencia", "") or "",
                "comentario": r.get("Comentario", "") or "",
            })








        

        
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # 🔥 Borrar previos (caja, cxc y materia prima)
            cursor.execute("""
                DELETE FROM balancegeneraldetalles
                WHERE cliente_identificacion = ? AND mes_iso = ? 
                  AND seccion IN ('caja_bancos','cxc_clientes','inv_mp','inv_pp','inv_pt','activo_fijo','cpp')
            """, (cliente_id, mes_iso))

            
            # Insertar nuevos (incluye monto_secundario)
            for reg in registros:
                cursor.execute("""
                    INSERT INTO balancegeneraldetalles
                    (cliente_identificacion, mes_iso, seccion, descripcion, monto, monto_secundario, verificado, evidencia, comentario, fecha_registro)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
                """, (
                    reg["cliente_identificacion"], reg["mes_iso"], reg["seccion"],
                    reg["descripcion"], reg["monto"],
                    reg.get("monto_secundario", None),  # <- aquí va la depreciación (o NULL para otras secciones)
                    reg["verificado"], reg["evidencia"], reg["comentario"]
                ))



            

            conn.commit()
            conn.close()
            st.success("✅ Datos de Balance General guardados correctamente.")

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
