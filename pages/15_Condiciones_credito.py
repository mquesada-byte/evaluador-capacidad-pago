# pages/15_Condiciones_credito.py
import streamlit as st

st.set_page_config(page_title="Paso 15: Condiciones de Crédito", page_icon="💳")

st.title("💳 Paso 15: Condiciones de Crédito")
st.caption("Cálculo de la cuota con y sin póliza del INS.")

# ===== Entradas =====
col1, col2 = st.columns(2)
with col1:
    monto_solicitado = st.number_input("Monto solicitado (₡)", min_value=0, step=50000, value=0)
with col2:
    saldo_payoff = st.number_input("Saldo Pay Off (₡)", min_value=0, step=50000, value=0)
    st.caption("Saldo pay off solo para recréditos")

col3, col4, col5 = st.columns(3)
with col3:
    comision_pct = st.selectbox("Porcentaje de comisión (%)", [1.5, 2, 4, 6, 8, 10], index=None, placeholder="Selecciona...")
with col4:
    tasa_interes_anual = st.selectbox("Tasa de interés anual (%)", [14, 22, 24, 26, 30, 34], index=None, placeholder="Selecciona...")
with col5:
    plazo_meses = st.number_input("Plazo (meses)", min_value=6, max_value=120, step=1, value=0)

# ===== Validación =====
if monto_solicitado > 0 and comision_pct and tasa_interes_anual and plazo_meses > 0:
    # ===== Cálculos =====
    monto_con_comision = monto_solicitado * (1 + comision_pct / 100)

    tasa_mensual = tasa_interes_anual / 100 / 12
    n = plazo_meses

    if tasa_mensual > 0:
        cuota_base = monto_con_comision * (tasa_mensual * (1 + tasa_mensual)**n) / ((1 + tasa_mensual)**n - 1)
    else:
        cuota_base = monto_con_comision / n

    # Póliza INS: 100 colones por cada 100 mil de préstamo (incluyendo comisión)
    poliza = (monto_con_comision / 100000) * 100
    cuota_con_poliza = cuota_base + poliza

    # ===== Salida =====
    st.subheader("Resultados")
    colr1, colr2 = st.columns(2)
    with colr1:
        st.metric("Monto solicitado", f"₡{monto_solicitado:,.0f}")
        st.metric("Monto con comisión", f"₡{monto_con_comision:,.0f}")
        st.metric("Saldo Pay Off", f"₡{saldo_payoff:,.0f}")
    with colr2:
        st.metric("Comisión aplicada", f"{comision_pct:.1f}%")
        st.metric("Tasa de interés anual", f"{tasa_interes_anual:.1f}%")
        st.metric("Plazo", f"{plazo_meses} meses")
        st.metric("Póliza INS (mensual)", f"₡{poliza:,.0f}")

    st.divider()
    st.subheader("💰 Cuotas calculadas")
    colq1, colq2 = st.columns(2)
    with colq1:
        st.metric("Cuota sin póliza", f"₡{cuota_base:,.0f}")
    with colq2:
        st.metric("Cuota con póliza", f"₡{cuota_con_poliza:,.0f}")
else:
    st.info("Por favor ingresa el monto, comisión, tasa y plazo para calcular las condiciones.")
