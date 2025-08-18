import streamlit as st
from fpdf import FPDF
from io import BytesIO
import base64

# Configuración de página
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
    capacidad_pago = max(flujo_neto * 0.30, 0)

    # Clasificación de riesgo simple
    if flujo_neto > 300000:
        riesgo = "Bajo"
    elif flujo_neto > 100000:
        riesgo = "Medio"
    else:
        riesgo = "Alto"

    # 🔍 Informe mostrado en la app (con ₡)
    informe_md = f"""
**Actividad:** {actividad}  
**Experiencia:** {experiencia} años  
**Ingresos mensuales:** ₡{ingresos:,.0f}  
**Gastos + Deudas:** ₡{(gastos + deudas):,.0f}  
**Flujo de caja neto:** ₡{flujo_neto:,.0f}  
**Capacidad de pago estimada (30%):** ₡{capacidad_pago:,.0f}  
**Nivel de riesgo:** {riesgo}

💡 **Recomendación:** {'Se recomienda aprobar el crédito.' if riesgo == 'Bajo' else 'Requiere evaluación adicional por comité de crédito.'}
"""
    # Encabezado + botón a la par
    c1, c2 = st.columns([0.75, 0.25])
    with c1:
        st.subheader("📄 Informe automático")
    with c2:
        # --- Generar PDF en memoria (reemplazamos ₡ por CRC por compatibilidad con FPDF) ---
        informe_pdf_txt = (
            f"Actividad: {actividad}\n"
            f"Experiencia: {experiencia} años\n"
            f"Ingresos mensuales: CRC {ingresos:,.0f}\n"
            f"Gastos + Deudas: CRC {(gastos + deudas):,.0f}\n"
            f"Flujo de caja neto: CRC {flujo_neto:,.0f}\n"
            f"Capacidad de pago (30%): CRC {capacidad_pago:,.0f}\n"
            f"Nivel de riesgo: {riesgo}\n\n"
            f"Recomendación: {'Se recomienda aprobar el crédito.' if riesgo == 'Bajo' else 'Requiere evaluación adicional por comité de crédito.'}"
        )

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        for linea in informe_pdf_txt.split("\n"):
            pdf.cell(0, 8, txt=linea, ln=True)

        pdf_bytes = pdf.output(dest="S").encode("latin-1")

        st.download_button(
            label="📥 Descargar PDF",
            data=BytesIO(pdf_bytes),
            file_name="informe_capacidad_pago.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    # Mostrar el informe en pantalla (markdown)
    st.markdown(informe_md)

    # (Opcional) Ver PDF embebido
    if st.checkbox("Ver PDF embebido"):
        b64 = base64.b64encode(pdf_bytes).decode()
        st.markdown(
            f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="600"></iframe>',
            unsafe_allow_html=True
        )




