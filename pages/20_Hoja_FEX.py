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
# NAVEGACIÓN
# ============================================================

st.divider()

if st.button(
    "⬅️ Volver a 19 – Hechos relevantes",
    use_container_width=True,
):
    st.switch_page("pages/19_Hechos_relevantes.py")
