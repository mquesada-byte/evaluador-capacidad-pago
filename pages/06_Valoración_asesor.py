# =========================
# PASO 3VAL – Valoración del asesor
# =========================
def init_valoracion_asesor_state():
    st.session_state.setdefault("valoracion_asesor", {})
    v = st.session_state.valoracion_asesor
    v.setdefault("conocimiento_0a10", 5)     # ¿Conoce su negocio / números?
    v.setdefault("credibilidad_0a10", 5)     # ¿Qué tan creíble es su declaración?
    v.setdefault("dudas_declaracion", "Sin dudas")  # Sin dudas / Dudas leves / Dudas serias
    v.setdefault("clasificacion", "Microempresario/a")  # Microempresario/a / Inci piente / Dudoso
    v.setdefault("evidencia", [])            # checkboxes
    v.setdefault("comentario", "")

def _factor_asesor(v: dict) -> float:
    # Base 0.60–1.00 según promedio de conocimiento y credibilidad,
    # multiplicado por ajuste de dudas (Sin:1.00, Leves:0.85, Serias:0.60)
    know = float(v.get("conocimiento_0a10") or 0)
    cred = float(v.get("credibilidad_0a10") or 0)
    avg = (know + cred) / 2.0
    base = 0.6 + 0.04 * avg                     # 0.60–1.00
    dudas = (v.get("dudas_declaracion") or "Sin dudas")
    mult_dudas = {"Sin dudas": 1.00, "Dudas leves": 0.85, "Dudas serias": 0.60}.get(dudas, 1.00)
    factor = base * mult_dudas
    return max(0.40, min(1.00, factor))         # límites de seguridad

if st.session_state.get("step") == 3 and st.session_state.get("step3") == "VAL":
    init_valoracion_asesor_state()
    v = st.session_state.valoracion_asesor

    st.title("📝 Paso 3 – Valoración del asesor")
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
            ["Microempresario/a", "Actividad incipiente", "Dudoso / posible no negocio"]
        )

    v["evidencia"] = st.multiselect(
        "Evidencia observada (opcional)",
        ["Facturación/POS", "Extractos bancarios", "Cuaderno/Excel", "Fotos del negocio", "Ninguna"],
        default=v["evidencia"]
    )

    v["comentario"] = st.text_area(
        "Comentario del asesor (opcional)",
        value=v["comentario"],
        placeholder="Notas breves: incoherencias, señales de manejo, ejemplos citados, etc.",
        height=90
    )

    factor = _factor_asesor(v)
    # Nota informativa mostrando base × ajuste por dudas
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
        if st.button("⬅️ Volver a 3C", key="val_back_3C", use_container_width=True):
            st.session_state.step3 = "C"
            st.rerun()
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
            st.session_state.step3 = "RES"
            st.rerun()

    # 👇 Detiene el render aquí mientras sigas en el Paso 1
    st.stop()
