import streamlit as st

st.title("Calculadora de capacidad de pago")

ingresos = st.number_input("Ingresos mensuales")
gastos = st.number_input("Gastos mensuales")

if st.button("Calcular"):
    flujo = ingresos - gastos
    st.write(f"Flujo neto: {flujo}")
