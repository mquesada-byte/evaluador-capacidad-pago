# =========================
# PASO 3C – Ventas (Insumos/Margen simple desde COMPRAS)
# =========================
def init_paso3C_state_simple():
    st.session_state.setdefault("ventas_insumos_simple", {})
    vin = st.session_state.ventas_insumos_simple
    vin.setdefault("tiene_registros", "Sí")        # "Sí" | "No"
    vin.setdefault("compras_mes", 0)               # ₡
    vin.setdefault("tipo_margen", "Sobre ventas")  # "Sobre ventas" | "Sobre compras (markup)"
    vin.setdefault("margen_pct", 30)               # % entero
    vin.setdefault("comentario", "")

def _calc_ventas_desde_compras_simple(compras: float, tipo_margen: str, margen_pct: float):
    m = max(0.0, float(margen_pct) / 100.0)
    if tipo_margen == "Sobre ventas":
        denom = 1.0 - m
        if denom <= 0:
            return None, "El margen sobre ventas debe ser menor a 100%."
        ventas = compras / denom
        return int(round(ventas)), None
    else:  # "Sobre compras (markup)"
        ventas = compras * (1.0 + m)
        return int(round(ventas)), None

if st.session_state.get("step") == 3 and st.session_state.get("step3") == "C":

    # 3C SIEMPRE APLICA (se eliminó filtro por 'Servicios')
    init_paso3C_state_simple()
    vin = st.session_state.ventas_insumos_simple

    mes_etiqueta, mes_iso = _mes_anterior_label()  # p.ej. "julio 2025", "2025-07"
    st.title("🧮 Paso 3C: Ventas – Insumos/Margen (simple desde compras)")
    st.caption(f"Mes de referencia: **{mes_etiqueta}**. Sin IVA ni mermas; aproximamos COGS ≈ Compras del mes.")

    colR1, colR2 = st.columns([0.5, 0.5])
    with colR1:
        vin["tiene_registros"] = st.radio(
            "¿Tiene facturas o registros de compras del mes?",
            options=["Sí", "No"],
            index=0 if vin["tiene_registros"] == "Sí" else 1,
            help="No es obligatorio para continuar, pero mejora la confiabilidad."
        )

    vin["compras_mes"] = st.number_input(
        f"Compras del mes de {mes_etiqueta} (₡) *",
        min_value=0, step=1000, value=int(vin["compras_mes"]),
        help="Total pagado/por pagar a proveedores durante el mes de referencia."
    )

    st.markdown("---")

    colM1, colM2 = st.columns([0.55, 0.45])
    with colM1:
        vin["tipo_margen"] = st.radio(
            "¿El margen lo expresa sobre…?",
            options=["Sobre ventas", "Sobre compras (markup)"],
            index=0 if vin["tipo_margen"] == "Sobre ventas" else 1,
            help="Si dice 'gano 30% de lo que vendo' → Sobre ventas. Si dice 'vendo 50% más caro que el costo' → Sobre compras (markup)."
        )
    with colM2:
        max_pct = 95 if vin["tipo_margen"] == "Sobre ventas" else 500
        vin["margen_pct"] = st.number_input(
            "Margen (%) *",
            min_value=0, max_value=max_pct, step=1, value=int(vin["margen_pct"]),
            help=("Debe ser < 100% si es sobre ventas." if vin["tipo_margen"] == "Sobre ventas"
                  else "Puede ser >100% si es markup sobre compras (p. ej., 120%).")
        )

    vin["comentario"] = st.text_area(
        "Comentario (opcional)",
        value=vin["comentario"],
        placeholder="Notas breves: compras extraordinarias para stock, cambios de precios, feriados, etc.",
        height=80
    )

    st.divider()

    ventas_est, warn = _calc_ventas_desde_compras_simple(
        compras=float(vin["compras_mes"] or 0),
        tipo_margen=vin["tipo_margen"],
        margen_pct=float(vin["margen_pct"] or 0),
    )

    if warn:
        st.warning(warn)
    elif ventas_est is not None and int(vin["compras_mes"]) > 0:
        st.info(f"**Ventas estimadas (Insumos/Margen) para {mes_etiqueta}:** ₡ {ventas_est:,}".replace(",", "."))

    oblig_ok = (int(vin["compras_mes"]) > 0 and ventas_est is not None)

    # --- Navegación ---
    colNav1, colNav2 = st.columns([0.5, 0.5])
    with colNav1:
        if st.button("⬅️ Volver a 3B (Bottom-up)", key="back_to_3B_from_3C_simple", use_container_width=True):
            st.session_state.step3 = "B"
            st.rerun()

    with colNav2:
        if st.button(
            "Siguiente ➡️ (Valoración)",
            key="next_step_3C_simple",
            disabled=not oblig_ok,
            use_container_width=True,
        ):
            st.session_state.setdefault("reporte", {})
            st.session_state["reporte"]["ventas_insumos_simple"] = {
                "mes_referencia": mes_etiqueta,
                "mes_iso": mes_iso,
                "tiene_registros_compras": vin["tiene_registros"],
                "compras_mes_colones": int(vin["compras_mes"]),
                "tipo_margen": vin["tipo_margen"],
                "margen_pct": int(vin["margen_pct"]),
                "ventas_estimadas_colones": int(ventas_est) if ventas_est is not None else None,
                "comentario": vin["comentario"].strip(),
                "supuesto_cogs_equivale_compras": True,
            }
            st.session_state.step3 = "VAL"   # salto a Valoración del asesor
            st.rerun()

    # 👇 Detiene el render aquí mientras sigas en el Paso 1
    st.stop()
