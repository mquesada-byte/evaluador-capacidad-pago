# pages/15_Condiciones_credito.py
import streamlit as st
import numpy as np

st.set_page_config(page_title="Paso 15: Condiciones de Crédito", page_icon="💳")

st.title("💳 Paso 15: Condiciones de Crédito")
st.caption("Cálculo de la cuota con y sin póliza del INS.")

# ===== Entradas =====
col1, col2 = st.columns(2)
with col1:
    monto_solicitado = st.number_input("Monto solicitado (₡)", min_value=0, step=50000, value=0)
with col2:
    saldo_payoff = st.number_input("Saldo pay off (₡)", min_value=0, step=50000, value=0,
                                   help="Saldo pay off solo para recréditos")

col3, col4, col5 = st.columns(3)
with col3:
    comision_pct = st.selectbox("Porcentaje de comisión (%)", [1.5, 2, 4, 6, 8, 10],
                                index=None, placeholder="Selecciona")
with col4:
    tasa_interes_anual = st.selectbox("Tasa de interés anual (%)", [14, 22, 24, 26, 30, 34],
                                      index=None, placeholder="Selecciona")
with col5:
    plazo_meses = st.number_input("Plazo (meses)", min_value=0, max_value=120, step=1, value=0)

col6, col7 = st.columns(2)
with col6:
    honorarios_timbres = st.number_input("Honorarios y timbres (₡)", min_value=0, step=5000, value=0,
                                         help="Monto único que nos cotiza el abogado")
with col7:
    tir_output = st.empty()  # 👈 espacio reservado para la TIR anualizada

# ===== Cálculos =====
if comision_pct and tasa_interes_anual and plazo_meses > 0:
    # Fórmula: ((monto solicitado + honorarios y timbres) * (1 + comisión/100)) + saldo pay off
    monto_total = ((monto_solicitado + honorarios_timbres) * (1 + comision_pct / 100)) + saldo_payoff

    tasa_mensual = tasa_interes_anual / 100 / 12
    n = plazo_meses

    if tasa_mensual > 0:
        cuota_base = monto_total * (tasa_mensual * (1 + tasa_mensual)**n) / ((1 + tasa_mensual)**n - 1)
    else:
        cuota_base = monto_total / n

    # Póliza INS: 100 colones por cada 100 mil del monto solicitado total
    poliza = (monto_total / 100000) * 100
    cuota_con_poliza = cuota_base + poliza

    # Calcular TIR mensual y anualizada
    flujos = [-monto_solicitado] + [-(cuota_con_poliza) for _ in range(plazo_meses)]
    try:
        tir_mensual = np.irr(flujos)
        tir_anual = (1 + tir_mensual) ** 12 - 1 if tir_mensual is not None else None
    except Exception:
        tir_anual = None

    # Mostrar TIR anualizada en la parte superior
    if tir_anual is not None:
        tir_output.metric("TIR anualizada", f"{tir_anual*100:.2f}%")
    else:
        tir_output.metric("TIR anualizada", "—")

    # ===== Salida =====
    st.subheader("Resultados")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Monto solicitado total", f"₡{monto_total:,.0f}")
        st.metric("Honorarios y timbres", f"₡{honorarios_timbres:,.0f}")
        st.metric("Comisión aplicada", f"{comision_pct:.1f}%")
    with col2:
        st.metric("Saldo pay off", f"₡{saldo_payoff:,.0f}")
        st.metric("Tasa de interés anual", f"{tasa_interes_anual:.1f}%")
        st.metric("Plazo", f"{plazo_meses} meses")

    st.divider()
    st.subheader("💰 Cuotas calculadas")
    col3, col4 = st.columns(2)
    with col3:
        st.metric("Cuota sin póliza", f"₡{cuota_base:,.0f}")
    with col4:
        st.metric("Cuota con póliza", f"₡{cuota_con_poliza:,.0f}")
else:
    st.info("Por favor completa comisión, tasa y plazo para calcular las cuotas.")
