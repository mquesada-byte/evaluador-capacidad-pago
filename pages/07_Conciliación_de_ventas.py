# =========================
# PASO 4 – Conciliación de ventas (Top-down vs Bottom-up vs Insumos)
# Requiere: que 3VAL haya guardado reporte["valoracion_asesor"]["factor_asesor_0a1"]
# =========================
def _ajuste_tipicidad(valor: float, tipicidad: str) -> tuple[float, str]:
    """Devuelve (valor_ajustado, texto_ajuste). Regla simple: Alto -10%, Bajo +10%."""
    f = 1.0
    detalle = "Típico (sin ajuste)"
    if tipicidad == "Alto":
        f = 0.90
        detalle = "Alto → −10%"
    elif tipicidad == "Bajo":
        f = 1.10
        detalle = "Bajo → +10%"
    return valor * f, detalle

def _desv_pct(a: float | None, b: float | None) -> float | None:
    if not a or not b or a <= 0 or b <= 0:
        return None
    base = (a + b) / 2
    return abs(a - b) / base

def _fmt_col(x: int | float | None) -> str:
    if x is None:
        return "—"
    try:
        return f"₡ {int(round(x)):,}".replace(",", ".")
    except Exception:
        return str(x)

def _nivel_confiabilidad(max_dev: float | None, num_metodos: int, fuente: str | None,
                         conf_cli: int | None, factor_asesor: float, dudas: str) -> str:
    # Si hay dudas serias, capea en "Baja"
    if dudas == "Dudas serias":
        return "Baja"
    # Reglas base
    fuente_formal = (fuente in ["Facturación electrónica", "POS/Datáfono", "Extractos bancarios/SINPE"])
    if num_metodos >= 2 and max_dev is not None and max_dev <= 0.20 and (conf_cli or 0) >= 8 and fuente_formal:
        base = "Alta"
    elif num_metodos >= 2 and max_dev is not None and max_dev <= 0.40:
        base = "Media"
    else:
        base = "Baja"
    # Ajuste por factor del asesor
    if factor_asesor < 0.55 and base == "Alta":
        return "Media"
    if factor_asesor < 0.55 and base == "Media":
        return "Baja"
    if factor_asesor < 0.70 and base == "Alta":
        return "Media"
    return base

if st.session_state.get("step") == 3 and st.session_state.get("step3") == "RES":
    st.title("🧮 Paso 4: Conciliación de ventas")
    st.caption("Comparamos las estimaciones (3A, 3B y 3C si aplica), ponderamos por calidad/valoración y fijamos un monto mensual defendible.")

    rep = st.session_state.get("reporte", {})

    # Asegurar que haya valoración del asesor
    if "valoracion_asesor" not in rep:
        st.info("Antes de conciliar, registra tu **valoración del asesor**.")
        if st.button("Ir a valoración del asesor ➡️", key="go_val_from_res", use_container_width=True):
            st.session_state.step3 = "VAL"
            st.rerun()
        st.stop()

    # ---- Tomar valores disponibles de 3A / 3B / 3C ----
    # 3A Top-down
    vtd = rep.get("ventas_topdown", {})
    top_raw = vtd.get("monto_colones")
    tipicidad = vtd.get("tipicidad")
    fuente = vtd.get("fuente")
    conf_cli = vtd.get("confianza_cliente_0a10")
    top_adj, top_ajuste_txt = (None, "—")
    if isinstance(top_raw, (int, float)) and top_raw > 0 and tipicidad in ["Típico", "Alto", "Bajo"]:
        top_adj, top_ajuste_txt = _ajuste_tipicidad(float(top_raw), tipicidad)

    # 3B Bottom-up
    vbu = rep.get("ventas_bottomup", {})
    bottom_val = vbu.get("ventas_estimadas_colones")

    # 3C Insumos (puede no aplicar)
    vin = rep.get("ventas_insumos_simple", rep.get("ventas_insumos", {}))
    insumos_no_aplica = bool(vin.get("no_aplica")) if isinstance(vin, dict) else False
    insumos_val = None if insumos_no_aplica else vin.get("ventas_estimadas_colones")

    disponibles = [x for x in [top_adj, bottom_val, insumos_val] if isinstance(x, (int, float)) and x > 0]
    if len(disponibles) == 0:
        st.warning("Aún no hay estimaciones suficientes para conciliar. Regrese a 3A/3B/3C y complete al menos una.")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Volver a 3A", key="res_back_3A", use_container_width=True):
                st.session_state.step3 = "A"
                st.rerun()
        with c2:
            if st.button("Volver a 3B", key="res_back_3B", use_container_width=True):
                st.session_state.step3 = "B"
                st.rerun()
        st.stop()

    # ---- Mostrar tabla de estimaciones ----
    filas = [
        {"Ángulo": "Top-down", "Monto": _fmt_col(top_raw), "Ajuste tipicidad": top_ajuste_txt if top_adj else "—", "Usado en conciliación": _fmt_col(top_adj)},
        {"Ángulo": "Bottom-up", "Monto": _fmt_col(bottom_val), "Ajuste tipicidad": "—", "Usado en conciliación": _fmt_col(bottom_val)},
        {"Ángulo": "Insumos/Margen", "Monto": "No aplica" if insumos_no_aplica else _fmt_col(insumos_val), "Ajuste tipicidad": "—", "Usado en conciliación": "—" if insumos_no_aplica else _fmt_col(insumos_val)},
    ]
    st.write("**Estimaciones disponibles**")
    st.table(filas)

    # ---- Pesos base ----
    w_top_base, w_bottom_base, w_ins_base = 0.40, 0.35, 0.25  # puedes ajustar por sector si quieres

    # Calidad de fuente (Top-down)
    fuente_factor = {
        "Facturación electrónica": 1.00,
        "POS/Datáfono": 0.95,
        "Extractos bancarios/SINPE": 0.95,
        "Cuaderno/Excel": 0.80,
        "Memoria": 0.60,
        "Otro": 0.70,
        None: 0.75,
        "": 0.75,
    }.get(fuente, 0.75)

    # Confianza declarada del cliente (Top-down): 0.40–1.00
    conf_factor = 0.40 + 0.06 * float(conf_cli or 0)
    conf_factor = max(0.40, min(1.00, conf_factor))

    # ---- Valoración del asesor (3VAL) ----
    val = rep.get("valoracion_asesor", {})
    factor_asesor = float(val.get("factor_asesor_0a1") or 1.0)  # ya incluye castigo por dudas (0.40–1.00)
    dudas = val.get("dudas_declaracion", "Sin dudas")
    # Penalización EXTRA solo al Top-down (suave, para que la normalización no la elimine)
    dudas_extra_top = {"Sin dudas": 1.00, "Dudas leves": 0.90, "Dudas serias": 0.75}.get(dudas, 1.00)

    # ---- Pesos crudos antes de outliers ----
    w_top = (w_top_base * fuente_factor * conf_factor * factor_asesor * dudas_extra_top) if top_adj else 0.0
    w_bottom = (w_bottom_base * factor_asesor) if bottom_val else 0.0
    w_ins = (w_ins_base * factor_asesor * (1.0 if (vin.get("tiene_registros_compras") == "Sí") else 0.80)) if insumos_val else 0.0

    # Consistencia (penaliza outliers >40% vs mediana)
    vals = [x for x in [top_adj, bottom_val, insumos_val] if x]
    median_ref = None
    if len(vals) >= 2:
        median_ref = sorted(vals)[len(vals)//2]
    def penaliza_outlier(v, w):
        if v and median_ref:
            d = abs(v - median_ref) / median_ref
            return w * (0.30 if d > 0.40 else 1.0)
        return w
    w_top = penaliza_outlier(top_adj, w_top)
    w_bottom = penaliza_outlier(bottom_val, w_bottom)
    w_ins = penaliza_outlier(insumos_val, w_ins)

    # Normalizar pesos
    w_sum = w_top + w_bottom + w_ins
    if w_sum == 0:
        # fallback si todo quedó en 0
        w_top = 1.0 if top_adj else 0.0
        w_bottom = 1.0 if bottom_val else 0.0
        w_ins = 1.0 if insumos_val else 0.0
        w_sum = w_top + w_bottom + w_ins
    w_top_n, w_bottom_n, w_ins_n = (w_top / w_sum, w_bottom / w_sum, w_ins / w_sum)

    # Promedio ponderado
    ventas_conc = 0.0
    if top_adj:
        ventas_conc += top_adj * w_top_n
    if bottom_val:
        ventas_conc += bottom_val * w_bottom_n
    if insumos_val:
        ventas_conc += insumos_val * w_ins_n

    # Desviación máxima entre pares
    desv_list = []
    for a, b in [(top_adj, bottom_val), (top_adj, insumos_val), (bottom_val, insumos_val)]:
        d = _desv_pct(a, b)
        if d is not None:
            desv_list.append(d)
    max_dev = max(desv_list) if desv_list else None

    # Confiabilidad final (incluye valoración del asesor y dudas)
    num_metodos = len([x for x in [top_adj, bottom_val, insumos_val] if x])
    confiab = _nivel_confiabilidad(max_dev, num_metodos, fuente, conf_cli, factor_asesor, dudas)

    # Rango
    rango_min = min(disponibles) if disponibles else None
    rango_max = max(disponibles) if disponibles else None

    # Mostrar resultados
    st.subheader("Resultado conciliado")
    st.success(
        f"**Ventas conciliadas (mes típico):** {_fmt_col(ventas_conc)}  \n"
        f"**Rango de estimaciones:** {_fmt_col(rango_min)} – {_fmt_col(rango_max)}  \n"
        f"**Desviación máx. entre métodos:** {('%.0f%%' % (max_dev*100)) if max_dev is not None else '—'}  \n"
        f"**Confiabilidad:** {confiab}"
    )

    with st.expander("Ver ponderaciones y detalle"):
        st.write({
            "Peso Top-down": round(w_top_n, 3),
            "Peso Bottom-up": round(w_bottom_n, 3),
            "Peso Insumos": round(w_ins_n, 3),
            "Fuente Top-down": fuente or "—",
            "Confianza cliente (Top-down)": conf_cli if conf_cli is not None else "—",
            "Factor del asesor (0.40–1.00)": round(factor_asesor, 2),
            "Penalización extra Top-down por dudas": dudas_extra_top,
            "Penalización por outliers (>40%)": "Aplicada" if (max_dev and max_dev > 0.40) else "No",
        })

    st.divider()

    # Navegación / Guardar
    c1, c2, c3 = st.columns([0.34, 0.33, 0.33])
    with c1:
        if st.button("⬅️ Volver a 3C", key="res_back_3C", use_container_width=True):
            st.session_state.step3 = "C"
            st.rerun()
    with c2:
        if st.button("Editar 3A/3B", key="res_back_3AB", use_container_width=True):
            st.session_state.step3 = "A"
            st.rerun()
    with c3:
        if st.button("Guardar y continuar ➡️", key="res_go_step4", use_container_width=True):
            st.session_state.setdefault("reporte", {})
            st.session_state["reporte"]["ventas_conciliacion"] = {
                "ventas_conciliadas_colones": int(round(ventas_conc)),
                "rango_min_colones": int(round(rango_min)) if rango_min else None,
                "rango_max_colones": int(round(rango_max)) if rango_max else None,
                "desviacion_max_pct": float(round(max_dev, 4)) if max_dev is not None else None,
                "confiabilidad": confiab,
                "pesos": {
                    "top_down": round(w_top_n, 4),
                    "bottom_up": round(w_bottom_n, 4),
                    "insumos": round(w_ins_n, 4),
                },
                "detalle": {
                    "top_down_ajuste_tipicidad": (tipicidad or "—"),
                    "fuente_top_down": fuente,
                    "confianza_cliente": conf_cli,
                    "factor_asesor": round(factor_asesor, 2),
                    "dudas_declaracion": dudas,
                }
            }
            st.session_state.step = 4  # avanza a tu próximo paso
            st.success("Conciliación guardada. Avanzando al Paso 5…")
            st.rerun()

    # 👇 Detiene el render aquí mientras sigas en el Paso 1
    st.stop()
