import streamlit as st
import pandas as pd
from utils.db import save_deudas_activas, load_visita


st.set_page_config(page_title="Paso 9: Deudas activas del hogar", page_icon="💳")

# =========================
# PASO 9 – Deudas activas del hogar (multipágina)
# =========================
def _mensualizar_pago(monto: float, periodicidad: str) -> float:
    per = (periodicidad or "").lower()
    if per == "diario":        return monto * 30.0
    if per == "semanal":       return monto * (52.0 / 12.0)
    if per == "quincenal":     return monto * 2.0
    if per == "mensual":       return monto
    if per == "bimestral":     return monto / 2.0
    if per == "trimestral":    return monto / 3.0
    if per == "semestral":     return monto / 6.0
    if per == "anual":         return monto / 12.0
    return 0.0

st.title("💳 Paso 9: Deudas activas del hogar")
st.caption(
    "Registre los préstamos/obligaciones vigentes del cliente o su núcleo. "
    "Se calculará la **cuota mensual total** (para resultados) y el **saldo total adeudado** (para balance). "
    "Incluye **clasificación por plazo** para separar **pasivo circulante** y **pasivo a largo plazo**."
)

# Catálogos
relaciones = ["Cliente", "Pareja", "Hogar (compartida)", "Otro"]
tipos_deuda = ["Préstamo personal", "Préstamo de negocio", "Hipotecario", "Vehículo",
               "Tarjeta de crédito", "Comercio/Tienda", "Microcrédito", "Otro"]
periodicidades_pago = ["Mensual", "Quincenal", "Semanal", "Diario", "Bimestral", "Trimestral", "Semestral", "Anual"]
evidencias = ["Estado de cuenta", "Contrato", "Tabla de amortización", "Recibo de pago",
              "SINPE/Extracto", "Credid", "Equifax", "Foto/Chat", "No aplica", "Otro"]
estados = ["Al día", "Atraso"]
plazos = ["Corto plazo (≤12 meses)", "Largo plazo (>12 meses)"]

# Columnas base (entrada)
base_cols = [
    "Titular",
    "Acreedor/Entidad",
    "Tipo de deuda",
    "Saldo adeudado (₡)",
    "Cuota por período (₡)",
    "Periodicidad de pago",
    "Verificado por asesor",
    "Tipo de evidencia",
    "Estado",
    "Días de atraso",
    "Comentario",
    "Meses restantes (opcional)",
    "Plazo (clasificación)",
]

# ========= CARGA INICIAL DESDE LO GUARDADO O SQL =========
cliente_id = st.session_state.get("cliente", {}).get("identificacion", "").strip()
df_base_inicial = None

# 1) Intentar cargar desde SQL
if cliente_id:
    datos = load_visita(cliente_id)
    if datos and "deudas_activas" in datos:
        try:
            df_base_inicial = pd.DataFrame(datos["deudas_activas"])
        except Exception:
            df_base_inicial = None

# 2) Si no hay en SQL, intentar con lo guardado en session_state
if df_base_inicial is None or df_base_inicial.empty:
    guardado = (st.session_state.get("reporte", {})
                .get("deudas_activas", {})
                .get("tabla", []))
    if guardado:
        df_base_inicial = pd.DataFrame(guardado).copy()
        for c in base_cols:
            if c not in df_base_inicial.columns:
                if c in ["Saldo adeudado (₡)", "Cuota por período (₡)", "Días de atraso", "Meses restantes (opcional)"]:
                    df_base_inicial[c] = 0
                elif c == "Verificado por asesor":
                    df_base_inicial[c] = False
                else:
                    df_base_inicial[c] = ""
        df_base_inicial = df_base_inicial[base_cols]

# 3) Si tampoco hay en session_state, crear 4 filas vacías
if df_base_inicial is None or df_base_inicial.empty:
    df_base_inicial = pd.DataFrame([{c: "" for c in base_cols}] * 4)
    for c in ["Saldo adeudado (₡)", "Cuota por período (₡)", "Días de atraso", "Meses restantes (opcional)"]:
        df_base_inicial[c] = 0
    df_base_inicial["Verificado por asesor"] = False
# =========================================================

# Editor de captura
df_in = st.data_editor(
    df_base_inicial,
    use_container_width=True,
    num_rows="dynamic",
    hide_index=True,
    key="de_deudas_activas",
    column_config={
        "Titular": st.column_config.SelectboxColumn("Titular", options=relaciones, required=False),
        "Acreedor/Entidad": st.column_config.TextColumn("Acreedor/Entidad"),
        "Tipo de deuda": st.column_config.SelectboxColumn("Tipo de deuda", options=tipos_deuda, required=False),
        "Saldo adeudado (₡)": st.column_config.NumberColumn("Saldo adeudado (₡)", min_value=0, step=10000, format="₡ %d"),
        "Cuota por período (₡)": st.column_config.NumberColumn("Cuota por período (₡)", min_value=0, step=1000, format="₡ %d"),
        "Periodicidad de pago": st.column_config.SelectboxColumn("Periodicidad de pago", options=periodicidades_pago, required=False),
        "Verificado por asesor": st.column_config.CheckboxColumn("Verificado por asesor", default=False),
        "Tipo de evidencia": st.column_config.SelectboxColumn("Tipo de evidencia", options=evidencias, required=False),
        "Estado": st.column_config.SelectboxColumn("Estado", options=estados, required=False),
        "Días de atraso": st.column_config.NumberColumn("Días de atraso", min_value=0, max_value=3650, step=1, format="%d"),
        "Comentario": st.column_config.TextColumn("Comentario"),
        "Meses restantes (opcional)": st.column_config.NumberColumn("Meses restantes (opcional)", min_value=0, max_value=600, step=1, format="%d"),
        "Plazo (clasificación)": st.column_config.SelectboxColumn("Plazo (clasificación)", options=plazos, required=False),
    },
)

# --- Derivados ---
df = df_in.copy()
for c in ["Saldo adeudado (₡)", "Cuota por período (₡)", "Días de atraso", "Meses restantes (opcional)"]:
    if c not in df.columns:
        df[c] = 0
    df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
if "Verificado por asesor" not in df.columns:
    df["Verificado por asesor"] = False
df["Verificado por asesor"] = df["Verificado por asesor"].fillna(False).astype(bool)

if "Plazo (clasificación)" not in df.columns:
    df["Plazo (clasificación)"] = ""
df["Plazo (clasificación)"] = df["Plazo (clasificación)"].astype(str)

auto_mask = df["Plazo (clasificación)"].isin(["", "nan", "None"])
df.loc[auto_mask & (df["Meses restantes (opcional)"] > 0) & (df["Meses restantes (opcional)"] <= 12),
       "Plazo (clasificación)"] = "Corto plazo (≤12 meses)"
df.loc[auto_mask & (df["Meses restantes (opcional)"] > 12),
       "Plazo (clasificación)"] = "Largo plazo (>12 meses)"

cuotas_mens = []
for _, r in df.iterrows():
    cuota = float(r.get("Cuota por período (₡)") or 0)
    per = r.get("Periodicidad de pago") or ""
    cuotas_mens.append(_mensualizar_pago(cuota, per))
df["Cuota mensualizada (₡)"] = (
    pd.to_numeric(pd.Series(cuotas_mens), errors="coerce")
    .fillna(0)
    .round(0)
    .astype(int)
)





# Editor con cálculos bloqueados
with st.expander("Editar tabla con cálculos (derivados bloqueados)"):
    df_edit = st.data_editor(
        df,
        use_container_width=True,
        num_rows="dynamic",
        hide_index=True,
        key="de_deudas_activas_calc",
        column_config={
            "Titular": st.column_config.SelectboxColumn("Titular", options=relaciones),
            "Acreedor/Entidad": st.column_config.TextColumn("Acreedor/Entidad"),
            "Tipo de deuda": st.column_config.SelectboxColumn("Tipo de deuda", options=tipos_deuda),
            "Saldo adeudado (₡)": st.column_config.NumberColumn("Saldo adeudado (₡)", min_value=0, step=10000, format="₡ %d"),
            "Cuota por período (₡)": st.column_config.NumberColumn("Cuota por período (₡)", min_value=0, step=1000, format="₡ %d"),
            "Periodicidad de pago": st.column_config.SelectboxColumn("Periodicidad de pago", options=periodicidades_pago),
            "Verificado por asesor": st.column_config.CheckboxColumn("Verificado por asesor", default=False),
            "Tipo de evidencia": st.column_config.SelectboxColumn("Tipo de evidencia", options=evidencias),
            "Estado": st.column_config.SelectboxColumn("Estado", options=estados),
            "Días de atraso": st.column_config.NumberColumn("Días de atraso", min_value=0, max_value=3650, step=1, format="%d"),
            "Comentario": st.column_config.TextColumn("Comentario"),
            "Meses restantes (opcional)": st.column_config.NumberColumn("Meses restantes (opcional)", min_value=0, max_value=600, step=1, format="%d"),
            "Plazo (clasificación)": st.column_config.SelectboxColumn("Plazo (clasificación)", options=plazos),
            "Cuota mensualizada (₡)": st.column_config.NumberColumn("Cuota mensualizada (₡)", format="₡ %d", disabled=True),
        },
    )

# Reaplicar numéricos y cuota mensualizada por si se editó en el expander
for c in ["Saldo adeudado (₡)", "Cuota por período (₡)", "Días de atraso", "Meses restantes (opcional)"]:
    if c not in df_edit.columns:
        df_edit[c] = 0
    df_edit[c] = pd.to_numeric(df_edit[c], errors="coerce").fillna(0)
if "Verificado por asesor" not in df_edit.columns:
    df_edit["Verificado por asesor"] = False
df_edit["Verificado por asesor"] = df_edit["Verificado por asesor"].fillna(False).astype(bool)

cuotas_mens = []
for _, r in df_edit.iterrows():
    cuota = float(r.get("Cuota por período (₡)") or 0)
    per = r.get("Periodicidad de pago") or ""
    cuotas_mens.append(_mensualizar_pago(cuota, per))
df = df_edit.copy()
df["Cuota mensualizada (₡)"] = (
    pd.to_numeric(pd.Series(cuotas_mens), errors="coerce")
    .fillna(0)
    .round(0)
    .astype(int)
)



# --- Resumen ---
valid_mask = (df["Periodicidad de pago"].isin(periodicidades_pago)) & \
             ((df["Cuota por período (₡)"] > 0) | (df["Saldo adeudado (₡)"] > 0))
df_valid = df[valid_mask].copy()

total_pago_mensual = int(df_valid["Cuota mensualizada (₡)"].sum()) if not df_valid.empty else 0
total_adeudado = int(df_valid["Saldo adeudado (₡)"].sum()) if not df_valid.empty else 0
total_pago_verificado = int(df_valid.loc[df_valid["Verificado por asesor"], "Cuota mensualizada (₡)"].sum()) if not df_valid.empty else 0

corto_mask = df_valid["Plazo (clasificación)"].eq("Corto plazo (≤12 meses)")
largo_mask = df_valid["Plazo (clasificación)"].eq("Largo plazo (>12 meses)")
total_adeudado_corto = int(df_valid.loc[corto_mask, "Saldo adeudado (₡)"].sum()) if not df_valid.empty else 0
total_adeudado_largo = int(df_valid.loc[largo_mask, "Saldo adeudado (₡)"].sum()) if not df_valid.empty else 0

st.markdown("**Resumen**")
st.write({
    "Total pago mensual (a Resultados)": f"₡ {total_pago_mensual:,}".replace(",", "."),
    "Total pago mensual verificado": f"₡ {total_pago_verificado:,}".replace(",", "."),
    "Total adeudado (a Balance general)": f"₡ {total_adeudado:,}".replace(",", "."),
    "→ Pasivo circulante (corto plazo)": f"₡ {total_adeudado_corto:,}".replace(",", "."),
    "→ Pasivo a largo plazo": f"₡ {total_adeudado_largo:,}".replace(",", "."),
    "Registros válidos": int(valid_mask.sum()),
})

st.divider()


# --- NUEVO: CHECKBOX Y LÓGICA DE BOTÓN ---
st.subheader("Finalizar este paso")

# Recuperar valor previo de sin_deudas si existe
sin_deudas_val = bool(
    st.session_state.get("reporte", {})
    .get("deudas_activas", {})
    .get("totales", {})
    .get("sin_deudas", False)
)

sin_deudas = st.checkbox(
    "El hogar no tiene deudas activas que reportar.",
    key="sin_deudas",
    value=sin_deudas_val
)

puede_continuar = (valid_mask.sum() > 0) or sin_deudas





# Navegación / Guardar
c1, c2 = st.columns([0.5, 0.5])
with c1:
    if st.button("⬅️ Volver a 08 – Otros ingresos", key="deudas_back_08", use_container_width=True):
        for p in ["pages/08_Otros_ingresos.py"]:
            try:
                st.switch_page(p)
                break
            except Exception:
                continue

with c2:
    if st.button("Guardar y continuar ➡️", key="deudas_save_next", use_container_width=True, disabled=not puede_continuar):
        st.session_state.setdefault("reporte", {})
        st.session_state["reporte"]["deudas_activas"] = {
            "tabla": df.fillna("").to_dict(orient="records") if valid_mask.sum() > 0 else [],
            "totales": {
                "total_pago_mensual_colones": total_pago_mensual if not sin_deudas else 0,
                "total_pago_mensual_verificado_colones": total_pago_verificado if not sin_deudas else 0,
                "total_adeudado_colones": total_adeudado if not sin_deudas else 0,
                "total_adeudado_corto_plazo_colones": total_adeudado_corto if not sin_deudas else 0,
                "total_adeudado_largo_plazo_colones": total_adeudado_largo if not sin_deudas else 0,
                "registros_validos": int(valid_mask.sum()) if not sin_deudas else 0,
                "sin_deudas": bool(sin_deudas)
            }
        }
        st.session_state["done_09"] = True

        # 👇 NUEVO: Guardar en SQL
        cliente_id = st.session_state.get("cliente", {}).get("identificacion", "")
        try:
            save_ok = save_deudas_activas(
                cliente_id=cliente_id,
                df=df if not sin_deudas else pd.DataFrame(),
                totales=st.session_state["reporte"]["deudas_activas"]["totales"],
                sin_deudas=sin_deudas
            )
            if save_ok:
                st.success("✅ Deudas activas guardadas en la base de datos.")
            else:
                st.warning("⚠️ No se pudieron guardar las deudas en la base de datos.")
        except Exception as e:
            st.error(f"Error guardando en SQL: {e}")


        # Ir directamente al paso 10: Gastos operativos
        try:
            st.switch_page("pages/10_Gastos_operativos.py")
        except Exception:
            st.success("Deudas activas guardadas. Abrí **10 – Gastos operativos** desde el menú lateral.")
            st.stop()

