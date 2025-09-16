# pages/08_Otros_ingresos.py
import streamlit as st
import pandas as pd
import datetime as dt
from zoneinfo import ZoneInfo
from utils.db import save_otros_ingresos   # 👈 usamos la versión corregida

st.set_page_config(page_title="Paso 8: Otros ingresos del hogar", page_icon="💸")

# =========================
# Asegurar mes_iso
# =========================
TZ = ZoneInfo("America/Costa_Rica")
if "mes_iso" not in st.session_state:
    now = dt.datetime.now(TZ)
    st.session_state["mes_iso"] = f"{now.year}-{now.month:02d}"

# =========================
# PASO 8 – Otros ingresos del hogar
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
    # simplificación: confiabilidad = combinación de factores
    base = 0.5
    if verificado:
        base += 0.2
    if meses >= 12: base += 0.2
    elif meses >= 6: base += 0.1
    base += (prob / 10) * 0.1
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

# tabla editable inicial
df_in = pd.DataFrame([{c: "" for c in base_cols}] * 3)
df_in["Monto por período (₡)"] = 0
df_in["Meses de continuidad"] = 0
df_in["Prob. continuidad (0–10)"] = 0
df_in["Verificado por asesor"] = False

df = st.data_editor(
    df_in,
    use_container_width=True,
    num_rows="dynamic",
    hide_index=True,
)

# =========================
# Cálculos derivados
# =========================
mensualizados, factores, ponderados = [], [], []
for _, r in df.iterrows():
    monto = float(r.get("Monto por período (₡)", 0) or 0)
    per = r.get("Periodicidad") or ""
    verif = bool(r.get("Verificado por asesor", False))
    evid = r.get("Tipo de evidencia", "")
    meses = int(r.get("Meses de continuidad", 0) or 0)
    prob = int(r.get("Prob. continuidad (0–10)", 0) or 0)

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
c1, c2 = st.columns([0.5, 0.5])
with c1:
    if st.button("⬅️ Volver a 07 – Conciliación", use_container_width=True):
        st.switch_page("pages/07_Conciliacion_de_ventas.py")

with c2:
    if st.button("Guardar y continuar ➡️", use_container_width=True, disabled=df_valid.empty):
        ok = save_otros_ingresos(
            cliente_id=st.session_state["cliente"]["identificacion"],
            mes_iso=st.session_state["mes_iso"],
            df=df_valid
        )
        if ok:
            st.success("✅ Otros ingresos guardados en la base de datos")
            st.session_state["done_08"] = True
            try:
                st.switch_page("pages/09_Deudas.py")
            except Exception:
                st.info("Continúa con el Paso 9 desde el menú lateral.")
        else:
            st.error("❌ No se pudieron guardar los otros ingresos en la base de datos")

