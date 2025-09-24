# pages/15_Condiciones_credito.py
import streamlit as st

st.set_page_config(page_title="Paso 15: Condiciones de Crédito", page_icon="💳")

st.title("💳 Paso 15: Condiciones de Crédito")
st.caption("Cálculo de la cuota con y sin póliza del INS.")

# ===== Entradas =====
# Línea 1: monto solicitado + saldo pay off
col1, col2 = st.columns(2)
with col1:
    monto_solicitado = st.number_input("Monto solicitado (₡)", min_value=0, step=50000, value=0)
with col2:
    monto_payoff = st.number_input("Saldo pay off (solo recréditos)", min_value=0, step=50000, value=0)

# Línea 2: comisión, tasa, plazo
col3, col4, col5 = st.columns(3)
with col3:
    comision_pct = st.selectbox(
        "Porcentaje de comisión (%)",
        options=[None, 1.5, 2, 4, 6, 8, 10],
        format_func=lambda x: "— Selecciona —" if x is None else f"{x:.1f}%",
        index=0
    )
with col4:
    tasa_interes_anual = st.selectbox(
        "Tasa de interés anual (%)",
        options=[None, 14, 22, 24, 26, 30, 34],
        format_func=lambda x: "— Selecciona —" if x is None else f"{x:.1f}%",
        index=0
    )
with col5:
    plazo_meses = st.selectbox(
        "Plazo (meses)",
        options=[None] + list(range(6, 121)),
        format_func=lambda x: "— Selecciona —" if x is None else f"{x} meses",
        index=0
    )

# Línea 3: honorarios y timbres
honorarios_timbres = st.number_input("Honorarios y timbres (₡)", min_value=0, step=10000, value=0)

# ===== Cálculos =====
# Fórmula: ((monto solicitado + honorarios y timbres) * (1 + comisión/100)) + saldo pay off
monto_total = ((monto_solicitado + honorarios_timbres) * (1 + comision_pct / 100)) + saldo_payoff

tasa_mensual = tasa_interes_anual / 100 / 12
n = plazo_meses if plazo_meses > 0 else 1

if tasa_mensual > 0:
    cuota_base = monto_total * (tasa_mensual * (1 + tasa_mensual)**n) / ((1 + tasa_mensual)**n - 1)
else:
    cuota_base = monto_total / n

# Póliza INS: 100 colones por cada 100 mil de préstamo (incluyendo comisión y honorarios, más pay off)
poliza = (monto_total / 100000) * 100
cuota_con_poliza = cuota_base + poliza





# ===== Salida =====
st.subheader("Resultados")
col1, col2 = st.columns(2)
with col1:
    st.metric("Monto solicitado", f"₡{monto_solicitado:,.0f}")
    st.metric("Saldo pay off (recrédito)", f"₡{monto_payoff:,.0f}")
    if comision_pct:
        st.metric("Comisión aplicada", f"{comision_pct:.1f}%")
    if monto_con_comision:
        st.metric("Monto con comisión", f"₡{monto_con_comision:,.0f}")
with col2:
    if tasa_interes_anual:
        st.metric("Tasa de interés anual", f"{tasa_interes_anual:.1f}%")
    if plazo_meses:
        st.metric("Plazo", f"{plazo_meses} meses")
    if poliza:
        st.metric("Póliza INS (mensual)", f"₡{poliza:,.0f}")
    if honorarios_timbres:
        st.metric("Honorarios y timbres", f"₡{honorarios_timbres:,.0f}")

st.divider()
st.subheader("💰 Cuotas calculadas")
col3, col4 = st.columns(2)
with col3:
    st.metric("Cuota sin póliza", f"₡{cuota_base:,.0f}")
with col4:
    st.metric("Cuota con póliza", f"₡{cuota_con_poliza:,.0f}")
