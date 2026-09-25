import streamlit as st

st.set_page_config(
    page_title="Paso 19: Hechos relevantes",
    page_icon="📝",
    layout="wide"
)

st.title("📝 Paso 19: Hechos relevantes")

st.info(
    "Registre los hechos relevantes obtenidos durante la visita, entrevista "
    "o verificaciones realizadas que aporten contexto al análisis de crédito "
    "y que no estén suficientemente reflejados en las demás secciones del expediente."
)

# =========================================================
# 1. CLIENTE Y ACTIVIDAD ECONÓMICA
# =========================================================

st.subheader("1. Cliente y actividad económica")

cliente_actividad = st.text_area(
    "Describa aspectos relevantes sobre la persona y su actividad económica",
    placeholder=(
        "Indique aspectos relevantes sobre la experiencia de la persona en la actividad, "
        "antigüedad, forma de operar el negocio, estabilidad, principales características "
        "observadas durante la visita y cualquier elemento que ayude a comprender "
        "cómo desarrolla su actividad económica."
    ),
    height=140
)

# =========================================================
# 2. VIVIENDA Y ENTORNO FAMILIAR
# =========================================================

st.subheader("2. Vivienda y entorno familiar")

vivienda_entorno = st.text_area(
    "Detalle hechos relevantes relacionados con la vivienda y el entorno familiar",
    placeholder=(
        "Describa la situación de vivienda y cualquier aspecto familiar relevante. "
        "Si alquila, indique el monto, tiempo de residir en el lugar y las verificaciones "
        "realizadas con el arrendador, incluyendo si se encuentra al día. Indique cualquier "
        "otra circunstancia del hogar que pueda ser relevante para el análisis."
    ),
    height=140
)

# =========================================================
# 3. DESTINO Y NECESIDAD DEL CRÉDITO
# =========================================================

st.subheader("3. Destino y necesidad del crédito")

destino_credito = st.text_area(
    "Explique para qué necesita el crédito y por qué lo solicita en este momento",
    placeholder=(
        "Explique con claridad para qué necesita los recursos, cómo serán utilizados, "
        "por qué requiere el crédito en este momento y de qué manera el financiamiento "
        "se relaciona con su actividad económica o necesidad planteada."
    ),
    height=140
)

# =========================================================
# 4. INFORMACIÓN ADICIONAL VERIFICADA
# =========================================================

st.subheader("4. Información adicional verificada")

informacion_verificada = st.text_area(
    "Indique cualquier información adicional obtenida o verificada",
    placeholder=(
        "Detalle las verificaciones adicionales realizadas y su resultado. Incluya, cuando "
        "corresponda, información obtenida de arrendadores, proveedores, clientes, referencias "
        "u otras fuentes, así como documentos observados o información que haya sido necesario "
        "confirmar o aclarar."
    ),
    height=140
)

# =========================================================
# 5. OTROS HECHOS RELEVANTES
# =========================================================

st.subheader("5. Otros hechos relevantes")

otros_hechos = st.text_area(
    "¿Qué otros hechos considera importantes para comprender la situación de la persona solicitante?",
    placeholder=(
        "Registre cualquier situación, observación o información relevante que no haya sido "
        "incluida anteriormente y que considere que debe conocer quien analice o decida "
        "sobre el otorgamiento del crédito."
    ),
    height=140
)

# =========================================================
# 6. CRITERIO PERSONAL DEL ASESOR
# =========================================================

st.subheader("6. Criterio personal del asesor sobre el crédito")

criterio_asesor = st.radio(
    "Si los recursos para otorgar este crédito fueran suyos, "
    "¿usted se los prestaría a esta persona en las condiciones propuestas?",
    options=[
        "Sí",
        "Sí, pero con reservas",
        "No"
    ],
    index=None
)

razon_criterio = st.text_area(
    "Explique las razones de su respuesta",
    placeholder=(
        "Justifique su respuesta considerando lo observado durante la visita, la entrevista "
        "con la persona solicitante, las verificaciones realizadas y cualquier elemento que "
        "influya positiva o negativamente en su disposición personal a prestar los recursos."
    ),
    height=120
)

# =========================================================
# DECLARACIÓN DEL ASESOR
# =========================================================

st.divider()

st.subheader("Declaración de veracidad y responsabilidad del asesor")

st.markdown(
    """
Declaro que la información incorporada en el presente expediente de crédito
corresponde fielmente a la información obtenida durante el proceso de evaluación,
ya sea mediante documentación, registros, verificaciones realizadas,
observaciones efectuadas durante la visita o información suministrada
directamente por la persona solicitante.

Asimismo, declaro que he registrado de manera completa y objetiva la información
relevante de la que tuve conocimiento durante el proceso de evaluación y que,
a mi leal saber y entender, no he omitido, alterado o incorporado deliberadamente
información falsa que pueda incidir en el análisis, recomendación o decisión de
otorgamiento del crédito.

Entiendo que la veracidad de las manifestaciones realizadas por la persona
solicitante corresponde a esta cuando no haya sido posible verificarlas
independientemente; mi responsabilidad consiste en identificar adecuadamente
su fuente y registrar fielmente la información recibida y las verificaciones
realizadas.

Reconozco que la alteración, falsificación u omisión deliberada de información
relevante dentro de un expediente de crédito puede constituir un incumplimiento
de mis obligaciones laborales y dar lugar a las medidas que correspondan de
conformidad con la normativa interna de Credimujer y la legislación laboral
costarricense aplicable.
"""
)

acepta_declaracion = st.checkbox(
    "He leído y acepto la declaración de veracidad y responsabilidad anterior."
)

st.divider()

st.button(
    "💾 Guardar hechos relevantes",
    type="primary",
    use_container_width=True
)
