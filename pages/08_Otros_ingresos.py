# pages/08_Otros_ingresos.py
import streamlit as st
import pandas as pd
import datetime as dt
from zoneinfo import ZoneInfo
from utils.db import save_otros_ingresos, load_visita   # ✅ corregido

st.set_page_config(page_title="Paso 8: Otros ingresos del hogar", page_icon="💸")


# =========================
# Funciones auxiliares
# =========================
def _mensualizar(monto: float, periodicidad: str) -> float:
    per = (periodicidad or "").lower()
    if per == "diario": return monto * 30
    if per == "semanal": return monto * (52 / 12)
    if per == "quincenal": return monto * 2
    if per == "mensual": return monto
    if per == "bimestral": return monto / 2
    if per == "trimestral": return monto / 3
    if per == "semestral": return monto / 6
    if per == "anual": return monto / 12
    return 0.0

def _factor_confiabilidad(verificado: bool, evidencia: str, meses: int, prob: int) -> float:
    base = 0.5
    if verificado:
        base += 0.2
    if meses >= 12:
        base += 0.2
    elif meses >= 6:
        base += 0.1
    base += (prob / 10) * 0.1

    # 🔎 Ajuste: peso según tipo de evidencia
    evidencia_lower = (evidencia or "").lower()
    evidencias_fuertes = ["facturación electrónica", "extractos bancarios/sinpe", "pos/datáfono", "contrato"]
    evidencias_medias = ["recibos", "certificación", "equifax", "credid"]
    if any(e in evidencia_lower for e in evidencias_fuertes):
        base += 0.2
    elif any(e in evidencia_lower for e in evidencias_medias):
        base += 0.1
    # “Foto/Chat”, “No aplica” u “Otro” → sin incremento

    return min(1.0, max(0.2, base))

# =========================
# Catálogos
# =========================
periodicidades = ["Diario", "Semanal", "Quincenal", "Mensual", "Bimestral", "Trimestral", "Semestral", "Anual"]
fuentes = ["Salario", "Pensión", "Alquiler", "Negocio secundario", "Remesas", "Servicios profesionales", "Subsidio/Ayuda", "Otro"]
relaciones = ["Cliente", "Pareja", "Hijo/a", "Padre/Madre", "Familiar", "Otro"]
evidencias = ["Facturación electrónica", "Extractos bancarios/SINPE", "POS/Datáfono", "Recibos",
              "Foto/Chat", "Contrato", "Certificación", "Credid", "Equifax", "No aplica", "Otro"]

base_cols = [
    "Titular (nombre)", "Relación", "Fuente de ingreso", "Periodicidad",
    "Monto por período (₡)", "Verificado por asesor", "Tipo de evidencia",
    "Meses de continuidad", "Prob. continuidad (0–10)", "Comentario",
]
deriv_cols = ["Ingreso mensualizado (₡)", "Factor confiabilidad (0.2–1.0)", "Ingreso ponderado (₡)"]

# =========================
# UI
# =========================
st.title("💸 Paso 8: Otros ingresos del hogar")
st.caption("Registre otros ingresos del cliente y su núcleo familiar.")

# -------- Inicializar tabla con datos previos si existen --------
cliente_id = st.session_state.get("cliente", {}).get("identificacion", "").strip()
df_in = None

if cliente_id:
    datos = load_visita(cliente_id)
    if datos and "otros_ingresos" in datos:
        try:
            df_in = pd.DataFrame(datos["otros_ingresos"])
        except Exception:
            df_in = None

if df_in is None or df_in.empty:
    df_in = pd.DataFrame([{c: "" for c in base_cols}] * 3)
    df_in["Monto por período (₡)"] = 0
    df_in["Meses de continuidad"] = 0
    df_in["Prob. continuidad (0–10)"] = 0
    df_in["Verificado por asesor"] = False


# Editor con menús desplegables
df = st.data_editor(
    df_in,
    use_container_width=True,
    num_rows="dynamic",
    hide_index=True,
    column_config={
        "Titular (nombre)": st.column_config.TextColumn("Titular (nombre)"),
        "Relación": st.column_config.SelectboxColumn("Relación", options=relaciones),
        "Fuente de ingreso": st.column_config.SelectboxColumn("Fuente de ingreso", options=fuentes),
        "Periodicidad": st.column_config.SelectboxColumn("Periodicidad", options=periodicidades),
        "Monto por período (₡)": st.column_config.NumberColumn("Monto por período (₡)", min_value=0, step=1000, format="₡ %d"),
        "Verificado por asesor": st.column_config.CheckboxColumn("Verificado por asesor", default=False),
        "Tipo de evidencia": st.column_config.SelectboxColumn("Tipo de evidencia", options=evidencias),
        "Meses de continuidad": st.column_config.NumberColumn("Meses de continuidad", min_value=0, max_value=480, step=1, format="%d"),
        "Prob. continuidad (0–10)": st.column_config.NumberColumn("Prob. continuidad (0–10)", min_value=0, max_value=10, step=1, format="%d"),
        "Comentario": st.column_config.TextColumn("Comentario"),
    }
)

# =========================
# Cálculos derivados
# =========================
mensualizados, factores, ponderados = [], [], []
for _, r in df.iterrows():
    monto = float(r["Monto por período (₡)"]) if "Monto por período (₡)" in r and pd.notna(r["Monto por período (₡)"]) else 0
    per = r["Periodicidad"] if "Periodicidad" in r and pd.notna(r["Periodicidad"]) else ""
    verif = bool(r["Verificado por asesor"]) if "Verificado por asesor" in r and pd.notna(r["Verificado por asesor"]) else False
    evid = r["Tipo de evidencia"] if "Tipo de evidencia" in r and pd.notna(r["Tipo de evidencia"]) else ""
    meses = int(r["Meses de continuidad"]) if "Meses de continuidad" in r and pd.notna(r["Meses de continuidad"]) else 0
    prob = int(r["Prob. continuidad (0–10)"]) if "Prob. continuidad (0–10)" in r and pd.notna(r["Prob. continuidad (0–10)"]) else 0

    m_mensual = _mensualizar(monto, per)
    f_conf = _factor_confiabilidad(verif, evid, meses, prob)
    mensualizados.append(m_mensual)
    factores.append(f_conf)
    ponderados.append(m_mensual * f_conf)





df["Ingreso mensualizado (₡)"] = [int(x) for x in mensualizados]
df["Factor confiabilidad (0.2–1.0)"] = [round(x, 2) for x in factores]
df["Ingreso ponderado (₡)"] = [int(x) for x in ponderados]

# =========================
# Resumen
# =========================
df_valid = df[df["Monto por período (₡)"] > 0]
total_mensual = int(df_valid["Ingreso mensualizado (₡)"].sum()) if not df_valid.empty else 0
total_ponderado = int(df_valid["Ingreso ponderado (₡)"].sum()) if not df_valid.empty else 0

st.markdown("### Resumen")
st.write({
    "Total mensualizado": f"₡ {total_mensual:,}".replace(",", "."),
    "Total ponderado": f"₡ {total_ponderado:,}".replace(",", "."),
    "Registros válidos": len(df_valid)
})

st.divider()

# =========================
# Botones navegación/guardar
# =========================
st.subheader("Finalizar este paso")

# Recuperar valor previo de sin_ingresos si existe
sin_ingresos_val = bool(
    st.session_state.get("reporte", {})
    .get("otros_ingresos", {})
    .get("totales", {})
    .get("sin_ingresos", False)
)

sin_ingresos = st.checkbox(
    "El hogar no tiene otros ingresos que reportar.",
    key="sin_ingresos",
    value=sin_ingresos_val
)

puede_continuar = (len(df_valid) > 0) or sin_ingresos

c1, c2 = st.columns([0.5, 0.5])
with c1:
    if st.button("⬅️ Volver a 07 – Conciliación", use_container_width=True):
        st.switch_page("pages/07_Conciliacion_de_ventas.py")

with c2:
    if st.button("Guardar y continuar ➡️", use_container_width=True, disabled=not puede_continuar):
        ok = save_otros_ingresos(
            cliente_id=cliente_id,
            df=df_valid if not sin_ingresos else pd.DataFrame()
        )
        if ok:
            st.success("✅ Otros ingresos guardados en la base de datos")

            # ✅ Guardar también en session_state["reporte"]
            st.session_state.setdefault("reporte", {})
            st.session_state["reporte"]["otros_ingresos"] = {
                "tabla": df_valid.fillna("").to_dict(orient="records") if not sin_ingresos else [],
                "totales": {
                    "total_mensualizado": int(total_mensual) if not sin_ingresos else 0,
                    "total_ponderado": int(total_ponderado) if not sin_ingresos else 0,
                    "registros_validos": len(df_valid) if not sin_ingresos else 0,
                    "sin_ingresos": bool(sin_ingresos)
                }
            }

            st.session_state["done_08"] = True
            try:
                st.switch_page("pages/09_Deudas.py")
            except Exception:
                st.info("Continúa con el Paso 9 desde el menú lateral.")
        else:
            st.error("❌ No se pudieron guardar los otros ingresos en la base de datos")
