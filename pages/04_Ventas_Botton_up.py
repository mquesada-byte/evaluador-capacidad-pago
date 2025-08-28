# =========================
# PASO 3B – Ventas (Bottom-up / operativa)
# Nota: usa _mes_anterior_label() definido en 3A para mostrar el mes de referencia.
# =========================
def init_paso3B_state():
    st.session_state.setdefault("ventas_bottomup", {})
    vbu = st.session_state.ventas_bottomup
    vbu.setdefault("unidad_clientes", "Día")     # "Día" | "Semana" | "Mes"
    vbu.setdefault("clientes", 0)                # clientes por unidad seleccionada
    vbu.setdefault("dias_abiertos", 0)           # si unidad = Día
    vbu.setdefault("semanas_abiertas", 4)        # si unidad = Semana
    vbu.setdefault("ticket_promedio", 0)         # ₡ por cliente
    vbu.setdefault("comentario", "")

def _calc_bottom_up_total(vbu: dict) -> int:
    unidad = vbu.get("unidad_clientes", "Día")
    clientes = float(vbu.get("clientes") or 0)
    ticket = float(vbu.get("ticket_promedio") or 0)
    if unidad == "Día":
        dias = int(vbu.get("dias_abiertos") or 0)
        total = dias * clientes * ticket
    elif unidad == "Semana":
        semanas = int(vbu.get("semanas_abiertas") or 0)
        total = semanas * clientes * ticket
    else:  # "Mes"
        total = clientes * ticket
    return int(round(total))

if st.session_state.get("step") == 3 and st.session_state.get("step3") == "B":
    init_paso3B_state()
    vbu = st.session_state.ventas_bottomup

    # Mes de referencia (del mes calendario anterior)
    mes_etiqueta, mes_iso = _mes_anterior_label()

    st.title("📊 Paso 3B: Ventas – Bottom-up (operativa)")
    st.caption(f"Estimación del último mes calendario: **{mes_etiqueta}**.")

    # Unidad de medición de clientes
    vbu["unidad_clientes"] = st.selectbox(
        "Clientes medidos por *",
        options=["Día", "Semana", "Mes"],
        index=["Día", "Semana", "Mes"].index(vbu["unidad_clientes"]) if vbu["unidad_clientes"] in ["Día", "Semana", "Mes"] else 0,
        help="Elija si los clientes que declarará son por día, por semana o por mes."
    )

    # Entradas según la unidad
    if vbu["unidad_clientes"] == "Día":
        col1, col2, col3 = st.columns([0.33, 0.33, 0.34])
        with col1:
            vbu["dias_abiertos"] = st.number_input(
                "Días abiertos en el mes *", min_value=0, max_value=31, step=1, value=int(vbu["dias_abiertos"]),
                help="Cantidad de días que operó el negocio en el mes de referencia."
            )
        with col2:
            vbu["clientes"] = st.number_input(
                "Clientes por día *", min_value=0, step=1, value=int(vbu["clientes"]),
                help="Promedio de clientes atendidos por día."
            )
        with col3:
            vbu["ticket_promedio"] = st.number_input(
                "Ticket promedio (₡/cliente) *", min_value=0, step=100, value=int(vbu["ticket_promedio"]),
                help="Venta promedio por cliente en colones."
            )
    elif vbu["unidad_clientes"] == "Semana":
        col1, col2, col3 = st.columns([0.33, 0.33, 0.34])
        with col1:
            vbu["semanas_abiertas"] = st.number_input(
                "Semanas abiertas en el mes *", min_value=0, max_value=5, step=1, value=int(vbu["semanas_abiertas"]),
                help="Número de semanas efectivas trabajadas en el mes (usualmente 4–5)."
            )
        with col2:
            vbu["clientes"] = st.number_input(
                "Clientes por semana *", min_value=0, step=1, value=int(vbu["clientes"]),
                help="Promedio de clientes atendidos por semana."
            )
        with col3:
            vbu["ticket_promedio"] = st.number_input(
                "Ticket promedio (₡/cliente) *", min_value=0, step=100, value=int(vbu["ticket_promedio"]),
                help="Venta promedio por cliente en colones."
            )
    else:  # "Mes"
        col1, col2 = st.columns([0.5, 0.5])
        with col1:
            vbu["clientes"] = st.number_input(
                "Clientes en el mes *", min_value=0, step=1, value=int(vbu["clientes"]),
                help="Total de clientes atendidos en todo el mes."
            )
        with col2:
            vbu["ticket_promedio"] = st.number_input(
                "Ticket promedio (₡/cliente) *", min_value=0, step=100, value=int(vbu["ticket_promedio"]),
                help="Venta promedio por cliente en colones."
            )

    vbu["comentario"] = st.text_area(
        "Comentario (opcional)",
        value=vbu["comentario"],
        placeholder="Notas breves: p. ej., cierres, feriados, eventos o cambios que afecten este cálculo.",
        height=80
    )

    st.divider()

    # Cálculo y vista previa
    total_estimado = _calc_bottom_up_total(vbu)
    st.info(f"**Ventas estimadas (Bottom-up) para {mes_etiqueta}: ₡ {total_estimado:,}**".replace(",", "."))

    # -------- Validación obligatorios --------
    if vbu["unidad_clientes"] == "Día":
        obligatorios_ok = (vbu["dias_abiertos"] > 0 and vbu["clientes"] > 0 and vbu["ticket_promedio"] > 0)
    elif vbu["unidad_clientes"] == "Semana":
        obligatorios_ok = (vbu["semanas_abiertas"] > 0 and vbu["clientes"] > 0 and vbu["ticket_promedio"] > 0)
    else:
        obligatorios_ok = (vbu["clientes"] > 0 and vbu["ticket_promedio"] > 0)

    # Navegación
    colNav1, colNav2 = st.columns([0.5, 0.5])
    with colNav1:
        if st.button("⬅️ Volver a 3A (Top-down)", key="back_to_3A", use_container_width=True):
            st.session_state.step = 3
            st.session_state.step3 = "A"
            st.rerun()

    with colNav2:
        if st.button("Siguiente ➡️ (3C)", key="next_step_3B", disabled=not obligatorios_ok, use_container_width=True):
            # Guardar bloque de reporte Bottom-up
            st.session_state.setdefault("reporte", {})
            st.session_state["reporte"]["ventas_bottomup"] = {
                "mes_referencia": mes_etiqueta,
                "mes_iso": mes_iso,
                "unidad_clientes": vbu["unidad_clientes"],
                "clientes_valor": int(vbu["clientes"]),
                "dias_abiertos": int(vbu["dias_abiertos"]) if vbu["unidad_clientes"] == "Día" else None,
                "semanas_abiertas": int(vbu["semanas_abiertas"]) if vbu["unidad_clientes"] == "Semana" else None,
                "ticket_promedio_colones": int(vbu["ticket_promedio"]),
                "ventas_estimadas_colones": int(total_estimado),
                "comentario": vbu["comentario"].strip(),
            }
            # Avanza a 3C (Insumos/Margen)
            st.session_state.step = 3
            st.session_state.step3 = "C"
            st.success("Bottom-up guardado. Avanzando a 3C…")
            st.rerun()

    # 👇 Detiene el render aquí mientras sigas en el Paso 1
    st.stop()
