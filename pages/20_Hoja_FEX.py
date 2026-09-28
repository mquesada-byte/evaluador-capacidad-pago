import logging

import pymssql
import streamlit as st


# ============================================================
# CONFIGURACIÓN
# ============================================================

st.set_page_config(
    page_title="Paso 20: Hoja FEX",
    page_icon="📄",
)

st.title("📄 Paso 20 – Hoja FEX")


# ============================================================
# CONEXIÓN AL HISTORIAL DE CRÉDITOS
# Usa la sección [fex_sql] de Secrets.
# ============================================================

def get_fex_connection():
    config = st.secrets["fex_sql"]

    return pymssql.connect(
        server=config["server"],
        database=config["database"],
        user=config["user"],
        password=config["password"],
        login_timeout=10,
        timeout=30,
        charset="UTF-8",
        appname="Streamlit Hoja FEX",
        autocommit=True,
    )


# ============================================================
# CONSULTA POR CÉDULA
# ============================================================

def consultar_datos_credito(cedula):
    query = """
    ;WITH Cliente AS (
        SELECT DISTINCT
            cd.clientcode
        FROM clientdoc AS cd
        WHERE cd.docnum = %s
    ),
    Creditos AS (
        SELECT
            l.lnr,
            l.seq,
            l.lamount
        FROM loan AS l
        WHERE EXISTS (
            SELECT 1
            FROM Cliente AS c
            WHERE c.clientcode = l.clcode
        )
    ),
    Pagos AS (
        SELECT
            m.lnr,
            SUM(m.mprinc) AS capitalPagado
        FROM memrepay AS m
        WHERE EXISTS (
            SELECT 1
            FROM Creditos AS c
            WHERE c.lnr = m.lnr
        )
        GROUP BY m.lnr
    ),
    Saldos AS (
        SELECT
            c.lnr,
            ROUND(
                CAST(
                    c.lamount - ISNULL(p.capitalPagado, 0)
                    AS FLOAT
                ),
                0
            ) AS saldo
        FROM Creditos AS c
        LEFT JOIN Pagos AS p
            ON p.lnr = c.lnr
    )
    SELECT
        CASE
            WHEN NOT EXISTS (
                SELECT 1 FROM Cliente
            ) THEN 'Nuevo'

            WHEN EXISTS (
                SELECT 1
                FROM Saldos
                WHERE saldo > 0
            ) THEN 'Recrédito'

            WHEN EXISTS (
                SELECT 1
                FROM Saldos
                WHERE saldo < 0 OR saldo IS NULL
            ) THEN 'Revisar saldo'

            ELSE 'Anterior'
        END AS tipoCredito,

        (
            SELECT ISNULL(MAX(seq), 0) + 1
            FROM Creditos
        ) AS numeroCredito;
    """

    conn = get_fex_connection()
    cursor = None

    try:
        cursor = conn.cursor()
        cursor.execute(query, (cedula,))
        resultado = cursor.fetchone()

        if resultado is None:
            raise RuntimeError(
                "La consulta no devolvió información."
            )

        return {
            "tipo_credito": resultado[0],
            "numero_credito": resultado[1],
        }

    finally:
        try:
            if cursor is not None:
                cursor.close()
        finally:
            conn.close()
# ============================================================
# CONSULTA DE SECTORES PRODUCTIVOS — CATÁLOGO LPF
# ============================================================

def consultar_sectores():
    conn = get_fex_connection()
    cursor = None

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                sectorid,
                LTRIM(RTRIM(sector)) AS sector
            FROM busssec
            WHERE sectorid NOT IN (4, 5)
            ORDER BY sectorid
        """)

        return [
            {"sectorid": fila[0], "sector": fila[1]}
            for fila in cursor.fetchall()
        ]

    finally:
        try:
            if cursor is not None:
                cursor.close()
        finally:
            conn.close()

# ============================================================
# CLIENTE CARGADO
# ============================================================

cliente = st.session_state.get("cliente") or {}

nombre_cliente = str(
    cliente.get("nombre_completo") or ""
).strip()

cedula_mostrar = str(
    cliente.get("identificacion") or ""
).strip()

cedula_consulta = cedula_mostrar.strip()

if not cedula_consulta:
    st.warning("Primero cargá un cliente en el Paso 2.")
    st.stop()


# ============================================================
# DATOS DE LA HOJA FEX
# ============================================================

st.subheader("Datos del cliente")

# El botón vuelve a ejecutar la página y consulta SQL nuevamente.
st.button(
    "🔄 Actualizar datos de crédito",
    use_container_width=True,
)

try:
    with st.spinner("Consultando información del crédito..."):
        datos_credito = consultar_datos_credito(
            cedula_consulta
        )

except Exception as error:
    logging.getLogger(__name__).exception(
        "Error consultando los datos de la Hoja FEX"
    )

    detalle = f"{type(error).__name__}: {error}"

    try:
        clave = st.secrets["fex_sql"]["password"]
        if clave:
            detalle = detalle.replace(clave, "***")
    except Exception:
        pass

    st.code(detalle, language="text")
    

    st.error(
        "No se pudo consultar la base LPFCREDIMUJER. "
        "Revisá las credenciales de fex_sql y el acceso "
        "al servidor SQL desde la aplicación."
    )

    st.text_input(
        "Nombre del cliente",
        value=nombre_cliente,
        disabled=True,
    )

    st.text_input(
        "Cédula del cliente",
        value=cedula_mostrar,
        disabled=True,
    )

    st.stop()


# Actualiza los campos incluso al cambiar de cliente.
valores_campos = {
    "fex_tipo_credito": datos_credito["tipo_credito"],
    "fex_nombre_cliente": nombre_cliente,
    "fex_cedula_cliente": cedula_mostrar,
    "fex_numero_credito": str(
        datos_credito["numero_credito"]
    ),
}

for clave, valor in valores_campos.items():
    st.session_state[clave] = valor

st.text_input(
    "Tipo de crédito",
    key="fex_tipo_credito",
    disabled=True,
)

st.text_input(
    "Nombre del cliente",
    key="fex_nombre_cliente",
    disabled=True,
)

st.text_input(
    "Cédula del cliente",
    key="fex_cedula_cliente",
    disabled=True,
)

st.text_input(
    "Crédito número",
    key="fex_numero_credito",
    disabled=True,
)

if not nombre_cliente:
    st.warning(
        "El cliente cargado no tiene nombre completo. "
        "Revisá la información del Paso 2."
    )

if datos_credito["tipo_credito"] == "Revisar saldo":
    st.warning(
        "El historial contiene un saldo negativo o "
        "sin información que requiere revisión."
    )

# ============================================================
# SECTOR PRODUCTIVO — LISTA DESDE LPF
# ============================================================

try:
    sectores = consultar_sectores()

except Exception:
    logging.getLogger(__name__).exception(
        "Error consultando los sectores productivos"
    )
    st.error("No se pudo cargar el catálogo de sectores de LPF.")
    st.stop()

if not sectores:
    st.warning("No hay sectores productivos disponibles en LPF.")
    st.stop()

sectores_por_id = {
    sector["sectorid"]: sector["sector"]
    for sector in sectores
}

sector_id = st.selectbox(
    "Sector productivo",
    options=[None] + list(sectores_por_id),
    format_func=lambda valor: (
        "Seleccione un sector"
        if valor is None
        else sectores_por_id[valor]
    ),
    key=f"fex_sector_{cedula_consulta}",
)

# ============================================================
# CONSULTA DE TIPOS DE NEGOCIO — CATÁLOGO LPF
# ============================================================

def consultar_tipos_negocio():
    conn = get_fex_connection()
    cursor = None

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                udf3,
                LTRIM(RTRIM(lab3)) AS actividad
            FROM ud3
            WHERE udf3 <> 0
            ORDER BY actividad
        """)

        return [
            {
                "actividad_id": fila[0],
                "actividad": fila[1],
            }
            for fila in cursor.fetchall()
        ]

    finally:
        try:
            if cursor is not None:
                cursor.close()
        finally:
            conn.close()


# ============================================================
# ACTIVIDAD PRINCIPAL — CATÁLOGO LPF Y OTRAS ACTIVIDADES
# ============================================================

try:
    actividades = consultar_tipos_negocio()

except Exception:
    logging.getLogger(__name__).exception(
        "Error consultando las actividades de LPF"
    )
    st.error("No se pudo cargar el catálogo de actividades.")
    st.stop()

actividades_por_id = {
    item["actividad_id"]: item["actividad"]
    for item in actividades
}

OPCION_OTROS = "__otros__"

actividad_id = st.selectbox(
    "Actividad principal",
    options=[None] + list(actividades_por_id) + [OPCION_OTROS],
    format_func=lambda valor: (
        "Seleccione una actividad"
        if valor is None
        else "Otros — especificar"
        if valor == OPCION_OTROS
        else actividades_por_id[valor]
    ),
    help="Seleccione la actividad que genera más ingresos.",
    key=f"fex_actividad_{cedula_consulta}",
)

actividad_principal_codigo = None
actividad_principal_descripcion = ""
actividad_principal_valida = False

if actividad_id == OPCION_OTROS:
    actividad_principal_descripcion = st.text_input(
        "Especifique la actividad principal",
        placeholder="Ejemplo: Elaboración de velas artesanales",
        key=f"fex_otra_actividad_{cedula_consulta}",
    ).strip()

    actividad_principal_valida = bool(
        actividad_principal_descripcion
    )

    if not actividad_principal_valida:
        st.warning("Debe describir la actividad principal.")

elif actividad_id is not None:
    actividad_principal_codigo = actividad_id
    actividad_principal_descripcion = actividades_por_id[actividad_id]
    actividad_principal_valida = True

# ============================================================
# CONSULTA DE PROPÓSITOS DEL PRÉSTAMO — CATÁLOGO LPF
# ============================================================

def consultar_propositos():
    conn = get_fex_connection()
    cursor = None

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                udf2,
                LTRIM(RTRIM(lab2)) AS proposito
            FROM ud2
            WHERE udf2 NOT IN (0, 1)
            ORDER BY proposito
        """)

        return [
            {
                "proposito_id": fila[0],
                "proposito": fila[1],
            }
            for fila in cursor.fetchall()
        ]

    finally:
        try:
            if cursor is not None:
                cursor.close()
        finally:
            conn.close()


# ============================================================
# PROPÓSITO DEL PRÉSTAMO — LISTA Y OTROS
# ============================================================

try:
    propositos = consultar_propositos()

except Exception:
    logging.getLogger(__name__).exception(
        "Error consultando los propósitos del préstamo"
    )
    st.error("No se pudo cargar el catálogo de propósitos.")
    st.stop()

propositos_por_id = {
    item["proposito_id"]: item["proposito"]
    for item in propositos
}

OTRO_PROPOSITO = "__otro_proposito__"

proposito_id = st.selectbox(
    "Propósito principal del préstamo",
    options=[None] + list(propositos_por_id) + [OTRO_PROPOSITO],
    format_func=lambda valor: (
        "Seleccione un propósito"
        if valor is None
        else "Otros — especificar"
        if valor == OTRO_PROPOSITO
        else propositos_por_id[valor]
    ),
    key=f"fex_proposito_{cedula_consulta}",
)

proposito_codigo = None
proposito_descripcion = ""
proposito_valido = False

if proposito_id == OTRO_PROPOSITO:
    proposito_descripcion = st.text_input(
        "Especifique el propósito principal del préstamo",
        placeholder="Describa en qué utilizará los recursos",
        key=f"fex_otro_proposito_{cedula_consulta}",
    ).strip()

    proposito_valido = bool(proposito_descripcion)

    if not proposito_valido:
        st.warning("Debe describir el propósito del préstamo.")

elif proposito_id is not None:
    proposito_codigo = proposito_id
    proposito_descripcion = propositos_por_id[proposito_id]
    proposito_valido = True

# ============================================================
# MONTO TOTAL DEL CRÉDITO — RECUPERADO DEL PASO 15
# ============================================================

from utils.db import load_condiciones_credito

try:
    condiciones_fex = load_condiciones_credito(
        cliente["identificacion"]
    )

except Exception:
    logging.getLogger(__name__).exception(
        "Error recuperando las condiciones del Paso 15"
    )
    st.error("No se pudieron recuperar las condiciones del crédito.")
    st.stop()

if (
    not condiciones_fex
    or condiciones_fex.get("monto_total") is None
):
    st.warning(
        "Primero guardá las condiciones del crédito en el Paso 15."
    )
    st.stop()

monto_credito_fex = float(condiciones_fex["monto_total"])

if monto_credito_fex <= 0:
    st.warning(
        "El monto total del crédito debe ser mayor que cero. "
        "Revisá el Paso 15."
    )
    st.stop()

st.subheader("Garantía del crédito")

st.metric(
    "Monto total del crédito",
    f"₡{monto_credito_fex:,.0f}",
)

# ============================================================
# TIPO DE GARANTÍA — SELECCIÓN
# ============================================================

tipos_garantia = {
    1: "Hipoteca en primer grado",
    2: "Hipoteca en segundo grado",
    3: "Cédula hipotecaria",
    4: "Fianza",
    5: "Fianza moral",
    6: "Sin garantía",
}

tipo_garantia_id = st.selectbox(
    "Tipo de garantía",
    options=[None] + list(tipos_garantia),
    format_func=lambda valor: (
        "Seleccione el tipo de garantía"
        if valor is None
        else tipos_garantia[valor]
    ),
    key=f"fex_tipo_garantia_{cedula_consulta}",
)

# ============================================================
# GARANTÍA — HIPOTECA EN PRIMER GRADO
# ============================================================

observaciones_garantia = ""

if tipo_garantia_id == 1:
    st.subheader("Datos de la propiedad")

    provincia_garantia = st.text_input(
        "Provincia",
        key=f"fex_hip1_provincia_{cedula_consulta}",
    ).strip()

    canton_garantia = st.text_input(
        "Cantón",
        key=f"fex_hip1_canton_{cedula_consulta}",
    ).strip()

    distrito_garantia = st.text_input(
        "Distrito",
        key=f"fex_hip1_distrito_{cedula_consulta}",
    ).strip()

    numero_finca = st.text_input(
        "Número de finca",
        key=f"fex_hip1_finca_{cedula_consulta}",
    ).strip()

    valor_propiedad = st.number_input(
        "Valor estimado de la propiedad (₡)",
        min_value=0.0,
        step=100000.0,
        format="%.2f",
        key=f"fex_hip1_valor_{cedula_consulta}",
    )

    firma_codeudor = st.selectbox(
        "¿Firma con codeudor?",
        options=["Seleccione", "Sí", "No"],
        key=f"fex_hip1_codeudor_{cedula_consulta}",
    )

    nombre_codeudor = ""
    cedula_codeudor = ""

    if firma_codeudor == "Sí":
        nombre_codeudor = st.text_input(
            "Nombre completo del codeudor",
            key=f"fex_hip1_nombre_codeudor_{cedula_consulta}",
        ).strip()

        cedula_codeudor = st.text_input(
            "Cédula del codeudor",
            key=f"fex_hip1_cedula_codeudor_{cedula_consulta}",
        ).strip()

    observaciones = []

    campos_propiedad = {
        "provincia": provincia_garantia,
        "cantón": canton_garantia,
        "distrito": distrito_garantia,
        "número de finca": numero_finca,
    }

    faltantes = [
        nombre
        for nombre, valor in campos_propiedad.items()
        if not valor
    ]

    if faltantes:
        observaciones.append(
            "Datos de propiedad pendientes: "
            + ", ".join(faltantes)
            + "."
        )

    if valor_propiedad > 0:
        cobertura_garantia = monto_credito_fex / valor_propiedad

        st.metric(
            "Relación crédito / valor de la propiedad",
            f"{cobertura_garantia:.2%}",
        )

        # Equivale a crédito / valor de propiedad > 80 %.
        if monto_credito_fex > valor_propiedad * 0.80:
            observaciones.append(
                f"El monto total del crédito (₡{monto_credito_fex:,.2f}) "
                f"supera el 80 % del valor estimado de la propiedad "
                f"(₡{valor_propiedad * 0.80:,.2f}). "
                "No cumple el límite de cobertura establecido."
            )

    else:
        cobertura_garantia = None
        observaciones.append(
            "No se puede evaluar la cobertura: "
            "falta un valor estimado de la propiedad mayor que cero."
        )

    if firma_codeudor == "Seleccione":
        observaciones.append(
            "Está pendiente indicar si firma con codeudor."
        )

    elif firma_codeudor == "Sí":
        if not nombre_codeudor or not cedula_codeudor:
            observaciones.append(
                "Debe completar el nombre y la cédula del codeudor."
            )

    observaciones_garantia = "\n".join(observaciones)

    # Actualiza el contenido automáticamente en cada cálculo.
    clave_observaciones = (
        f"fex_hip1_observaciones_{cedula_consulta}"
    )
    st.session_state[clave_observaciones] = observaciones_garantia

    if observaciones_garantia:
        st.text_area(
            "Observaciones sobre la garantía",
            key=clave_observaciones,
            height=180,
            disabled=True,
        )

# ============================================================
# GARANTÍA — HIPOTECA EN SEGUNDO GRADO
# ============================================================

elif tipo_garantia_id == 2:
    st.subheader("Datos de la propiedad")

    provincia_garantia = st.text_input(
        "Provincia",
        key=f"fex_hip2_provincia_{cedula_consulta}",
    ).strip()

    canton_garantia = st.text_input(
        "Cantón",
        key=f"fex_hip2_canton_{cedula_consulta}",
    ).strip()

    distrito_garantia = st.text_input(
        "Distrito",
        key=f"fex_hip2_distrito_{cedula_consulta}",
    ).strip()

    numero_finca = st.text_input(
        "Número de finca",
        key=f"fex_hip2_finca_{cedula_consulta}",
    ).strip()

    acreedor_primer_grado = st.text_input(
        "Acreedor de la hipoteca en primer grado",
        key=f"fex_hip2_acreedor_{cedula_consulta}",
    ).strip()

    saldo_primer_grado = st.number_input(
        "Saldo de la hipoteca en primer grado (₡)",
        min_value=0.0,
        step=100000.0,
        format="%.2f",
        key=f"fex_hip2_saldo_{cedula_consulta}",
    )

    valor_propiedad = st.number_input(
        "Valor estimado de la propiedad (₡)",
        min_value=0.0,
        step=100000.0,
        format="%.2f",
        key=f"fex_hip2_valor_{cedula_consulta}",
    )

    firma_codeudor = st.selectbox(
        "¿Firma con codeudor?",
        options=["Seleccione", "Sí", "No"],
        key=f"fex_hip2_codeudor_{cedula_consulta}",
    )

    nombre_codeudor = ""
    cedula_codeudor = ""

    if firma_codeudor == "Sí":
        nombre_codeudor = st.text_input(
            "Nombre completo del codeudor",
            key=f"fex_hip2_nombre_codeudor_{cedula_consulta}",
        ).strip()

        cedula_codeudor = st.text_input(
            "Cédula del codeudor",
            key=f"fex_hip2_cedula_codeudor_{cedula_consulta}",
        ).strip()

    observaciones = []
    cobertura_garantia = None
    valor_residual_propiedad = None

    campos_propiedad = {
        "provincia": provincia_garantia,
        "cantón": canton_garantia,
        "distrito": distrito_garantia,
        "número de finca": numero_finca,
        "acreedor de primer grado": acreedor_primer_grado,
    }

    faltantes = [
        nombre
        for nombre, valor in campos_propiedad.items()
        if not valor
    ]

    if faltantes:
        observaciones.append(
            "Datos pendientes: "
            + ", ".join(faltantes)
            + "."
        )

    if valor_propiedad <= 0:
        observaciones.append(
            "No se puede evaluar la cobertura: "
            "falta un valor estimado de la propiedad mayor que cero."
        )

    else:
        valor_residual_propiedad = (
            valor_propiedad - saldo_primer_grado
        )

        st.metric(
            "Valor residual de la propiedad",
            f"₡{valor_residual_propiedad:,.2f}",
        )

        if valor_residual_propiedad <= 0:
            observaciones.append(
                "El saldo de la primera hipoteca es igual o superior "
                "al valor estimado de la propiedad. "
                "No existe valor residual positivo para respaldar "
                "el crédito en segundo grado."
            )

        else:
            cobertura_garantia = (
                monto_credito_fex / valor_residual_propiedad
            )

            monto_maximo_garantia = (
                valor_residual_propiedad * 0.80
            )

            st.metric(
                "Relación crédito / valor residual de la propiedad",
                f"{cobertura_garantia:.2%}",
            )

            st.metric(
                "80 % del valor residual",
                f"₡{monto_maximo_garantia:,.2f}",
            )

            if monto_credito_fex > monto_maximo_garantia:
                observaciones.append(
                    f"El monto total del crédito "
                    f"(₡{monto_credito_fex:,.2f}) supera el 80 % "
                    f"del valor residual de la propiedad "
                    f"(₡{monto_maximo_garantia:,.2f}). "
                    "No cumple el límite de cobertura establecido."
                )

    if firma_codeudor == "Seleccione":
        observaciones.append(
            "Está pendiente indicar si firma con codeudor."
        )

    elif firma_codeudor == "Sí":
        if not nombre_codeudor or not cedula_codeudor:
            observaciones.append(
                "Debe completar el nombre y la cédula del codeudor."
            )

    observaciones_garantia = "\n".join(observaciones)

    clave_observaciones = (
        f"fex_hip2_observaciones_{cedula_consulta}"
    )
    st.session_state[clave_observaciones] = observaciones_garantia

    if observaciones_garantia:
        st.text_area(
            "Observaciones sobre la garantía",
            key=clave_observaciones,
            height=180,
            disabled=True,
        )


# ============================================================
# NAVEGACIÓN
# ============================================================

st.divider()

if st.button(
    "⬅️ Volver a 19 – Hechos relevantes",
    use_container_width=True,
):
    st.switch_page("pages/19_Hechos_relevantes.py")
