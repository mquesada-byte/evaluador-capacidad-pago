# pages/15_Analisis_IA.py
import os
import io
import datetime as dt
import streamlit as st
import pandas as pd
import statistics

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

# ====== Leer reglamentos ======
def _load_pdf_text(path: str) -> str:
    try:
        from PyPDF2 import PdfReader
        if not os.path.exists(path):
            return ""
        reader = PdfReader(path)
        texto = ""
        for page in reader.pages:
            texto += page.extract_text() + "\n"
        return texto.strip()
    except Exception as e:
        return f"[No se pudo cargar {path}: {e}]"

if "reglamentos_texto" not in st.session_state:
    texto_credito = _load_pdf_text(os.path.join("assets", "reglamento_de_crédito.pdf"))
    texto_fondo   = _load_pdf_text(os.path.join("assets", "reglamento_del_fondo_de_utilidad_pública.pdf"))
    st.session_state["reglamentos_texto"] = f"{texto_credito}\n\n{texto_fondo}".strip()

# ====== Perfil cliente ======
def _perfil_cliente(rep: dict) -> str:
    cliente = st.session_state.get("cliente", {})
    negocio = st.session_state.get("negocio", {})

    faltantes = []
    if not negocio.get("persona_juridica"):
        faltantes.append("carece de personería jurídica")
    if not negocio.get("registros_contables"):
        faltantes.append("no lleva registros contables")

    gastos_tabla = (rep.get("gastos_operativos") or {}).get("tabla", [])
    sueldos = next((r for r in gastos_tabla if str(r.get("Rubro", "")).lower() == "sueldos"), None)
    monto_sueldos = 0
    if sueldos:
        try:
            monto_sueldos = float(sueldos.get("Gasto mensualizado (₡)", 0))
        except Exception:
            monto_sueldos = 0
    if monto_sueldos <= 0:
        faltantes.append("no asigna un salario (sueldos = 0)")

    es_informal = len(faltantes) > 0
    tipo_local = negocio.get("tipo_local", "N/D")

    anios = negocio.get("antiguedad_anios", 0)
    meses = negocio.get("antiguedad_meses", 0)
    total_meses = anios * 12 + meses
    if total_meses < 24:
        etapa = "fase inicial con alta probabilidad de no consolidarse (<2 años)"
    elif total_meses <= 60:
        etapa = "fase de maduración (2–5 años)"
    else:
        etapa = "fase de consolidación (>5 años)"

    patente = negocio.get("patente_municipal", False)
    incoherencias = []
    if not patente and negocio.get("registros_contables"):
        incoherencias.append("declara llevar registros contables pero no cuenta con patente")

    return f"""
**Evaluación inicial del cliente:**
- Formalidad: {"Informal" if es_informal else "Formal"} ({", ".join(faltantes) if faltantes else "cumple con requisitos"}).
- Tipo de negocio: {tipo_local}.
- Antigüedad: {etapa}.
- Patente municipal: {"Sí" if patente else "No"}.
- Observaciones: {"; ".join(incoherencias) if incoherencias else "Sin incoherencias aparentes"}.
"""

# ====== Análisis de Ventas ======
def _analisis_ventas(rep: dict) -> str:
    vtd = (rep.get("ventas_topdown") or {})
    vbu = (rep.get("ventas_bottomup") or {})
    vin = (rep.get("ventas_p5") or {})
    vas = (rep.get("valoracion_asesor") or {})

    monto_td = _num(vtd.get("monto_colones"))
    monto_bu = _num(vbu.get("ventas_estimadas_colones"))
    monto_in = _num(vin.get("ventas_estimadas_colones"))
    ventas_list = [m for m in [monto_td, monto_bu, monto_in] if m > 0]

    promedio = statistics.mean(ventas_list) if ventas_list else 0
    desv = statistics.pstdev(ventas_list) if len(ventas_list) > 1 else 0
    rango = max(ventas_list) - min(ventas_list) if len(ventas_list) > 1 else 0

    evidencias = vas.get("evidencia", [])
    verificados = 0
    if "Facturación/POS" in evidencias: verificados += 1
    if "Extractos bancarios" in evidencias: verificados += 1
    if "Cuaderno/Excel" in evidencias: verificados += 1
    pct_verificado = verificados / 3 if 3 else 0

    factor_asesor = float(vas.get("factor_asesor_0a1") or 0.7)
    estimacion_final = promedio * (0.5 + 0.5 * pct_verificado) * factor_asesor

    return f"""
**Análisis de las Ventas:**
- Top-down declarado: {_fmt_col(monto_td)}
- Bottom-up estimado: {_fmt_col(monto_bu)}
- Insumos/margen: {_fmt_col(monto_in)}

- Promedio simple: {_fmt_col(promedio)}
- Desviación estándar entre métodos: {_fmt_col(desv)}
- Rango (máx – mín): {_fmt_col(rango)}

- Porcentaje de verificación documental: {pct_verificado:.0%}
- Factor de asesor aplicado: {factor_asesor:.2f}

**Estimación ajustada de ventas:** {_fmt_col(estimacion_final)}
"""

# ====== Ratios Financieros ======
def _ratios_financieros(rep: dict) -> str:
    er = rep.get("estado_resultados", {}) or {}
    bg = (rep.get("balance_general") or {}).get("totales", {}) or {}

    ventas = _num(er.get("ventas_colones"))
    utilidad_neta_ope = _num(er.get("utilidad_neta_operativa_colones"))
    disponible = _num(er.get("disponible_para_prestamo_colones"))
    gastos_fam = _num(er.get("gastos_familiares_colones"))
    otros_ing = _num(er.get("otros_ingresos_colones"))
    deudas = _num(er.get("pago_de_deudas_colones"))

    # --- ratios ER ---
    margen_operativo = (utilidad_neta_ope / ventas) if ventas > 0 else None
    dscr = (disponible + deudas) / deudas if deudas > 0 else None
    gastos_fam_ratio = gastos_fam / (ventas + otros_ing) if (ventas + otros_ing) > 0 else None

    # --- ratios BG ---
    activo_circ = _num(bg.get("activo_circulante"))
    pasivo_circ = _num(bg.get("pasivo_circulante"))
    total_activos = _num(bg.get("total_activos"))
    total_pasivo = _num(bg.get("total_pasivo"))
    patrimonio = _num(bg.get("patrimonio"))

    razon_circulante = (activo_circ / pasivo_circ) if pasivo_circ > 0 else None
    apalancamiento = (total_pasivo / patrimonio) if patrimonio > 0 else None
    solvencia = (patrimonio / total_activos) if total_activos > 0 else None

    def _fmt_pct(val):
        return f"{val:.2%}" if val is not None else "N/D"

    def _semaforo_ratio(nombre, val, bueno, medio, invertido=False):
        """Clasifica un ratio según umbrales"""
        if val is None:
            return f"- {nombre}: N/D ⚪"
        if invertido:
            if val <= bueno: color = "🟢"
            elif val <= medio: color = "🟡"
            else: color = "🔴"
        else:
            if val >= bueno: color = "🟢"
            elif val >= medio: color = "🟡"
            else: color = "🔴"
        return f"- {nombre}: {_fmt_pct(val)} {color}"

    return f"""
**Análisis de Ratios Financieros:**

{_semaforo_ratio("Margen operativo", margen_operativo, 0.20, 0.10)}
{_semaforo_ratio("DSCR (cobertura deuda)", dscr, 1.5, 1.0)}
{_semaforo_ratio("Gastos familiares / Ingresos", gastos_fam_ratio, 0.30, 0.40, invertido=True)}

{_semaforo_ratio("Razón circulante (AC/PC)", razon_circulante, 1.5, 1.0)}
{_semaforo_ratio("Apalancamiento (Deuda/Patrimonio)", apalancamiento, 2.0, 3.0, invertido=True)}
{_semaforo_ratio("Solvencia (Patrimonio/Activos)", solvencia, 0.40, 0.25)}
"""


# ====== Prompt ======
def _mk_prompt(rep: dict, tono: str, reglamento: str) -> str:
    er = rep.get("estado_resultados", {}) or {}
    bg = rep.get("balance_general", {}) or {}
    deudas = rep.get("deudas_activas", {}).get("totales", {}) or {}

    ventas = er.get("ventas_colones")
    utilidad_neta_ope = er.get("utilidad_neta_operativa_colones")
    otros = er.get("otros_ingresos_colones")
    gastos_fam = er.get("gastos_familiares_colones")
    deudas_mens = er.get("pago_de_deudas_colones") or deudas.get("total_pago_mensual_colones")
    disponible = er.get("disponible_para_prestamo_colones")

    pasivo_circ = ((bg.get("totales") or {}).get("pasivo_circulante"))
    pasivo_largo = ((bg.get("totales") or {}).get("pasivo_largo"))
    patrimonio = (bg.get("totales") or {}).get("patrimonio")
    capital_trabajo = (bg.get("totales") or {}).get("capital_trabajo")

    perfil = _perfil_cliente(rep)
    analisis_ventas = _analisis_ventas(rep)
    ratios_financieros = _ratios_financieros(rep)

    return f"""
Eres analista senior de crédito en microfinanzas. Con tono **{tono.lower()}**, realiza un análisis integral.

1) Evaluación del cliente y negocio:
{perfil}

2) Análisis de las ventas:
{analisis_ventas}

3) Análisis de ratios financieros:
{ratios_financieros}

Además, ajusta tu criterio tomando en cuenta las reglas de política crediticia incluidas en los siguientes reglamentos internos:

---
{reglamento[:3000]}
---

Datos del cliente (valores mensuales y totales):

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
1) Evaluación del cliente y negocio
2) Análisis de las ventas (comparativo y confiabilidad)
3) Análisis de ratios financieros
4) Fortalezas del negocio (viñetas)
5) Riesgos / banderas rojas (viñetas)
6) Lectura financiera (2–3 párrafos)
7) Capacidad de pago y holgura (cálculos simples con los datos)
8) Recomendación (monto sugerido, plazo y ratio cuota/ingreso objetivo)
9) Pendientes de verificación (checklist breve)

Concluye con un párrafo final de criterio del analista.
    """.strip()




# (el resto del archivo sigue igual, sin cambios)


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

        try:
            pdfmetrics.registerFont(TTFont("DejaVu", "DejaVuSans.ttf"))
            font_name = "DejaVu"
        except Exception:
            font_name = "Helvetica"

        styles = getSampleStyleSheet()
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

        for raw in md_text.split("\n"):
            line = raw.strip()
            if not line:
                story.append(Spacer(1, 6))
                continue

            # 🔧 Reemplazo solo para PDF: traducir los emojis a texto legible
            line = (
                line.replace("🟢", "(positivo)")
                    .replace("🟡", "(intermedio)")
                    .replace("🔴", "(negativo)")
                    .replace("⚪", "(sin dato)")
            )

            line = line.replace("**", "").replace("__", "")
            story.append(Paragraph(line, styles["CustomBody"]))

        doc.build(story)
        pdf_bytes = buf.getvalue()
        buf.close()
        return pdf_bytes
    except Exception as e:
        st.warning("No se pudo generar el PDF. Verificá que `reportlab` esté instalado.")
        st.exception(e)
        return b""

def _get_openai_key():
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

# ====== Opciones de la IA ======
with st.expander("Opciones de análisis IA"):
    modelo = st.selectbox("Modelo", ["gpt-4o-mini", "gpt-4o", "gpt-4.1"], index=0)
    tono = st.selectbox("Tono", ["Profesional", "Conciso", "Detallado"], index=0)
    ver_prompt = st.checkbox("Mostrar prompt generado", value=False)

# ====== Generación ======
col_g, col_d = st.columns([0.6, 0.4])

with col_g:
    if st.button("Generar análisis", type="primary", use_container_width=True):
        reglamentos = st.session_state.get("reglamentos_texto", "")
        prompt = _mk_prompt(reporte, tono, reglamentos)
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
