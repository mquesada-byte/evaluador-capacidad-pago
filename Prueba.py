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

st.set_page_config(page_title="Evaluación Crédito - Paso 1", page_icon="🧭")

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
    # ---- NUEVO: si el sector es Servicios, este paso no aplica ----
    sector = (st.session_state.get("negocio", {}).get("sector_economico") or "").strip()
    if sector.lower() == "servicios":
        st.title("🧮 Paso 3C: (No aplica para Servicios)")
        st.info("Para actividades 100% de servicios, la estimación por compras no es representativa. "
                "Usaremos 3A (Top-down) y 3B (Bottom-up) para la conciliación.")

        st.session_state.setdefault("reporte", {})
        st.session_state["reporte"]["ventas_insumos_simple"] = {
            "no_aplica": True,
            "motivo": "Actividad de servicios",
            "sector": sector
        }

        colS1, colS2 = st.columns([0.5, 0.5])
        with colS1:
            if st.button("⬅️ Volver a 3B (Bottom-up)", key="skip3C_back3B", use_container_width=True):
                st.session_state.step3 = "B"
                st.rerun()
        with colS2:
            if st.button("Ir a Conciliación ➡️", key="skip3C_goRES", use_container_width=True):
                st.session_state.step3 = "RES"
                st.rerun()
        st.stop()
    # ----------------------------------------------------------------

    # (tu 3C original continúa aquí sin cambios)
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

    colNav1, colNav2 = st.columns([0.5, 0.5])
    with colNav1:
        if st.button("⬅️ Volver a 3B (Bottom-up)", key="back_to_3B_from_3C_simple", use_container_width=True):
            st.session_state.step3 = "B"
            st.rerun()
    with colNav2:
        if st.button("Siguiente ➡️ (Conciliación)", key="next_step_3C_simple", disabled=not oblig_ok, use_container_width=True):
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
            st.session_state.step3 = "RES"  # conciliación
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
    # Escala 0.6–1.0 según conocimiento y credibilidad (promedio)
    know = float(v.get("conocimiento_0a10") or 0)
    cred = float(v.get("credibilidad_0a10") or 0)
    avg = (know + cred) / 2.0
    return 0.6 + 0.04 * avg  # 0.6 (muy baja) … 1.0 (muy alta)

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
    st.info(f"**Factor de confiabilidad del asesor (aplicado en conciliación):** {factor:.2f} (0.60–1.00)")

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





