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
        "Ej.: Tiene 8 años de dedicarse a la actividad. Trabaja principalmente "
        "por encargo. La actividad constituye su principal fuente de ingresos. "
        "Durante la visita se observó inventario, herramientas y movimiento "
        "propio de la actividad..."
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
        "Ej.: Alquila la vivienda desde hace 4 años por ₡180.000 mensuales. "
        "Se verificó con el propietario que se encuentra al día con el alquiler. "
        "Vive con su pareja y dos hijos. La pareja contribuye con los gastos "
        "del hogar..."
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
        "Ej.: Solicita el crédito para comprar inventario debido a un aumento "
        "en los pedidos. Indica que utilizará los recursos para adquirir materia "
        "prima y productos que actualmente compra en pequeñas cantidades..."
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
        "Ej.: Se verificó el ingreso adicional indicado por la solicitante. "
        "Se conversó con el arrendador y confirmó la información suministrada. "
        "La solicitante mostró facturas de proveedores y registros de ventas. "
        "Se aclararon diferencias encontradas durante la entrevista..."
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
        "Ej.: La solicitante explicó una situación particular que afectó "
        "temporalmente sus ingresos. Cuenta con apoyo familiar para atender "
        "el negocio. Se observó una situación que debe ser considerada al "
        "analizar el crédito..."
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
        "Ej.: Sí, porque durante la visita observé una actividad estable, "
        "la información suministrada fue consistente con las verificaciones "
        "realizadas y considero razonable la capacidad de la persona para "
        "atender la obligación..."
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
