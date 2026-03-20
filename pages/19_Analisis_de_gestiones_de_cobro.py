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
        mora_prom = round(df["DiasAtraso"].mean(), 1)
        
        promesas = df["PromesaPago"].astype(str).str.contains("Si", na=False).sum()
        
        mora_severa = df[df["NivelMora"] == "MORA_SEVERA"].shape[0]
        
        ultimo_nivel = df.iloc[-1]["NivelMora"]
        
        df["MesGestion"] = pd.to_datetime(df["FechaGestion"]).dt.to_period("M")
        intensidad = round(df.groupby("MesGestion").size().mean(), 1)
        
        st.subheader("📊 Resumen conductual automático")
        
        col1, col2, col3, col4 = st.columns(4)
        
        col1.metric("Total gestiones", total_gestiones)
        col2.metric("% sin contacto", porc_sin_contacto)
        col3.metric("Mora máxima", mora_max)
        col4.metric("Mora promedio", mora_prom)
        
        col5, col6, col7, col8 = st.columns(4)
        
        col5.metric("Promesas de pago", promesas)
        col6.metric("Gestiones en mora severa", mora_severa)
        col7.metric("Último nivel mora", ultimo_nivel)
        
        interpretacion_intensidad = """
        🎯 Interpretación profesional del rango (microfinanzas)
        
        🟢 0 a 1  
        Cobranza normal / crédito sano  
        Cliente paga casi sin presión.  
        ✔ Riesgo bajo.
        
        🟡 1 a 3  
        Cobranza moderada  
        Cliente requiere seguimiento ocasional.  
        ✔ Riesgo medio manejable.
        
        🟠 3 a 6  
        Cobranza intensiva  
        Cliente paga de forma reactiva y necesita presión frecuente.  
        ✔ Riesgo medio-alto.
        
        🔴 Más de 6  
        Cobranza crítica  
        Dependencia total de presión para pagar.  
        ✔ Riesgo alto para recrédito.
        """
        
        col8.metric(
            "Intensidad cobranza",
            intensidad,
            help=interpretacion_intensidad
        )


        
        # ==============================
        # 6️⃣ ANÁLISIS IA COMPORTAMIENTO DE PAGO
        # ==============================
        
        import io
        from openai import OpenAI
        
        st.divider()
        st.subheader("🧠 Análisis automático del comportamiento de pago")
        
        if "df_cobranza" in st.session_state:
        
            if st.button("Analizar comportamiento de pago con IA"):
        
                try:
        
                    df = st.session_state["df_cobranza"]
        
                    texto_historial = ""
        
                    for _, row in df.iterrows():
                        texto_historial += f"""
        Fecha gestión: {row['FechaGestion']}
        Días atraso: {row['DiasAtraso']}
        Nivel mora: {row['NivelMora']}
        Resultado contacto: {row['ResultadoContacto']}
        Promesa pago: {row['PromesaPago']}
        Descripción: {row['DescripcionGestion']}
        -------------------------
        """
        
                    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        
                    prompt = f"""
        Actúas como JEFE DE RIESGO MICROFINANCIERO experto en análisis conductual de pago.
        
        Tu objetivo es determinar la calidad real del comportamiento de pago del cliente
        durante este ciclo crediticio específico.
        
        Debes analizar:
        
        1️⃣ DISCIPLINA DE PAGO  
        - cliente preventivo o reactivo  
        - tendencia a atrasarse  
        - gravedad de la mora alcanzada  
        
        2️⃣ REACCIÓN ANTE PRESIÓN  
        - paga solo cuando se le contacta  
        - evasión de contacto  
        - promesas incumplidas  
        
        3️⃣ DETERIORO O MEJORA  
        - evolución cronológica del riesgo  
        - estabilidad o desgaste financiero  
        
        4️⃣ CREDIBILIDAD FINANCIERA  
        - coherencia entre promesas y pagos  
        - responsabilidad frente a la deuda  
        
        5️⃣ PERFIL CONDUCTUAL FINAL  
        Clasificar como:
        
        EXCELENTE  
        ACEPTABLE  
        RIESGOSO  
        CRÍTICO  
        
        6️⃣ RECOMENDACIÓN DE RECRÉDITO  
        - monto sugerido (igual / menor / no recomendable)
        - necesidad de seguimiento
        - plazo prudente
        
        Historial de gestiones:
        
        {texto_historial[:18000]}
        """
        
                    with st.spinner("Analizando comportamiento de pago..."):
        
                        response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[
                                {"role": "system", "content": "Eres experto en riesgo microfinanciero."},
                                {"role": "user", "content": prompt}
                            ],
                            temperature=0.2
                        )
        
                    analisis = response.choices[0].message.content
        
                    st.success("Informe IA generado correctamente")
                    st.markdown(analisis)
        
                    # ==============================
                    # 📄 GENERAR PDF
                    # ==============================
        
                    pdf_bytes = generar_pdf_analisis(analisis, numero_operacion)
        
                    st.download_button(
                        label="📄 Descargar informe de comportamiento de pago",
                        data=pdf_bytes,
                        file_name=f"Informe_cobranza_{numero_operacion}.pdf",
                        mime="application/pdf"
                    )
        
                except Exception as e:
                    st.error(f"Error en análisis IA: {e}")


        
       #-------------------------------------------------------------------------------------------- 

        # guardar dataframe en sesión para IA futura
        st.session_state["df_cobranza"] = df

    except Exception as e:
        st.error(f"Error cargando historial: {e}")
