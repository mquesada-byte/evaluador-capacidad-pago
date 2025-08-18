import streamlit as st

# Título
st.set_page_config(page_title="Evaluador de Capacidad de Pago", page_icon="💰")
st.title("💰 Evaluador de Capacidad de Pago para Clientes")

st.markdown("Por favor, complete la siguiente información para evaluar la capacidad de pago del cliente:")

# 🧾 Formulario
ingresos = st.number_input("Ingresos mensuales (₡)", min_value=0, step=1000)
gastos = st.number_input("Gastos mensuales (₡)", min_value=0, step=1000)
deudas = st.number_input("Cuotas mensuales por otras deudas (₡)", min_value=0, step=1000)
actividad = st.text_input("Actividad del negocio")
experiencia = st.number_input("Años de experiencia en la actividad", min_value=0, step=1)

# 📊 Procesamiento
if st.button("Evaluar capacidad de pago"):
    flujo_neto = ingresos - gastos - deudas
    capacidad_pago = max(flujo_neto * 0.3, 0)

    # Clasificación de riesgo simple
    if flujo_neto > 300000:
        riesgo = "Bajo"
    elif flujo_neto > 100000:
        riesgo = "Medio"
    else:
        riesgo = "Alto"

    # 🔍 Informe generado automáticamente (versión sin GPT)
    st.subheader("📄 Informe automático")

    informe = f"""
**Actividad:** {actividad}  
**Experiencia:** {experiencia} años  
**Ingresos mensuales:** ₡{ingresos:,.0f}  
**Gastos + Deudas:** ₡{gastos + deudas:,.0f}  
**Flujo de caja neto:** ₡{flujo_neto:,.0f}  
**Capacidad de pago estimada (30%):** ₡{capacidad_pago:,.0f}  
**Nivel de riesgo:** {riesgo}

💡 **Recomendación:** {'Se recomienda aprobar el crédito.' if riesgo == 'Bajo' else 'Requiere evaluación adicional por comité de crédito.'}
"""
    st.markdown(informe)
