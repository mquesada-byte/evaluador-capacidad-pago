# =========================
# PASO 8 – Gastos familiares (step == 7)
# =========================
def _mensualizar_gasto_fam(monto: float, periodicidad: str) -> float:
    per = (periodicidad or "").lower()
    if per == "diario":       return monto * 30.0
    if per == "semanal":      return monto * (52.0 / 12.0)  # ≈ 4.333
    if per == "quincenal":    return monto * 2.0
    if per == "mensual":      return monto
    if per == "bimestral":    return monto / 2.0
    if per == "trimestral":   return monto / 3.0
    if per == "semestral":    return monto / 6.0
    if per == "anual":        return monto / 12.0
    return 0.0

if st.session_state.get("step") == 7:
    import pandas as pd

    st.title("🏠 Paso 8: Gastos familiares")
    st.caption("Registre los gastos del **hogar** (familia): alimentación, vivienda, educación, salud, transporte, servicios públicos y otros. Indique si fueron **verificados** y el **tipo de evidencia**.")

    # Catálogos
    rubros_fam = ["Alimentación", "Vivienda", "Educación", "Salud", "Transporte", "Servicios públicos", "Otros"]
    periodicidades = ["Mensual", "Quincenal", "Semanal", "Diario", "Bimestral", "Trimestral", "Semestral", "Anual"]
    evidencias = [
        "Factura/Recibo", "Contrato/Arrendamiento", "Estado de cuenta/SINPE",
        "Planilla/CCSS", "Recibos", "Foto/Chat", "No aplica", "Otro"
    ]

    # Columnas base (entrada) — usaremos esto para recargar lo guardado
    base_cols = [
        "Rubro", "Detalle", "Monto por período (₡)", "Periodicidad",
        "Verificado por asesor", "Tipo de evidencia", "Comentario",
    ]

    # ================== NUEVO: cargar lo guardado si existe ==================
    guardado = (st.session_state.get("reporte", {})
                .get("gastos_familiares", {})
                .get("tabla", []))

    if guardado:
        df_base = pd.DataFrame(guardado).copy()
        # Asegurar columnas base y tipos
        for c in base_cols:
            if c not in df_base.columns:
                if c == "Monto por período (₡)":
                    df_base[c] = 0
                elif c == "Verificado por asesor":
                    df_base[c] = False
                else:
                    df_base[c] = ""
        df_base = df_base[base_cols]
        df_base["Monto por período (₡)"] = pd.to_numeric(df_base["Monto por período (₡)"], errors="coerce").fillna(0)
        df_base["Verificado por asesor"] = df_base["Verificado por asesor"].fillna(False).astype(bool)
    else:
        # Placeholders iniciales (una fila por rubro)
        placeholder_rows = []
        for r in rubros_fam:
            placeholder_rows.append({
                "Rubro": r, "Detalle": "", "Monto por período (₡)": 0, "Periodicidad": "Mensual",
                "Verificado por asesor": False, "Tipo de evidencia": "", "Comentario": "",
            })
        df_base = pd.DataFrame(placeholder_rows)
    # ========================================================================

    # Editor de captura (ahora con df_base que puede venir del reporte guardado)
    df_in = st.data_editor(
        df_base,
        use_container_width=True,
        num_rows="dynamic",
        hide_index=True,
        key="de_gastos_familiares",
        column_config={
            "Rubro": st.column_config.SelectboxColumn("Rubro", options=rubros_fam, required=False),
            "Detalle": st.column_config.TextColumn("Detalle"),
            "Monto por período (₡)": st.column_config.NumberColumn("Monto por período (₡)", min_value=0, step=1000, format="₡ %d"),
            "Periodicidad": st.column_config.SelectboxColumn("Periodicidad", options=periodicidades, required=False),
            "Verificado por asesor": st.column_config.CheckboxColumn("Verificado por asesor", default=False),
            "Tipo de evidencia": st.column_config.SelectboxColumn("Tipo de evidencia", options=evidencias, required=False),
            "Comentario": st.column_config.TextColumn("Comentario"),
        },
    )

    # --- Preparación y derivados ---
    df = df_in.copy()
    if "Monto por período (₡)" not in df.columns:
        df["Monto por período (₡)"] = 0
    df["Monto por período (₡)"] = pd.to_numeric(df["Monto por período (₡)"], errors="coerce").fillna(0)
    if "Verificado por asesor" not in df.columns:
        df["Verificado por asesor"] = False
    df["Verificado por asesor"] = df["Verificado por asesor"].fillna(False).astype(bool)

    # Calcular mensualización
    mensualizados = []
    for _, r in df.iterrows():
        monto = float(r.get("Monto por período (₡)") or 0)
        per = r.get("Periodicidad") or ""
        mensualizados.append(_mensualizar_gasto_fam(monto, per))
    df["Gasto mensualizado (₡)"] = pd.Series(mensualizados).round(0).astype(int)

    # Editor con cálculos (derivadas bloqueadas)
    with st.expander("Editar tabla con cálculos (derivados bloqueados)"):
        df_edit = st.data_editor(
            df,
            use_container_width=True,
            num_rows="dynamic",
            hide_index=True,
            key="de_gastos_familiares_calc",
            column_config={
                "Rubro": st.column_config.SelectboxColumn("Rubro", options=rubros_fam),
                "Detalle": st.column_config.TextColumn("Detalle"),
                "Monto por período (₡)": st.column_config.NumberColumn("Monto por período (₡)", min_value=0, step=1000, format="₡ %d"),
                "Periodicidad": st.column_config.SelectboxColumn("Periodicidad", options=periodicidades),
                "Verificado por asesor": st.column_config.CheckboxColumn("Verificado por asesor", default=False),
                "Tipo de evidencia": st.column_config.SelectboxColumn("Tipo de evidencia", options=evidencias),
                "Comentario": st.column_config.TextColumn("Comentario"),
                "Gasto mensualizado (₡)": st.column_config.NumberColumn("Gasto mensualizado (₡)", format="₡ %d", disabled=True),
            },
        )

    # Recalcular por si hubo cambios
    if "Monto por período (₡)" not in df_edit.columns:
        df_edit["Monto por período (₡)"] = 0
    df_edit["Monto por período (₡)"] = pd.to_numeric(df_edit["Monto por período (₡)"], errors="coerce").fillna(0)
    if "Verificado por asesor" not in df_edit.columns:
        df_edit["Verificado por asesor"] = False
    df_edit["Verificado por asesor"] = df_edit["Verificado por asesor"].fillna(False).astype(bool)

    mensualizados = []
    for _, r in df_edit.iterrows():
        monto = float(r.get("Monto por período (₡)") or 0)
        per = r.get("Periodicidad") or ""
        mensualizados.append(_mensualizar_gasto_fam(monto, per))
    df = df_edit.copy()
    df["Gasto mensualizado (₡)"] = pd.Series(mensualizados).round(0).astype(int)

    # --- Resumen ---
    df["Monto por período (₡)"] = pd.to_numeric(df["Monto por período (₡)"], errors="coerce").fillna(0)
    valid_mask = df["Periodicidad"].isin(periodicidades) & (df["Monto por período (₡)"] > 0)
    df_valid = df[valid_mask].copy()

    total_gasto_fam_mensual = int(df_valid["Gasto mensualizado (₡)"].sum()) if not df_valid.empty else 0
    total_gasto_fam_verificado = int(df_valid.loc[df_valid["Verificado por asesor"], "Gasto mensualizado (₡)"].sum()) if not df_valid.empty else 0
    reg_validos = int(valid_mask.sum())

    st.markdown("**Resumen**")
    st.write({
        "Total gastos familiares (mensualizado)": f"₡ {total_gasto_fam_mensual:,}".replace(",", "."),
        "Total verificado (mensualizado)": f"₡ {total_gasto_fam_verificado:,}".replace(",", "."),
        "Registros válidos": reg_validos,
    })

    st.divider()

    # ========= Navegación / Guardar =========
    disabled_next = (reg_validos == 0)

    c1, c2 = st.columns([0.5, 0.5])
    with c1:
        if st.button("⬅️ Volver a Gastos operativos", key="gfam_back_gop", use_container_width=True):
            st.session_state.step = 6
            st.rerun()
    with c2:
        if st.button("Guardar y continuar ➡️", key="gfam_save_next", use_container_width=True,
                     disabled=disabled_next):
            st.session_state.setdefault("reporte", {})
            st.session_state["reporte"]["gastos_familiares"] = {
                "tabla": df.fillna("").to_dict(orient="records"),
                "totales": {
                    "total_gastos_familiares_mensualizado_colones": total_gasto_fam_mensual,
                    "total_gastos_familiares_verificado_colones": total_gasto_fam_verificado,
                    "registros_validos": reg_validos,
                }
            }
            st.success("Gastos familiares guardados. Avanzando…")
            st.session_state.step = 8
            st.rerun()

    st.stop()
