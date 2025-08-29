# Home.py
import os
import streamlit as st

st.set_page_config(page_title="Evaluador de Capacidad de Pago", page_icon="💻")

def step_status(flag: str) -> str:
    return "✅" if st.session_state.get(flag) else "⏳"

def first_existing(paths):
    """Devuelve el primer path que exista en disco (o None)."""
    for p in paths:
        if os.path.exists(p):
            return p
    return None

st.title("🏠 Evaluador de Capacidad de Pago")
st.write("Usa el menú lateral o los enlaces de abajo para navegar por los pasos.")
st.divider()

# Paso 1
with st.container(border=True):
    st.page_link("pages/01_Asesor.py",
        label=f"{step_status('done_01')} 01 – Datos del asesor",
        help="Identificación del asesor, fecha/hora (CR) y geolocalización."
    )

# Paso 2
with st.container(border=True):
    st.page_link("pages/02_Cliente_y_negocio.py",
        label=f"{step_status('done_02')} 02 – Cliente y negocio",
        help="Datos del cliente y del negocio para iniciar la evaluación."
    )

# Paso 3A
with st.container(border=True):
    st.page_link("pages/03_Ventas_top_down.py",
        label=f"{step_status('done_03A')} 03A – Ventas (Top-down)",
        help="Declaración directa de ventas del último mes calendario."
    )

# Paso 4 (Bottom-up) – contempla posibles nombres
with st.container(border=True):
    p4 = first_existing([
        "pages/04_Ventas_botton_up.py",  # si tu archivo se llama así
        "pages/04_Ventas_bottom_up.py",  # alternativa corregida
    ])
    if p4:
        st.page_link(p4,
            label=f"{step_status('done_04')} 04 – Ventas (Bottom-up)",
            help="Estimación operativa (clientes x ticket) para el último mes calendario."
        )
    else:
        st.warning("No se encontró la página del Paso 4. Verificá el nombre del archivo en /pages.")

# Paso 5
with st.container(border=True):
    st.page_link("pages/05_Ventas_insumos_margen.py",
        label=f"{step_status('done_05')} 05 – Ventas (insumos/margen)",
        help="Estimación de ventas a partir de compras y margen declarado."
    )

# Paso 6 – Valoración del asesor
with st.container(border=True):
    st.page_link("pages/06_Valoración_asesor.py",
        label=f"{step_status('done_06')} 06 – Valoración del asesor",
        help="Evaluación cualitativa (conocimiento, credibilidad, dudas y evidencia)."
    )

# Paso 7 – Conciliación de ventas
with st.container(border=True):
    st.page_link("pages/07_Conciliación_de_ventas.py",
        label=f"{step_status('done_07')} 07 – Conciliación de ventas",
        help="Compara Top-down, Bottom-up e Insumos y fija ventas conciliadas."
    )

# Paso 8 – Otros ingresos
with st.container(border=True):
    st.page_link("pages/08_Otros_ingresos.py",
        label=f"{step_status('done_08')} 08 – Otros ingresos del hogar",
        help="Registro y ponderación de otros ingresos del hogar."
    )

# Paso 9 – Deudas activas del hogar
with st.container(border=True):
    st.page_link("pages/09_Deudas.py",
        label=f"{step_status('done_09')} 09 – Deudas activas del hogar",
        help="Préstamos/obligaciones vigentes; cuota mensual, saldos y clasificación por plazo."
    )

# Paso 10 – Gastos operativos
with st.container(border=True):
    st.page_link("pages/10_Gastos_operativos.py",
        label=f"{step_status('done_10')} 10 – Gastos operativos",
        help="Gastos del negocio/hogar relacionados a la operación, mensualizados."
    )

# Paso 11 – Gastos familiares
with st.container(border=True):
    st.page_link("pages/11_Gastos_familiares.py",
        label=f"{step_status('done_11')} 11 – Gastos familiares",
        help="Registro y mensualización de gastos del hogar, con opción de verificación/evidencia."
    )

# Paso 12 – Estado de Resultados (robusto ante nombres distintos)
with st.container(border=True):
    p12 = first_existing([
        "pages/12_Estado_de_resultadosl.py",  # con 'l' final
        "pages/12_Estado_de_resultados.py",
        "pages/12_Estado_resultados.py",
        "pages/12_Resultados.py",
        "pages/12_Resumen.py",
        "pages/estado_resultados.py",
        "estado_resultados.py",
    ])
    if p12:
        st.page_link(p12,
            label=f"{step_status('done_12')} 12 – Estado de resultados",
            help="Resumen automático de ventas, costos y gastos; calcula el disponible para préstamo."
        )
    else:
        st.error("No se encontró la página del Paso 12. Verificá el nombre real del archivo en /pages.")

# Paso 13 – Balance general
with st.container(border=True):
    st.page_link("pages/13_Balance_general.py",
        label=f"{step_status('done_13')} 13 – Balance general",
        help="Activos, pasivos, patrimonio y capital de trabajo."
    )

# Paso 14 – Informe final (PDF) (verifica existencia)
with st.container(border=True):
    p14 = first_existing(["pages/14_Informe_final.py", "14_Informe_final.py"])
    if p14:
        st.page_link(p14,
            label=f"{step_status('done_14')} 14 – Informe final (PDF)",
            help="Portada + cliente/negocio + valoración + análisis de ventas, con descarga en PDF."
        )
    else:
        st.info("Crea `pages/14_Informe_final.py` para habilitar el Paso 14.")

# Paso 15 – Análisis asistido (IA) (sin acentos en el nombre de archivo)
with st.container(border=True):
    p15 = first_existing([
        "pages/15_Analisis_IA.py",
        "pages/15_Análisis_IA.py",  # por si existe con tilde
    ])
    if p15:
        st.page_link(p15,
            label=f"{step_status('done_15')} 15 – Análisis asistido (IA)",
            help="Genera el análisis del caso con IA y permite descargarlo en PDF."
        )
    else:
        st.info("Crea `pages/15_Analisis_IA.py` para habilitar el Paso 15.")

st.divider()
st.info("También podés abrir los pasos desde el menú lateral.")


