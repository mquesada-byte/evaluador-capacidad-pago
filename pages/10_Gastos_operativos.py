# pages/10_Gastos_operativos.py
import streamlit as st
import pandas as pd
from utils.db import save_gastos_operativos   # 👈 nuevo import

st.set_page_config(page_title="Paso 10: Gastos operativos", page_icon="🧾")

# =========================
# PASO 10 – Gastos operativos (multipágina)
# =========================
def _mensualizar_gasto(monto: float, periodicidad: str) -> float:
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

st.title("🧾 Paso 10: Gastos operativos")
st.caption("Registre los gastos del negocio u hogar relacionados a la operación. Puede indicar si fueron **verificados** y el **tipo de evidencia**.")

# Catálogos
rubros = ["Sueldos", "Alquileres", "Servicios públicos", "Impuestos/Patentes", "Pagos a proveedores", "Otros"]
periodicidades = ["Mensual", "Quincenal", "Semanal", "Diario", "Bimestral", "Trimestral", "Semestral", "Anual"]
evidencias = [
    "Factura/Recibo", "Contrato/Arrendamiento", "Estado de cuenta/SINPE",
    "Planilla/CCSS", "Recibos", "Foto/Chat", "No aplica", "Otro"
]

# Columnas base (entrada)
base_cols = [
    "Rubro", "Detalle", "Monto por período (₡)", "Periodicidad",
    "Verificado por asesor", "Tipo de evidencia", "Comentario",
]

# ---------- CARGA INICIAL DESDE LO GUARDADO (si existe) ----------
guardado = []

# Primero intentamos desde la sesión
guardado = (
    st.session_state.get("reporte", {})
    .get("gastos_operativos", {})
    .get("tabla", [])
)

# Si no hay en sesión, intentamos desde lo cargado en Paso 2 (Azure)
if not guardado:
    guardado = st.session_state.get("datos", {}).get("gastos_operativos", [])


if guardado:
    df_base = pd.DataFrame(guardado).copy()
    # Asegurar columnas base y tipos
    for c in base_cols:
        if c not in df_base.columns:
            if c == "Monto por período (₡)":
                df_base[c] = 0
            elif c == "Verificado por asesor":
                df_base[c] = False
            else:
                df_base[c] = ""
    df_base = df_base[base_cols]
    df_base["Monto por período (₡)"] = pd.to_numeric(df_base["Monto por período (₡)"], errors="coerce").fillna(0)
    df_base["Verificado por asesor"] = df_base["Verificado por asesor"].fillna(False).astype(bool)
else:
    # Placeholders iniciales (una fila por rubro)
    df_base = pd.DataFrame([
        {
            "Rubro": r, "Detalle": "", "Monto por período (₡)": 0, "Periodicidad": "Mensual",
            "Verificado por asesor": False, "Tipo de evidencia": "", "Comentario": "",
        } for r in rubros
    ])

# --- Editor base ---
df_in = st.data_editor(
    df_base,
    use_container_width=True,
    num_rows="dynamic",
    hide_index=True,
    key="de_gastos_operativos",
    column_config={
        "Rubro": st.column_config.SelectboxColumn("Rubro", options=rubros, required=False),
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
if "Monto por período (₡)" not in df.columns:
    df["Monto por período (₡)"] = 0
df["Monto por período (₡)"] = pd.to_numeric(df["Monto por período (₡)"], errors="coerce").fillna(0)
if "Verificado por asesor" not in df.columns:
    df["Verificado por asesor"] = False
df["Verificado por asesor"] = df["Verificado por asesor"].fillna(False).astype(bool)

mensualizados = []
for _, r in df.iterrows():
    monto = float(r.get("Monto por período (₡)") or 0)
    per = r.get("Periodicidad") or ""
    mensualizados.append(_mensualizar_gasto(monto, per))
df["Gasto mensualizado (₡)"] = pd.Series(mensualizados).round(0).astype(int)

# Editor con cálculos bloqueados
df_edit = df.copy()
with st.expander("Editar tabla con cálculos (derivados bloqueados)"):
    df_edit = st.data_editor(
        df,
        use_container_width=True,
        num_rows="dynamic",
        hide_index=True,
        key="de_gastos_operativos_calc",
        column_config={
            "Rubro": st.column_config.SelectboxColumn("Rubro", options=rubros),
            "Detalle": st.column_config.TextColumn("Detalle"),
            "Monto por período (₡)": st.column_config.NumberColumn("Monto por período (₡)", min_value=0, step=1000, format="₡ %d"),
            "Periodicidad": st.column_config.SelectboxColumn("Periodicidad", options=periodicidades),
            "Verificado por asesor": st.column_config.CheckboxColumn("Verificado por asesor", default=False),
            "Tipo de evidencia": st.column_config.SelectboxColumn("Tipo de evidencia", options=evidencias),
            "Comentario": st.column_config.TextColumn("Comentario"),
            "Gasto mensualizado (₡)": st.column_config.NumberColumn("Gasto mensualizado (₡)", format="₡ %d", disabled=True),
        },
    )

# Reaplicar numéricos por si se editó en el expander
if "Monto por período (₡)" not in df_edit.columns:
    df_edit["Monto por período (₡)"] = 0
df_edit["Monto por período (₡)"] = pd.to_numeric(df_edit["Monto por período (₡)"], errors="coerce").fillna(0)
if "Verificado por asesor" not in df_edit.columns:
    df_edit["Verificado por asesor"] = False
df_edit["Verificado por asesor"] = df_edit["Verificado por asesor"].fillna(False).astype(bool)

mensualizados = []
for _, r in df_edit.iterrows():
    monto = float(r.get("Monto por período (₡)") or 0)
    per = r.get("Periodicidad") or ""
    mensualizados.append(_mensualizar_gasto(monto, per))
df = df_edit.copy()
df["Gasto mensualizado (₡)"] = pd.Series(mensualizados).round(0).astype(int)

# --- Resumen ---
valid_mask = (df["Periodicidad"].isin(periodicidades)) & (df["Monto por período (₡)"] > 0)
df_valid = df[valid_mask].copy()
total_gasto_mensual = int(df_valid["Gasto mensualizado (₡)"].sum()) if not df_valid.empty else 0
total_gasto_verificado = int(df_valid.loc[df_valid["Verificado por asesor"], "Gasto mensualizado (₡)"].sum()) if not df_valid.empty else 0

st.markdown("**Resumen**")
st.write({
    "Total gastos operativos (mensualizado)": f"₡ {total_gasto_mensual:,}".replace(",", "."),
    "Total verificado (mensualizado)": f"₡ {total_gasto_verificado:,}".replace(",", "."),
    "Registros válidos": int(valid_mask.sum()),
})

st.divider()

# --- NUEVO: CHECKBOX Y LÓGICA DE BOTÓN ---
st.subheader("Finalizar este paso")
sin_gastos = st.checkbox("El hogar o negocio no tiene gastos operativos que reportar.", key="sin_gastos")
puede_continuar = (valid_mask.sum() > 0) or sin_gastos

# Navegación / Guardar
c1, c2 = st.columns([0.5, 0.5])
with c1:
    if st.button("⬅️ Volver a 09 – Deudas", key="gastos_back_09", use_container_width=True):
        try:
            st.switch_page("pages/09_Deudas.py")
        except Exception:
            st.stop()

with c2:
    if st.button(
        "Guardar y continuar ➡️",
        key="gastos_save_next",
        use_container_width=True,
        disabled=not puede_continuar
    ):
        st.session_state.setdefault("reporte", {})
        st.session_state["reporte"]["gastos_operativos"] = {
            "tabla": df.fillna("").to_dict(orient="records") if valid_mask.sum() > 0 else [],
            "totales": {
                "total_gasto_operativo_mensualizado_colones": total_gasto_mensual if not sin_gastos else 0,
                "total_gasto_operativo_verificado_colones": total_gasto_verificado if not sin_gastos else 0,
                "registros_validos": int(valid_mask.sum()) if not sin_gastos else 0,
            }
        }
        st.session_state["done_10"] = True

        # 👇 Guardar en SQL
        cliente_id = st.session_state.get("cliente", {}).get("identificacion", "")
        mes_iso = st.session_state.get("mes_iso", "")

        try:
            save_ok = save_gastos_operativos(
                cliente_id=cliente_id,
                mes_iso=mes_iso,
                df=df if not sin_gastos else pd.DataFrame(),
                totales=st.session_state["reporte"]["gastos_operativos"]["totales"],
                sin_gastos=sin_gastos
            )
            if save_ok:
                st.success("✅ Gastos operativos guardados en la base de datos.")
            else:
                st.warning("⚠️ No se pudieron guardar los gastos en la base de datos.")
        except Exception as e:
            st.error(f"Error guardando en SQL: {e}")

        # Ir al próximo paso: 11_Gastos_familiares.py
        try:
            st.switch_page("pages/11_Gastos_familiares.py")
        except Exception:
            st.success("Gastos operativos guardados. Abrí **11 – Gastos familiares** desde el menú lateral.")
            st.stop()

