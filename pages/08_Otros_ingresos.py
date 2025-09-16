# pages/08_Otros_ingresos.py
import streamlit as st
import pandas as pd
import datetime as dt
from zoneinfo import ZoneInfo   # 👈 import agregado

st.set_page_config(page_title="Paso 8: Otros ingresos del hogar", page_icon="💸")


# =========================
# Asegurar mes_iso
# =========================
TZ = ZoneInfo("America/Costa_Rica")
if "mes_iso" not in st.session_state:
    now = dt.datetime.now(TZ)
    st.session_state["mes_iso"] = f"{now.year}-{now.month:02d}"




# =========================
# PASO 8 – Otros ingresos del hogar (multipágina)
# =========================
def _mensualizar(monto: float, periodicidad: str) -> float:
    per = (periodicidad or "").lower()
    if per == "diario":       return monto * 30.0
    if per == "semanal":      return monto * (52.0 / 12.0)
    if per == "quincenal":    return monto * 2.0
    if per == "mensual":      return monto
    if per == "bimestral":    return monto / 2.0
    if per == "trimestral":   return monto / 3.0
    if per == "semestral":    return monto / 6.0
    if per == "anual":        return monto / 12.0
    return 0.0

def _factor_verificacion(verificado: bool, evidencia: str) -> float:
    if not verificado:
        return 0.70
    ev = (evidencia or "").lower()
    if ev in ["facturación electrónica", "extractos bancarios", "extractos bancarios/sinpe", "contrato", "certificación"]:
        return 1.00
    if ev in ["recibos", "comprobantes", "pos/datáfono", "captura pos", "captura sinpe", "credid", "equifax"]:
        return 0.90
    if ev in ["foto/chat", "whatsapp", "mensaje", "captura pantalla", "otro"]:
        return 0.80
    if ev in ["", "no aplica", None]:
        return 0.85
    return 0.85

def _factor_estabilidad(meses_cont: int) -> float:
    m = int(meses_cont or 0)
    if m >= 24: return 1.00
    if m >= 12: return 0.90
    if m >= 6:  return 0.80
    if m >= 3:  return 0.60
    if m >= 1:  return 0.50
    return 0.40

def _factor_probabilidad(prob_0a10: int) -> float:
    p = max(0, min(10, int(prob_0a10 or 0)))
    return 0.50 + 0.05 * p

def _factor_confiabilidad_ingreso(verificado: bool, evidencia: str, meses_cont: int, prob_0a10: int) -> float:
    f = _factor_verificacion(verificado, evidencia) * _factor_estabilidad(meses_cont) * _factor_probabilidad(prob_0a10)
    return max(0.20, min(1.00, f))

# ---------- UI ----------
st.title("💸 Paso 8: Otros ingresos del hogar")
st.caption("Registre otros ingresos del cliente y su núcleo familiar. Cada ingreso debe indicar si fue **verificado por el asesor** y con qué evidencia.")

# --- Catálogos ---
periodicidades = ["Diario", "Semanal", "Quincenal", "Mensual", "Bimestral", "Trimestral", "Semestral", "Anual"]
fuentes = ["Salario", "Pensión", "Alquiler", "Negocio secundario", "Remesas", "Servicios profesionales", "Subsidio/Ayuda", "Otro"]
relaciones = ["Cliente", "Pareja", "Hijo/a", "Padre/Madre", "Familiar", "Otro"]
evidencias = ["Facturación electrónica", "Extractos bancarios/SINPE", "POS/Datáfono", "Recibos",
              "Foto/Chat", "Contrato", "Certificación", "Credid", "Equifax", "No aplica", "Otro"]

base_cols = [
    "Titular (nombre)", "Relación", "Fuente de ingreso", "Periodicidad",
    "Monto por período (₡)", "Verificado por asesor", "Tipo de evidencia",
    "Meses de continuidad", "Prob. continuidad (0–10)", "Comentario",
]
deriv_cols = ["Ingreso mensualizado (₡)", "Factor confiabilidad (0.2–1.0)", "Ingreso ponderado (₡)"]

# ---------- CARGA INICIAL ----------
guardado = (
    st.session_state.get("reporte", {})
    .get("otros_ingresos", {})
    .get("tabla", [])
)

if guardado:
    df_base_inicial = pd.DataFrame(guardado).copy()
    for c in base_cols:
        if c not in df_base_inicial.columns:
            if c == "Verificado por asesor":
                df_base_inicial[c] = False
            elif c in ["Monto por período (₡)", "Meses de continuidad", "Prob. continuidad (0–10)"]:
                df_base_inicial[c] = 0
            else:
                df_base_inicial[c] = ""
    df_base_inicial = df_base_inicial[base_cols]
else:
    df_base_inicial = pd.DataFrame([{c: "" for c in base_cols}] * 4)
    df_base_inicial["Monto por período (₡)"] = 0
    df_base_inicial["Meses de continuidad"] = 0
    df_base_inicial["Prob. continuidad (0–10)"] = 0
    df_base_inicial["Verificado por asesor"] = False

# --- Data Editor base ---
df_in = st.data_editor(
    df_base_inicial,
    use_container_width=True,
    num_rows="dynamic",
    hide_index=True,
    key="de_otros_ingresos",
    column_config={
        "Titular (nombre)": st.column_config.TextColumn("Titular (nombre)"),
        "Relación": st.column_config.SelectboxColumn("Relación", options=relaciones, required=False),
        "Fuente de ingreso": st.column_config.SelectboxColumn("Fuente de ingreso", options=fuentes, required=False),
        "Periodicidad": st.column_config.SelectboxColumn("Periodicidad", options=periodicidades, required=False),
        "Monto por período (₡)": st.column_config.NumberColumn("Monto por período (₡)", min_value=0, step=1000, format="₡ %d"),
        "Verificado por asesor": st.column_config.CheckboxColumn("Verificado por asesor", default=False),
        "Tipo de evidencia": st.column_config.SelectboxColumn("Tipo de evidencia", options=evidencias, required=False),
        "Meses de continuidad": st.column_config.NumberColumn("Meses de continuidad", min_value=0, max_value=480, step=1, format="%d"),
        "Prob. continuidad (0–10)": st.column_config.NumberColumn("Prob. continuidad (0–10)", min_value=0, max_value=10, step=1, format="%d"),
        "Comentario": st.column_config.TextColumn("Comentario"),
    },
)

# --- Cálculos ---
df = df_in.copy()
num_cols = ["Monto por período (₡)", "Meses de continuidad", "Prob. continuidad (0–10)"]
for c in num_cols:
    if c not in df.columns:
        df[c] = 0
    df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
if "Verificado por asesor" not in df.columns:
    df["Verificado por asesor"] = False
df["Verificado por asesor"] = df["Verificado por asesor"].fillna(False).astype(bool)

def _recalcular_derivados(df_src: pd.DataFrame) -> pd.DataFrame:
    mensualizados, factores, ponderados = [], [], []
    for _, r in df_src.iterrows():
        monto = float(r.get("Monto por período (₡)") or 0)
        per = r.get("Periodicidad") or ""
        verif = bool(r.get("Verificado por asesor") or False)
        evid = r.get("Tipo de evidencia") or ""
        meses_cont = int(r.get("Meses de continuidad") or 0)
        prob = int(r.get("Prob. continuidad (0–10)") or 0)
        m_mensual = _mensualizar(monto, per)
        f_conf = _factor_confiabilidad_ingreso(verif, evid, meses_cont, prob)
        mensualizados.append(m_mensual)
        factores.append(f_conf)
        ponderados.append(m_mensual * f_conf)
    df_out = df_src.copy()
    df_out["Ingreso mensualizado (₡)"] = pd.Series(mensualizados).round(0).astype(int)
    df_out["Factor confiabilidad (0.2–1.0)"] = pd.Series(factores).round(2)
    df_out["Ingreso ponderado (₡)"] = pd.Series(ponderados).round(0).astype(int)
    return df_out

df = _recalcular_derivados(df)

# Editor con cálculos dentro del expander
df_edit = df.copy()
with st.expander("Editar tabla con cálculos (factor congelado)"):
    df_edit = st.data_editor(
        df,
        use_container_width=True,
        num_rows="dynamic",
        hide_index=True,
        key="de_otros_ingresos_calc",
        column_config={
            "Titular (nombre)": st.column_config.TextColumn("Titular (nombre)"),
            "Relación": st.column_config.SelectboxColumn("Relación", options=relaciones),
            "Fuente de ingreso": st.column_config.SelectboxColumn("Fuente de ingreso", options=fuentes),
            "Periodicidad": st.column_config.SelectboxColumn("Periodicidad", options=periodicidades),
            "Monto por período (₡)": st.column_config.NumberColumn("Monto por período (₡)", min_value=0, step=1000, format="₡ %d"),
            "Verificado por asesor": st.column_config.CheckboxColumn("Verificado por asesor", default=False),
            "Tipo de evidencia": st.column_config.SelectboxColumn("Tipo de evidencia", options=evidencias),
            "Meses de continuidad": st.column_config.NumberColumn("Meses de continuidad", min_value=0, max_value=480, step=1, format="%d"),
            "Prob. continuidad (0–10)": st.column_config.NumberColumn("Prob. continuidad (0–10)", min_value=0, max_value=10, step=1, format="%d"),
            "Comentario": st.column_config.TextColumn("Comentario"),
            "Ingreso mensualizado (₡)": st.column_config.NumberColumn("Ingreso mensualizado (₡)", format="₡ %d", disabled=True),
            "Factor confiabilidad (0.2–1.0)": st.column_config.NumberColumn("Factor confiabilidad (0.2–1.0)", format="%.2f", disabled=True),
            "Ingreso ponderado (₡)": st.column_config.NumberColumn("Ingreso ponderado (₡)", format="₡ %d", disabled=True),
        },
    )

# Recalcular por si hubo cambios
for c in num_cols:
    if c not in df_edit.columns:
        df_edit[c] = 0
    df_edit[c] = pd.to_numeric(df_edit[c], errors="coerce").fillna(0)
if "Verificado por asesor" not in df_edit.columns:
    df_edit["Verificado por asesor"] = False
df_edit["Verificado por asesor"] = df_edit["Verificado por asesor"].fillna(False).astype(bool)
df = _recalcular_derivados(df_edit)

# --- Resumen ---
valid_mask = (df["Monto por período (₡)"] > 0) & (df["Periodicidad"].isin(periodicidades))
df_valid = df[valid_mask].copy()
total_mensual = int(df_valid["Ingreso mensualizado (₡)"].sum()) if not df_valid.empty else 0
total_ponderado = int(df_valid["Ingreso ponderado (₡)"].sum()) if not df_valid.empty else 0
total_verif_mensual = int(df_valid.loc[df_valid["Verificado por asesor"], "Ingreso mensualizado (₡)"].sum()) if not df_valid.empty else 0

st.markdown("**Resumen**")
st.write({
    "Total mensualizado (bruto)": f"₡ {total_mensual:,}".replace(",", "."),
    "Total verificado (mensualizado)": f"₡ {total_verif_mensual:,}".replace(",", "."),
    "Total ponderado por confiabilidad": f"₡ {total_ponderado:,}".replace(",", "."),
    "Registros válidos": int(valid_mask.sum()),
})

st.divider()

from utils.db import save_otros_ingresos

# Navegación / Guardar
st.divider()

# ✅ Nueva opción: marcar si no hay otros ingresos
sin_otros = st.checkbox("No hay otros ingresos en el hogar")

c1, c2 = st.columns([0.5, 0.5])
with c1:
    if st.button("⬅️ Volver a 07 – Conciliación", key="otros_back_res", use_container_width=True):
        for prev_page in ["pages/07_Conciliación_de_ventas.py", "pages/07_Conciliacion_de_ventas.py"]:
            try:
                st.switch_page(prev_page)
                break
            except Exception:
                continue
with c2:
    if st.button(
        "Guardar y continuar ➡️",
        key="otros_save_next",
        use_container_width=True,
        disabled=(not sin_otros and valid_mask.sum() == 0)
    ):
        st.session_state.setdefault("reporte", {})

        if sin_otros:
            # Guardamos totales en cero explícitamente
            st.session_state["reporte"]["otros_ingresos"] = {
                "tabla": [],
                "totales": {
                    "total_mensualizado_colones": 0,
                    "total_verificado_mensualizado_colones": 0,
                    "total_ponderado_colones": 0,
                    "registros_validos": 0,
                }
            }
            # Persistimos en BD un registro vacío (opcional, según diseño)
            save_otros_ingresos(
                cliente_id=st.session_state["cliente"]["identificacion"],
                mes_iso=st.session_state["mes_iso"],
                df=pd.DataFrame([])  # DataFrame vacío
            )
        else:
            # Guardamos en sesión
            st.session_state["reporte"]["otros_ingresos"] = {
                "tabla": df.fillna("").to_dict(orient="records"),
                "totales": {
                    "total_mensualizado_colones": total_mensual,
                    "total_verificado_mensualizado_colones": total_verif_mensual,
                    "total_ponderado_colones": total_ponderado,
                    "registros_validos": int(valid_mask.sum()),
                }
            }
            # Persistimos en BD
            ok = save_otros_ingresos(
                cliente_id=st.session_state["cliente"]["identificacion"],
                mes_iso=st.session_state["mes_iso"],
                df=df if not df_valid.empty else df  # 👈 aseguramos que siempre se intente guardar
            )
            
            if ok:
                st.success("Otros ingresos guardados en la base de datos")
            else:
                st.error("No se pudieron guardar los otros ingresos en la base de datos")

        st.session_state["done_08"] = True
        try:
            st.switch_page("pages/09_Deudas.py")
        except Exception:
            st.success("Otros ingresos guardados. Abrí **Paso 9 – Deudas** desde el menú lateral.")
            st.stop()


