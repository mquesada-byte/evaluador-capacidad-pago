# =========================
# PASO 1 – Datos del asesor de crédito
# =========================

# app.py – Paso 1: Datos del asesor (hora OK + geolocalización robusta y compatible + links de mapa estables)
import time
import datetime as dt
from zoneinfo import ZoneInfo
import requests
import streamlit as st
from streamlit_js_eval import get_geolocation

st.set_page_config(page_title="Evaluación Crédito - Paso 1", page_icon="🧭",  layout="centered")

# =========================
# Configuración y utilidades
# =========================
TZ = ZoneInfo("America/Costa_Rica")
USE_INTERNET_TIME = True  # dejar hora exacta por Internet si está disponible

# Parámetros de geolocalización (reintentos controlados)
MAX_RERUNS = 6     # ~6 intentos
SLEEP_SEC = 0.4    # pausa breve entre intentos

def now_in_cr_via_internet():
    """Intenta obtener hora exacta por internet; si falla, retorna None."""
    try:
        r = requests.get("https://worldtimeapi.org/api/timezone/America/Costa_Rica", timeout=5)
        r.raise_for_status()
        j = r.json()
        return dt.datetime.fromisoformat(j["datetime"].replace("Z", "+00:00")).astimezone(TZ)
    except Exception:
        return None

def now_in_cr_fallback():
    return dt.datetime.now(TZ)

def _coords_plausibles(lat, lon):
    try:
        lat = float(lat); lon = float(lon)
        return -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0
    except Exception:
        return False

# ---- Helpers para links de mapas (clave para evitar desvíos) ----
def maps_links(lat: float, lon: float):
    """Devuelve links estables a Google y OSM en orden lat,lon."""
    lat_s = f"{lat:.6f}"
    lon_s = f"{lon:.6f}"
    google = f"https://www.google.com/maps/search/?api=1&query={lat_s},{lon_s}"
    google_at = f"https://www.google.com/maps/@{lat_s},{lon_s},18z"
    osm = f"https://www.openstreetmap.org/?mlat={lat_s}&mlon={lon_s}#map=18/{lat_s}/{lon_s}"
    return google, google_at, osm

def swapped_links(lat: float, lon: float):
    """Links con orden invertido (lon,lat) por si el proveedor interpreta al revés."""
    lat_s = f"{lat:.6f}"
    lon_s = f"{lon:.6f}"
    google_sw = f"https://www.google.com/maps/search/?api=1&query={lon_s},{lat_s}"
    osm_sw = f"https://www.openstreetmap.org/?mlat={lon_s}&mlon={lat_s}#map=18/{lon_s}/{lat_s}"
    return google_sw, osm_sw

def plausible_cr_area(lat: float, lon: float) -> bool:
    """Chequeo rápido para Costa Rica (8–12 lat, -90–-80 lon aprox)."""
    return (8.0 <= lat <= 12.0) and (-90.0 <= lon <= -80.0)

# ==========
# Estado
# ==========
def init_asesor_state():
    st.session_state.setdefault("step", 1)
    st.session_state.setdefault("asesor", {})
    st.session_state.setdefault("geo_request", False)   # solicitar geolocalización
    st.session_state.setdefault("geo_status", "idle")   # idle|waiting|ok|denied|timeout|unavailable|error
    st.session_state.setdefault("geo_attempts", 0)      # contador de intentos

    asesor = st.session_state.asesor
    asesor.setdefault("nombre", "")

    # === HORA: NO TOCAR (queda como te gustó) ===
    if "fecha_hora" not in asesor:
        ts = None
        if USE_INTERNET_TIME:
            ts = now_in_cr_via_internet()
            asesor["timestamp_source"] = "internet" if ts else "device"
        if ts is None:
            ts = now_in_cr_fallback()
            asesor["timestamp_source"] = "device"
        asesor["fecha_hora"] = ts  # se fija 1 vez e inmutable para el usuario
    # ============================================

    asesor.setdefault("lat", None)
    asesor.setdefault("lon", None)
    asesor.setdefault("maps_url", None)
    asesor.setdefault("maps_url_alt", None)
    asesor.setdefault("osm_url", None)

init_asesor_state()
asesor = st.session_state.asesor

# ------- Helper para empaquetar datos del asesor al reporte -------
def asesor_para_reporte():
    a = st.session_state.get("asesor", {})
    fecha = a.get("fecha_hora")
    fecha_str = fecha.strftime("%d/%m/%Y %H:%M:%S") if fecha else "N/D"
    lat = a.get("lat"); lon = a.get("lon")
    gps_str = f"{lat:.6f}, {lon:.6f}" if lat is not None and lon is not None else "No disponible"
    return {
        "nombre": a.get("nombre", "").strip(),
        "fecha_hora": fecha_str,
        "hora_fuente": "Internet" if a.get("timestamp_source") == "internet" else "Dispositivo",
        "gps": gps_str,
        "google_maps": a.get("maps_url"),
        "google_maps_vista": a.get("maps_url_alt"),
        "openstreetmap": a.get("osm_url"),
    }

# ==========
# Interfaz UI
# ==========
st.title("🧭 Paso 1: Datos del asesor")
st.caption("Complete la información. La fecha y hora se registran automáticamente y no pueden ser modificadas.")

# Nombre (obligatorio)
asesor["nombre"] = st.text_input(
    "Nombre completo del asesor *",
    value=asesor["nombre"],
    placeholder="Ej.: María Pérez Delgado",
)

# Fecha y hora (solo lectura) — indicador de fuente
fecha_hora_registro = asesor["fecha_hora"].strftime("%d/%m/%Y %H:%M:%S")
st.text_input(
    "📅 Fecha y hora de registro",
    value=fecha_hora_registro + (" (Internet)" if asesor.get("timestamp_source") == "internet" else " (Dispositivo)"),
    disabled=True
)

# ===========================
# Ubicación GPS (opcional) – ROBUSTA y COMPATIBLE
# ===========================
st.write("**Ubicación GPS (opcional)**")
col1, col2 = st.columns([0.45, 0.55])

with col1:
    if st.button("📍 Obtener mi ubicación"):
        st.session_state.geo_request = True
        st.session_state.geo_status = "waiting"
        st.session_state.geo_attempts = 0
        asesor["lat"] = None
        asesor["lon"] = None
        asesor["maps_url"] = None
        asesor["maps_url_alt"] = None
        asesor["osm_url"] = None
        st.rerun()

    # Ejecutar fuera del botón para capturar el resultado en reruns
    if st.session_state.geo_request and st.session_state.geo_status != "ok":
        try:
            # Llamada sin parámetros (compatibilidad con tu versión de streamlit_js_eval)
            loc = get_geolocation()
        except Exception:
            loc = None  # si la lib falla, seguimos con reintentos amables

        if isinstance(loc, dict):
            # Distintas formas posibles de la respuesta según versión
            coords = loc.get("coords") or {}
            lat = coords.get("latitude")
            lon = coords.get("longitude")

            # Algunas variantes ponen errores en 'msg'/'message'
            msg = (loc.get("msg") or loc.get("message") or "").lower()

            # Éxito con coordenadas plausibles
            if lat is not None and lon is not None and _coords_plausibles(lat, lon):
                asesor["lat"] = float(lat)
                asesor["lon"] = float(lon)
                g, g_at, osm = maps_links(asesor["lat"], asesor["lon"])
                asesor["maps_url"] = g
                asesor["maps_url_alt"] = g_at
                asesor["osm_url"] = osm
                st.session_state.geo_status = "ok"
                st.session_state.geo_request = False

            # Errores explícitos
            elif "denied" in msg:
                st.session_state.geo_status = "denied"
                st.session_state.geo_request = False
            elif "timeout" in msg:
                st.session_state.geo_status = "timeout"
                st.session_state.geo_request = False
            elif "unavailable" in msg:
                st.session_state.geo_status = "unavailable"
                st.session_state.geo_request = False

            # Sin coords ni error claro: reintenta con espera corta
            else:
                st.session_state.geo_attempts += 1
                if st.session_state.geo_attempts < MAX_RERUNS:
                    with st.spinner("Solicitando permiso o esperando señal de GPS…"):
                        time.sleep(SLEEP_SEC)
                    st.rerun()
                else:
                    st.session_state.geo_status = "error"
                    st.session_state.geo_request = False
        else:
            # Primeros renders suelen devolver None: reintenta antes de declarar error
            st.session_state.geo_attempts += 1
            if st.session_state.geo_attempts < MAX_RERUNS:
                with st.spinner("Solicitando permiso o esperando señal de GPS…"):
                    time.sleep(SLEEP_SEC)
                st.rerun()
            else:
                st.session_state.geo_status = "error"
                st.session_state.geo_request = False

with col2:
    status = st.session_state.geo_status
    if asesor["lat"] is not None and asesor["lon"] is not None:
        lat, lon = asesor["lat"], asesor["lon"]
        st.success(f"Ubicación: {lat:.6f}, {lon:.6f}")

        # Enlaces confiables
        st.markdown(
            f"[Abrir en Google Maps]({asesor['maps_url']}) · "
            f"[Vista @18z]({asesor['maps_url_alt']}) · "
            f"[OpenStreetMap]({asesor['osm_url']})"
        )

        # Si parece fuera de Costa Rica, ofrece enlaces “invertidos”
        if not plausible_cr_area(lat, lon):
            g_sw, osm_sw = swapped_links(lat, lon)
            st.warning(
                "Las coordenadas no parecen estar en Costa Rica. "
                "Si el mapa abre en un lugar extraño, prueba el orden invertido:"
            )
            st.markdown(f"• [Google (invertido)]({g_sw}) · [OSM (invertido)]({osm_sw})")
    else:
        if status == "waiting":
            st.info("Solicitando permiso o esperando señal de GPS…")
        elif status == "denied":
            st.warning("Permiso de ubicación denegado en el navegador. Actívalo en el candado de la URL y vuelve a intentar.")
        elif status == "timeout":
            st.warning("Tiempo de espera agotado al obtener la ubicación.")
        elif status == "unavailable":
            st.warning("Ubicación no disponible en este dispositivo/red.")
        elif status == "error":
            st.warning("No fue posible obtener la ubicación en este momento. Puedes reintentar.")
        else:
            st.caption("Aún no hay coordenadas registradas.")

st.divider()

# ===========================
# Validación y navegación
# ===========================
disabled_next = not bool(asesor["nombre"].strip())
colA, colB = st.columns([0.7, 0.3])
with colA:
    st.write("Campo obligatorio: **Nombre del asesor**.")
with colB:
    if st.button("Siguiente ➡️", key="next_step_1", disabled=disabled_next, use_container_width=True):
        st.session_state.step = 2
        st.session_state.setdefault("reporte", {})
        st.session_state["reporte"]["asesor"] = asesor_para_reporte()
        st.success("Datos del asesor guardados. Avanzando al Paso 2…")
        st.rerun()


# =========================
# PASO 2 – Datos del cliente y del negocio
# =========================
def init_paso2_state():
    st.session_state.setdefault("cliente", {})
    st.session_state.setdefault("negocio", {})
    c = st.session_state.cliente
    n = st.session_state.negocio

    # Cliente
    c.setdefault("nombre_completo", "")
    c.setdefault("identificacion", "")

    # Negocio
    n.setdefault("nombre_comercial", "")
    n.setdefault("persona_juridica", False)          # True/False
    n.setdefault("ubicacion", "")
    n.setdefault("sector_economico", "")             # comercio/servicios/industria
    n.setdefault("actividad_principal", "")
    n.setdefault("patente_municipal", False)
    n.setdefault("registros_contables", False)
    n.setdefault("tipo_local", "")
    n.setdefault("antiguedad_anios", 0)
    n.setdefault("antiguedad_meses", 0)

def antiguedad_str(anios:int, meses:int) -> str:
    return f"{anios} año(s) y {meses} mes(es)"

if st.session_state.get("step") == 2:
    init_paso2_state()
    c = st.session_state.cliente
    n = st.session_state.negocio

    st.title("👤 Paso 2: Datos del cliente y del negocio")
    st.caption("Complete los campos. Los marcados con * son obligatorios.")

    with st.container():
        st.subheader("Datos del cliente")
        col1, col2 = st.columns(2)
        with col1:
            c["nombre_completo"] = st.text_input(
                "Nombre completo *",
                value=c["nombre_completo"],
                placeholder="Ej.: Juan Carlos Rodríguez"
            )
        with col2:
            c["identificacion"] = st.text_input(
                "Número de identificación (cédula, DIMEX, pasaporte) *",
                value=c["identificacion"],
                placeholder="Ej.: 1-2345-0678"
            )

    st.divider()

    st.subheader("Datos del negocio")
    colA, colB = st.columns(2)
    with colA:
        n["nombre_comercial"] = st.text_input(
            "Nombre comercial del negocio *",
            value=n["nombre_comercial"],
            placeholder="Ej.: Mini Súper La Esquina"
        )
        n["persona_juridica"] = st.selectbox(
            "¿Es persona jurídica?",
            options=["No", "Sí"],
            index=1 if n["persona_juridica"] else 0
        ) == "Sí"
        n["sector_economico"] = st.selectbox(
            "Sector económico *",
            options=["", "Comercio", "Servicios", "Industria"],
            index=["", "Comercio", "Servicios", "Industria"].index(n["sector_economico"]) if n["sector_economico"] in ["", "Comercio", "Servicios", "Industria"] else 0
        )
        n["actividad_principal"] = st.text_input(
            "Actividad económica principal *",
            value=n["actividad_principal"],
            placeholder="Ej.: Tienda de abarrotes / Salón de belleza / Agricultura"
        )
    with colB:
        n["ubicacion"] = st.text_area(
            "Ubicación del negocio (dirección física)",
            value=n["ubicacion"],
            placeholder="Provincia, cantón, distrito, señas…",
            height=96
        )
        n["patente_municipal"] = st.selectbox(
            "¿Cuenta con patente municipal?",
            options=["No", "Sí"],
            index=1 if n["patente_municipal"] else 0
        ) == "Sí"
        n["registros_contables"] = st.selectbox(
            "¿Lleva registros contables?",
            options=["No", "Sí"],
            index=1 if n["registros_contables"] else 0
        ) == "Sí"

    colC, colD = st.columns([0.5, 0.5])
    with colC:
        n["tipo_local"] = st.selectbox(
            "Tipo de local *",
            options=["", "Propio", "Alquilado", "Ambulante", "Casa de habitación", "Otro"],
            index=["", "Propio", "Alquilado", "Ambulante", "Casa de habitación", "Otro"].index(n["tipo_local"]) if n["tipo_local"] in ["", "Propio", "Alquilado", "Ambulante", "Casa de habitación", "Otro"] else 0
        )
    with colD:
        st.markdown("**Antigüedad del negocio (años/meses en operación)***")
        colY, colZ = st.columns(2)
        with colY:
            n["antiguedad_anios"] = st.number_input(
                "Años", min_value=0, max_value=80, step=1, value=int(n["antiguedad_anios"])
            )
        with colZ:
            n["antiguedad_meses"] = st.number_input(
                "Meses", min_value=0, max_value=11, step=1, value=int(n["antiguedad_meses"])
            )
        st.caption(f"Antigüedad: {antiguedad_str(n['antiguedad_anios'], n['antiguedad_meses'])}")

    st.divider()

    # -------- Validación obligatorios --------
    obligatorios_ok = all([
        c["nombre_completo"].strip(),
        c["identificacion"].strip(),
        n["nombre_comercial"].strip(),
        n["sector_economico"] in ["Comercio", "Servicios", "Industria"],
        n["actividad_principal"].strip(),
        n["tipo_local"] in ["Propio", "Alquilado", "Ambulante", "Casa de habitación", "Otro"],
        (n["antiguedad_anios"] > 0 or n["antiguedad_meses"] > 0)
    ])

    colNav1, colNav2 = st.columns([0.5, 0.5])
    with colNav1:
        if st.button("⬅️ Volver al Paso 1", key="back_to_step_1", use_container_width=True):
            st.session_state.step = 1
            st.rerun()
    with colNav2:
        # Guardar y avanzar
        if st.button("Siguiente ➡️", key="next_step_2", disabled=not obligatorios_ok, use_container_width=True):
            # preparar bloque de reporte
            st.session_state.setdefault("reporte", {})
            st.session_state["reporte"]["cliente_negocio"] = {
                "cliente_nombre": c["nombre_completo"].strip(),
                "cliente_identificacion": c["identificacion"].strip(),
                "nombre_comercial": n["nombre_comercial"].strip(),
                "persona_juridica": "Sí" if n["persona_juridica"] else "No",
                "ubicacion": n["ubicacion"].strip(),
                "sector_economico": n["sector_economico"],
                "actividad_principal": n["actividad_principal"].strip(),
                "patente_municipal": "Sí" if n["patente_municipal"] else "No",
                "registros_contables": "Sí" if n["registros_contables"] else "No",
                "tipo_local": n["tipo_local"],
                "antiguedad": antiguedad_str(n["antiguedad_anios"], n["antiguedad_meses"]),
            }
            st.session_state.step = 3
            st.success("Datos guardados. Avanzando al Paso 3…")
            st.rerun()


# =========================
# PASO 3A – Ventas (Top-down / declaración directa)
# =========================
def _mes_anterior_label():
    """Devuelve ('mes nombre año', 'YYYY-MM') del mes calendario anterior en TZ CR."""
    now = dt.datetime.now(TZ)
    year, month = now.year, now.month
    if month == 1:
        prev_year, prev_month = year - 1, 12
    else:
        prev_year, prev_month = year, month - 1
    meses_es = ["enero","febrero","marzo","abril","mayo","junio",
                "julio","agosto","septiembre","octubre","noviembre","diciembre"]
    etiqueta = f"{meses_es[prev_month-1]} {prev_year}"
    iso_ym = f"{prev_year:04d}-{prev_month:02d}"
    return etiqueta, iso_ym

def init_paso3A_state():
    st.session_state.setdefault("step3", "A")  # subpaso dentro del paso 3
    st.session_state.setdefault("ventas_topdown", {})
    vtd = st.session_state.ventas_topdown
    vtd.setdefault("monto", 0)
    vtd.setdefault("tipicidad", "")  # "", "Típico", "Alto", "Bajo"
    vtd.setdefault("fuente", "")     # lista de opciones abajo
    vtd.setdefault("fuente_otro", "")
    vtd.setdefault("confianza_cliente", 5)  # 0–10
    vtd.setdefault("comentario", "")

if st.session_state.get("step") == 3 and st.session_state.get("step3", "A") == "A":
    init_paso3A_state()
    vtd = st.session_state.ventas_topdown
    mes_etiqueta, mes_iso = _mes_anterior_label()

    st.title("📈 Paso 3A: Ventas – Top-down (declaración directa)")
    st.caption(f"Ingrese las ventas del último mes calendario: **{mes_etiqueta}**.")

    with st.container():
        col1, col2 = st.columns([0.55, 0.45])
        with col1:
            vtd["monto"] = st.number_input(
                f"Ventas de {mes_etiqueta} (₡) *",
                min_value=0, step=1000, value=int(vtd["monto"]),
                help="Monto total vendido en el mes calendario anterior."
            )
            vtd["tipicidad"] = st.selectbox(
                "¿Ese mes fue…? *",
                options=["", "Típico", "Alto", "Bajo"],
                index=["", "Típico", "Alto", "Bajo"].index(vtd["tipicidad"]) if vtd["tipicidad"] in ["", "Típico", "Alto", "Bajo"] else 0,
                help="Cómo se compara ese mes con un mes normal del negocio."
            )
        with col2:
            fuente_opts = [
                "", "Facturación electrónica", "POS/Datáfono",
                "Extractos bancarios/SINPE", "Cuaderno/Excel", "Memoria", "Otro"
            ]
            vtd["fuente"] = st.selectbox(
                "Fuente del dato *",
                options=fuente_opts,
                index=fuente_opts.index(vtd["fuente"]) if vtd["fuente"] in fuente_opts else 0,
                help="De dónde sale el monto declarado."
            )
            if vtd["fuente"] == "Otro":
                vtd["fuente_otro"] = st.text_input(
                    "Especifique la fuente",
                    value=vtd.get("fuente_otro", "")
                )
            vtd["confianza_cliente"] = st.slider(
                "Confianza declarada por el cliente (0–10)",
                min_value=0, max_value=10, step=1, value=int(vtd["confianza_cliente"]),
                help="En una escala de 0 a 10, ¿qué tan seguro está del monto del último mes?"
            )

    vtd["comentario"] = st.text_area(
        "Comentario (opcional)",
        value=vtd["comentario"],
        placeholder="Notas breves: p. ej., promociones, feriados, cierres, etc.",
        height=80
    )

    st.divider()

    # -------- Validación obligatorios --------
    fuente_valida = (vtd["fuente"] and vtd["fuente"] != "Otro") or (vtd["fuente"] == "Otro" and vtd["fuente_otro"].strip())
    obligatorios_ok = all([
        vtd["monto"] > 0,
        vtd["tipicidad"] in ["Típico", "Alto", "Bajo"],
        fuente_valida
    ])

    colNav1, colNav2 = st.columns([0.5, 0.5])
    with colNav1:
        if st.button("⬅️ Volver al Paso 2", key="back_to_step_2", use_container_width=True):
            st.session_state.step = 2
            st.rerun()

    with colNav2:
        if st.button("Siguiente ➡️ (3B)", key="next_step_3A", disabled=not obligatorios_ok, use_container_width=True):
            # Guardar bloque de reporte Top-down
            st.session_state.setdefault("reporte", {})
            fuente_final = vtd["fuente_otro"].strip() if vtd["fuente"] == "Otro" else vtd["fuente"]
            st.session_state["reporte"]["ventas_topdown"] = {
                "mes_referencia": mes_etiqueta,
                "mes_iso": mes_iso,  # YYYY-MM para cálculos
                "monto_colones": int(vtd["monto"]),
                "tipicidad": vtd["tipicidad"],
                "fuente": fuente_final,
                "confianza_cliente_0a10": int(vtd["confianza_cliente"]),
                "comentario": vtd["comentario"].strip(),
            }
            # Avanza al siguiente subpaso (3B)
            st.session_state.step = 3
            st.session_state.step3 = "B"
            st.success("Top-down guardado. Avanzando a 3B…")
            st.rerun()


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


# =========================
# PASO 5 – Otros ingresos del hogar (step == 4)
# =========================
def _mensualizar(monto: float, periodicidad: str) -> float:
    """Convierte monto por período a monto mensual aproximado."""
    per = (periodicidad or "").lower()
    if per == "diario":       return monto * 30.0
    if per == "semanal":      return monto * (52.0 / 12.0)  # ≈4.333
    if per == "quincenal":    return monto * 2.0
    if per == "mensual":      return monto
    if per == "bimestral":    return monto / 2.0
    if per == "trimestral":   return monto / 3.0
    if per == "semestral":    return monto / 6.0
    if per == "anual":        return monto / 12.0
    return 0.0

def _factor_verificacion(verificado: bool, evidencia: str) -> float:
    """Factor por verificación y tipo de evidencia (1.00 = máxima)."""
    if not verificado:
        return 0.70
    ev = (evidencia or "").lower()
    # Evidencias fuertes
    if ev in ["facturación electrónica", "extractos bancarios", "extractos bancarios/sinpe",
              "contrato", "certificación"]:
        return 1.00
    # Evidencias moderadas (incluye bureaus)
    if ev in ["recibos", "comprobantes", "pos/datáfono", "captura pos", "captura sinpe",
              "credid", "equifax"]:
        return 0.90
    # Evidencias débiles
    if ev in ["foto/chat", "whatsapp", "mensaje", "captura pantalla", "otro"]:
        return 0.80
    # Verificado sin documento fuerte (p. ej., constatación in situ)
    if ev in ["", "no aplica", None]:
        return 0.85
    return 0.85

def _factor_estabilidad(meses_cont: int) -> float:
    """Factor por continuidad del ingreso en meses."""
    m = int(meses_cont or 0)
    if m >= 24: return 1.00
    if m >= 12: return 0.90
    if m >= 6:  return 0.80
    if m >= 3:  return 0.60
    if m >= 1:  return 0.50
    return 0.40

def _factor_probabilidad(prob_0a10: int) -> float:
    """Factor por probabilidad de continuidad declarada (0–10 → 0.50–1.00)."""
    p = max(0, min(10, int(prob_0a10 or 0)))
    return 0.50 + 0.05 * p

def _factor_confiabilidad_ingreso(verificado: bool, evidencia: str, meses_cont: int, prob_0a10: int) -> float:
    """Multiplicativo con límites de seguridad (0.20–1.00)."""
    f = _factor_verificacion(verificado, evidencia) \
        * _factor_estabilidad(meses_cont) \
        * _factor_probabilidad(prob_0a10)
    return max(0.20, min(1.00, f))

if st.session_state.get("step") == 4:
    import pandas as pd

    st.title("💸 Paso 5: Otros ingresos del hogar")
    st.caption("Registre otros ingresos del cliente y su núcleo familiar. Cada ingreso debe indicar si fue **verificado por el asesor** y con qué evidencia.")

    # --- Data Editor base (captura rápida) ---
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

    placeholder_rows = pd.DataFrame([{c: "" for c in base_cols}] * 4)
    df_in = st.data_editor(
        placeholder_rows,
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

    # --- Cálculos y tabla con cálculos (factor congelado) ---
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
            f_conf = _factor_confiabilidad_ingreso(verif, evid, meses_cont, prob)  # SIEMPRE calculado
            mensualizados.append(m_mensual)
            factores.append(f_conf)
            ponderados.append(m_mensual * f_conf)

        df_out = df_src.copy()
        df_out["Ingreso mensualizado (₡)"] = pd.Series(mensualizados).round(0).astype(int)
        df_out["Factor confiabilidad (0.2–1.0)"] = pd.Series(factores).round(2)
        df_out["Ingreso ponderado (₡)"] = pd.Series(ponderados).round(0).astype(int)
        return df_out

    df = _recalcular_derivados(df)

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
                # Derivadas (solo lectura, FACTOR CONGELADO)
                "Ingreso mensualizado (₡)": st.column_config.NumberColumn("Ingreso mensualizado (₡)", format="₡ %d", disabled=True),
                "Factor confiabilidad (0.2–1.0)": st.column_config.NumberColumn("Factor confiabilidad (0.2–1.0)", format="%.2f", disabled=True),
                "Ingreso ponderado (₡)": st.column_config.NumberColumn("Ingreso ponderado (₡)", format="₡ %d", disabled=True),
            },
        )

    # Recalcular (por si cambiaron entradas en el editor)
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

    # Navegación / Guardar
    c1, c2 = st.columns([0.5, 0.5])
    with c1:
        if st.button("⬅️ Volver a Conciliación", key="otros_back_res", use_container_width=True):
            st.session_state.step = 3
            st.session_state.step3 = "RES"
            st.rerun()
    with c2:
        if st.button("Guardar y continuar ➡️", key="otros_save_next", use_container_width=True, disabled=(valid_mask.sum() == 0)):
            st.session_state.setdefault("reporte", {})
            st.session_state["reporte"]["otros_ingresos"] = {
                "tabla": df.fillna("").to_dict(orient="records"),
                "totales": {
                    "total_mensualizado_colones": total_mensual,
                    "total_verificado_mensualizado_colones": total_verif_mensual,
                    "total_ponderado_colones": total_ponderado,
                    "registros_validos": int(valid_mask.sum()),
                }
            }
            st.success("Otros ingresos guardados. Avanzando…")
            st.session_state.step = 5
            st.rerun()


# =========================
# PASO 6 – Deudas activas del hogar (step == 5)
# =========================
def _mensualizar_pago(monto: float, periodicidad: str) -> float:
    """Convierte una cuota por período a cuota mensual aproximada."""
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

if st.session_state.get("step") == 5:
    import pandas as pd

    st.title("💳 Paso 6: Deudas activas del hogar")
    st.caption(
        "Registre los préstamos/obligaciones vigentes del cliente o su núcleo. "
        "Se calculará la **cuota mensual total** (para resultados) y el **saldo total adeudado** (para balance). "
        "Incluye **clasificación por plazo** para separar **pasivo circulante** y **pasivo a largo plazo**."
    )

    # Catálogos
    relaciones = ["Cliente", "Pareja", "Hogar (compartida)", "Otro"]
    tipos_deuda = ["Préstamo personal", "Préstamo de negocio", "Hipotecario", "Vehículo",
                   "Tarjeta de crédito", "Comercio/Tienda", "Microcrédito", "Otro"]
    periodicidades_pago = ["Mensual", "Quincenal", "Semanal", "Diario", "Bimestral", "Trimestral", "Semestral", "Anual"]
    evidencias = ["Estado de cuenta", "Contrato", "Tabla de amortización", "Recibo de pago",
                  "SINPE/Extracto", "Credid", "Equifax", "Foto/Chat", "No aplica", "Otro"]
    estados = ["Al día", "Atraso"]

    # NUEVO: catálogo de plazo
    plazos = ["Corto plazo (≤12 meses)", "Largo plazo (>12 meses)"]

    # Columnas base (entrada)
    base_cols = [
        "Titular",                    # relación con el cliente
        "Acreedor/Entidad",          # banco/financiera/tienda
        "Tipo de deuda",             # catálogo
        "Saldo adeudado (₡)",        # saldo actual
        "Cuota por período (₡)",     # monto de la cuota en la periodicidad indicada
        "Periodicidad de pago",      # catálogo
        "Verificado por asesor",     # bool
        "Tipo de evidencia",         # catálogo
        "Estado",                    # al día/atraso
        "Días de atraso",            # número (opcional)
        "Comentario",                # texto
        # NUEVOS CAMPOS
        "Meses restantes (opcional)",   # num (si se indica, auto-clasifica plazo)
        "Plazo (clasificación)",        # corto / largo
    ]

    # Editor de captura rápido (con nuevas columnas)
    placeholder_rows = pd.DataFrame([{c: "" for c in base_cols}] * 4)
    df_in = st.data_editor(
        placeholder_rows,
        use_container_width=True,
        num_rows="dynamic",
        hide_index=True,
        key="de_deudas_activas",
        column_config={
            "Titular": st.column_config.SelectboxColumn("Titular", options=relaciones, required=False),
            "Acreedor/Entidad": st.column_config.TextColumn("Acreedor/Entidad"),
            "Tipo de deuda": st.column_config.SelectboxColumn("Tipo de deuda", options=tipos_deuda, required=False),
            "Saldo adeudado (₡)": st.column_config.NumberColumn("Saldo adeudado (₡)", min_value=0, step=10000, format="₡ %d"),
            "Cuota por período (₡)": st.column_config.NumberColumn("Cuota por período (₡)", min_value=0, step=1000, format="₡ %d"),
            "Periodicidad de pago": st.column_config.SelectboxColumn("Periodicidad de pago", options=periodicidades_pago, required=False),
            "Verificado por asesor": st.column_config.CheckboxColumn("Verificado por asesor", default=False),
            "Tipo de evidencia": st.column_config.SelectboxColumn("Tipo de evidencia", options=evidencias, required=False),
            "Estado": st.column_config.SelectboxColumn("Estado", options=estados, required=False),
            "Días de atraso": st.column_config.NumberColumn("Días de atraso", min_value=0, max_value=3650, step=1, format="%d"),
            "Comentario": st.column_config.TextColumn("Comentario"),
            # NUEVOS
            "Meses restantes (opcional)": st.column_config.NumberColumn("Meses restantes (opcional)", min_value=0, max_value=600, step=1, format="%d"),
            "Plazo (clasificación)": st.column_config.SelectboxColumn("Plazo (clasificación)", options=plazos, required=False),
        },
    )

    # --- Preparación y derivados ---
    df = df_in.copy()

    # Asegurar tipos numéricos
    for c in ["Saldo adeudado (₡)", "Cuota por período (₡)", "Días de atraso", "Meses restantes (opcional)"]:
        if c not in df.columns:
            df[c] = 0
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    if "Verificado por asesor" not in df.columns:
        df["Verificado por asesor"] = False
    df["Verificado por asesor"] = df["Verificado por asesor"].fillna(False).astype(bool)

    # AUTOCLASIFICACIÓN DE PLAZO (si hay meses restantes y no seleccionaron plazo)
    if "Plazo (clasificación)" not in df.columns:
        df["Plazo (clasificación)"] = ""
    df["Plazo (clasificación)"] = df["Plazo (clasificación)"].astype(str)

    auto_mask = df["Plazo (clasificación)"].isin(["", "nan", "None"])
    df.loc[auto_mask & (df["Meses restantes (opcional)"] > 0) & (df["Meses restantes (opcional)"] <= 12),
           "Plazo (clasificación)"] = "Corto plazo (≤12 meses)"
    df.loc[auto_mask & (df["Meses restantes (opcional)"] > 12),
           "Plazo (clasificación)"] = "Largo plazo (>12 meses)"

    # Calcular cuota mensualizada y campos bloqueados
    cuotas_mens = []
    for _, r in df.iterrows():
        cuota = float(r.get("Cuota por período (₡)") or 0)
        per = r.get("Periodicidad de pago") or ""
        cuotas_mens.append(_mensualizar_pago(cuota, per))
    df["Cuota mensualizada (₡)"] = pd.Series(cuotas_mens).round(0).astype(int)

    # Editor con cálculos (derivadas bloqueadas)
    with st.expander("Editar tabla con cálculos (derivados bloqueados)"):
        df_edit = st.data_editor(
            df,
            use_container_width=True,
            num_rows="dynamic",
            hide_index=True,
            key="de_deudas_activas_calc",
            column_config={
                "Titular": st.column_config.SelectboxColumn("Titular", options=relaciones),
                "Acreedor/Entidad": st.column_config.TextColumn("Acreedor/Entidad"),
                "Tipo de deuda": st.column_config.SelectboxColumn("Tipo de deuda", options=tipos_deuda),
                "Saldo adeudado (₡)": st.column_config.NumberColumn("Saldo adeudado (₡)", min_value=0, step=10000, format="₡ %d"),
                "Cuota por período (₡)": st.column_config.NumberColumn("Cuota por período (₡)", min_value=0, step=1000, format="₡ %d"),
                "Periodicidad de pago": st.column_config.SelectboxColumn("Periodicidad de pago", options=periodicidades_pago),
                "Verificado por asesor": st.column_config.CheckboxColumn("Verificado por asesor", default=False),
                "Tipo de evidencia": st.column_config.SelectboxColumn("Tipo de evidencia", options=evidencias),
                "Estado": st.column_config.SelectboxColumn("Estado", options=estados),
                "Días de atraso": st.column_config.NumberColumn("Días de atraso", min_value=0, max_value=3650, step=1, format="%d"),
                "Comentario": st.column_config.TextColumn("Comentario"),
                # Nuevos de plazo
                "Meses restantes (opcional)": st.column_config.NumberColumn("Meses restantes (opcional)", min_value=0, max_value=600, step=1, format="%d"),
                "Plazo (clasificación)": st.column_config.SelectboxColumn("Plazo (clasificación)", options=plazos),
                # Derivadas bloqueadas
                "Cuota mensualizada (₡)": st.column_config.NumberColumn("Cuota mensualizada (₡)", format="₡ %d", disabled=True),
            },
        )

    # Recalcular por si hubo cambios en el editor de cálculos
    for c in ["Saldo adeudado (₡)", "Cuota por período (₡)", "Días de atraso", "Meses restantes (opcional)"]:
        if c not in df_edit.columns:
            df_edit[c] = 0
        df_edit[c] = pd.to_numeric(df_edit[c], errors="coerce").fillna(0)
    if "Verificado por asesor" not in df_edit.columns:
        df_edit["Verificado por asesor"] = False
    df_edit["Verificado por asesor"] = df_edit["Verificado por asesor"].fillna(False).astype(bool)

    cuotas_mens = []
    for _, r in df_edit.iterrows():
        cuota = float(r.get("Cuota por período (₡)") or 0)
        per = r.get("Periodicidad de pago") or ""
        cuotas_mens.append(_mensualizar_pago(cuota, per))
    df = df_edit.copy()
    df["Cuota mensualizada (₡)"] = pd.Series(cuotas_mens).round(0).astype(int)

    # --- Resumen ---
    # Filas válidas: cuota o saldo con periodicidad definida
    valid_mask = (df["Periodicidad de pago"].isin(periodicidades_pago)) & \
                 ((df["Cuota por período (₡)"] > 0) | (df["Saldo adeudado (₡)"] > 0))
    df_valid = df[valid_mask].copy()

    total_pago_mensual = int(df_valid["Cuota mensualizada (₡)"].sum()) if not df_valid.empty else 0
    total_adeudado = int(df_valid["Saldo adeudado (₡)"].sum()) if not df_valid.empty else 0
    total_pago_verificado = int(df_valid.loc[df_valid["Verificado por asesor"], "Cuota mensualizada (₡)"].sum()) if not df_valid.empty else 0

    # NUEVO: totales por plazo para Balance
    corto_mask = df_valid["Plazo (clasificación)"].eq("Corto plazo (≤12 meses)")
    largo_mask = df_valid["Plazo (clasificación)"].eq("Largo plazo (>12 meses)")
    total_adeudado_corto = int(df_valid.loc[corto_mask, "Saldo adeudado (₡)"].sum()) if not df_valid.empty else 0
    total_adeudado_largo = int(df_valid.loc[largo_mask, "Saldo adeudado (₡)"].sum()) if not df_valid.empty else 0

    st.markdown("**Resumen**")
    st.write({
        "Total pago mensual (a Resultados)": f"₡ {total_pago_mensual:,}".replace(",", "."),
        "Total pago mensual verificado": f"₡ {total_pago_verificado:,}".replace(",", "."),
        "Total adeudado (a Balance general)": f"₡ {total_adeudado:,}".replace(",", "."),
        "→ Pasivo circulante (corto plazo)": f"₡ {total_adeudado_corto:,}".replace(",", "."),
        "→ Pasivo a largo plazo": f"₡ {total_adeudado_largo:,}".replace(",", "."),
        "Registros válidos": int(valid_mask.sum()),
    })

    st.divider()

    # Navegación / Guardar
    c1, c2 = st.columns([0.5, 0.5])
    with c1:
        if st.button("⬅️ Volver a Otros ingresos", key="deudas_back_step4", use_container_width=True):
            st.session_state.step = 4
            st.session_state.step3 = "RES"  # por si vienes de conciliación previamente
            st.rerun()
    with c2:
        if st.button("Guardar y continuar ➡️", key="deudas_save_next", use_container_width=True,
                     disabled=(valid_mask.sum() == 0)):
            st.session_state.setdefault("reporte", {})
            st.session_state["reporte"]["deudas_activas"] = {
                "tabla": df.fillna("").to_dict(orient="records"),
                "totales": {
                    "total_pago_mensual_colones": total_pago_mensual,
                    "total_pago_mensual_verificado_colones": total_pago_verificado,
                    "total_adeudado_colones": total_adeudado,
                    # NUEVOS CAMPOS PARA BALANCE:
                    "total_adeudado_corto_plazo_colones": total_adeudado_corto,   # → pasivo circulante
                    "total_adeudado_largo_plazo_colones": total_adeudado_largo,   # → pasivo a largo plazo
                    "registros_validos": int(valid_mask.sum()),
                }
            }
            st.success("Deudas activas guardadas. Avanzando…")
            st.session_state.step = 6
            st.rerun()


# =========================
# PASO 7 – Gastos operativos (step == 6)
# =========================
def _mensualizar_gasto(monto: float, periodicidad: str) -> float:
    """Convierte un gasto por período a gasto mensual aproximado."""
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

if st.session_state.get("step") == 6:
    import pandas as pd

    st.title("🧾 Paso 7: Gastos operativos")
    st.caption("Registre los gastos del negocio u hogar relacionados a la operación. Puede indicar si fueron **verificados** y el **tipo de evidencia**.")

    # Catálogos
    rubros = ["Sueldos", "Alquileres", "Servicios públicos", "Impuestos/Patentes", "Pagos a proveedores", "Otros"]
    periodicidades = ["Mensual", "Quincenal", "Semanal", "Diario", "Bimestral", "Trimestral", "Semestral", "Anual"]
    evidencias = [
        "Factura/Recibo", "Contrato/Arrendamiento", "Estado de cuenta/SINPE",
        "Planilla/CCSS", "Recibos", "Foto/Chat", "No aplica", "Otro"
    ]

    # Columnas base (entrada)
    base_cols = [
        "Rubro",                    # select
        "Detalle",                  # texto
        "Monto por período (₡)",    # num
        "Periodicidad",             # select
        "Verificado por asesor",    # bool
        "Tipo de evidencia",        # select
        "Comentario",               # texto
    ]

    # Placeholders iniciales (una fila por rubro)
    placeholder_rows = []
    for r in rubros:
        placeholder_rows.append({
            "Rubro": r,
            "Detalle": "",
            "Monto por período (₡)": 0,
            "Periodicidad": "Mensual",
            "Verificado por asesor": False,
            "Tipo de evidencia": "",
            "Comentario": "",
        })
    df_in = st.data_editor(
        pd.DataFrame(placeholder_rows),
        use_container_width=True,
        num_rows="dynamic",
        hide_index=True,
        key="de_gastos_operativos",
        column_config={
            "Rubro": st.column_config.SelectboxColumn("Rubro", options=rubros, required=False),
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

    # Asegurar tipos numéricos y booleanos
    if "Monto por período (₡)" not in df.columns:
        df["Monto por período (₡)"] = 0
    df["Monto por período (₡)"] = pd.to_numeric(df["Monto por período (₡)"], errors="coerce").fillna(0)

    if "Verificado por asesor" not in df.columns:
        df["Verificado por asesor"] = False
    df["Verificado por asesor"] = df["Verificado por asesor"].fillna(False).astype(bool)

    # Calcular "Gasto mensualizado (₡)"
    mensualizados = []
    for _, r in df.iterrows():
        monto = float(r.get("Monto por período (₡)") or 0)
        per = r.get("Periodicidad") or ""
        mensualizados.append(_mensualizar_gasto(monto, per))

    df["Gasto mensualizado (₡)"] = pd.Series(mensualizados).round(0).astype(int)

    # Editor con cálculos (derivadas bloqueadas)
    with st.expander("Editar tabla con cálculos (derivados bloqueados)"):
        df_edit = st.data_editor(
            df,
            use_container_width=True,
            num_rows="dynamic",
            hide_index=True,
            key="de_gastos_operativos_calc",
            column_config={
                "Rubro": st.column_config.SelectboxColumn("Rubro", options=rubros),
                "Detalle": st.column_config.TextColumn("Detalle"),
                "Monto por período (₡)": st.column_config.NumberColumn("Monto por período (₡)", min_value=0, step=1000, format="₡ %d"),
                "Periodicidad": st.column_config.SelectboxColumn("Periodicidad", options=periodicidades),
                "Verificado por asesor": st.column_config.CheckboxColumn("Verificado por asesor", default=False),
                "Tipo de evidencia": st.column_config.SelectboxColumn("Tipo de evidencia", options=evidencias),
                "Comentario": st.column_config.TextColumn("Comentario"),
                # Derivadas bloqueadas
                "Gasto mensualizado (₡)": st.column_config.NumberColumn("Gasto mensualizado (₡)", format="₡ %d", disabled=True),
            },
        )

    # Recalcular por si cambian entradas en el editor con cálculos
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
        mensualizados.append(_mensualizar_gasto(monto, per))

    df = df_edit.copy()
    df["Gasto mensualizado (₡)"] = pd.Series(mensualizados).round(0).astype(int)

    # --- Resumen ---
    valid_mask = (df["Periodicidad"].isin(periodicidades)) & (df["Monto por período (₡)"] > 0)
    df_valid = df[valid_mask].copy()

    total_gasto_mensual = int(df_valid["Gasto mensualizado (₡)"].sum()) if not df_valid.empty else 0
    total_gasto_verificado = int(df_valid.loc[df_valid["Verificado por asesor"], "Gasto mensualizado (₡)"].sum()) if not df_valid.empty else 0

    st.markdown("**Resumen**")
    st.write({
        "Total gastos operativos (mensualizado)": f"₡ {total_gasto_mensual:,}".replace(",", "."),
        "Total verificado (mensualizado)": f"₡ {total_gasto_verificado:,}".replace(",", "."),
        "Registros válidos": int(valid_mask.sum()),
    })

    st.divider()

    # Navegación / Guardar
    c1, c2 = st.columns([0.5, 0.5])
    with c1:
        if st.button("⬅️ Volver a Deudas", key="gastos_back_deudas", use_container_width=True):
            st.session_state.step = 5
            st.rerun()
    with c2:
        if st.button("Guardar y continuar ➡️", key="gastos_save_next", use_container_width=True,
                     disabled=(valid_mask.sum() == 0)):
            st.session_state.setdefault("reporte", {})
            st.session_state["reporte"]["gastos_operativos"] = {
                "tabla": df.fillna("").to_dict(orient="records"),
                "totales": {
                    "total_gasto_operativo_mensualizado_colones": total_gasto_mensual,
                    "total_gasto_operativo_verificado_colones": total_gasto_verificado,
                    "registros_validos": int(valid_mask.sum()),
                }
            }
            st.success("Gastos operativos guardados. Avanzando…")
            st.session_state.step = 7
            st.rerun()







