import logging
import math

import pymssql
import streamlit as st

# ============================================================
# PDF FEX — ENCABEZADO Y DATOS DEL CLIENTE
# ============================================================

def crear_encabezado_fex(
    nombre,
    cedula,
    numero_credito,
    sector,
    actividad,
    proposito,
    ancho=516,
):
    from xml.sax.saxutils import escape

    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

    estilo_titulo = ParagraphStyle(
        "fex_titulo",
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        alignment=1,
        spaceAfter=12,
        keepWithNext=True,
    )

    estilo_etiqueta = ParagraphStyle(
        "fex_etiqueta",
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        alignment=2,
    )

    estilo_valor = ParagraphStyle(
        "fex_valor",
        fontName="Helvetica",
        fontSize=9,
        leading=12,
    )

    def parrafo(valor, estilo):
        texto = str(valor).strip() if valor is not None else ""
        texto = texto or "Pendiente"
        return Paragraph(
            escape(texto).replace("\n", "<br/>"),
            estilo,
        )


    campos = [
        ("NOMBRE DEL CLIENTE", nombre),
        ("CÉDULA DEL CLIENTE", cedula),
        ("TIPO DE CRÉDITO", datos_credito["tipo_credito"]),
        ("CRÉDITO NÚMERO", numero_credito),
        ("SECTOR PRODUCTIVO", sector),
        ("ACTIVIDAD PRINCIPAL", actividad),
        ("PROPÓSITO PRINCIPAL DEL PRÉSTAMO", proposito),
    ]

    
    filas = [
        [
            parrafo(etiqueta, estilo_etiqueta),
            parrafo(valor, estilo_valor),
        ]
        for etiqueta, valor in campos
    ]

    tabla = Table(
        filas,
        colWidths=[ancho * 0.40, ancho * 0.60],
        hAlign="CENTER",
    )

    tabla.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (0, -1), 12),
        ("RIGHTPADDING", (1, 0), (1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        (
            "LINEBELOW",
            (0, -1), (-1, -1),
            0.5,
            colors.HexColor("#D5DADD"),
        ),
    ]))

    return [
        Paragraph("HOJA DE APROBACIÓN", estilo_titulo),
        tabla,
        Spacer(1, 12),
    ]

# ============================================================
# PDF FEX — GARANTÍA DEL CRÉDITO
# ============================================================

def crear_garantia_fex(
    tipo_garantia,
    detalles,
    advertencias,
    ancho=516,
):
    from xml.sax.saxutils import escape

    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

    titulo = ParagraphStyle(
        "garantia_titulo",
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        alignment=1,
        spaceBefore=10,
        spaceAfter=8,
        keepWithNext=True,
    )

    etiqueta = ParagraphStyle(
        "garantia_etiqueta",
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        alignment=2,
    )

    valor = ParagraphStyle(
        "garantia_valor",
        fontName="Helvetica",
        fontSize=9,
        leading=12,
    )

    advertencia = ParagraphStyle(
        "garantia_advertencia",
        parent=valor,
        textColor=colors.HexColor("#9C3024"),
        spaceAfter=5,
    )

    def parrafo(texto, estilo):
        contenido = str(texto) if texto is not None else ""
        contenido = contenido.strip() or "Pendiente"
        contenido = (
            contenido.replace("₡", "CRC ")
            .replace("≤", "<=")
            .replace("≥", ">=")
        )
        return Paragraph(
            escape(contenido).replace("\n", "<br/>"),
            estilo,
        )

    campos = [("TIPO DE GARANTÍA", tipo_garantia)] + list(detalles)

    filas = [
        [
            parrafo(nombre, etiqueta),
            parrafo(contenido, valor),
        ]
        for nombre, contenido in campos
    ]

    tabla = Table(
        filas,
        colWidths=[ancho * 0.40, ancho * 0.60],
        hAlign="LEFT",
    )

    tabla.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (0, -1), 12),
        ("RIGHTPADDING", (1, 0), (1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))

    contenido = [
        Paragraph("GARANTÍA DEL CRÉDITO", titulo),
        tabla,
        Spacer(1, 8),
    ]

    if advertencias and advertencias.strip():
        contenido.append(
            Paragraph("ADVERTENCIAS AUTOMÁTICAS", titulo)
        )

        for linea in advertencias.splitlines():
            if linea.strip():
                contenido.append(
                    parrafo(linea, advertencia)
                )

    contenido.append(Spacer(1, 8))

    return contenido



# ============================================================
# PDF FEX — ESTADOS FINANCIEROS Y RATIOS
# ============================================================

def crear_finanzas_fex(filas_er, filas_bg, indicadores, ancho=516):
    from xml.sax.saxutils import escape

    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

    estilo_texto = ParagraphStyle(
        "finanzas_texto",
        fontName="Helvetica",
        fontSize=8,
        leading=10,
    )

    estilo_numero = ParagraphStyle(
        "finanzas_numero",
        parent=estilo_texto,
        alignment=2,
    )

    estilo_negrita = ParagraphStyle(
        "finanzas_negrita",
        parent=estilo_texto,
        fontName="Helvetica-Bold",
    )

    estilo_titulo = ParagraphStyle(
        "finanzas_titulo",
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        alignment=1,
        spaceBefore=10,
        spaceAfter=8,
        keepWithNext=True,
    )

    def parrafo(valor, estilo=None):
        texto = "Sin información" if valor is None else str(valor)
        texto = (
            texto.replace("₡", "")
            .replace("≤", "<=")
            .replace("≥", ">=")
        )
        return Paragraph(
            escape(texto).replace("\n", "<br/>"),
            estilo or estilo_texto,
        )

    def aplicar_estilo(tabla):
        tabla.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            (
                "BACKGROUND",
                (0, 0), (-1, 0),
                colors.HexColor("#EDF1F3"),
            ),
            (
                "LINEBELOW",
                (0, 0), (-1, -1),
                0.3,
                colors.HexColor("#D5DADD"),
            ),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        return tabla

    def crear_estado(titulo, filas, campo_monto, ancho_tabla):
        contenido = [[
            parrafo(titulo, estilo_negrita),
            parrafo("Colones", estilo_negrita),
        ]]

        for fila in filas:
            contenido.append([
                parrafo(fila["Concepto"]),
                parrafo(fila[campo_monto], estilo_numero),
            ])

        return aplicar_estilo(Table(
            contenido,
            colWidths=[
                ancho_tabla * 0.67,
                ancho_tabla * 0.33,
            ],
            repeatRows=1,
            hAlign="LEFT",
        ))

    separacion = 16
    ancho_estado = (ancho - separacion) / 2

    resultados = crear_estado(
        "ESTADO DE RESULTADOS",
        filas_er,
        "Monto mensual",
        ancho_estado,
    )

    balance = crear_estado(
        "BALANCE GENERAL",
        filas_bg,
        "Monto",
        ancho_estado,
    )

    estados = Table(
        [[resultados, "", balance]],
        colWidths=[ancho_estado, separacion, ancho_estado],
        hAlign="LEFT",
    )

    estados.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    filas_ratios = [[
        parrafo("Indicador", estilo_negrita),
        parrafo("Resultado", estilo_negrita),
        parrafo("Evaluación", estilo_negrita),
    ]]

    for indicador in indicadores:
        filas_ratios.append([
            parrafo(indicador["indicador"]),
            parrafo(indicador["resultado"], estilo_numero),
            parrafo(indicador["evaluacion"]),
        ])

    ratios = aplicar_estilo(Table(
        filas_ratios,
        colWidths=[ancho * 0.52, ancho * 0.18, ancho * 0.30],
        repeatRows=1,
        hAlign="LEFT",
    ))

    return [
        Paragraph("ESTADOS FINANCIEROS", estilo_titulo),
        parrafo("Importes en colones. Estado de resultados mensual."),
        Spacer(1, 6),
        estados,
        Paragraph("INDICADORES FINANCIEROS", estilo_titulo),
        ratios,
        Spacer(1, 6),
        parrafo(
            "El DSCR considera las deudas existentes y no incluye "
            "la cuota del nuevo crédito. Las evaluaciones no "
            "equivalen a una aprobación."
        ),
        Spacer(1, 12),
    ]

# ============================================================
# PDF FEX — GENERACIÓN DEL DOCUMENTO
# ============================================================

def generar_pdf_fex(datos):
    from io import BytesIO

    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate

    archivo = BytesIO()

    documento = SimpleDocTemplate(
        archivo,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
        title="Hoja de aprobación",
        author="Asociación Credimujer",
    )

    contenido = crear_encabezado_fex(
        nombre=datos["nombre"],
        cedula=datos["cedula"],
        numero_credito=datos["numero_credito"],
        sector=datos["sector"],
        actividad=datos["actividad"],
        proposito=datos["proposito"],
        ancho=documento.width,
    )

    contenido.extend(
        crear_garantia_fex(
            tipo_garantia=tipos_garantia.get(
                tipo_garantia_id,
                "Pendiente de seleccionar",
            ),
            detalles=[],
            advertencias=observaciones_garantia,
            ancho=documento.width,
        )
    )
    
    if (
        datos.get("filas_er")
        and datos.get("filas_bg")
        and datos.get("indicadores")
    ):
        contenido.extend(
            crear_finanzas_fex(
                filas_er=datos["filas_er"],
                filas_bg=datos["filas_bg"],
                indicadores=datos["indicadores"],
                ancho=documento.width,
            )
        )


    # ========================================================
    # PDF FEX — CONDICIONES DEL CRÉDITO
    # ========================================================

    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

    titulo_condiciones = ParagraphStyle(
        "fex_titulo_condiciones",
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        alignment=1,
        spaceBefore=12,
        spaceAfter=8,
        keepWithNext=True,
    )

    etiqueta_condiciones = ParagraphStyle(
        "fex_etiqueta_condiciones",
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
    )

    valor_condiciones = ParagraphStyle(
        "fex_valor_condiciones",
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        alignment=2,
    )

    unidad_condiciones = ParagraphStyle(
        "fex_unidad_condiciones",
        fontName="Helvetica",
        fontSize=9,
        leading=12,
    )

    def importe_condiciones(valor):
        if valor is None:
            return "Pendiente"
        return f"{valor:,.2f}"

    monto_pdf = condiciones_fex.get("monto_total")
    plazo_pdf = condiciones_fex.get("plazo_meses")
    cuota_pdf = condiciones_fex.get("cuota_con_poliza")
    if cuota_pdf is not None:
        cuota_pdf = math.ceil(float(cuota_pdf))

    plazo_visible = (
        f"{plazo_pdf:,.0f}"
        if plazo_pdf is not None
        else "Pendiente"
    )

    filas_condiciones = [
        (
            "MONTO SOLICITADO TOTAL",
            importe_condiciones(monto_pdf),
            "Colones",
        ),
        (
            "PLAZO",
            plazo_visible,
            "Meses",
        ),
        (
            "CUOTA + INS",
            importe_condiciones(cuota_pdf),
            "Colones mensuales",
        ),
    ]

    tabla_condiciones = Table(
        [
            [
                Paragraph(etiqueta, etiqueta_condiciones),
                Paragraph(valor, valor_condiciones),
                Paragraph(unidad, unidad_condiciones),
            ]
            for etiqueta, valor, unidad in filas_condiciones
        ],
        colWidths=[
            documento.width * 0.45,
            documento.width * 0.25,
            documento.width * 0.30,
        ],
        hAlign="LEFT",
    )

    tabla_condiciones.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F3F5F7")),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    contenido.append(
        Paragraph("PROPUESTA DEL ANALISTA", titulo_condiciones)
    )
    contenido.append(tabla_condiciones)
    contenido.append(Spacer(1, 10))
    

    # ========================================================
    # PDF FEX — COMENTARIOS DEL ASESOR DE CRÉDITO
    # ========================================================

    from xml.sax.saxutils import escape

    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import Paragraph, Spacer

    estilo_titulo_comentarios = ParagraphStyle(
        "fex_titulo_comentarios",
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        spaceBefore=12,
        spaceAfter=8,
        keepWithNext=True,
    )

    estilo_comentarios = ParagraphStyle(
        "fex_texto_comentarios",
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        spaceAfter=6,
        backColor=colors.HexColor("#F3F5F7"),
        borderPadding=8,
        leftIndent=8,
        rightIndent=8,
        splitLongWords=True,
        allowWidows=0,
        allowOrphans=0,
    )

    contenido.append(
        Paragraph(
            "COMENTARIOS DEL ASESOR DE CRÉDITO",
            estilo_titulo_comentarios,
        )
    )

    comentarios_pdf = (
        observaciones_asesor_fex or ""
    ).strip()

    if not comentarios_pdf:
        comentarios_pdf = "Sin observaciones."

    for linea in comentarios_pdf.splitlines():
        if linea.strip():
            contenido.append(
                Paragraph(
                    escape(linea.strip()),
                    estilo_comentarios,
                )
            )
        else:
            contenido.append(Spacer(1, 6))

    contenido.append(Spacer(1, 8))
    
        # ========================================================
    # PDF FEX — NIVEL DE APROBACIÓN Y FIRMANTES
    # ========================================================

    from xml.sax.saxutils import escape

    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import (
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        KeepTogether,
    )

    titulo_firmas = ParagraphStyle(
        "fex_titulo_firmas",
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        alignment=1,
        spaceBefore=12,
        spaceAfter=8,
    )

    nombre_firma = ParagraphStyle(
        "fex_nombre_firma",
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=11,
        alignment=1,
    )

    texto_firmas = ParagraphStyle(
        "fex_texto_firmas",
        fontName="Helvetica",
        fontSize=8,
        leading=11,
    )

    bloque_firmas = [
        Paragraph("FIRMAS DE APROBACIÓN", titulo_firmas),
        Paragraph(
            f"Nivel de aprobación requerido: {nivel_aprobacion}.",
            texto_firmas,
        ),
        Paragraph(
            "La asignación de firmantes no implica que "
            "el crédito esté aprobado.",
            texto_firmas,
        ),
        Spacer(1, 10),
    ]

    separacion_firmas = 30
    ancho_firma = (
        documento.width - separacion_firmas
    ) / 2

    for inicio in range(0, len(firmantes_fex), 2):
        nombres = firmantes_fex[inicio:inicio + 2]

        nombre_izquierdo = nombres[0]
        nombre_derecho = nombres[1] if len(nombres) > 1 else ""

        tabla_firmas = Table(
            [
                ["", "", ""],
                [
                    Paragraph(
                        escape(nombre_izquierdo),
                        nombre_firma,
                    ),
                    "",
                    Paragraph(
                        escape(nombre_derecho),
                        nombre_firma,
                    ) if nombre_derecho else "",
                ],
            ],
            colWidths=[
                ancho_firma,
                separacion_firmas,
                ancho_firma,
            ],
            rowHeights=[45, None],
            hAlign="LEFT",
        )

        estilo_tabla_firmas = [
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 1), (-1, 1), 6),
            ("BOTTOMPADDING", (0, 1), (-1, 1), 6),
            ("LINEBELOW", (0, 0), (0, 0), 0.6, colors.black),
        ]

        if nombre_derecho:
            estilo_tabla_firmas.append(
                ("LINEBELOW", (2, 0), (2, 0), 0.6, colors.black)
            )

        tabla_firmas.setStyle(
            TableStyle(estilo_tabla_firmas)
        )

        bloque_firmas.append(tabla_firmas)
        bloque_firmas.append(Spacer(1, 12))

    bloque_firmas.append(
        Paragraph(
            "FECHA DE APROBACIÓN: __________________________",
            texto_firmas,
        )
    )

    contenido.append(KeepTogether(bloque_firmas))
    
    documento.build(contenido)
    return archivo.getvalue()


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
# GARANTÍA — HIPOTECA EN PRIMER GRADO O CÉDULA HIPOTECARIA
# ============================================================

observaciones_garantia = ""

if tipo_garantia_id in (1, 3):
    
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
# GARANTÍA — FIANZA
# ============================================================

elif tipo_garantia_id == 4:
    st.subheader("Datos del fiador")

    nombre_fiador = st.text_input(
        "Nombre completo del fiador",
        key=f"fex_fianza_nombre_{cedula_consulta}",
    ).strip()

    cedula_fiador = st.text_input(
        "Cédula del fiador",
        key=f"fex_fianza_cedula_{cedula_consulta}",
    ).strip()

    salario_bruto_fiador = st.number_input(
        "Salario bruto mensual del fiador (₡)",
        min_value=0.0,
        step=10000.0,
        format="%.2f",
        key=f"fex_fianza_salario_{cedula_consulta}",
    )

    observaciones = []
    cobertura_garantia = None

    if not nombre_fiador:
        observaciones.append(
            "Está pendiente el nombre completo del fiador."
        )

    if not cedula_fiador:
        observaciones.append(
            "Está pendiente la cédula del fiador."
        )

    tipo_credito_actual = datos_credito["tipo_credito"]

    if tipo_credito_actual == "Nuevo":
        cobertura_minima = 0.40

    elif tipo_credito_actual in ("Recrédito", "Anterior"):
        cobertura_minima = 0.30

    else:
        cobertura_minima = None
        observaciones.append(
            "No se puede determinar la cobertura mínima: "
            "el tipo de crédito requiere revisión."
        )

    if salario_bruto_fiador <= 0:
        observaciones.append(
            "No se puede evaluar la cobertura: "
            "falta un salario bruto del fiador mayor que cero."
        )

    else:
        cobertura_garantia = (
            salario_bruto_fiador / monto_credito_fex
        )

        st.metric(
            "Relación salario bruto / monto total del crédito",
            f"{cobertura_garantia:.2%}",
        )

        if cobertura_minima is not None:
            salario_minimo_requerido = (
                monto_credito_fex * cobertura_minima
            )

            st.metric(
                "Cobertura mínima requerida",
                f"{cobertura_minima:.0%}",
            )

            if salario_bruto_fiador < salario_minimo_requerido:
                observaciones.append(
                    f"El salario bruto del fiador "
                    f"(₡{salario_bruto_fiador:,.2f}) es inferior "
                    f"al mínimo requerido de "
                    f"₡{salario_minimo_requerido:,.2f}, "
                    f"equivalente al {cobertura_minima:.0%} "
                    f"del monto total para un crédito "
                    f"clasificado como {tipo_credito_actual}. "
                    "No cumple la cobertura requerida."
                )

    observaciones_garantia = "\n".join(observaciones)

    clave_observaciones = (
        f"fex_fianza_observaciones_{cedula_consulta}"
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
# GARANTÍA — FIANZA MORAL
# ============================================================

elif tipo_garantia_id == 5:
    st.subheader("Datos del garante moral")

    nombre_garante_moral = st.text_input(
        "Nombre completo del garante moral",
        key=f"fex_moral_nombre_{cedula_consulta}",
    ).strip()

    cedula_garante_moral = st.text_input(
        "Cédula del garante moral",
        key=f"fex_moral_cedula_{cedula_consulta}",
    ).strip()

    observaciones = []
    cobertura_garantia = None

    if not nombre_garante_moral:
        observaciones.append(
            "Está pendiente el nombre completo del garante moral."
        )

    if not cedula_garante_moral:
        observaciones.append(
            "Está pendiente la cédula del garante moral."
        )

    tipo_credito_actual = datos_credito["tipo_credito"]

    # Límite definido en el flujo de RAPTOR.
    limite_primer_credito = 693000.0

    if tipo_credito_actual == "Nuevo":
        if monto_credito_fex > limite_primer_credito:
            observaciones.append(
                f"El monto total del crédito "
                f"(₡{monto_credito_fex:,.2f}) supera el límite "
                f"de ₡{limite_primer_credito:,.2f} establecido "
                "en el flujo para un primer crédito "
                "con fianza moral."
            )

    elif tipo_credito_actual not in ("Recrédito", "Anterior"):
        observaciones.append(
            "No se puede evaluar el límite aplicable: "
            "el tipo de crédito requiere revisión."
        )

    observaciones_garantia = "\n".join(observaciones)

    clave_observaciones = (
        f"fex_moral_observaciones_{cedula_consulta}"
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
# GARANTÍA — SIN GARANTÍA
# ============================================================

elif tipo_garantia_id == 6:
    st.subheader("Crédito sin garantía")

    observaciones = []
    cobertura_garantia = None

    tipo_credito_actual = datos_credito["tipo_credito"]

    # Límite definido en el flujo de RAPTOR.
    limite_primer_credito = 693000.0

    if tipo_credito_actual == "Nuevo":
        if monto_credito_fex > limite_primer_credito:
            observaciones.append(
                f"El monto total del crédito "
                f"(₡{monto_credito_fex:,.2f}) supera el límite "
                f"de ₡{limite_primer_credito:,.2f} establecido "
                "en el flujo para un primer crédito "
                "sin garantía."
            )

    elif tipo_credito_actual not in ("Recrédito", "Anterior"):
        observaciones.append(
            "No se puede evaluar el límite aplicable: "
            "el tipo de crédito requiere revisión."
        )

    observaciones_garantia = "\n".join(observaciones)

    clave_observaciones = (
        f"fex_sin_garantia_observaciones_{cedula_consulta}"
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
# ESTADO DE RESULTADOS — VISTA PREVIA PARA LA FEX
# ============================================================

st.divider()

with st.expander("Estado de resultados", expanded=False):
    er_fex = (
        st.session_state.get("reporte", {})
        .get("estado_resultados", {})
        or {}
    )

    def normalizar_cedula_fex(valor):
        return (
            str(valor or "")
            .replace("-", "")
            .replace(" ", "")
            .strip()
        )

    cedula_resultados = normalizar_cedula_fex(
        er_fex.get("cliente_identificacion")
    )

    cedula_actual = normalizar_cedula_fex(
        cedula_consulta
    )

    if not er_fex or not cedula_resultados:
        st.warning(
            "Abrí el Paso 12 y presioná Continuar para "
            "preparar el Estado de resultados de este cliente."
        )

    elif cedula_resultados != cedula_actual:
        st.warning(
            "El Estado de resultados disponible corresponde "
            "a otro cliente. Actualizalo desde el Paso 12."
        )

    else:
        conceptos_er = [
            ("Ventas", "ventas_colones"),
            ("Compras / costos", "compras_costos_colones"),
            ("Utilidad bruta", "utilidad_bruta_colones"),
            ("Gastos operativos", "gastos_operativos_colones"),
            (
                "Utilidad neta operativa",
                "utilidad_neta_operativa_colones",
            ),
            ("Otros ingresos", "otros_ingresos_colones"),
            (
                "Subtotal después de otros ingresos",
                "subtotal_post_otros_colones",
            ),
            ("Gastos familiares", "gastos_familiares_colones"),
            ("Pago de deudas", "pago_de_deudas_colones"),
            (
                "Disponible para el préstamo",
                "disponible_para_prestamo_colones",
            ),
        ]

        filas_er = []
        faltantes_er = []

        for concepto, campo in conceptos_er:
            valor = er_fex.get(campo)

            if valor is None:
                monto_mostrar = "Sin información"
                faltantes_er.append(concepto)
            else:
                monto_mostrar = f"₡{valor:,.0f}"

            filas_er.append({
                "Concepto": concepto,
                "Monto mensual": monto_mostrar,
            })

        st.table(filas_er)

        if faltantes_er:
            st.warning(
                "Faltan datos: "
                + ", ".join(faltantes_er)
                + ". Revisá el Paso 12."
            )

        st.caption(
            "Información de solo lectura del último resultado "
            "enviado desde el Paso 12. Si modificaste datos "
            "anteriores, volvé a ese paso y presioná Continuar."
        )

# ============================================================
# BALANCE GENERAL — VISTA PREVIA PARA LA FEX
# ============================================================

with st.expander("Balance general", expanded=False):
    bg_fex = (
        st.session_state.get("reporte", {})
        .get("balance_general", {})
        or {}
    )

    cedula_balance = (
        str(bg_fex.get("cliente_identificacion") or "")
        .replace("-", "")
        .replace(" ", "")
        .strip()
    )

    cedula_actual_bg = (
        str(cedula_consulta or "")
        .replace("-", "")
        .replace(" ", "")
        .strip()
    )

    if not bg_fex or not cedula_balance:
        st.warning(
            "Abrí el Paso 13 y presioná Guardar y continuar "
            "para preparar el Balance General de este cliente."
        )

    elif cedula_balance != cedula_actual_bg:
        st.warning(
            "El Balance General disponible corresponde a otro "
            "cliente. Actualizalo desde el Paso 13."
        )

    else:
        totales_bg_fex = bg_fex.get("totales") or {}

        conceptos_bg = [
            ("Activo circulante", "activo_circulante"),
            ("Activo fijo neto", "activo_fijo"),
            ("Total activos", "total_activos"),
            ("Pasivo circulante", "pasivo_circulante"),
            ("Pasivo a largo plazo", "pasivo_largo"),
            ("Total pasivos", "total_pasivo"),
            ("Patrimonio", "patrimonio"),
            ("Capital de trabajo", "capital_trabajo"),
        ]

        filas_bg = []
        faltantes_bg = []

        for concepto, campo in conceptos_bg:
            valor = totales_bg_fex.get(campo)

            if valor is None:
                monto_mostrar = "Sin información"
                faltantes_bg.append(concepto)
            else:
                monto_mostrar = f"₡{valor:,.0f}"

            filas_bg.append({
                "Concepto": concepto,
                "Monto": monto_mostrar,
            })

        st.table(filas_bg)

        if faltantes_bg:
            st.warning(
                "Faltan datos: "
                + ", ".join(faltantes_bg)
                + ". Revisá el Paso 13."
            )

        st.caption(
            "Información de solo lectura del último balance "
            "guardado desde el Paso 13. Si modificaste datos "
            "anteriores, volvé a ese paso y presioná "
            "Guardar y continuar."
        )

# ============================================================
# INDICADORES FINANCIEROS — VISTA PREVIA PARA LA FEX
# ============================================================

with st.expander("Indicadores financieros", expanded=False):
    import math

    reporte_ratios = st.session_state.get("reporte") or {}
    er_ratios = reporte_ratios.get("estado_resultados") or {}
    bg_ratios = reporte_ratios.get("balance_general") or {}
    totales_ratios = bg_ratios.get("totales") or {}

    def cedula_ratio(valor):
        return (
            str(valor or "")
            .replace("-", "")
            .replace(" ", "")
            .strip()
        )

    def numero_ratio(valor):
        if valor is None:
            return None

        try:
            numero = float(
                str(valor)
                .replace("₡", "")
                .replace(",", "")
                .strip()
            )
            return numero if math.isfinite(numero) else None
        except (TypeError, ValueError):
            return None

    def dividir_ratio(numerador, denominador):
        if numerador is None or denominador is None:
            return None, "Sin información"

        if denominador <= 0:
            return None, "No calculable: denominador ≤ 0"

        return numerador / denominador, ""

    # Se reconstruye en cada ejecución para no conservar
    # resultados anteriores cuando faltan datos.
    indicadores_fex = []

    cliente_ratios = cedula_ratio(cedula_consulta)
    cliente_er = cedula_ratio(
        er_ratios.get("cliente_identificacion")
    )
    cliente_bg = cedula_ratio(
        bg_ratios.get("cliente_identificacion")
    )

    if (
        not cliente_ratios
        or cliente_er != cliente_ratios
        or cliente_bg != cliente_ratios
    ):
        st.warning(
            "Los indicadores requieren el Estado de resultados "
            "y el Balance General del cliente actual. "
            "Completá el Paso 12 con Continuar y el Paso 13 "
            "con Guardar y continuar."
        )

    else:
        ventas = numero_ratio(er_ratios.get("ventas_colones"))

        utilidad_operativa = numero_ratio(
            er_ratios.get("utilidad_neta_operativa_colones")
        )

        disponible = numero_ratio(
            er_ratios.get("disponible_para_prestamo_colones")
        )

        pago_deudas = numero_ratio(
            er_ratios.get("pago_de_deudas_colones")
        )

        gastos_familiares = numero_ratio(
            er_ratios.get("gastos_familiares_colones")
        )

        otros_ingresos = numero_ratio(
            er_ratios.get("otros_ingresos_colones")
        )

        activo_circulante = numero_ratio(
            totales_ratios.get("activo_circulante")
        )

        pasivo_circulante = numero_ratio(
            totales_ratios.get("pasivo_circulante")
        )

        total_activos = numero_ratio(
            totales_ratios.get("total_activos")
        )

        total_pasivos = numero_ratio(
            totales_ratios.get("total_pasivo")
        )

        patrimonio = numero_ratio(
            totales_ratios.get("patrimonio")
        )

        flujo_antes_deudas = (
            disponible + pago_deudas
            if disponible is not None and pago_deudas is not None
            else None
        )

        ingresos_base = (
            ventas + otros_ingresos
            if ventas is not None and otros_ingresos is not None
            else None
        )

        # Nombre, numerador, denominador, umbral positivo,
        # umbral intermedio, menor es mejor, mostrar en veces.
        definiciones_ratios = [
            (
                "Margen operativo",
                utilidad_operativa, ventas,
                0.20, 0.10, False, False,
            ),
            (
                "DSCR — deudas existentes",
                flujo_antes_deudas, pago_deudas,
                1.50, 1.00, False, True,
            ),
            (
                "Gastos familiares / (ventas + otros ingresos)",
                gastos_familiares, ingresos_base,
                0.30, 0.40, True, False,
            ),
            (
                "Razón circulante — AC / PC",
                activo_circulante, pasivo_circulante,
                1.50, 1.00, False, True,
            ),
            (
                "Apalancamiento — pasivos / patrimonio",
                total_pasivos, patrimonio,
                2.00, 3.00, True, True,
            ),
            (
                "Solvencia — patrimonio / activos",
                patrimonio, total_activos,
                0.40, 0.25, False, False,
            ),
        ]

        filas_ratios = []

        for (
            nombre,
            numerador,
            denominador,
            bueno,
            medio,
            menor_es_mejor,
            formato_veces,
        ) in definiciones_ratios:

            valor, motivo = dividir_ratio(
                numerador, denominador
            )

            if valor is None:
                valor_visible = "—"
                evaluacion = motivo
                estado_visible = f"⚪ {motivo}"

            else:
                valor_visible = (
                    f"{valor:.2f}x"
                    if formato_veces
                    else f"{valor:.2%}"
                )

                if menor_es_mejor:
                    if valor <= bueno:
                        evaluacion = "Positivo"
                    elif valor <= medio:
                        evaluacion = "Intermedio"
                    else:
                        evaluacion = "Negativo"
                else:
                    if valor >= bueno:
                        evaluacion = "Positivo"
                    elif valor >= medio:
                        evaluacion = "Intermedio"
                    else:
                        evaluacion = "Negativo"

                colores = {
                    "Positivo": "🟢",
                    "Intermedio": "🟡",
                    "Negativo": "🔴",
                }

                estado_visible = (
                    f"{colores[evaluacion]} {evaluacion}"
                )

            filas_ratios.append({
                "Indicador": nombre,
                "Resultado": valor_visible,
                "Evaluación": estado_visible,
            })

            # Datos estructurados para la futura impresión.
            indicadores_fex.append({
                "indicador": nombre,
                "valor": valor,
                "resultado": valor_visible,
                "evaluacion": evaluacion,
            })

        st.table(filas_ratios)

        st.caption(
            "Fórmulas y umbrales del Análisis IA. "
            "El DSCR considera las deudas existentes; "
            "no incluye la cuota del nuevo crédito. "
            "Los colores no equivalen a una aprobación."
        )

        st.caption(
            "Si cambiaste datos anteriores, actualizá los pasos "
            "12 y 13 para recalcular estos indicadores."
        )

# ============================================================
# PROPUESTA DEL ANALISTA — CONDICIONES DEL PASO 15
# ============================================================

st.divider()
st.subheader("Propuesta del analista")

campos_propuesta = {
    "Monto": "monto_total",
    "Plazo": "plazo_meses",
    "Cuota + INS": "cuota_con_poliza",
    "Tasa de interés": "tasa_interes_anual",
    "Comisión": "comision_pct",
    "TITA": "tita",
}

faltantes_propuesta = [
    nombre
    for nombre, campo in campos_propuesta.items()
    if condiciones_fex.get(campo) is None
]

if faltantes_propuesta:
    st.warning(
        "Faltan condiciones del crédito: "
        + ", ".join(faltantes_propuesta)
        + ". Volvé al Paso 15 y presioná Guardar y continuar."
    )

else:
    monto_propuesta = condiciones_fex["monto_total"]
    plazo_propuesta = condiciones_fex["plazo_meses"]
    cuota_propuesta = condiciones_fex["cuota_con_poliza"]
    tasa_propuesta = condiciones_fex["tasa_interes_anual"]
    comision_propuesta = condiciones_fex["comision_pct"]
    tita_propuesta = condiciones_fex["tita"]
    tita_limite_propuesta = condiciones_fex["tita_limite"]
    tita_tipo_limite_propuesta = condiciones_fex["tita_tipo_limite"]
    tita_estado_propuesta = condiciones_fex["tita_estado"]

    

    st.table([
        {
            "Condición": "Monto",
            "Valor": f"₡{monto_propuesta:,.0f}",
            "Unidad": "Colones",
        },
        {
            "Condición": "Plazo",
            "Valor": f"{plazo_propuesta:,.0f}",
            "Unidad": "Meses",
        },
        {
            "Condición": "Cuota + INS",
            "Valor": f"₡{cuota_propuesta:,.0f}",
            "Unidad": "Colones mensuales",
        },
                {
            "Condición": "Tasa de interés",
            "Valor": f"{tasa_propuesta:.2f}%",
            "Unidad": "Anual",
        },
        {
            "Condición": "Comisión",
            "Valor": f"{comision_propuesta:.2f}%",
            "Unidad": "Sobre el monto desembolsado",
        },
        {
            "Condición": "TITA",
            "Valor": f"{tita_propuesta:.2f}%",
            "Unidad": tita_estado_propuesta,
        },
    ])

    st.caption(
        "Condiciones guardadas en el Paso 15, de solo lectura. "
        "Para modificarlas, regresá a ese paso y guardá los cambios."
    )

# ============================================================
# OBSERVACIONES GENERALES DEL ASESOR DE CRÉDITO
# ============================================================

observaciones_asesor_fex = st.text_area(
    "Observaciones del asesor de crédito",
    height=150,
    placeholder="Indique las observaciones generales de la propuesta.",
    key=f"fex_observaciones_asesor_{cedula_consulta}",
)

# ============================================================
# NIVEL DE APROBACIÓN Y FIRMANTES
# Base: monto solicitado total del Paso 15
# ============================================================

monto_aprobacion = condiciones_fex["monto_total"]

if monto_aprobacion <= 750000:
    nivel_aprobacion = 1
    firmantes_fex = [
        "MAX QUESADA G.",
    ]

elif monto_aprobacion <= 3000000:
    nivel_aprobacion = 2
    firmantes_fex = [
        "MAX QUESADA G.",
        "LAURA CASTRO MORALES",
    ]

else:
    nivel_aprobacion = 3
    firmantes_fex = [
        "MAX QUESADA G.",
        "LAURA CASTRO MORALES",
        "JOSÉ RAFAEL BARRANTES C.",
        "HERNÁN SOLANO VEGA",
    ]

st.subheader("Nivel de aprobación y firmantes")

st.metric(
    "Nivel de aprobación requerido",
    f"Nivel {nivel_aprobacion}",
)

st.caption(
    f"Determinado por el monto solicitado total: "
    f"₡{monto_aprobacion:,.0f}. "
    "La asignación de firmantes no implica que el crédito esté aprobado."
)

for inicio in range(0, len(firmantes_fex), 2):
    columnas_firma = st.columns(2)

    for columna, nombre_firmante in zip(
        columnas_firma,
        firmantes_fex[inicio:inicio + 2],
    ):
        with columna:
            st.text("____________________________")
            st.write(nombre_firmante)

st.text("Fecha de aprobación: ____________________")

# ============================================================
# PDF FEX — DESCARGA CON ESTADOS FINANCIEROS Y RATIOS
# ============================================================

st.divider()
st.subheader("Vista de prueba de la Hoja FEX")

st.caption(
    "Incluye los datos del cliente, los estados financieros "
    "y los ratios. Todavía no es la Hoja FEX completa."
)


def normalizar_cedula_pdf(valor):
    return (
        str(valor or "")
        .replace("-", "")
        .replace(" ", "")
        .strip()
    )


cedula_pdf = normalizar_cedula_pdf(cedula_consulta)

resultados_correctos = (
    bool(er_fex)
    and bool(cedula_pdf)
    and normalizar_cedula_pdf(
        er_fex.get("cliente_identificacion")
    ) == cedula_pdf
)

balance_correcto = (
    bool(bg_fex)
    and bool(cedula_pdf)
    and normalizar_cedula_pdf(
        bg_fex.get("cliente_identificacion")
    ) == cedula_pdf
)

if not resultados_correctos:
    st.warning(
        "Actualizá el Estado de resultados de este cliente "
        "desde el Paso 12 antes de descargar el PDF."
    )

elif not balance_correcto:
    st.warning(
        "Actualizá el Balance general de este cliente "
        "desde el Paso 13 antes de descargar el PDF."
    )

elif faltantes_er or faltantes_bg:
    st.warning(
        "Hay importes sin información en los estados financieros. "
        "Completalos en los pasos 12 y 13 antes de descargar."
    )

elif not indicadores_fex:
    st.warning(
        "No están disponibles los indicadores financieros. "
        "Revisá los estados de resultados y balance general."
    )

else:
    datos_pdf = {
        "nombre": nombre_cliente,
        "cedula": cedula_mostrar,
        "numero_credito": datos_credito["numero_credito"],
        "sector": sectores_por_id.get(sector_id, ""),
        "actividad": actividad_principal_descripcion,
        "proposito": proposito_descripcion,
        "filas_er": filas_er,
        "filas_bg": filas_bg,
        "indicadores": indicadores_fex,
    }

    try:
        pdf_fex = generar_pdf_fex(datos_pdf)

    except ImportError as error:
        st.error("No se pudo cargar una librería necesaria.")
        st.code(
            f"{type(error).__name__}: {error}",
            language="text",
        )

    except Exception as error:
        logging.getLogger(__name__).exception(
            "Error generando el PDF de la Hoja FEX"
        )
        st.error("No se pudo generar el PDF.")
        st.code(
            f"{type(error).__name__}: {error}",
            language="text",
        )

    else:
        st.download_button(
            label="📄 Descargar prueba de la Hoja FEX",
            data=pdf_fex,
            file_name="FEX_prueba_estados_financieros.pdf",
            mime="application/pdf",
            key="fex_descarga_prueba",
            use_container_width=True,
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
