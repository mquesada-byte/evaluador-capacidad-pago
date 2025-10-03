# pages/11_Gastos_familiares.py
import streamlit as st
import pandas as pd
from utils.db import save_gastos_familiares, load_visita   # ✅ agregado load_visita

st.set_page_config(page_title="Paso 11: Gastos familiares", page_icon="🏠")

# =========================
# PASO 11 – Gastos familiares (multipágina)
# =========================
def _mensualizar_gasto_fam(monto: float, periodicidad: str) -> float:
    per = (periodicidad or "").lower()
    if per == "diario":       return monto * 30.0
    if per == "semanal":      return monto * (52.0 / 12.0)
    if per == "quincenal":    return monto * 2.0
    if per == "mensual":      return monto
    if per == "bimestral":    return monto / 2.0
    if per == "trimestral":   return monto / 3.0
    if per == "semestral":    return monto / 6.0
    if per == "anual":        return monto / 12.0
    return 0.0

st.title("🏠 Paso 11: Gastos familiares")
st.caption("Registre los gastos del hogar (familia): alimentación, vivienda, educación, salud, transporte, servicios públicos y otros. Indique si fueron **verificados** y el **tipo de evidencia**.")

# Catálogos
rubros_fam = ["Alimentación", "Vivienda", "Educación", "Salud", "Transporte", "Servicios públicos", "Otros"]
periodicidades = ["Mensual", "Quincenal", "Semanal", "Diario", "Bimestral", "Trimestral", "Semestral", "Anual"]
evidencias = [
    "Factura/Recibo", "Contrato/Arrendamiento", "Estado de cuenta/SINPE",
    "Planilla/CCSS", "Recibos", "Foto/Chat", "No aplica", "Otro"
]

base_cols = ["Rubro", "Detalle", "Monto por período (₡)", "Periodicidad",
             "Verificado por asesor", "Tipo de evidencia", "Comentario"]

# ---------- CARGA INICIAL DESDE SQL ----------
cliente_id = st.session_state.get("cliente", {}).get("identificacion", "").strip()
df_base = None
totales_guardados = {}
datos = None

if cliente_id:
    datos = load_visita(cliente_id)
    if datos and "gastos_familiares" in datos:
        try:
            gastos_data = datos["gastos_familiares"]
            df_base = pd.DataFrame(gastos_data.get("tabla", []))
            totales_guardados = gastos_data.get("totales", {})
        except Exception:
            df_base = None
            totales_guardados = {}

if df_base is None or df_base.empty:
    # Placeholders iniciales
    df_base = pd.DataFrame([
        {
            "Rubro": r, "Detalle": "", "Monto por período (₡)": 0, "Periodicidad": "Mensual",
            "Verificado por asesor": False, "Tipo de evidencia": "", "Comentario": "",
        } for r in rubros_fam
    ])

# --- Editor base ---
df_in = st.data_editor(
    df_base,
    use_container_width=True,
    num_rows="dynamic",
    hide_index=True,
    key="de_gastos_familiares",
    column_config={
        "Rubro": st.column_config.SelectboxColumn("Rubro", options=rubros_fam, required=False),
        "Detalle": st.column_config.TextColumn("Detalle"),
        "Monto por período (₡)": st.column_config.NumberColumn("Monto por período (₡)", min_value=0, step=1000, format="₡ %d"),
        "Periodicidad": st.column_config.SelectboxColumn("Periodicidad", options=periodicidades, required=False),
        "Verificado por asesor": st.column_config.CheckboxColumn("Verificado por asesor", default=False),
        "Tipo de evidencia": st.column_config.SelectboxColumn("Tipo de evidencia", options=evidencias, required=False),
        "Comentario": st.column_config.TextColumn("Comentario"),
    },
)

# --- Derivados ---
df = df_in.copy()
df["Monto por período (₡)"] = pd.to_numeric(df.get("Monto por período (₡)"), errors="coerce").fillna(0)
df["Verificado por asesor"] = df.get("Verificado por asesor", False).fillna(False).astype(bool)

df["Gasto mensualizado (₡)"] = [
    _mensualizar_gasto_fam(float(r.get("Monto por período (₡)") or 0), r.get("Periodicidad") or "")
    for _, r in df.iterrows()
]
df["Gasto mensualizado (₡)"] = df["Gasto mensualizado (₡)"].round(0).astype(int)

# --- Resumen ---
valid_mask = df["Periodicidad"].isin(periodicidades) & (df["Monto por período (₡)"] > 0)
df_valid = df[valid_mask].copy()
total_gasto_fam_mensual = int(df_valid["Gasto mensualizado (₡)"].sum()) if not df_valid.empty else 0
total_gasto_fam_verificado = int(df_valid.loc[df_valid["Verificado por asesor"], "Gasto mensualizado (₡)"].sum()) if not df_valid.empty else 0
reg_validos = int(valid_mask.sum())

st.markdown("**Resumen**")
st.write({
    "Total gastos familiares (mensualizado)": f"₡ {total_gasto_fam_mensual:,}".replace(",", "."),
    "Total verificado (mensualizado)": f"₡ {total_gasto_fam_verificado:,}".replace(",", "."),
    "Registros válidos": reg_validos,
})

st.divider()

# --- CHECKBOX DE SIN GASTOS ---
all_ceros = (df_valid.empty and df["Monto por período (₡)"].sum() == 0)
sin_gastos_val = totales_guardados.get("sin_gastos", False) if totales_guardados else all_ceros

sin_gastos = st.checkbox(
    "El hogar no tiene gastos familiares que reportar.",
    key="sin_gastos_fam",
    value=sin_gastos_val or all_ceros
)

puede_continuar = (reg_validos > 0) or sin_gastos or all_ceros

# --- Navegación / Guardar ---
c1, c2 = st.columns([0.5, 0.5])

with c1:
    if st.button("⬅️ Volver a 10 – Gastos operativos", key="gfam_back_gop", use_container_width=True):
        try:
            st.switch_page("pages/10_Gastos_operativos.py")
        except Exception:
            st.stop()

with c2:
    if st.button("Guardar y continuar ➡️", key="gfam_save_next", use_container_width=True, disabled=not puede_continuar):
        st.session_state.setdefault("reporte", {})

        if sin_gastos:
            df_ceros = df.copy()
            df_ceros["Monto por período (₡)"] = 0
            df_ceros["Gasto mensualizado (₡)"] = 0

            st.session_state["reporte"]["gastos_familiares"] = {
                "tabla": df_ceros.fillna("").to_dict(orient="records"),
                "totales": {
                    "total_gastos_familiares_mensualizado_colones": 0,
                    "total_gastos_familiares_verificado_colones": 0,
                    "registros_validos": 0,
                    "sin_gastos": True
                }
            }
            df_to_save = df_ceros
        else:
            st.session_state["reporte"]["gastos_familiares"] = {
                "tabla": df.fillna("").to_dict(orient="records"),
                "totales": {
                    "total_gastos_familiares_mensualizado_colones": total_gasto_fam_mensual,
                    "total_gastos_familiares_verificado_colones": total_gasto_fam_verificado,
                    "registros_validos": reg_validos,
                    "sin_gastos": False
                }
            }
            df_to_save = df

        st.session_state["done_11"] = True

        # Guardar en SQL
        try:
            save_ok = save_gastos_familiares(
                cliente_id=cliente_id,
                df=df if not sin_gastos else pd.DataFrame(),
                totales=st.session_state["reporte"]["gastos_familiares"]["totales"],
                sin_gastos=sin_gastos
            )
            if save_ok:
                st.success("✅ Gastos familiares guardados en la base de datos.")
            else:
                st.warning("⚠️ No se pudieron guardar los gastos familiares en la base de datos.")
        except Exception as e:
            st.error(f"Error guardando en SQL: {e}")

        # Ir al próximo paso
        try:
            st.switch_page("pages/12_Estado_de_resultadosl.py")
        except Exception:
            st.success("Gastos familiares guardados. Abrí el **siguiente paso** desde el menú lateral.")
            st.stop()
