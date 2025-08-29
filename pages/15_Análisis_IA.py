# pages/15_Analisis_IA.py
import os
import datetime as dt
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Paso 15: Análisis asistido (IA)", page_icon="🤖")

st.title("🤖 Paso 15: Análisis asistido (IA)")
st.caption("Resumen y recomendación automática a partir del informe final y el balance.")

# ====== Helpers ======
def _fmt_col(x):
    try:
        return f"₡ {int(round(float(str(x).replace(',', '').replace('₡', '').strip() or 0))):,}".replace(",", ".")
    except Exception:
        return "₡ 0"

def _mk_prompt(rep: dict) -> str:
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
Eres un analista de crédito microfinanzas. Con un tono profesional y claro,
haz un **análisis de capacidad de pago** y **riesgos** con estos datos (valores mensuales y totales):

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

Entrega el resultado en **Markdown** con estas secciones:
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
    disponible = er.get("disponible_para_prestamo_colones") or 0
    ventas = er.get("ventas_colones") or 0
    ratio = (float(disponible) / float(ventas)) if (ventas and float(ventas) > 0) else 0.0
    sug_cuota = max(0, int((disponible or 0) * 0.35))
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
Como referencia, una cuota objetivo del 30–35% del disponible sería {_fmt_col(int((disponible or 0)*0.30))} a {_fmt_col(int((disponible or 0)*0.35))}.

## Recomendación
- Monto y plazo a definir según política interna; cuota sugerida aprox.: **{_fmt_col(sug_cuota)}**.
- Mantener ratio cuota/ingreso ≤ 35%.

## Pendientes de verificación
- [ ] Confirmar registros/evidencia
- [ ] Revisión de burós
- [ ] Validar inventarios y pasivos operativos

**Criterio del analista:** sujeto a verificación de evidencias y política vigente.
""".strip()

def _save_pdf(md_text: str, filename: str = "analisis_ia.pdf"):
    try:
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.pagesizes import LETTER
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        # Fuente con tildes (si está en el repo). Si falla, usa Helvetica.
        try:
            pdfmetrics.registerFont(TTFont("DejaVu", "DejaVuSans.ttf"))
            font_name = "DejaVu"
        except Exception:
            font_name = "Helvetica"

        doc = SimpleDocTemplate(filename, pagesize=LETTER, leftMargin=40, rightMargin=40, topMargin=48, bottomMargin=36)
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name="Body", fontName=font_name, fontSize=10.5, leading=14))
        styles.add(ParagraphStyle(name="Title", fontName=font_name, fontSize=15, leading=19, spaceAfter=12))

        story = []
        story.append(Paragraph("Análisis asistido (IA)", styles["Title"]))
        story.append(Paragraph(dt.datetime.now().strftime("%d/%m/%Y %H:%M"), styles["Body"]))
        story.append(Spacer(1, 10))

        # Convierte el Markdown simple a párrafos (sin render completo de MD).
        for line in md_text.split("\n"):
            if not line.strip():
                story.append(Spacer(1, 6))
                continue
            # Reemplazo mínimo para títulos/viñetas
            line = line.replace("**", "").replace("__", "")
            story.append(Paragraph(line, styles["Body"]))

        doc.build(story)
        return filename
    except Exception as e:
        st.info("No se pudo generar el PDF. ¿Instalaste `reportlab` y (opcional) `DejaVuSans.ttf`?")
        st.exception(e)
        return None

# ====== Carga del reporte consolidado ======
reporte = st.session_state.get("reporte", {}) or {}
if not reporte:
    st.warning("No se encontró información previa en memoria. Volvé a generar el informe final.")
    st.stop()

# ====== Parámetros de la IA ======
with st.expander("Opciones de análisis IA"):
    modelo = st.selectbox("Modelo", ["gpt-4o-mini", "gpt-4o", "gpt-4.1"], index=0)
    tono = st.selectbox("Tono", ["Profesional", "Conciso", "Detallado"], index=0)

col_g, col_d = st.columns([0.6, 0.4])
with col_g:
    if st.button("Generar análisis", type="primary"):
        prompt = _mk_prompt(reporte) + f"\n\nTono pedido: {tono}."
        analysis_md = None

        # Intento con OpenAI (si hay API key y librería)
        api_key = st.secrets.get("OPENAI_API_KEY") if hasattr(st, "secrets") else None
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        try:
            from openai import OpenAI
            if not api_key:
                raise RuntimeError("Falta OPENAI_API_KEY")
            client = OpenAI(api_key=api_key)
            resp = client.chat.completions.create(
                model=modelo,
                messages=[
                    {"role": "system", "content": "Eres analista senior de crédito en microfinanzas."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
            )
            analysis_md = resp.choices[0].message.content
        except Exception:
            # Fallback local
            analysis_md = _fallback_local(reporte)

        st.session_state["analisis_ia_md"] = analysis_md
        st.success("Análisis generado.")

with col_d:
    if st.session_state.get("analisis_ia_md"):
        if st.button("📄 Descargar PDF"):
            path = _save_pdf(st.session_state["analisis_ia_md"], "analisis_ia.pdf")
            if path:
                st.download_button("Descargar análisis (PDF)", data=open(path, "rb").read(),
                                   file_name="analisis_ia.pdf", mime="application/pdf")

st.divider()
st.subheader("Resultado")
st.markdown(st.session_state.get("analisis_ia_md", "_Todavía no generaste el análisis._"))

# ====== Navegación ======
c1, c2 = st.columns([0.5, 0.5])
with c1:
    if st.button("⬅️ Volver a 14 – Informe final"):
        try:
            st.switch_page("pages/14_Informe_final.py")
        except Exception:
            st.stop()
with c2:
    if st.button("Ir al inicio 🏠"):
        st.switch_page("Home.py")
