# ==========================================
# Página 19 — Análisis IA de gestiones de cobro
# ==========================================

import streamlit as st
import pyodbc
import pandas as pd

st.set_page_config(
    page_title="Paso 19: Análisis de gestiones de cobro",
    page_icon="📞"
)

st.title("📞 Paso 19 — Análisis de comportamiento de pago (Cobranza)")

# ==============================
# FUNCIÓN CONEXIÓN SQL
# ==============================

def get_connection():
    return pyodbc.connect(
        f"DRIVER={{{st.secrets['azure_sql']['driver']}}};"
        f"SERVER={st.secrets['azure_sql']['server']};"
        f"DATABASE={st.secrets['azure_sql']['database']};"
        f"UID={st.secrets['azure_sql']['username']};"
        f"PWD={st.secrets['azure_sql']['password']};"
        "TrustServerCertificate=yes;"
    )

# ==============================
# INPUT OPERACIÓN
# ==============================

numero_operacion = st.text_input("Número de operación a analizar *")

# ==============================
# BOTÓN CARGAR HISTORIAL
# ==============================

if st.button("📊 Cargar historial de gestiones"):

    if not numero_operacion:
        st.error("Debe indicar el número de operación")
        st.stop()

    try:

        conn = get_connection()
        cursor = conn.cursor()

        query = """
        SELECT
            GestionID,
            NumeroOperacion,
            FechaGestion,
            DescripcionGestion,
            UsuarioGestion,
            TipoGestion,
            ResultadoContacto,
            PromesaPago,
            FechaPromesaPago,
            MontoPromesaPago,
            FechaCuotaMasAntigua,
            DiasAtraso,
            MontoAtraso,
            TipoContactoCobranza,

            DATEDIFF(DAY, FechaCuotaMasAntigua, FechaGestion) AS AntiguedadMoraGestion,

            CASE 
                WHEN DiasAtraso >= 60 THEN 'MORA_SEVERA'
                WHEN DiasAtraso >= 30 THEN 'MORA_MEDIA'
                WHEN DiasAtraso >= 8 THEN 'MORA_LEVE'
                ELSE 'AL_DIA'
            END AS NivelMora

        FROM GestionesCobranza
        WHERE NumeroOperacion = ?
        ORDER BY FechaGestion ASC
        """

        cursor.execute(query, numero_operacion)
        rows = cursor.fetchall()

        if not rows:
            st.warning("No existen gestiones registradas para esta operación.")
            st.stop()

        df = pd.DataFrame.from_records(rows, columns=[c[0] for c in cursor.description])

        conn.close()

        # ==============================
        # MOSTRAR TABLA CRONOLÓGICA
        # ==============================

        st.subheader("📋 Historial cronológico de gestiones")
        st.dataframe(df, use_container_width=True)

        # ==============================
        # RESUMEN CONDUCTUAL AUTOMÁTICO
        # ==============================

        total_gestiones = len(df)

        sin_contacto = df["ResultadoContacto"].astype(str).str.contains("No", na=False).sum()
        porc_sin_contacto = round((sin_contacto / total_gestiones) * 100, 1)

        mora_max = df["DiasAtraso"].max()
        mora_prom = round(df["DiasAtraso"].mean(),1)

        promesas = df["PromesaPago"].astype(str).str.contains("Si", na=False).sum()

        mora_severa = df[df["NivelMora"]=="MORA_SEVERA"].shape[0]

        ultimo_nivel = df.iloc[-1]["NivelMora"]

        df["MesGestion"] = pd.to_datetime(df["FechaGestion"]).dt.to_period("M")
        intensidad = round(df.groupby("MesGestion").size().mean(),1)

        st.subheader("📊 Resumen conductual automático")

        col1,col2,col3,col4 = st.columns(4)

        col1.metric("Total gestiones", total_gestiones)
        col2.metric("% sin contacto", porc_sin_contacto)
        col3.metric("Mora máxima", mora_max)
        col4.metric("Mora promedio", mora_prom)

        col5,col6,col7,col8 = st.columns(4)

        col5.metric("Promesas de pago", promesas)
        col6.metric("Gestiones en mora severa", mora_severa)
        col7.metric("Último nivel mora", ultimo_nivel)
        col8.metric("Intensidad cobranza", intensidad)

        # guardar dataframe en sesión para IA futura
        st.session_state["df_cobranza"] = df

    except Exception as e:
        st.error(f"Error cargando historial: {e}")
