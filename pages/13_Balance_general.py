# pages/13_Balance_general.py
import streamlit as st
import pandas as pd
from utils.db import save_balance_general, load_visita   # 👈 agregado load_visita

st.set_page_config(page_title="Paso 13: Balance General", page_icon="📒")

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

    # Normalizar: asegurar columnas del placeholder
    if cols is not None:
        for col in cols:
            if col not in df.columns:
                df[col] = placeholder[col] if col in placeholder else None
        df = df[cols]

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

caja_df = _as_df(bg_saved.get("caja_bancos"), cols=caja_placeholder.columns, placeholder=caja_placeholder)

# 🔧 Renombrar si vienen desde SQL
caja_df = caja_df.rename(columns={
    "descripcion": "Cuenta/Banco",
    "monto": "Saldo (₡)",
    "verificado": "Verificado por asesor",
    "evidencia": "Tipo de evidencia",
    "comentario": "Comentario",
})

# 🔧 Forzar tipos compatibles
caja_df["Saldo (₡)"] = pd.to_numeric(caja_df["Saldo (₡)"], errors="coerce").fillna(0).astype(int)
caja_df["Verificado por asesor"] = caja_df["Verificado por asesor"].map(
    {True: True, False: False, 1: True, 0: False, "1": True, "0": False}
).fillna(False).astype(bool)

caja_df = st.data_editor(
    caja_df,
    use_container_width=True, num_rows="dynamic", hide_index=True, key="bg_caja_bancos",
    column_config={
        "Cuenta/Banco": st.column_config.TextColumn("Cuenta/Banco"),
        "Saldo (₡)": st.column_config.NumberColumn("Saldo (₡)", min_value=0, step=10000, format="₡ %d"),
        "Verificado por asesor": st.column_config.CheckboxColumn("Verificado por asesor"),
        "Tipo de evidencia": st.column_config.SelectboxColumn("Tipo de evidencia", options=evidencias, required=False),
        "Comentario": st.column_config.TextColumn("Comentario"),
    },
)

caja_total = int(caja_df["Saldo (₡)"].sum())
st.metric("Subtotal Caja y Bancos", f"₡{caja_total:,.0f}")
st.markdown("---")


# 2) Cuentas por cobrar
st.markdown("**Cuentas por cobrar a clientes**")
cxc_placeholder = pd.DataFrame([{
    "Cliente/Descripción": "", "Monto (₡)": 0, "Verificado por asesor": False,
    "Tipo de evidencia": "", "Comentario": ""
} for _ in range(3)])

cxc_df = _as_df(bg_saved.get("cxc_clientes"), cols=cxc_placeholder.columns, placeholder=cxc_placeholder)

# Renombrar si vienen desde SQL
cxc_df = cxc_df.rename(columns={
    "descripcion": "Cliente/Descripción",
    "monto": "Monto (₡)",
    "verificado": "Verificado por asesor",
    "evidencia": "Tipo de evidencia",
    "comentario": "Comentario",
})

# Asegurar columnas faltantes y tipos
for col in cxc_placeholder.columns:
    if col not in cxc_df.columns:
        cxc_df[col] = cxc_placeholder[col]

cxc_df["Monto (₡)"] = pd.to_numeric(cxc_df["Monto (₡)"], errors="coerce").fillna(0).astype(int)
cxc_df["Verificado por asesor"] = cxc_df["Verificado por asesor"].map(
    {True: True, False: False, 1: True, 0: False, "1": True, "0": False}
).fillna(False).astype(bool)

cxc_df = st.data_editor(
    cxc_df,
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
inv_placeholder = pd.DataFrame([{
    "Detalle": "", "Valor (₡)": 0, "Verificado por asesor": False,
    "Tipo de evidencia": "", "Comentario": ""
} for _ in range(3)])

def inv_editor(name, key):
    df = _as_df(bg_saved.get(name), cols=inv_placeholder.columns, placeholder=inv_placeholder)
    df["Valor (₡)"] = pd.to_numeric(df["Valor (₡)"], errors="coerce").fillna(0).astype(int)
    df["Verificado por asesor"] = df["Verificado por asesor"].astype(bool)
    df = st.data_editor(
        df,
        use_container_width=True, num_rows="dynamic", hide_index=True, key=key,
        column_config={
            "Detalle": st.column_config.TextColumn("Detalle"),
            "Valor (₡)": st.column_config.NumberColumn("Valor (₡)", min_value=0, step=10000, format="₡ %d"),
            "Verificado por asesor": st.column_config.CheckboxColumn("Verificado por asesor"),
            "Tipo de evidencia": st.column_config.SelectboxColumn("Tipo de evidencia", options=evidencias, required=False),
            "Comentario": st.column_config.TextColumn("Comentario"),
        },
    )
    subtotal = int(df["Valor (₡)"].sum())
    return df, subtotal

st.markdown("*Materia prima*")
inv_placeholder = pd.DataFrame([{
    "Detalle": "", "Valor (₡)": 0, "Verificado por asesor": False,
    "Tipo de evidencia": "", "Comentario": ""
} for _ in range(3)])

df_inv_mp = _as_df(bg_saved.get("inv_mp"), cols=inv_placeholder.columns, placeholder=inv_placeholder)

# Renombrar si vienen desde SQL
df_inv_mp = df_inv_mp.rename(columns={
    "descripcion": "Detalle",
    "monto": "Valor (₡)",
    "verificado": "Verificado por asesor",
    "evidencia": "Tipo de evidencia",
    "comentario": "Comentario",
})

for col in inv_placeholder.columns:
    if col not in df_inv_mp.columns:
        df_inv_mp[col] = inv_placeholder[col]

df_inv_mp["Valor (₡)"] = pd.to_numeric(df_inv_mp["Valor (₡)"], errors="coerce").fillna(0).astype(int)
df_inv_mp["Verificado por asesor"] = df_inv_mp["Verificado por asesor"].map(
    {True: True, False: False, 1: True, 0: False, "1": True, "0": False}
).fillna(False).astype(bool)

df_inv_mp = st.data_editor(
    df_inv_mp,
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
df_inv_pp = _as_df(bg_saved.get("inv_pp"), cols=inv_placeholder.columns, placeholder=inv_placeholder)

df_inv_pp = df_inv_pp.rename(columns={
    "descripcion": "Detalle",
    "monto": "Valor (₡)",
    "verificado": "Verificado por asesor",
    "evidencia": "Tipo de evidencia",
    "comentario": "Comentario",
})
for col in inv_placeholder.columns:
    if col not in df_inv_pp.columns:
        df_inv_pp[col] = inv_placeholder[col]

df_inv_pp["Valor (₡)"] = pd.to_numeric(df_inv_pp["Valor (₡)"], errors="coerce").fillna(0).astype(int)
df_inv_pp["Verificado por asesor"] = df_inv_pp["Verificado por asesor"].map(
    {True: True, False: False, 1: True, 0: False, "1": True, "0": False}
).fillna(False).astype(bool)

df_inv_pp = st.data_editor(
    df_inv_pp,
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
df_inv_pt = _as_df(bg_saved.get("inv_pt"), cols=inv_placeholder.columns, placeholder=inv_placeholder)

df_inv_pt = df_inv_pt.rename(columns={
    "descripcion": "Detalle",
    "monto": "Valor (₡)",
    "verificado": "Verificado por asesor",
    "evidencia": "Tipo de evidencia",
    "comentario": "Comentario",
})
for col in inv_placeholder.columns:
    if col not in df_inv_pt.columns:
        df_inv_pt[col] = inv_placeholder[col]

df_inv_pt["Valor (₡)"] = pd.to_numeric(df_inv_pt["Valor (₡)"], errors="coerce").fillna(0).astype(int)
df_inv_pt["Verificado por asesor"] = df_inv_pt["Verificado por asesor"].map(
    {True: True, False: False, 1: True, 0: False, "1": True, "0": False}
).fillna(False).astype(bool)

df_inv_pt = st.data_editor(
    df_inv_pt,
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

af_df = _as_df(bg_saved.get("activo_fijo"), cols=af_placeholder.columns, placeholder=af_placeholder)

# Renombrar si llegan en genérico desde SQL
af_df = af_df.rename(columns={
    "descripcion": "Activo",
    "monto": "Valor bruto (₡)",
    "verificado": "Verificado por asesor",
    "evidencia": "Tipo de evidencia",
    "comentario": "Comentario",
    "depreciacion": "Depreciación acum. (₡)",
})
for col in af_placeholder.columns:
    if col not in af_df.columns:
        af_df[col] = af_placeholder[col]

af_df["Valor bruto (₡)"] = pd.to_numeric(af_df["Valor bruto (₡)"], errors="coerce").fillna(0).astype(int)
af_df["Depreciación acum. (₡)"] = pd.to_numeric(af_df["Depreciación acum. (₡)"], errors="coerce").fillna(0).astype(int)
af_df["Verificado por asesor"] = af_df["Verificado por asesor"].map(
    {True: True, False: False, 1: True, 0: False, "1": True, "0": False}
).fillna(False).astype(bool)

with st.expander("Agregar/editar activos fijos"):
    af_df = st.data_editor(
        af_df,
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

cpp_df = _as_df(bg_saved.get("cpp"), cols=cpp_placeholder.columns, placeholder=cpp_placeholder)

# Renombrar si vienen desde SQL
cpp_df = cpp_df.rename(columns={
    "descripcion": "Proveedor",
    "monto": "Monto (₡)",
    "verificado": "Verificado por asesor",
    "evidencia": "Tipo de evidencia",
    "comentario": "Comentario",
})

# Asegurar columnas faltantes y tipos
for col in cpp_placeholder.columns:
    if col not in cpp_df.columns:
        cpp_df[col] = cpp_placeholder[col]

cpp_df["Monto (₡)"] = pd.to_numeric(cpp_df["Monto (₡)"], errors="coerce").fillna(0).astype(int)
cpp_df["Verificado por asesor"] = cpp_df["Verificado por asesor"].map(
    {True: True, False: False, 1: True, 0: False, "1": True, "0": False}
).fillna(False).astype(bool)

cpp_df = st.data_editor(
    cpp_df,
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

antic_df = _as_df(bg_saved.get("anticipos"), cols=antic_placeholder.columns, placeholder=antic_placeholder)

antic_df = antic_df.rename(columns={
    "descripcion": "Cliente/Descripción",
    "monto": "Monto (₡)",
    "verificado": "Verificado por asesor",
    "evidencia": "Tipo de evidencia",
    "comentario": "Comentario",
})

for col in antic_placeholder.columns:
    if col not in antic_df.columns:
        antic_df[col] = antic_placeholder[col]

antic_df["Monto (₡)"] = pd.to_numeric(antic_df["Monto (₡)"], errors="coerce").fillna(0).astype(int)
antic_df["Verificado por asesor"] = antic_df["Verificado por asesor"].map(
    {True: True, False: False, 1: True, 0: False, "1": True, "0": False}
).fillna(False).astype(bool)

antic_df = st.data_editor(
    antic_df,
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
        def _clean(df, num_cols=None, bool_cols=None):
            """
            Limpia el DataFrame antes de guardarlo en la BD.
            - Mantiene filas con montos = 0 (ya que pueden ser válidas).
            - Solo elimina filas 100% vacías (todas las columnas NaN).
            """
            num_cols = num_cols or []
            bool_cols = bool_cols or []
            if df is None or df.empty:
                return pd.DataFrame()
            df = df.copy()
        
            # ✅ Solo eliminar filas completamente vacías
            df = df[~df.isna().all(axis=1)]
        
            # Convertir numéricos y booleanos
            for c in num_cols:
                if c in df.columns:
                    df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)
            for c in bool_cols:
                if c in df.columns:
                    df[c] = df[c].map({
                        True: True, False: False,
                        1: True, 0: False, "1": True, "0": False
                    }).fillna(False).astype(bool)
        
            return df

        def _records_genericos(df, desc_col, monto_col):
            """Mapea a la forma generica de la tabla: descripcion, monto, verificado, evidencia, comentario."""
            if df is None or df.empty:
                return []
            out = []
            for r in df.to_dict(orient="records"):
                out.append({
                    "descripcion": r.get(desc_col, "") or "",
                    "monto": int(pd.to_numeric(r.get(monto_col, 0), errors="coerce") or 0),
                    "verificado": bool(r.get("Verificado por asesor", False)),
                    "evidencia": r.get("Tipo de evidencia", "") or "",
                    "comentario": r.get("Comentario", "") or "",
                })
            return out

        def _records_activo_fijo(df):
            """Activo fijo requiere valor_bruto y depreciacion."""
            if df is None or df.empty:
                return []
            out = []
            for r in df.to_dict(orient="records"):
                out.append({
                    "activo": r.get("Activo", "") or "",
                    "valor_bruto": int(pd.to_numeric(r.get("Valor bruto (₡)", 0), errors="coerce") or 0),
                    "depreciacion": int(pd.to_numeric(r.get("Depreciación acum. (₡)", 0), errors="coerce") or 0),
                    "verificado": bool(r.get("Verificado por asesor", False)),
                    "evidencia": r.get("Tipo de evidencia", "") or "",
                    "comentario": r.get("Comentario", "") or "",
                })
            return out

        # --- Limpiar DFs que ya tienes en memoria ---
        caja_df_clean = _clean(caja_df, num_cols=["Saldo (₡)"], bool_cols=["Verificado por asesor"])
        cxc_df_clean = _clean(cxc_df, num_cols=["Monto (₡)"], bool_cols=["Verificado por asesor"])
        df_inv_mp_clean = _clean(df_inv_mp, num_cols=["Valor (₡)"], bool_cols=["Verificado por asesor"])
        df_inv_pp_clean = _clean(df_inv_pp, num_cols=["Valor (₡)"], bool_cols=["Verificado por asesor"])
        df_inv_pt_clean = _clean(df_inv_pt, num_cols=["Valor (₡)"], bool_cols=["Verificado por asesor"])
        af_df_clean = _clean(af_df, num_cols=["Valor bruto (₡)", "Depreciación acum. (₡)"], bool_cols=["Verificado por asesor"])
        cpp_df_clean = _clean(cpp_df, num_cols=["Monto (₡)"], bool_cols=["Verificado por asesor"])
        antic_df_clean = _clean(antic_df, num_cols=["Monto (₡)"], bool_cols=["Verificado por asesor"])

        # --- Armar payload para DB (genérico + AF) ---
        payload = {
            "caja_bancos": _records_genericos(caja_df_clean, "Cuenta/Banco", "Saldo (₡)"),
            "cxc_clientes": _records_genericos(cxc_df_clean, "Cliente/Descripción", "Monto (₡)"),
            "inv_mp": _records_genericos(df_inv_mp_clean, "Detalle", "Valor (₡)"),
            "inv_pp": _records_genericos(df_inv_pp_clean, "Detalle", "Valor (₡)"),
            "inv_pt": _records_genericos(df_inv_pt_clean, "Detalle", "Valor (₡)"),
            "activo_fijo": _records_activo_fijo(af_df_clean),
            "cpp": _records_genericos(cpp_df_clean, "Proveedor", "Monto (₡)"),
            "anticipos": _records_genericos(antic_df_clean, "Cliente/Descripción", "Monto (₡)"),
            "totales": {
                "activo_circulante": int(caja_total + cxc_total + (subtotal_mp + subtotal_pp + subtotal_pt)),
                # "activo_fijo": int((af_df_clean["Valor bruto (₡)"] - af_df_clean["Depreciación acum. (₡)"]).clip(lower=0).sum()) if not af_df_clean.empty else 0,
                # "total_activos": int(activo_circulante + (af_df_clean["Valor bruto (₡)"] - af_df_clean["Depreciación acum. (₡)"]).clip(lower=0).sum()) if not af_df_clean.empty else int(activo_circulante),
                "activo_fijo": af_neto_total,
                "total_activos": total_activos,
                "pasivo_circulante": int(cpp_total + antic_total + tot_corto),
                "pasivo_largo": int(tot_largo),
                "total_pasivo": int((cpp_total + antic_total + tot_corto) + int(tot_largo)),
                "patrimonio": int(total_activos - (cpp_total + antic_total + tot_corto + tot_largo)),
                "capital_trabajo": int(activo_circulante - (cpp_total + antic_total + tot_corto)),
            },
            "comentarios": comentarios or "",
        }

        # También guardamos en session_state por consistencia
        st.session_state.setdefault("reporte", {})
        st.session_state["reporte"]["balance_general"] = payload
        st.session_state["done_13"] = True

        # --- Validaciones claves ---
        cliente_id = st.session_state.get("cliente", {}).get("identificacion", "")
        mes_iso = st.session_state.get("mes_iso", "")
        if not cliente_id or not mes_iso:
            st.error("Falta `cliente.identificacion` o `mes_iso` en el estado de la sesión. No se puede guardar.")
            st.stop()

        # --- Guardar en DB: DELETE + INSERT por cliente/mes ---
        with st.spinner("Guardando balance general en la base de datos…"):
            try:
                save_ok = save_balance_general(
                    cliente_id=cliente_id,
                    mes_iso=mes_iso,
                    datos=payload  # La función debe hacer DELETE por (cliente_id, mes_iso) y luego INSERT masivo
                )
            except Exception as e:
                st.error(f"Error guardando balance general en SQL: {e}")
                st.stop()

        if save_ok:
            st.success("✅ Balance general guardado/actualizado correctamente.")
            # Ir al paso 14
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
                st.info("Abrí el **siguiente paso** desde el menú lateral.")
                st.stop()
        else:
            st.warning("⚠️ No se guardó. Verifica que `save_balance_general` haga DELETE+INSERT por cliente y mes, y que retorne True al éxito.")
