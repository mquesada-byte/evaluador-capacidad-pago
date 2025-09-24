# pages/15_Condiciones_credito.py
import streamlit as st
import numpy as np
import numpy_financial as npf


# ======================
# 📌 Parámetros globales
# ======================
TASA_MAX_CREDITO = 36.65   # % anual, tasa máxima para todo tipo de créditos
TASA_MAX_MICROCREDITO = 51.74  # % anual, tasa máxima para microcrédito
SALARIO_BASE = 462_200     # Salario base en colones
MONTO_MAX_MICROCREDITO = SALARIO_BASE * 2.5  # Monto máximo permitido para microcrédito
# ======================


st.set_page_config(page_title="Paso 15: Condiciones de Crédito", page_icon="💳")

st.title("💳 Paso 15: Condiciones de Crédito")
st.caption("Cálculo de la cuota con y sin póliza del INS.")

# ===== Entradas =====
col1, col2 = st.columns(2)
with col1:
    monto_solicitado = st.number_input("Monto solicitado (₡)", min_value=0, step=50000, value=0)
with col2:
    saldo_payoff = st.number_input(
        "Saldo pay off (₡)", min_value=0, step=50000, value=0,
        help="Saldo pay off solo para recréditos"
    )

col3, col4, col5 = st.columns(3)
with col3:
    comision_pct = st.selectbox(
        "Porcentaje de comisión (%)", [1.5, 2, 4, 6, 8, 10],
        index=None, placeholder="Selecciona"
    )
with col4:
    tasa_interes_anual = st.selectbox(
        "Tasa de interés anual (%)", [14, 22, 24, 26, 30, 34],
        index=None, placeholder="Selecciona"
    )
with col5:
    plazo_meses = st.number_input("Plazo (meses)", min_value=0, max_value=120, step=1, value=0)

# Honorarios + espacio para TIR
col6, col7 = st.columns(2)
with col6:
    honorarios_timbres = st.number_input(
        "Honorarios y timbres (₡)", min_value=0, step=5000, value=0,
        help="Monto único que nos cotiza el abogado"
    )
with col7:
    tir_placeholder = st.empty()  # 👈 aquí pondremos la TIR anualizada

# ===== Botón y alerta en la misma fila =====
col_boton, col_alerta = st.columns([1, 3])  # botón pequeño a la izquierda, alerta a la derecha

with col_boton:
    calcular = st.button("Calcular condiciones")

if calcular:
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

        # ===== Cálculo de la TIR =====
        flujos = [monto_solicitado + saldo_payoff] + [-cuota_con_poliza for _ in range(plazo_meses)]

        try:
            tir_mensual = npf.irr(flujos)
            if tir_mensual is not None and not np.isnan(tir_mensual):
                tir_anual = (1 + tir_mensual)**12 - 1
            else:
                tir_anual = None
        except Exception:
            tir_anual = None

        # Mostrar la TIR en el espacio junto a honorarios
        with col7:
            if tir_anual is not None and tir_anual > 0:
                tir_placeholder.metric("TIR anualizada", f"{tir_anual*100:.2f}%")

                # 🚨 Verificación contra la ley de usura (alerta ahora va junto al botón)
                with col_alerta:
                    if monto_total <= MONTO_MAX_MICROCREDITO:
                        # Caso 1: Microcrédito
                        if tir_anual * 100 > TASA_MAX_MICROCREDITO:
                            st.warning(
                                f"⚠️ ALERTA: La TIR ({tir_anual*100:.2f}%) supera el límite legal para microcrédito ({TASA_MAX_MICROCREDITO:.2f}%)"
                            )
                        else:
                            st.success(
                                f"🟢 OK: La TIR ({tir_anual*100:.2f}%) está dentro del límite de microcrédito ({TASA_MAX_MICROCREDITO:.2f}%)"
                            )
                    else:
                        # Caso 2: Crédito normal
                        if tir_anual * 100 > TASA_MAX_CREDITO:
                            st.warning(
                                f"⚠️ ALERTA: La TIR ({tir_anual*100:.2f}%) supera el límite legal para crédito ({TASA_MAX_CREDITO:.2f}%)"
                            )
                        else:
                            st.success(
                                f"🟢 OK: La TIR ({tir_anual*100:.2f}%) está dentro del límite de crédito ({TASA_MAX_CREDITO:.2f}%)"
                            )

            else:
                tir_placeholder.metric("TIR anualizada", "—")

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
        st.warning("⚠️ Por favor completa comisión, tasa y plazo antes de calcular.")
