# pages/13_Balance_general.py
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Paso 13: Balance General", page_icon="📒")

st.title("📒 Paso 13: Balance General")
st.caption(
    "Registre y/o verifique los saldos para construir el Balance General. "
    "Los pasivos por deudas se toman automáticamente del **Paso 9 – Deudas activas**: "
    "corto plazo → pasivo circulante; largo plazo → pasivo a largo plazo."
)

# ========= Helpers =========
def _as_df(obj, cols=None):
    """Devuelve un DataFrame a partir de obj (DF, lista de filas, dicts, etc.)."""
    if isinstance(obj, pd.DataFrame):
        return obj.copy()
    if obj is None:
        return pd.DataFrame(columns=cols or [])
    if isinstance(obj, list):
        try:
            return pd.DataFrame(obj)
        except Exception:
            return pd.DataFrame(columns=cols or [])
    if isinstance(obj, dict):
        try:
            return pd.DataFrame.from_records(obj)
        except Exception:
            return pd.DataFrame(columns=cols or [])
    return pd.DataFrame(columns=cols or [])

# Cargar totales de deudas (si existen; si no, 0)
tot_corto = 0
tot_largo = 0
try:
    _tot = st.session_state["reporte"]["deudas_activas"]["totales"]
    tot_corto = int(_tot.get("total_adeudado_corto_plazo_colones", 0) or 0)
    tot_largo = int(_tot.get("total_adeudado_largo_plazo_colones", 0) or 0)
except Exception:
    pass

# Catálogo de evidencias
evidencias = [
    "Los tiene en caja", "Estado de cuenta", "Movimientos/SINPE", "Factura/Recibo",
    "Contrato", "Inventario físico", "Fotos/Video", "Otro", "No aplica"
]

# Cargar datos previos si existen
bg_saved = st.session_state.get("reporte", {}).get("balance_general", {})

# ===================== ACTIVO CIRCULANTE =====================
st.subheader("I. Activo Circulante")

# 1) Caja y Bancos
st.markdown("**Caja y bancos**")
caja_placeholder = pd.DataFrame([{
    "Cuenta/Banco": "", "Saldo (₡)": 0, "Verificado por asesor": False,
    "Tipo de evidencia": "", "Comentario": ""
} for _ in range(3)])
caja_df = st.data_editor(
    _as_df(bg_saved.get("caja_bancos"), caja_placeholder.columns) or caja_placeholder,
    use_container_width=True, num_rows="dynamic", hide_index=True, key="bg_caja_bancos",
    column_config={
        "Cuenta/Banco": st.column_config.TextColumn("Cuenta/Banco"),
        "Saldo (₡)": st.column_config.NumberColumn("Saldo (₡)", min_value=0, step=10000, format="₡ %d"),
        "Verificado por asesor": st.column_config.CheckboxColumn("Verificado por asesor"),
        "Tipo de evidencia": st.column_config.SelectboxColumn("Tipo de evidencia", options=evidencias),
        "Comentario": st.column_config.TextColumn("Comentario"),
    },
)
caja_total = int(pd.to_numeric(caja_df.get("Saldo (₡)", pd.Series()), errors="coerce").fillna(0).sum())
st.metric("Subtotal Caja y Bancos", f"₡{caja_total:,.0f}")
st.markdown("---")

# 2) Cuentas por cobrar a clientes
st.markdown("**Cuentas por cobrar a clientes**")
cxc_placeholder = pd.DataFrame([{
    "Cliente/Descripción": "", "Monto (₡)": 0, "Verificado por asesor": False,
    "Tipo de evidencia": "", "Comentario": ""
} for _ in range(3)])
cxc_df = st.data_editor(
    _as_df(bg_saved.get("cxc_clientes"), cxc_placeholder.columns) or cxc_placeholder,
    use_container_width=True, num_rows="dynamic", hide_index=True, key="bg_cxc_clientes",
    column_config={
        "Cliente/Descripción": st.column_config.TextColumn("Cliente/Descripción"),
        "Monto (₡)": st.column_config.NumberColumn("Monto (₡)", min_value=0, step=10000, format="₡ %d"),
        "Verificado por asesor": st.column_config.CheckboxColumn("Verificado por asesor"),
        "Tipo de evidencia": st.column_config.SelectboxColumn("Tipo de evidencia", options=evidencias),
        "Comentario": st.column_config.TextColumn("Comentario"),
    },
)
cxc_total = int(pd.to_numeric(cxc_df.get("Monto (₡)", pd.Series()), errors="coerce").fillna(0).sum())
st.metric("Subtotal Cuentas por Cobrar a Clientes", f"₡{cxc_total:,.0f}")
st.markdown("---")

# 3) Inventarios
st.markdown("**Inventarios**")
inv_opts = {
    "Materia prima": "bg_inv_mp",
    "Producto en proceso": "bg_inv_pp",
    "Producto terminado": "bg_inv_pt",
}
subtotales_inv = {}
inv_dict = {}
for titulo, keyname in inv_opts.items():
    st.markdown(f"*{titulo}*")
    inv_placeholder = pd.DataFrame([{
        "Detalle": "", "Valor (₡)": 0, "Verificado por asesor": False,
        "Tipo de evidencia": "", "Comentario": ""
    } for _ in range(3)])
    df_inv = st.data_editor(
        _as_df(bg_saved.get("inventarios", {}).get(keyname), inv_placeholder.columns) or inv_placeholder,
        use_container_width=True, num_rows="dynamic", hide_index=True, key=keyname,
        column_config={
            "Detalle": st.column_config.TextColumn("Detalle"),
            "Valor (₡)": st.column_config.NumberColumn("Valor (₡)", min_value=0, step=10000, format="₡ %d"),
            "Verificado por asesor": st.column_config.CheckboxColumn("Verificado por asesor"),
            "Tipo de evidencia": st.column_config.SelectboxColumn("Tipo de evidencia", options=evidencias),
            "Comentario": st.column_config.TextColumn("Comentario"),
        },
    )
    subtotal = int(pd.to_numeric(df_inv.get("Valor (₡)", pd.Series()), errors="coerce").fillna(0).sum())
    subtotales_inv[titulo] = subtotal
    inv_dict[keyname] = df_inv.to_dict(orient="records")
    st.caption(f"Subtotal {titulo}: **₡{subtotal:,.0f}**")
    st.markdown("")
total_inventarios = int(sum(subtotales_inv.values()))
st.metric("**Total Inventarios**", f"₡{total_inventarios:,.0f}")
st.markdown("---")

# Total Activo Circulante
activo_circulante = int(caja_total + cxc_total + total_inventarios)
st.metric("💼 **Total Activo Circulante**", f"₡{activo_circulante:,.0f}")
st.divider()

# ===================== ACTIVO FIJO NETO =====================
st.subheader("II. Activo Fijo Neto")
st.caption("Ingrese cada activo fijo; se calcula neto = valor bruto – depreciación acumulada.")

af_placeholder = pd.DataFrame([{
    "Activo": "",
    "Valor bruto (₡)": 0,
    "Depreciación acum. (₡)": 0,
    "Verificado por asesor": False,
    "Tipo de evidencia": "",
    "Comentario": "",
} for _ in range(4)])

with st.expander("Agregar/editar activos fijos"):
    af_df = st.data_editor(
        _as_df(bg_saved.get("activo_fijo"), af_placeholder.columns) or af_placeholder,
        use_container_width=True, num_rows="dynamic", hide_index=True, key="bg_activo_fijo",
        column_config={
            "Activo": st.column_config.TextColumn("Activo"),
            "Valor bruto (₡)": st.column_config.NumberColumn("Valor bruto (₡)", min_value=0, step=25000, format="₡ %d"),
            "Depreciación acum. (₡)": st.column_config.NumberColumn("Depreciación acum. (₡)", min_value=0, step=25000, format="₡ %d"),
            "Verificado por asesor": st.column_config.CheckboxColumn("Verificado por asesor"),
            "Tipo de evidencia": st.column_config.SelectboxColumn("Tipo de evidencia", options=evidencias),
            "Comentario": st.column_config.TextColumn("Comentario"),
        },
    )
af_bruto = pd.to_numeric(af_df.get("Valor bruto (₡)", pd.Series()), errors="coerce").fillna(0)
af_depr  = pd.to_numeric(af_df.get("Depreciación acum. (₡)", pd.Series()), errors="coerce").fillna(0)
af_neto_series = (af_bruto - af_depr).clip(lower=0)
af_neto_total = int(af_neto_series.sum())
st.metric("🏭 **Activo Fijo Neto**", f"₡{af_neto_total:,.0f}")
st.divider()

# ===================== TOTALES DE ACTIVO =====================
total_activos = int(activo_circulante + af_neto_total)
st.metric("🧮 **Total Activos**", f"₡{total_activos:,.0f}")
st.divider()

# ===================== PASIVO =====================
st.subheader("III. Pasivo")

# A) Pasivo circulante
st.markdown("**Pasivo circulante**")

# CxP Proveedores
st.markdown("*Cuentas por pagar a proveedores*")
cpp_placeholder = pd.DataFrame([{
    "Proveedor": "", "Monto (₡)": 0, "Verificado por asesor": False,
    "Tipo de evidencia": "", "Comentario": ""
} for _ in range(3)])
cpp_df = st.data_editor(
    _as_df(bg_saved.get("cpp"), cpp_placeholder.columns) or cpp_placeholder,
    use_container_width=True, num_rows="dynamic", hide_index=True, key="bg_cpp",
    column_config={
        "Proveedor": st.column_config.TextColumn("Proveedor"),
        "Monto (₡)": st.column_config.NumberColumn("Monto (₡)", min_value=0, step=10000, format="₡ %d"),
        "Verificado por asesor": st.column_config.CheckboxColumn("Verificado por asesor"),
        "Tipo de evidencia": st.column_config.SelectboxColumn("Tipo de evidencia", options=evidencias),
        "Comentario": st.column_config.TextColumn("Comentario"),
    },
)
cpp_total = int(pd.to_numeric(cpp_df.get("Monto (₡)", pd.Series()), errors="coerce").fillna(0).sum())
st.caption(f"Subtotal CxP Proveedores: **₡{cpp_total:,.0f}**")

# Anticipos de clientes
st.markdown("*Anticipos de clientes*")
antic_placeholder = pd.DataFrame([{
    "Cliente/Descripción": "", "Monto (₡)": 0, "Verificado por asesor": False,
    "Tipo de evidencia": "", "Comentario": ""
} for _ in range(2)])
antic_df = st.data_editor(
    _as_df(bg_saved.get("anticipos"), antic_placeholder.columns) or antic_placeholder,
    use_container_width=True, num_rows="dynamic", hide_index=True, key="bg_anticipos",
    column_config={
        "Cliente/Descripción": st.column_config.TextColumn("Cliente/Descripción"),
        "Monto (₡)": st.column_config.NumberColumn("Monto (₡)", min_value=0, step=10000, format="₡ %d"),
        "Verificado por asesor": st.column_config.CheckboxColumn("Verificado por asesor"),
        "Tipo de evidencia": st.column_config.SelectboxColumn("Tipo de evidencia", options=evidencias),
        "Comentario": st.column_config.TextColumn("Comentario"),
    },
)
antic_total = int(pd.to_numeric(antic_df.get("Monto (₡)", pd.Series()), errors="coerce").fillna(0).sum())
st.caption(f"Subtotal Anticipos de clientes: **₡{antic_total:,.0f}**")

# Deudas corto (desde Paso 9)
st.markdown("*Cuentas por pagar a corto plazo (de Deudas Paso 9)*")
st.info(f"Total de corto plazo desde Deudas: **₡{tot_corto:,.0f}**")

pasivo_circulante = int(cpp_total + antic_total + tot_corto)
st.metric("💳 **Total Pasivo Circulante**", f"₡{pasivo_circulante:,.0f}")
st.markdown("---")

# B) Pasivo a largo plazo
st.markdown("**Pasivo a largo plazo**")
st.info(f"Total de largo plazo desde Deudas: **₡{tot_largo:,.0f}**")
pasivo_largo = int(tot_largo)

# Total Pasivo
total_pasivo = int(pasivo_circulante + pasivo_largo)
st.metric("📉 **Total Pasivos**", f"₡{total_pasivo:,.0f}")
st.divider()

# Patrimonio y Capital de Trabajo
patrimonio = int(total_activos - total_pasivo)
capital_trabajo = int(activo_circulante - pasivo_circulante)

colA, colB = st.columns(2)
with colA:
    st.metric("📈 **Patrimonio (Activo - Pasivo)**", f"₡{patrimonio:,.0f}")
with colB:
    st.metric("🧰 **Capital de trabajo (AC - PC)**", f"₡{capital_trabajo:,.0f}")
st.divider()

# Comentarios del asesor
st.subheader("Comentarios del asesor")
comentarios = st.text_area(
    "Observaciones, aclaraciones o notas relevantes para el análisis:",
    key="bg_comentarios", height=140, value=bg_saved.get("comentarios", "")
)
st.divider()

# ===================== Guardar / Navegación =====================
c1, c2 = st.columns([0.5, 0.5])
with c1:
    if st.button("⬅️ Volver a 12 – Estado de Resultados", key="bg_back_er", use_container_width=True):
        for prev in [
            "pages/12_Estado_de_resultadosl.py",
            "pages/12_Estado_resultados.py",
            "pages/12_Resultados.py",
        ]:
            try:
                st.switch_page(prev)
                break
            except Exception:
                continue

with c2:
    if st.button("Guardar Balance y continuar ➡️", key="bg_save_next", use_container_width=True):
        st.session_state.setdefault("reporte", {})
        st.session_state["reporte"]["balance_general"] = {
            "caja_bancos": caja_df.to_dict(orient="records"),
            "cxc_clientes": cxc_df.to_dict(orient="records"),
            "inventarios": inv_dict,
            "activo_fijo": af_df.to_dict(orient="records"),
            "cpp": cpp_df.to_dict(orient="records"),
            "anticipos": antic_df.to_dict(orient="records"),
            "comentarios": comentarios,
        }
        st.session_state["done_13"] = True

        for nxt in [
            "pages/14_Informe_final.py",
            "pages/14_informe_final.py",
            "pages/14_Informe.py",
            "pages/14_Resumen_financiero.py",
            "pages/14_Cierre.py",
        ]:
            try:
                st.switch_page(nxt)
                break
            except Exception:
                continue
        else:
            st.success("Balance general guardado. Abrí el **siguiente paso** desde el menú lateral.")
            st.stop()


