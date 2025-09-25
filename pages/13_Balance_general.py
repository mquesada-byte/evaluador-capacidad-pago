# pages/13_Balance_general.py
import streamlit as st
import pandas as pd
from utils.db import save_balance_general, load_visita   # 👈 agregado load_visita

st.set_page_config(page_title="Paso 13: Balance General", page_icon="📒")

st.title("📒 Paso 13: Balance General")
st.caption(
    "Registre y/o verifique los saldos para construir el Balance General. "
    "Los pasivos por deudas se toman automáticamente del **Paso 9 – Deudas activas**: "
    "corto plazo → pasivo circulante; largo plazo → pasivo a largo plazo."
)

# ========= Helpers =========
def _as_df(obj, cols=None, placeholder=None):
    """Convierte obj a DataFrame, o devuelve placeholder si está vacío."""
    if cols is not None:
        cols = list(cols)

    try:
        if isinstance(obj, pd.DataFrame):
            df = obj.copy()
        elif isinstance(obj, dict):
            if "data" in obj and isinstance(obj["data"], list):
                df = pd.DataFrame.from_records(obj["data"])
            else:
                df = pd.DataFrame.from_records([obj])
        elif isinstance(obj, (list, tuple)):
            df = pd.DataFrame(obj, columns=cols)
        else:
            df = pd.DataFrame(columns=cols or [])
    except Exception:
        df = pd.DataFrame(columns=cols or [])

    if df.empty and placeholder is not None:
        return placeholder.copy()
    return df


# ===================== Cargar totales de deudas =====================
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

# Inicializar "reporte" en session_state si no existe o si no es dict
if "reporte" not in st.session_state or not isinstance(st.session_state["reporte"], dict):
    st.session_state["reporte"] = {"balance_general": {}}

# Recuperar datos guardados si existen
bg_saved = st.session_state["reporte"].get("balance_general", {})




# 👇 Ajuste: cargar desde SQL si no hay en session_state
if not bg_saved:
    cliente_id = st.session_state.get("cliente", {}).get("identificacion", "")
    mes_iso = st.session_state.get("mes_iso", "")
    try:
        datos = load_visita(cliente_id)
        if "balance_general" in datos:
            bg_saved = datos["balance_general"]
            st.session_state["reporte"]["balance_general"] = bg_saved
    except Exception as e:
        st.warning(f"No se pudo cargar balance general desde SQL: {e}")


# ===================== ACTIVO CIRCULANTE =====================
st.subheader("I. Activo Circulante")

# 1) Caja y Bancos
st.markdown("**Caja y bancos**")
caja_placeholder = pd.DataFrame([{
    "Cuenta/Banco": "", "Saldo (₡)": 0, "Verificado por asesor": False,
    "Tipo de evidencia": "", "Comentario": ""
} for _ in range(3)])
caja_df = st.data_editor(
    _as_df(bg_saved.get("caja_bancos"), cols=caja_placeholder.columns, placeholder=caja_placeholder),
    use_container_width=True, num_rows="dynamic", hide_index=True, key="bg_caja_bancos",
    column_config={
        "Cuenta/Banco": st.column_config.TextColumn("Cuenta/Banco"),
        "Saldo (₡)": st.column_config.NumberColumn("Saldo (₡)", min_value=0, step=10000, format="₡ %d"),
        "Verificado por asesor": st.column_config.CheckboxColumn("Verificado por asesor"),
        "Tipo de evidencia": st.column_config.SelectboxColumn("Tipo de evidencia", options=evidencias, required=False),
        "Comentario": st.column_config.TextColumn("Comentario"),
    },
)
caja_total = int(pd.to_numeric(caja_df.get("Saldo (₡)", pd.Series()), errors="coerce").fillna(0).sum())
st.metric("Subtotal Caja y Bancos", f"₡{caja_total:,.0f}")
st.markdown("---")

# 2) Cuentas por cobrar
st.markdown("**Cuentas por cobrar a clientes**")
cxc_placeholder = pd.DataFrame([{
    "Cliente/Descripción": "", "Monto (₡)": 0, "Verificado por asesor": False,
    "Tipo de evidencia": "", "Comentario": ""
} for _ in range(3)])
cxc_df = st.data_editor(
    _as_df(bg_saved.get("cxc_clientes"), cols=cxc_placeholder.columns, placeholder=cxc_placeholder),
    use_container_width=True, num_rows="dynamic", hide_index=True, key="bg_cxc_clientes",
    column_config={
        "Cliente/Descripción": st.column_config.TextColumn("Cliente/Descripción"),
        "Monto (₡)": st.column_config.NumberColumn("Monto (₡)", min_value=0, step=10000, format="₡ %d"),
        "Verificado por asesor": st.column_config.CheckboxColumn("Verificado por asesor"),
        "Tipo de evidencia": st.column_config.SelectboxColumn("Tipo de evidencia", options=evidencias, required=False),
        "Comentario": st.column_config.TextColumn("Comentario"),
    },
)
cxc_total = int(pd.to_numeric(cxc_df.get("Monto (₡)", pd.Series()), errors="coerce").fillna(0).sum())
st.metric("Subtotal Cuentas por Cobrar", f"₡{cxc_total:,.0f}")
st.markdown("---")

# 3) Inventarios
st.markdown("**Inventarios**")
inv_cols = ["Detalle", "Valor (₡)", "Verificado por asesor", "Tipo de evidencia", "Comentario"]

inv_placeholder = pd.DataFrame([{
    "Detalle": "", "Valor (₡)": 0, "Verificado por asesor": False,
    "Tipo de evidencia": "", "Comentario": ""
} for _ in range(3)])

st.markdown("*Materia prima*")
df_inv_mp = st.data_editor(
    _as_df(bg_saved.get("inv_mp"), cols=inv_placeholder.columns, placeholder=inv_placeholder),
    use_container_width=True, num_rows="dynamic", hide_index=True, key="bg_inv_mp",
    column_config={
        "Detalle": st.column_config.TextColumn("Detalle"),
        "Valor (₡)": st.column_config.NumberColumn("Valor (₡)", min_value=0, step=10000, format="₡ %d"),
        "Verificado por asesor": st.column_config.CheckboxColumn("Verificado por asesor"),
        "Tipo de evidencia": st.column_config.SelectboxColumn("Tipo de evidencia", options=evidencias, required=False),
        "Comentario": st.column_config.TextColumn("Comentario"),
    },
)
subtotal_mp = int(pd.to_numeric(df_inv_mp.get("Valor (₡)", pd.Series()), errors="coerce").fillna(0).sum())
st.caption(f"Subtotal Materia Prima: **₡{subtotal_mp:,.0f}**")

st.markdown("*Producto en proceso*")
df_inv_pp = st.data_editor(
    _as_df(bg_saved.get("inv_pp"), cols=inv_placeholder.columns, placeholder=inv_placeholder),
    use_container_width=True, num_rows="dynamic", hide_index=True, key="bg_inv_pp",
    column_config={
        "Detalle": st.column_config.TextColumn("Detalle"),
        "Valor (₡)": st.column_config.NumberColumn("Valor (₡)", min_value=0, step=10000, format="₡ %d"),
        "Verificado por asesor": st.column_config.CheckboxColumn("Verificado por asesor"),
        "Tipo de evidencia": st.column_config.SelectboxColumn("Tipo de evidencia", options=evidencias, required=False),
        "Comentario": st.column_config.TextColumn("Comentario"),
    },
)
subtotal_pp = int(pd.to_numeric(df_inv_pp.get("Valor (₡)", pd.Series()), errors="coerce").fillna(0).sum())
st.caption(f"Subtotal Producto en Proceso: **₡{subtotal_pp:,.0f}**")

st.markdown("*Producto terminado*")
df_inv_pt = st.data_editor(
    _as_df(bg_saved.get("inv_pt"), cols=inv_placeholder.columns, placeholder=inv_placeholder),
    use_container_width=True, num_rows="dynamic", hide_index=True, key="bg_inv_pt",
    column_config={
        "Detalle": st.column_config.TextColumn("Detalle"),
        "Valor (₡)": st.column_config.NumberColumn("Valor (₡)", min_value=0, step=10000, format="₡ %d"),
        "Verificado por asesor": st.column_config.CheckboxColumn("Verificado por asesor"),
        "Tipo de evidencia": st.column_config.SelectboxColumn("Tipo de evidencia", options=evidencias, required=False),
        "Comentario": st.column_config.TextColumn("Comentario"),
    },
)
subtotal_pt = int(pd.to_numeric(df_inv_pt.get("Valor (₡)", pd.Series()), errors="coerce").fillna(0).sum())
st.caption(f"Subtotal Producto Terminado: **₡{subtotal_pt:,.0f}**")

total_inventarios = subtotal_mp + subtotal_pp + subtotal_pt
st.metric("**Total Inventarios**", f"₡{total_inventarios:,.0f}")
st.markdown("---")

# Total Activo Circulante
activo_circulante = int(caja_total + cxc_total + total_inventarios)
st.metric("💼 **Total Activo Circulante**", f"₡{activo_circulante:,.0f}")
st.divider()

# ===================== ACTIVO FIJO NETO =====================
st.subheader("II. Activo Fijo Neto")
af_placeholder = pd.DataFrame([{
    "Activo": "", "Valor bruto (₡)": 0, "Depreciación acum. (₡)": 0,
    "Verificado por asesor": False, "Tipo de evidencia": "", "Comentario": ""
} for _ in range(4)])
with st.expander("Agregar/editar activos fijos"):
    af_df = st.data_editor(
        _as_df(bg_saved.get("activo_fijo"), cols=af_placeholder.columns, placeholder=af_placeholder),
        use_container_width=True, num_rows="dynamic", hide_index=True, key="bg_activo_fijo",
        column_config={
            "Activo": st.column_config.TextColumn("Activo"),
            "Valor bruto (₡)": st.column_config.NumberColumn("Valor bruto (₡)", min_value=0, step=25000, format="₡ %d"),
            "Depreciación acum. (₡)": st.column_config.NumberColumn("Depreciación acum. (₡)", min_value=0, step=25000, format="₡ %d"),
            "Verificado por asesor": st.column_config.CheckboxColumn("Verificado por asesor"),
            "Tipo de evidencia": st.column_config.SelectboxColumn("Tipo de evidencia", options=evidencias, required=False),
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

# Proveedores
st.markdown("*Cuentas por pagar a proveedores*")
cpp_placeholder = pd.DataFrame([{
    "Proveedor": "", "Monto (₡)": 0, "Verificado por asesor": False,
    "Tipo de evidencia": "", "Comentario": ""
} for _ in range(3)])
cpp_df = st.data_editor(
    _as_df(bg_saved.get("cpp"), cols=cpp_placeholder.columns, placeholder=cpp_placeholder),
    use_container_width=True, num_rows="dynamic", hide_index=True, key="bg_cpp",
    column_config={
        "Proveedor": st.column_config.TextColumn("Proveedor"),
        "Monto (₡)": st.column_config.NumberColumn("Monto (₡)", min_value=0, step=10000, format="₡ %d"),
        "Verificado por asesor": st.column_config.CheckboxColumn("Verificado por asesor"),
        "Tipo de evidencia": st.column_config.SelectboxColumn("Tipo de evidencia", options=evidencias, required=False),
        "Comentario": st.column_config.TextColumn("Comentario"),
    },
)
cpp_total = int(pd.to_numeric(cpp_df.get("Monto (₡)", pd.Series()), errors="coerce").fillna(0).sum())
st.caption(f"Subtotal CxP Proveedores: **₡{cpp_total:,.0f}**")

# Anticipos
st.markdown("*Anticipos de clientes*")
antic_placeholder = pd.DataFrame([{
    "Cliente/Descripción": "", "Monto (₡)": 0, "Verificado por asesor": False,
    "Tipo de evidencia": "", "Comentario": ""
} for _ in range(2)])
antic_df = st.data_editor(
    _as_df(bg_saved.get("anticipos"), cols=antic_placeholder.columns, placeholder=antic_placeholder),
    use_container_width=True, num_rows="dynamic", hide_index=True, key="bg_anticipos",
    column_config={
        "Cliente/Descripción": st.column_config.TextColumn("Cliente/Descripción"),
        "Monto (₡)": st.column_config.NumberColumn("Monto (₡)", min_value=0, step=10000, format="₡ %d"),
        "Verificado por asesor": st.column_config.CheckboxColumn("Verificado por asesor"),
        "Tipo de evidencia": st.column_config.SelectboxColumn("Tipo de evidencia", options=evidencias, required=False),
        "Comentario": st.column_config.TextColumn("Comentario"),
    },
)
antic_total = int(pd.to_numeric(antic_df.get("Monto (₡)", pd.Series()), errors="coerce").fillna(0).sum())
st.caption(f"Subtotal Anticipos de clientes: **₡{antic_total:,.0f}**")

# Deudas de paso 9
st.markdown("*Cuentas por pagar a corto plazo (de Deudas Paso 9)*")
st.info(f"Total de corto plazo desde Deudas: **₡{tot_corto:,.0f}**")

pasivo_circulante = int(cpp_total + antic_total + tot_corto)
st.metric("💳 **Total Pasivo Circulante**", f"₡{pasivo_circulante:,.0f}")
st.markdown("---")

st.markdown("**Pasivo a largo plazo**")
st.info(f"Total de largo plazo desde Deudas: **₡{tot_largo:,.0f}**")
pasivo_largo = int(tot_largo)

total_pasivo = int(pasivo_circulante + pasivo_largo)
st.metric("📉 **Total Pasivos**", f"₡{total_pasivo:,.0f}")
st.divider()

# ===================== PATRIMONIO =====================
patrimonio = int(total_activos - total_pasivo)
capital_trabajo = int(activo_circulante - pasivo_circulante)
colA, colB = st.columns(2)
with colA:
    st.metric("📈 **Patrimonio (Activo - Pasivo)**", f"₡{patrimonio:,.0f}")
with colB:
    st.metric("🧰 **Capital de trabajo (AC - PC)**", f"₡{capital_trabajo:,.0f}")
st.divider()

# ===================== COMENTARIOS =====================
st.subheader("Comentarios del asesor")
comentarios = st.text_area(
    "Observaciones, aclaraciones o notas relevantes para el análisis:",
    key="bg_comentarios", height=140,
    value=bg_saved.get("comentarios", "")
)
st.divider()

# ===================== GUARDAR / NAVEGACIÓN =====================
c1, c2 = st.columns([0.5, 0.5])
with c1:
    if st.button("⬅️ Volver a 12 – Estado de Resultados", key="bg_back_er", use_container_width=True):
        for prev in [
            "pages/12_Estado_de_resultados.py",
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
            "inv_mp": df_inv_mp.to_dict(orient="records"),
            "inv_pp": df_inv_pp.to_dict(orient="records"),
            "inv_pt": df_inv_pt.to_dict(orient="records"),
            "activo_fijo": af_df.to_dict(orient="records"),
            "cpp": cpp_df.to_dict(orient="records"),
            "anticipos": antic_df.to_dict(orient="records"),
            "totales": {
                "activo_circulante": activo_circulante,
                "activo_fijo": af_neto_total,
                "total_activos": total_activos,
                "pasivo_circulante": pasivo_circulante,
                "pasivo_largo": pasivo_largo,
                "total_pasivo": total_pasivo,
                "patrimonio": patrimonio,
                "capital_trabajo": capital_trabajo,
            },
            "comentarios": comentarios,
        }
        st.session_state["done_13"] = True


        # 👇 Guardar en SQL
        cliente_id = st.session_state.get("cliente", {}).get("identificacion", "")
        mes_iso = st.session_state.get("mes_iso", "")

        try:
            save_ok = save_balance_general(
                cliente_id=cliente_id,
                mes_iso=mes_iso,
                datos=st.session_state["reporte"]["balance_general"]
            )
            if save_ok:
                st.success("✅ Balance general guardado en la base de datos.")
            else:
                st.warning("⚠️ No se pudo guardar el balance en la base de datos.")
        except Exception as e:
            st.error(f"Error guardando balance general en SQL: {e}")


        
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
