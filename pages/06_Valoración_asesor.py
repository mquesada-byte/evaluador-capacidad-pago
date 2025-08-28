# pages/06_Valoración_asesor.py
import streamlit as st

st.set_page_config(page_title="Paso 6: Valoración del asesor", page_icon="📝")

# =========================
# PASO 6 – Valoración del asesor (multipágina)
# =========================
def init_valoracion_asesor_state():
    st.session_state.setdefault("valoracion_asesor", {})
    v = st.session_state.valoracion_asesor
    v.setdefault("conocimiento_0a10", 5)           # ¿Conoce su negocio / números?
    v.setdefault("credibilidad_0a10", 5)           # ¿Qué tan creíble es su declaración?
    v.setdefault("dudas_declaracion", "Sin dudas") # Sin dudas / Dudas leves / Dudas serias
    v.setdefault("clasificacion", "Microempresario/a")  # Microempresario/a / Actividad incipiente / Dudoso...
    v.setdefault("evidencia", [])                  # checkboxes
    v.setdefault("comentario", "")

def _factor_asesor(v: dict) -> float:
    """0.60–1.00 según promedio (conocimiento, credibilidad) y ajuste por dudas."""
    know = float(v.get("conocimiento_0a10") or 0)
    cred = float(v.get("credibilidad_0a10") or 0)
    avg = (know + cred) / 2.0
    base = 0.6 + 0.04 * avg                      # 0.60–1.00 con avg en [0..10]
    dudas = (v.get("dudas_declaracion") or "Sin dudas")
    mult_dudas = {"Sin dudas": 1.00, "Dudas leves": 0.85, "Dudas serias": 0.60}.get(dudas, 1.00)
    factor = base * mult_dudas
    return max(0.40, min(1.00, factor))          # límites de seguridad

# ---------- UI (multipágina; sin 'step') ----------
init_valoracion_asesor_state()
v = st.session_state.valoracion_asesor

st.title("📝 Paso 6: Valoración del asesor")
st.caption("Tu evaluación cualitativa antes de conciliar las ventas.")

col1, col2 = st.columns(2)
with col1:
    v["conocimiento_0a10"] = st.slider(
        "Conocimiento del negocio (0–10) *",
        0, 10, int(v["conocimiento_0a10"]),
        help="¿Domina clientes, ticket, precios, costos, operación?"
    )
with col2:
    v["credibilidad_0a10"] = st.slider(
        "Credibilidad de la información (0–10) *",
        0, 10, int(v["credibilidad_0a10"]),
        help="¿La explicación y los números parecen consistentes?"
    )

col3, col4 = st.columns(2)
with col3:
    v["dudas_declaracion"] = st.selectbox(
        "Tu percepción sobre la veracidad",
        ["Sin dudas", "Dudas leves", "Dudas serias"],
        index=["Sin dudas","Dudas leves","Dudas serias"].index(v["dudas_declaracion"])
    )
with col4:
    v["clasificacion"] = st.selectbox(
        "Clasificación",
        ["Microempresario/a", "Actividad incipiente", "Dudoso / posible no negocio"],
        index=0 if v["clasificacion"] not in ["Microempresario/a", "Actividad incipiente", "Dudoso / posible no negocio"]
        else ["Microempresario/a", "Actividad incipiente", "Dudoso / posible no negocio"].index(v["clasificacion"])
    )

v["evidencia"] = st.multiselect(
    "Evidencia observada (opcional)",
    ["Facturación/POS", "Extractos bancarios", "Cuaderno/Excel", "Fotos del negocio", "Ninguna"],
    default=v.get("evidencia", [])
)

v["comentario"] = st.text_area(
    "Comentario del asesor (opcional)",
    value=v["comentario"],
    placeholder="Notas breves: incoherencias, señales de manejo, ejemplos citados, etc.",
    height=90
)

factor = _factor_asesor(v)
avg = (float(v["conocimiento_0a10"]) + float(v["credibilidad_0a10"])) / 2.0
base = 0.6 + 0.04 * avg
mult_dudas = {"Sin dudas": 1.00, "Dudas leves": 0.85, "Dudas serias": 0.60}[v["dudas_declaracion"]]
st.info(
    f"**Factor de confiabilidad del asesor (aplicado en conciliación):** "
    f"{factor:.2f}  (base {base:.2f} × ajuste por dudas {mult_dudas:.2f})"
)

st.divider()

colb1, colb2 = st.columns(2)
with colb1:
    if st.button("⬅️ Volver a 5 (Insumos/Margen)", key="val_back_5", use_container_width=True):
        for prev_page in ["pages/05_Ventas_insumos_margen.py"]:
            try:
                st.switch_page(prev_page)
                break
            except Exception:
                continue

with colb2:
    if st.button("Continuar a Conciliación ➡️", key="val_go_res", use_container_width=True):
        st.session_state.setdefault("reporte", {})
        st.session_state["reporte"]["valoracion_asesor"] = {
            "conocimiento_0a10": int(v["conocimiento_0a10"]),
            "credibilidad_0a10": int(v["credibilidad_0a10"]),
            "dudas_declaracion": v["dudas_declaracion"],
            "clasificacion": v["clasificacion"],
            "evidencia": list(v["evidencia"]),
            "comentario": v["comentario"].strip(),
            "factor_asesor_0a1": float(factor),
        }
        st.session_state["done_06"] = True

        # Ir a 07_Conciliación_de_ventas.py (con fallbacks)
        for nxt in [
            "pages/07_Conciliación_de_ventas.py",
            "pages/07_Conciliacion_de_ventas.py",
            "pages/07_Conciliación_ventas.py",
            "pages/07_Conciliacion_ventas.py",
            "pages/07_Conciliacion.py",
        ]:
            try:
                st.switch_page(nxt)
                break
            except Exception:
                continue
        else:
            st.success("Valoración guardada. Abrí **Conciliación de ventas** desde el menú lateral.")
            st.stop()

# 👇 Detiene el render aquí mientras sigas en esta página
st.stop()



    # 👇 Detiene el render aquí mientras sigas en el Paso 1
    st.stop()
