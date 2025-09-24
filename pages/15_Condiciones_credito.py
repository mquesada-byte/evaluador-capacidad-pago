# pages/15_Condiciones_credito.py
import streamlit as st

st.set_page_config(page_title="Paso 15: Condiciones de Crédito", page_icon="💳")

st.title("💳 Paso 15: Condiciones de Crédito")
st.caption("Cálculo de la cuota con y sin póliza del INS.")

# ===== Entradas =====
col1, col2 = st.columns(2)

with col1:
    monto_solicitado = st.number_input("Monto solicitado (₡)", min_value=0, step=50000, value=0)
    tasa_opts = ["", 14, 22, 24, 26, 30, 34]
    tasa_interes_anual = st.selectbox("Tasa de interés anual (%)", tasa_opts, index=0)

with col2:
    comision_opts = ["", 1.5, 2, 4, 6, 8, 10]
    comision_pct = st.selectbox("Porcentaje de comisión (%)", comision_opts, index=0)
    plazo_meses = st.number_input("Plazo (meses)", min_value=0, max_value=120, step=1, value=0)

st.divider()

# ===== Validación de campos =====
if monto_solicitado > 0 and plazo_meses > 0 and comision_pct != "" and tasa_interes_anual != "":
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
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Monto solicitado", f"₡{monto_solicitado:,.0f}")
        st.metric("Comisión aplicada", f"{comision_pct:.1f}%")
        st.metric("Monto con comisión", f"₡{monto_con_comision:,.0f}")
    with col2:
        st.metric("Tasa de interés anual", f"{tasa_interes_anual:.1f}%")
        st.metric("Plazo", f"{plazo_meses} meses")
        st.metric("Póliza INS (mensual)", f"₡{poliza:,.0f}")

    st.divider()
    st.subheader("💰 Cuotas calculadas")
    col3, col4 = st.columns(2)
    with col3:
        st.metric("Cuota sin póliza", f"₡{cuota_base:,.0f}")
    with col4:
        st.metric("Cuota con póliza", f"₡{cuota_con_poliza:,.0f}")

else:
    st.info("⚠️ Complete todos los campos para calcular la cuota.")
