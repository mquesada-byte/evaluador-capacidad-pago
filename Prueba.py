import os
import base64
from io import BytesIO

import streamlit as st
from fpdf import FPDF
from openai import OpenAI

# =========================
# Utilidades
# =========================
def make_pdf_bytes(texto: str) -> bytes:
    """
    Genera PDF en memoria a partir de 'texto'.
    Nota: FPDF clásico no soporta Unicode; reemplazamos '₡' por 'CRC'.
    """
    texto = texto.replace("₡", "CRC")
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)

    # Escribir línea a línea con MultiCell para saltos largos
    for linea in texto.split("\n"):
        pdf.multi_cell(0, 8, linea)

    return pdf.output(dest="S").encode("latin-1")


def generar_informe_reglas(actividad, experiencia, ingresos, gastos, deudas,
                           flujo_neto, capacidad_pago, riesgo) -> str:
    """Informe básico (reglas) en Markdown."""
    return f"""
**Actividad:** {actividad}  
**Experiencia:** {experiencia} años  
**Ingresos mensuales:** ₡{ingresos:,.0f}  
**Gastos + Deudas:** ₡{(gastos + deudas):,.0f}  
**Flujo de caja neto:** ₡{flujo_neto:,.0f}  
**Capacidad de pago estimada (30%):** ₡{capacidad_pago:,.0f}  
**Nivel de riesgo:** {riesgo}

💡 **Recomendación:** {'Se recomienda aprobar el crédito.' if riesgo == 'Bajo' else 'Requiere evaluación adicional por comité de crédito.'}
""".strip()


def generar_informe_gpt(payload: dict) -> str:
    """
    Redacta un informe con IA (GPT) en Markdown.
    Requiere OPENAI_API_KEY en entorno/Secrets.
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    system = (
        "Eres un analista de microfinanzas. Redacta informes claros y accionables "
        "para comité de crédito. Separa: Resumen ejecutivo, Datos clave, "
        "Análisis y señales de alerta (consistencias/inconsistencias), "
        "Recomendación y Datos faltantes/requeridos si aplica."
    )

    user = f"""
Datos del caso:
- Actividad: {payload['actividad']}
- Experiencia (años): {payload['experiencia']}
- Ingresos mensuales: {payload['ingresos']}
- Gastos mensuales: {payload['gastos']}
- Deudas (cuotas mensuales): {payload['deudas']}

Cálculos:
- Flujo neto = ingresos - gastos - deudas = {payload['flujo_neto']}
- Capacidad de pago (30% del flujo neto) = {payload['capacidad_pago']}
- Nivel de riesgo (regla interna) = {payload['riesgo']}

Política simplificada:
- Sugerir no exceder 30% del flujo neto como cuota.
- Riesgo 'Bajo' si flujo_neto > 300000; 'Medio' si > 100000; caso contrario 'Alto'.

Tareas:
1) Redacta un informe breve en markdown con estas secciones:
   - **Resumen ejecutivo** (2-4 líneas)
   - **Datos clave**
   - **Análisis y señales de alerta**
   - **Recomendación** (aprobar / revisar / rechazar) con breve justificación
2) Si faltan datos, inclúyelos en **Datos faltantes/requeridos**.
3) Mantén tono profesional, concreto y específico a los datos.
"""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.3,
    )
    return resp.choices[0].message.content


# =========================
# App Streamlit
# =========================
st.set_page_config(page_title="Evaluador de Capacidad de Pago", page_icon="💰")
st.title("💰 Evaluador de Capacidad de Pago para Clientes")
st.markdown("Complete la información para evaluar la capacidad de pago del cliente:")

# Formulario
ingresos = st.number_input("Ingresos mensuales (₡)", min_value=0, step=1000)
gastos = st.number_input("Gastos mensuales (₡)", min_value=0, step=1000)
deudas = st.number_input("Cuotas mensuales por otras deudas (₡)", min_value=0, step=1000)
actividad = st.text_input("Actividad del negocio")
experiencia = st.number_input("Años de experiencia en la actividad", min_value=0, step=1)

# Evaluar
if st.button("Evaluar capacidad de pago"):
    flujo_neto = ingresos - gastos - deudas
    capacidad_pago = max(flujo_neto * 0.30, 0)

    # Riesgo básico
    if flujo_neto > 300000:
        riesgo = "Bajo"
    elif flujo_neto > 100000:
        riesgo = "Medio"
    else:
        riesgo = "Alto"

    # Informe por reglas (siempre disponible)
    informe_reglas = generar_informe_reglas(
        actividad, experiencia, ingresos, gastos, deudas,
        flujo_neto, capacidad_pago, riesgo
    )

    # Cabecera + botón de PDF (reglas)
    c1, c2 = st.columns([0.75, 0.25])
    with c1:
        st.subheader("📄 Informe automático (reglas)")
    with c2:
        pdf_bytes_reglas = make_pdf_bytes(informe_reglas)
        st.download_button(
            "📥 PDF (reglas)",
            data=BytesIO(pdf_bytes_reglas),
            file_name="informe_capacidad_pago_reglas.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    st.markdown(informe_reglas)

    # Opción IA (GPT)
    st.divider()
    usar_ia = st.checkbox("Generar informe avanzado con IA (GPT)")

    if usar_ia:
        if not os.getenv("OPENAI_API_KEY"):
            st.warning("No hay OPENAI_API_KEY configurada. Cárguela en Secrets o variable de entorno.")
        else:
            with st.spinner("Generando informe con IA..."):
                payload = {
                    "actividad": actividad,
                    "experiencia": experiencia,
                    "ingresos": ingresos,
                    "gastos": gastos,
                    "deudas": deudas,
                    "flujo_neto": flujo_neto,
                    "capacidad_pago": capacidad_pago,
                    "riesgo": riesgo,
                }
                try:
                    informe_gpt = generar_informe_gpt(payload)
                    c3, c4 = st.columns([0.75, 0.25])
                    with c3:
                        st.subheader("🧠 Informe generado por IA (GPT)")
                    with c4:
                        pdf_bytes_gpt = make_pdf_bytes(informe_gpt)
                        st.download_button(
                            "📥 PDF (IA)",
                            data=BytesIO(pdf_bytes_gpt),
                            file_name="informe_capacidad_pago_IA.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                        )
                    st.markdown(informe_gpt)

                    # (Opcional) ver PDF embebido
                    if st.checkbox("Ver PDF (IA) embebido"):
                        b64 = base64.b64encode(pdf_bytes_gpt).decode()
                        st.markdown(
                            f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="600"></iframe>',
                            unsafe_allow_html=True
                        )
                except Exception as e:
                    st.error(f"No se pudo generar el informe con IA: {e}")
                    st.info("Mostrando solamente el informe automático por reglas.")




