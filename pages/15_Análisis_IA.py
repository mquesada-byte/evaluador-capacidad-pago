# pages/15_Analisis_IA.py
import os
import io
import datetime as dt
import streamlit as st
import pandas as pd  # opcional, por si lo necesitás más adelante

st.set_page_config(page_title="Paso 15: Análisis asistido (IA)", page_icon="🤖")

st.title("🤖 Paso 15: Análisis asistido (IA)")
st.caption("Resumen y recomendación automática a partir de TODA la información consolidada en `reporte`.")

# ====== Helpers ======
def _num(x):
    try:
        if x is None: return 0.0
        return float(str(x).replace(",", "").replace("₡", "").strip())
    except Exception:
        return 0.0

def _fmt_col(x):
    try:
        return f"₡ {int(round(_num(x))):,}".replace(",", ".")
    except Exception:
        return "₡ 0"

def _mk_prompt(rep: dict, tono: str) -> str:
    er = rep.get("estado_resultados", {}) or {}
    bg = rep.get("balance_general", {}) or {}
    deudas = rep.get("deudas_activas", {}).get("totales", {}) or {}

    ventas = er.get("ventas_colones")
    utilidad_neta_ope = er.get("utilidad_neta_operativa_colones")
    otros = er.get("otros_ingresos_colones")
    gastos_fam = er.get("gastos_familiares_colones")
    deudas_mens = er.get("pago_de_deudas_colones") or deudas.get("total_pago_mensual_colones")
    disponible = er.get("disponible_para_prestamo_colones")

    pasivo_circ = ((bg.get("pasivo") or {}).get("pasivo_circulante") or {}).get("total_pasivo_circulante")
    pasivo_largo = (bg.get("pasivo") or {}).get("pasivo_largo_plazo")
    patrimonio = bg.get("patrimonio")
    capital_trabajo = bg.get("capital_trabajo")

    return f"""
Eres analista senior de crédito en microfinanzas. Con tono **{tono.lower()}**, realiza un **análisis de capacidad de pago** y **riesgos** con estos datos (valores mensuales y totales):

- Ventas: {ventas}
- Utilidad neta operativa: {utilidad_neta_ope}
- Otros ingresos: {otros}
- Gastos familiares: {gastos_fam}
- Cuota total de deudas vigentes: {deudas_mens}
- Disponible final para el préstamo: {disponible}

- Pasivo circulante: {pasivo_circ}
- Pasivo a largo plazo: {pasivo_largo}
- Patrimonio: {patrimonio}
- Capital de trabajo: {capital_trabajo}

Entrega la respuesta en **Markdown** con estas secciones:
1) Fortalezas del negocio (viñetas)
2) Riesgos / banderas rojas (viñetas)
3) Lectura financiera (2–3 párrafos)
4) Capacidad de pago y holgura (cálculos simples con los datos)
5) Recomendación (monto sugerido, plazo y ratio cuota/ingreso objetivo)
6) Pendientes de verificación (checklist breve)
Concluye con un párrafo final de criterio del analista.
    """.strip()

def _fallback_local(rep: dict) -> str:
    er = rep.get("estado_resultados", {}) or {}
    disponible = _num(er.get("disponible_para_prestamo_colones") or 0)
    ventas = _num(er.get("ventas_colones") or 0)
    ratio = (disponible / ventas) if ventas > 0 else 0.0
    sug_cuota_30 = int(disponible * 0.30)
    sug_cuota_35 = int(disponible * 0.35)
    return f"""
## Fortalezas
- Flujo disponible estimado: {_fmt_col(disponible)}
- Ventas declaradas: {_fmt_col(ventas)}

## Riesgos / banderas
- Este análisis es básico porque no se pudo contactar a la API de OpenAI.
- Verificar evidencia documental y consistencias.

## Lectura financiera
El negocio muestra un disponible mensual de {_fmt_col(disponible)}. La relación disponible/ventas es {ratio:.0%}.
Consolidar documentación y validar estacionalidad.

## Capacidad de pago
Como referencia, una cuota objetivo del 30–35% del disponible sería {_fmt_col(sug_cuota_30)} a {_fmt_col(sug_cuota_35)}.

## Recomendación
- Monto y plazo a definir según política interna; mantener ratio cuota/ingreso ≤ 35%.

## Pendientes de verificación
- [ ] Confirmar registros/evidencia
- [ ] Revisión de burós
- [ ] Validar inventarios y pasivos operativos

**Criterio del analista:** sujeto a verificación de evidencias y política vigente.
""".strip()

def _pdf_from_md(md_text: str) -> bytes:
    """Convierte un markdown simple en PDF (texto plano estilizado) y devuelve bytes."""
    try:
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.pagesizes import LETTER
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.lib import colors

        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=LETTER,
            leftMargin=40, rightMargin=40, topMargin=48, bottomMargin=36
        )

        # Registrar fuente con tildes (si está disponible)
        try:
            pdfmetrics.registerFont(TTFont("DejaVu", "DejaVuSans.ttf"))
            font_name = "DejaVu"
        except Exception:
            font_name = "Helvetica"

        styles = getSampleStyleSheet()
        # ⚠️ Usamos nombres únicos para no chocar con estilos ya existentes
        styles.add(ParagraphStyle(
            name="CustomBody",
            fontName=font_name,
            fontSize=10.5,
            leading=14,
            textColor=colors.black
        ))
        styles.add(ParagraphStyle(
            name="CustomTitle",
            fontName=font_name,
            fontSize=15,
            leading=19,
            spaceAfter=12,
            textColor=colors.black
        ))

        story = []
        story.append(Paragraph("Análisis asistido (IA)", styles["CustomTitle"]))
        story.append(Paragraph(dt.datetime.now().strftime("%d/%m/%Y %H:%M"), styles["CustomBody"]))
        story.append(Spacer(1, 10))

        # Render muy simple de MD
        for raw in md_text.split("\n"):
            line = raw.strip()
            if not line:
                story.append(Spacer(1, 6))
                continue
            # Limpieza mínima para **negritas**
            line = line.replace("**", "").replace("__", "")
            story.append(Paragraph(line, styles["CustomBody"]))

        doc.build(story)
        pdf_bytes = buf.getvalue()
        buf.close()
        return pdf_bytes
    except Exception as e:
        st.warning("No se pudo generar el PDF. Verificá que `reportlab` esté instalado y (opcionalmente) `DejaVuSans.ttf`.")
        st.exception(e)
        return b""


def _get_openai_key():
    # Prioriza st.secrets, luego variables de entorno comunes
    candidates = []
    try:
        if hasattr(st, "secrets"):
            for k in ["OPENAI_API_KEY", "openai_api_key", "OPENAI_KEY"]:
                if k in st.secrets:
                    candidates.append(st.secrets[k])
    except Exception:
        pass
    for envk in ["OPENAI_API_KEY", "openai_api_key", "OPENAI_KEY"]:
        if os.getenv(envk):
            candidates.append(os.getenv(envk))
    return next((c for c in candidates if c), None)

def _call_openai_chat(model: str, system_prompt: str, user_prompt: str, api_key: str) -> str:
    """

    Llama a la API de OpenAI (>=1.0.0) y devuelve el contenido en Markdown.
    """
    from openai import OpenAI
    client = OpenAI(api_key=api_key)

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
    )
    return resp.choices[0].message.content

# ====== Carga del reporte consolidado ======
reporte = st.session_state.get("reporte", {}) or {}
if not reporte:
    st.warning("No se encontró información previa en memoria (`st.session_state['reporte']`). Volvé al Paso 14 y generá el informe.")
    st.stop()

# ====== Test de API Key ======
api_key_test = _get_openai_key()
if api_key_test:
    st.info(f"✅ API Key detectada. Empieza con: {api_key_test[:6]}... y tiene {len(api_key_test)} caracteres.")
else:
    st.error("❌ No se detectó ninguna API Key. Revisá que esté en st.secrets o en las variables de entorno.")

# ====== Test de conexión con OpenAI ======
try:
    from openai import OpenAI
    client = OpenAI(api_key=api_key_test)

    test_resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hola, ¿me recibes?"}],
        max_tokens=20,
    )
    st.success(f"✅ Conexión exitosa. OpenAI respondió: {test_resp.choices[0].message.content}")
except Exception as e:
    st.error(f"❌ Falló la conexión con OpenAI: {e}")



# ====== Opciones de la IA ======
with st.expander("Opciones de análisis IA"):
    modelo = st.selectbox("Modelo", ["gpt-4o-mini", "gpt-4o", "gpt-4.1"], index=0)
    tono = st.selectbox("Tono", ["Profesional", "Conciso", "Detallado"], index=0)
    ver_prompt = st.checkbox("Mostrar prompt generado", value=False)

# ====== Generación ======
col_g, col_d = st.columns([0.6, 0.4])

with col_g:
    if st.button("Generar análisis", type="primary", use_container_width=True):
        prompt = _mk_prompt(reporte, tono)
        if ver_prompt:
            with st.expander("Prompt utilizado"):
                st.code(prompt)

        api_key = _get_openai_key()
        try:
            if not api_key:
                raise RuntimeError("Falta OPENAI_API_KEY en st.secrets o variables de entorno.")

            md = _call_openai_chat(
                model=modelo,
                system_prompt="Eres analista senior de crédito en microfinanzas.",
                user_prompt=prompt,
                api_key=api_key,
            )
        except Exception:
            md = _fallback_local(reporte)

        st.session_state["analisis_ia_md"] = md
        st.session_state["analisis_ia_pdf_bytes"] = _pdf_from_md(md)
        st.success("Análisis generado.")

with col_d:
    pdf_bytes = st.session_state.get("analisis_ia_pdf_bytes", b"")
    if pdf_bytes:
        st.download_button(
            "📄 Descargar análisis (PDF)",
            data=pdf_bytes,
            file_name="analisis_ia.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

st.divider()
st.subheader("Resultado")
st.markdown(st.session_state.get("analisis_ia_md", "_Todavía no generaste el análisis._"))

# ====== Navegación ======
c1, c2 = st.columns([0.5, 0.5])
with c1:
    if st.button("⬅️ Volver a 14 – Informe final", use_container_width=True):
        try:
            st.switch_page("pages/14_Informe_final.py")
        except Exception:
            st.stop()
with c2:
    if st.button("Ir al inicio 🏠", use_container_width=True):
        try:
            st.switch_page("Home.py")
        except Exception:
            st.experimental_rerun()

