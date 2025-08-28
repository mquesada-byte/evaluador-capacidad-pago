# =========================
# PASO 1 – Datos del asesor (pantalla independiente)
# =========================
import datetime as dt
from zoneinfo import ZoneInfo
import time, requests
import streamlit as st
from streamlit_js_eval import get_geolocation

TZ = ZoneInfo("America/Costa_Rica")
USE_INTERNET_TIME = True
MAX_RERUNS = 6
SLEEP_SEC = 0.4

def now_in_cr_via_internet():
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

def maps_links(lat, lon):
    lat_s, lon_s = f"{lat:.6f}", f"{lon:.6f}"
    google = f"https://www.google.com/maps/search/?api=1&query={lat_s},{lon_s}"
    google_at = f"https://www.google.com/maps/@{lat_s},{lon_s},18z"
    osm = f"https://www.openstreetmap.org/?mlat={lat_s}&mlon={lon_s}#map=18/{lat_s}/{lon_s}"
    return google, google_at, osm

def swapped_links(lat, lon):
    lat_s, lon_s = f"{lat:.6f}", f"{lon:.6f}"
    return (
        f"https://www.google.com/maps/search/?api=1&query={lon_s},{lat_s}",
        f"https://www.openstreetmap.org/?mlat={lon_s}&mlon={lat_s}#map=18/{lon_s}/{lat_s}",
    )

def plausible_cr_area(lat, lon):
    return (8.0 <= lat <= 12.0) and (-90.0 <= lon <= -80.0)

def init_asesor_state():
    st.session_state.setdefault("step", 1)
    st.session_state.setdefault("asesor", {})
    st.session_state.setdefault("geo_request", False)
    st.session_state.setdefault("geo_status", "idle")
    st.session_state.setdefault("geo_attempts", 0)
    a = st.session_state.asesor
    a.setdefault("nombre", "")
    if "fecha_hora" not in a:
        ts = now_in_cr_via_internet() if USE_INTERNET_TIME else None
        a["timestamp_source"] = "internet" if ts else "device"
        a["fecha_hora"] = ts or now_in_cr_fallback()
    a.setdefault("lat", None); a.setdefault("lon", None)
    a.setdefault("maps_url", None); a.setdefault("maps_url_alt", None); a.setdefault("osm_url", None)

def asesor_para_reporte():
    a = st.session_state.get("asesor", {})
    fecha = a.get("fecha_hora")
    return {
        "nombre": (a.get("nombre") or "").strip(),
        "fecha_hora": fecha.strftime("%d/%m/%Y %H:%M:%S") if fecha else "N/D",
        "hora_fuente": "Internet" if a.get("timestamp_source") == "internet" else "Dispositivo",
        "gps": f"{a['lat']:.6f}, {a['lon']:.6f}" if a.get("lat") is not None and a.get("lon") is not None else "No disponible",
        "google_maps": a.get("maps_url"),
        "google_maps_vista": a.get("maps_url_alt"),
        "openstreetmap": a.get("osm_url"),
    }

if st.session_state.get("step", 1) == 1:
    init_asesor_state()
    asesor = st.session_state.asesor

    st.title("🧭 Paso 1: Datos del asesor")
    st.caption("La fecha y hora se registran automáticamente y no pueden ser modificadas.")

    asesor["nombre"] = st.text_input("Nombre completo del asesor *", value=asesor["nombre"])
    fecha_hora_registro = asesor["fecha_hora"].strftime("%d/%m/%Y %H:%M:%S")
    st.text_input("📅 Fecha y hora de registro",
                  value=fecha_hora_registro + (" (Internet)" if asesor.get("timestamp_source") == "internet" else " (Dispositivo)"),
                  disabled=True)

    st.write("**Ubicación GPS (opcional)**")
    col1, col2 = st.columns([0.45, 0.55])

    with col1:
        if st.button("📍 Obtener mi ubicación"):
            st.session_state.geo_request = True
            st.session_state.geo_status = "waiting"
            st.session_state.geo_attempts = 0
            asesor.update({"lat": None, "lon": None, "maps_url": None, "maps_url_alt": None, "osm_url": None})
            st.rerun()

        if st.session_state.geo_request and st.session_state.geo_status != "ok":
            loc = None
            try:
                loc = get_geolocation()
            except Exception:
                pass

            if isinstance(loc, dict):
                coords = loc.get("coords") or {}
                lat = coords.get("latitude"); lon = coords.get("longitude")
                msg = (loc.get("msg") or loc.get("message") or "").lower()

                if lat is not None and lon is not None and _coords_plausibles(lat, lon):
                    asesor["lat"], asesor["lon"] = float(lat), float(lon)
                    g, g_at, osm = maps_links(asesor["lat"], asesor["lon"])
                    asesor["maps_url"], asesor["maps_url_alt"], asesor["osm_url"] = g, g_at, osm
                    st.session_state.geo_status = "ok"; st.session_state.geo_request = False
                elif "denied" in msg:
                    st.session_state.geo_status = "denied"; st.session_state.geo_request = False
                elif "timeout" in msg:
                    st.session_state.geo_status = "timeout"; st.session_state.geo_request = False
                elif "unavailable" in msg:
                    st.session_state.geo_status = "unavailable"; st.session_state.geo_request = False
                else:
                    st.session_state.geo_attempts += 1
                    if st.session_state.geo_attempts < MAX_RERUNS:
                        with st.spinner("Solicitando permiso o esperando señal de GPS…"):
                            time.sleep(SLEEP_SEC)
                        st.rerun()
                    else:
                        st.session_state.geo_status = "error"; st.session_state.geo_request = False
            else:
                st.session_state.geo_attempts += 1
                if st.session_state.geo_attempts < MAX_RERUNS:
                    with st.spinner("Solicitando permiso o esperando señal de GPS…"):
                        time.sleep(SLEEP_SEC)
                    st.rerun()
                else:
                    st.session_state.geo_status = "error"; st.session_state.geo_request = False

    with col2:
        status = st.session_state.geo_status
        if asesor["lat"] is not None and asesor["lon"] is not None:
            lat, lon = asesor["lat"], asesor["lon"]
            st.success(f"Ubicación: {lat:.6f}, {lon:.6f}")
            st.markdown(f"[Abrir en Google Maps]({asesor['maps_url']}) · "
                        f"[Vista @18z]({asesor['maps_url_alt']}) · "
                        f"[OpenStreetMap]({asesor['osm_url']})")
            if not plausible_cr_area(lat, lon):
                g_sw, osm_sw = swapped_links(lat, lon)
                st.warning("Las coordenadas no parecen estar en Costa Rica. Prueba el orden invertido si el mapa no coincide:")
                st.markdown(f"• [Google (invertido)]({g_sw}) · [OSM (invertido)]({osm_sw})")
        else:
            msgs = {
                "waiting": "Solicitando permiso o esperando señal de GPS…",
                "denied": "Permiso de ubicación denegado en el navegador.",
                "timeout": "Tiempo de espera agotado al obtener la ubicación.",
                "unavailable": "Ubicación no disponible en este dispositivo/red.",
                "error": "No fue posible obtener la ubicación en este momento.",
                "idle": "Aún no hay coordenadas registradas.",
            }
            st.caption(msgs.get(status, "Aún no hay coordenadas registradas."))

    st.divider()

    disabled_next = not bool(asesor["nombre"].strip())
    colA, colB = st.columns([0.7, 0.3])
    with colA:
        st.write("Campo obligatorio: **Nombre del asesor**.")
    with colB:
        if st.button("Siguiente ➡️", key="next_step_1",
                     disabled=disabled_next, use_container_width=True):
            st.session_state.setdefault("reporte", {})
            st.session_state["reporte"]["asesor"] = asesor_para_reporte()
            st.session_state.step = 2
            st.rerun()

    # 👇 Detiene el render aquí mientras sigas en el Paso 1
    st.stop()




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
   
    # 👇 Detiene el render aquí mientras sigas en el Paso 1
    st.stop()




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
    
    # 👇 Detiene el render aquí mientras sigas en el Paso 1
    st.stop()




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




# =========================
# PASO 5 – Otros ingresos del hogar (step == 4)
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

if st.session_state.get("step") == 4:
    import pandas as pd

    st.title("💸 Paso 5: Otros ingresos del hogar")
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

    # ---------- CARGA INICIAL: si ya guardaste, reusar lo guardado ----------
    guardado = (st.session_state.get("reporte", {})
                .get("otros_ingresos", {})
                .get("tabla", []))
    if guardado:
        df_base_inicial = pd.DataFrame(guardado).copy()
        # Si la tabla guardada viene con derivadas, las removemos para el editor base
        cols_a_dejar = [c for c in df_base_inicial.columns if c in base_cols]
        for c in base_cols:
            if c not in df_base_inicial.columns:
                df_base_inicial[c] = "" if c not in ["Monto por período (₡)", "Meses de continuidad", "Prob. continuidad (0–10)", "Verificado por asesor"] else 0
        df_base_inicial = df_base_inicial[base_cols]
    else:
        df_base_inicial = pd.DataFrame([{c: "" for c in base_cols}] * 4)

    # --- Data Editor base (captura) ---
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

    # Recalcular por si hubo cambios en el editor con cálculos
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

    # 👇 Detiene el render aquí mientras sigas en el Paso 1
    st.stop()




# =========================
# PASO 6 – Deudas activas del hogar (step == 5)
# =========================
def _mensualizar_pago(monto: float, periodicidad: str) -> float:
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
    plazos = ["Corto plazo (≤12 meses)", "Largo plazo (>12 meses)"]

    # Columnas base (entrada)
    base_cols = [
        "Titular",
        "Acreedor/Entidad",
        "Tipo de deuda",
        "Saldo adeudado (₡)",
        "Cuota por período (₡)",
        "Periodicidad de pago",
        "Verificado por asesor",
        "Tipo de evidencia",
        "Estado",
        "Días de atraso",
        "Comentario",
        "Meses restantes (opcional)",
        "Plazo (clasificación)",
    ]

    # ========= NUEVO: CARGA INICIAL DESDE LO GUARDADO (si existe) =========
    guardado = (st.session_state.get("reporte", {})
                .get("deudas_activas", {})
                .get("tabla", []))
    if guardado:
        df_base_inicial = pd.DataFrame(guardado).copy()
        # Quitar columnas derivadas si vinieron en la tabla guardada
        cols_presentes = [c for c in df_base_inicial.columns if c in base_cols]
        for c in base_cols:
            if c not in df_base_inicial.columns:
                # defaults sensatos por tipo
                if c in ["Saldo adeudado (₡)", "Cuota por período (₡)", "Días de atraso", "Meses restantes (opcional)"]:
                    df_base_inicial[c] = 0
                elif c == "Verificado por asesor":
                    df_base_inicial[c] = False
                else:
                    df_base_inicial[c] = ""
        df_base_inicial = df_base_inicial[base_cols]
    else:
        df_base_inicial = pd.DataFrame([{c: "" for c in base_cols}] * 4)
        # tipos numéricos por defecto en base
        for c in ["Saldo adeudado (₡)", "Cuota por período (₡)", "Días de atraso", "Meses restantes (opcional)"]:
            df_base_inicial[c] = 0
        df_base_inicial["Verificado por asesor"] = False
    # ======================================================================

    # Editor de captura rápido
    df_in = st.data_editor(
        df_base_inicial,
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
            "Meses restantes (opcional)": st.column_config.NumberColumn("Meses restantes (opcional)", min_value=0, max_value=600, step=1, format="%d"),
            "Plazo (clasificación)": st.column_config.SelectboxColumn("Plazo (clasificación)", options=plazos, required=False),
        },
    )

    # --- Preparación y derivados (SIN CAMBIOS) ---
    df = df_in.copy()
    for c in ["Saldo adeudado (₡)", "Cuota por período (₡)", "Días de atraso", "Meses restantes (opcional)"]:
        if c not in df.columns:
            df[c] = 0
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    if "Verificado por asesor" not in df.columns:
        df["Verificado por asesor"] = False
    df["Verificado por asesor"] = df["Verificado por asesor"].fillna(False).astype(bool)

    if "Plazo (clasificación)" not in df.columns:
        df["Plazo (clasificación)"] = ""
    df["Plazo (clasificación)"] = df["Plazo (clasificación)"].astype(str)

    auto_mask = df["Plazo (clasificación)"].isin(["", "nan", "None"])
    df.loc[auto_mask & (df["Meses restantes (opcional)"] > 0) & (df["Meses restantes (opcional)"] <= 12),
           "Plazo (clasificación)"] = "Corto plazo (≤12 meses)"
    df.loc[auto_mask & (df["Meses restantes (opcional)"] > 12),
           "Plazo (clasificación)"] = "Largo plazo (>12 meses)"

    cuotas_mens = []
    for _, r in df.iterrows():
        cuota = float(r.get("Cuota por período (₡)") or 0)
        per = r.get("Periodicidad de pago") or ""
        cuotas_mens.append(_mensualizar_pago(cuota, per))
    df["Cuota mensualizada (₡)"] = pd.Series(cuotas_mens).round(0).astype(int)

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
                "Meses restantes (opcional)": st.column_config.NumberColumn("Meses restantes (opcional)", min_value=0, max_value=600, step=1, format="%d"),
                "Plazo (clasificación)": st.column_config.SelectboxColumn("Plazo (clasificación)", options=plazos),
                "Cuota mensualizada (₡)": st.column_config.NumberColumn("Cuota mensualizada (₡)", format="₡ %d", disabled=True),
            },
        )

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

    # --- Resumen (SIN CAMBIOS) ---
    valid_mask = (df["Periodicidad de pago"].isin(periodicidades_pago)) & \
                 ((df["Cuota por período (₡)"] > 0) | (df["Saldo adeudado (₡)"] > 0))
    df_valid = df[valid_mask].copy()

    total_pago_mensual = int(df_valid["Cuota mensualizada (₡)"].sum()) if not df_valid.empty else 0
    total_adeudado = int(df_valid["Saldo adeudado (₡)"].sum()) if not df_valid.empty else 0
    total_pago_verificado = int(df_valid.loc[df_valid["Verificado por asesor"], "Cuota mensualizada (₡)"].sum()) if not df_valid.empty else 0

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

    # Navegación / Guardar (SIN CAMBIOS)
    c1, c2 = st.columns([0.5, 0.5])
    with c1:
        if st.button("⬅️ Volver a Otros ingresos", key="deudas_back_step4", use_container_width=True):
            st.session_state.step = 4
            st.session_state.step3 = "RES"
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
                    "total_adeudado_corto_plazo_colones": total_adeudado_corto,
                    "total_adeudado_largo_plazo_colones": total_adeudado_largo,
                    "registros_validos": int(valid_mask.sum()),
                }
            }
            st.success("Deudas activas guardadas. Avanzando…")
            st.session_state.step = 6
            st.rerun()

    st.stop()




# =========================
# PASO 7 – Gastos operativos (step == 6)
# =========================
def _mensualizar_gasto(monto: float, periodicidad: str) -> float:
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
        "Rubro", "Detalle", "Monto por período (₡)", "Periodicidad",
        "Verificado por asesor", "Tipo de evidencia", "Comentario",
    ]

    # ================== NUEVO: cargar lo guardado si existe ==================
    guardado = (st.session_state.get("reporte", {})
                .get("gastos_operativos", {})
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
        # Tipos
        df_base["Monto por período (₡)"] = pd.to_numeric(df_base["Monto por período (₡)"], errors="coerce").fillna(0)
        df_base["Verificado por asesor"] = df_base["Verificado por asesor"].fillna(False).astype(bool)
    else:
        # Placeholders iniciales (una fila por rubro)
        placeholder_rows = []
        for r in rubros:
            placeholder_rows.append({
                "Rubro": r, "Detalle": "", "Monto por período (₡)": 0, "Periodicidad": "Mensual",
                "Verificado por asesor": False, "Tipo de evidencia": "", "Comentario": "",
            })
        df_base = pd.DataFrame(placeholder_rows)
    # ========================================================================

    df_in = st.data_editor(
        df_base,
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
    if "Monto por período (₡)" not in df.columns:
        df["Monto por período (₡)"] = 0
    df["Monto por período (₡)"] = pd.to_numeric(df["Monto por período (₡)"], errors="coerce").fillna(0)
    if "Verificado por asesor" not in df.columns:
        df["Verificado por asesor"] = False
    df["Verificado por asesor"] = df["Verificado por asesor"].fillna(False).astype(bool)

    mensualizados = []
    for _, r in df.iterrows():
        monto = float(r.get("Monto por período (₡)") or 0)
        per = r.get("Periodicidad") or ""
        mensualizados.append(_mensualizar_gasto(monto, per))
    df["Gasto mensualizado (₡)"] = pd.Series(mensualizados).round(0).astype(int)

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
                "Gasto mensualizado (₡)": st.column_config.NumberColumn("Gasto mensualizado (₡)", format="₡ %d", disabled=True),
            },
        )

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

    st.stop()




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




# estado_resultados.py
# ---------------------------------------------------------
# Lee st.session_state["reporte"] generado por los pasos 1–8
# y calcula el Disponible para pago del préstamo (Credimujer).
# No modifica los datos previos, solo los lee y resume.

import streamlit as st
import pandas as pd

# Evita conflicto si otra página ya llamó set_page_config
if not st.session_state.get("_page_config_set"):
    st.set_page_config(page_title="Estado de Resultados", page_icon="📑")
    st.session_state["_page_config_set"] = True


# ========= Helpers de lectura/formatos =========
def _getr(path, default=None):
    """Obtiene un valor anidado desde st.session_state['reporte']."""
    cur = st.session_state.get("reporte", {}) or {}
    try:
        for p in path:
            cur = cur[p]
        return cur
    except Exception:
        return default

def _num(x, default=0.0):
    try:
        if x is None:
            return float(default)
        return float(x)
    except Exception:
        try:
            s = str(x).strip().replace(",", "").replace("₡", "")
            return float(s or default)
        except Exception:
            return float(default)

def _num_or_none(x):
    try:
        if x is None or (isinstance(x, str) and x.strip() == ""):
            return None
        return float(str(x).strip().replace(",", "").replace("₡", ""))
    except Exception:
        return None

def _fmt_col(x):
    try:
        return f"₡{int(round(_num(x))):,}".replace(",", ".")
    except Exception:
        return "₡0"


# ========= Recolección (con rutas de origen) =========
src = {}

# 1) Ventas — preferir conciliadas
ventas_total = _getr(["ventas_conciliacion", "ventas_conciliadas_colones"])
if ventas_total:
    src["ventas"] = "reporte.ventas_conciliacion.ventas_conciliadas_colones"
else:
    # Fallback: Top-down, Bottom-up, Insumos simple
    ventas_total = (
        _getr(["ventas_topdown", "monto_colones"]) or
        _getr(["ventas_bottomup", "ventas_estimadas_colones"]) or
        _getr(["ventas_insumos_simple", "ventas_estimadas_colones"]) or
        _getr(["ventas_insumos", "ventas_estimadas_colones"])
    )
    if ventas_total:
        if _getr(["ventas_topdown", "monto_colones"]):
            src["ventas"] = "reporte.ventas_topdown.monto_colones"
        elif _getr(["ventas_bottomup", "ventas_estimadas_colones"]):
            src["ventas"] = "reporte.ventas_bottomup.ventas_estimadas_colones"
        else:
            src["ventas"] = "reporte.ventas_insumos_simple.ventas_estimadas_colones"
ventas_total = _num(ventas_total, 0)

# 2) Compras/Costos (de 3C simple)
compras_total = _getr(["ventas_insumos_simple", "compras_mes_colones"])
if compras_total is not None:
    src["compras"] = "reporte.ventas_insumos_simple.compras_mes_colones"
else:
    compras_total = 0.0
compras_total = _num(compras_total, 0)

# 3) Margen (tipo + % desde 3C simple)
tipo_margen = _getr(["ventas_insumos_simple", "tipo_margen"])      # "Sobre ventas" | "Sobre compras (markup)"
margen_pct_raw = _getr(["ventas_insumos_simple", "margen_pct"])    # entero/str, ej.: 30
margen_pct = _num_or_none(margen_pct_raw)
if tipo_margen is not None and margen_pct is not None:
    src["margen"] = "reporte.ventas_insumos_simple.(tipo_margen,margen_pct)"

# 4) Gastos operativos (mensualizado)
gastos_ope_total = _getr(["gastos_operativos", "totales", "total_gasto_operativo_mensualizado_colones"], 0)
src["gastos_operativos"] = "reporte.gastos_operativos.totales.total_gasto_operativo_mensualizado_colones"
gastos_ope_total = _num(gastos_ope_total, 0)

# 5) Otros ingresos — preferir ponderado; si no, mensualizado
otros_ing_total = _getr(["otros_ingresos", "totales", "total_ponderado_colones"])
ruta_oi = "reporte.otros_ingresos.totales.total_ponderado_colones"
if not otros_ing_total:
    otros_ing_total = _getr(["otros_ingresos", "totales", "total_mensualizado_colones"], 0)
    ruta_oi = "reporte.otros_ingresos.totales.total_mensualizado_colones"
src["otros_ingresos"] = ruta_oi
otros_ing_total = _num(otros_ing_total, 0)

# 6) Gastos familiares — **SOLO** total mensualizado del Paso 8 (sin fallbacks)
gastos_fam_total = _num(
    _getr(["gastos_familiares", "totales", "total_gastos_familiares_mensualizado_colones"], 0),
    0
)
src["gastos_familiares"] = "reporte.gastos_familiares.totales.total_gastos_familiares_mensualizado_colones"

# 7) Pago de deudas (mensualizado, para resultados)
deudas_total = _getr(["deudas_activas", "totales", "total_pago_mensual_colones"], 0)
src["deudas"] = "reporte.deudas_activas.totales.total_pago_mensual_colones"
deudas_total = _num(deudas_total, 0)


# ========= Cálculos del Estado de Resultados =========
# Utilidad bruta:
# - Si hay margen y base: usar regla solicitada.
# - Si no, fallback conservador: ventas - compras.
utilidad_bruta = None
if (margen_pct is not None) and (tipo_margen in ("Sobre ventas", "Sobre compras (markup)")):
    pct = margen_pct if margen_pct <= 1 else margen_pct / 100.0
    if tipo_margen == "Sobre ventas":
        utilidad_bruta = ventas_total * pct
    else:  # Sobre compras (markup)
        utilidad_bruta = compras_total * pct
if utilidad_bruta is None:
    utilidad_bruta = max(0.0, ventas_total - compras_total)

utilidad_neta_ope   = utilidad_bruta - gastos_ope_total
subtotal_post_otros = utilidad_neta_ope + otros_ing_total
disponible_final    = subtotal_post_otros - gastos_fam_total - deudas_total


# ========= UI =========
st.header("📑 Estado de Resultados (resumen de pasos previos)")

with st.expander("🔎 Origen de datos (rutas detectadas)"):
    st.json(src)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Ventas", _fmt_col(ventas_total))
with col2:
    st.metric("Compras/Costos", _fmt_col(compras_total))
with col3:
    base_txt = ("ventas" if (tipo_margen == "Sobre ventas")
                else ("compras" if (tipo_margen == "Sobre compras (markup)") else "—"))
    pct_show = (margen_pct if (margen_pct is not None and margen_pct <= 1)
                else (margen_pct or 0)/100) if (margen_pct is not None) else None
    st.metric("Margen (base)", f"{pct_show:.0%} sobre {base_txt}" if pct_show is not None else "— sobre —")

st.divider()

col4, col5 = st.columns(2)
with col4:
    st.metric("🧮 Utilidad Bruta", _fmt_col(utilidad_bruta))
with col5:
    st.metric("🧾 Gastos Operativos", _fmt_col(gastos_ope_total))

st.metric("📌 Utilidad Neta Operativa", _fmt_col(utilidad_neta_ope))

st.divider()

col6, col7 = st.columns(2)
with col6:
    st.metric("➕ Otros ingresos", _fmt_col(otros_ing_total))
with col7:
    st.metric("Subtotal post-otros", _fmt_col(subtotal_post_otros))

st.divider()

col8, col9 = st.columns(2)
with col8:
    st.metric("👪 Gastos familiares", _fmt_col(gastos_fam_total))
with col9:
    st.metric("💳 Pago de deudas", _fmt_col(deudas_total))

st.success(f"💰 **Disponible para el préstamo:** {_fmt_col(disponible_final)}")

# (Opcional) Vista de apoyo con tablas si están en el reporte
with st.expander("Ver tablas de origen (si están disponibles)"):
    rep = st.session_state.get("reporte", {})
    st.subheader("Otros ingresos")
    st.dataframe(pd.DataFrame(rep.get("otros_ingresos", {}).get("tabla", [])), use_container_width=True)
    st.subheader("Gastos operativos")
    st.dataframe(pd.DataFrame(rep.get("gastos_operativos", {}).get("tabla", [])), use_container_width=True)
    st.subheader("Gastos familiares")
    st.dataframe(pd.DataFrame(rep.get("gastos_familiares", {}).get("tabla", [])), use_container_width=True)
    st.subheader("Deudas activas")
    st.dataframe(pd.DataFrame(rep.get("deudas_activas", {}).get("tabla", [])), use_container_width=True)



# ====== Navegación desde Estado de Resultados ======
st.divider()
col_nav1, col_nav2 = st.columns([0.5, 0.5])

with col_nav1:
    if st.button("⬅️ Volver a Gastos familiares", use_container_width=True):
        st.session_state.step = 7  # Paso 8: Gastos familiares
        st.rerun()

with col_nav2:
    if st.button("Continuar ➡️ Balance general", type="primary", use_container_width=True):
        # Persistimos un resumen del ER para el reporte final
        st.session_state.setdefault("reporte", {})
        st.session_state["reporte"]["estado_resultados"] = {
            "ventas_colones": int(round(ventas_total)),
            "compras_costos_colones": int(round(compras_total)),
            "margen_tipo": (tipo_margen or ""),
            "margen_pct": float(margen_pct) if margen_pct is not None else None,
            "utilidad_bruta_colones": int(round(utilidad_bruta)),
            "gastos_operativos_colones": int(round(gastos_ope_total)),
            "utilidad_neta_operativa_colones": int(round(utilidad_neta_ope)),
            "otros_ingresos_colones": int(round(otros_ing_total)),
            "gastos_familiares_colones": int(round(gastos_fam_total)),
            "pago_de_deudas_colones": int(round(deudas_total)),
            "subtotal_post_otros_colones": int(round(subtotal_post_otros)),
            "disponible_para_prestamo_colones": int(round(disponible_final)),
        }

        # 1) Intento multipage
        try:
            st.switch_page("balance_general.py")
        except Exception:
            try:
                st.switch_page("pages/balance_general.py")
            except Exception:
                # 2) Fallback para flujo de una sola página
                st.session_state.step = 8  # <-- Balance general
                st.rerun()

# 🔧 FIX: solo detenemos el render si NO vamos a Balance (evita bloquear el bloque de step==8)
if st.session_state.get("step") != 8:
    st.stop()




# =========================
# PASO 9 – Balance general (step == 8)
# =========================
if st.session_state.get("step") == 8:
    import pandas as pd

    st.title("📒 Paso 9: Balance General")
    st.caption(
        "Registre y/o verifique los saldos para construir el Balance General. "
        "Los pasivos por deudas se toman automáticamente del Paso 6 (deudas activas): "
        "corto plazo → pasivo circulante; largo plazo → pasivo a largo plazo."
    )

    # ========= Helpers =========
    def _to_num(s):
        try:
            return float(s)
        except Exception:
            return 0.0

    # Cargar totales de deudas (si existen)
    tot_corto = 0
    tot_largo = 0
    try:
        _tot = st.session_state["reporte"]["deudas_activas"]["totales"]
        tot_corto = int(_tot.get("total_adeudado_corto_plazo_colones", 0))
        tot_largo = int(_tot.get("total_adeudado_largo_plazo_colones", 0))
    except Exception:
        pass

    # Catálogos de evidencia (cómo verificó el asesor)
    evidencias = [
        "Los tiene en caja", "Estado de cuenta", "Movimientos/SINPE", "Factura/Recibo",
        "Contrato", "Inventario físico", "Fotos/Video", "Otro", "No aplica"
    ]

    st.subheader("I. Activo Circulante")

    # 1) Caja y Bancos (detalle por cuenta) + verificación
    st.markdown("**Caja y bancos**")
    caja_cols = [
        "Cuenta/Banco", "Saldo (₡)", "Verificado por asesor", "Tipo de evidencia", "Comentario"
    ]
    caja_placeholder = pd.DataFrame([{
        "Cuenta/Banco": "", "Saldo (₡)": 0, "Verificado por asesor": False,
        "Tipo de evidencia": "", "Comentario": ""
    } for _ in range(3)])

    caja_df = st.data_editor(
        caja_placeholder,
        use_container_width=True,
        num_rows="dynamic",
        hide_index=True,
        key="bg_caja_bancos",
        column_config={
            "Cuenta/Banco": st.column_config.TextColumn("Cuenta/Banco"),
            "Saldo (₡)": st.column_config.NumberColumn("Saldo (₡)", min_value=0, step=10000, format="₡ %d"),
            "Verificado por asesor": st.column_config.CheckboxColumn("Verificado por asesor", default=False),
            "Tipo de evidencia": st.column_config.SelectboxColumn("Tipo de evidencia", options=evidencias, required=False),
            "Comentario": st.column_config.TextColumn("Comentario"),
        },
    )
    caja_total = int(pd.to_numeric(caja_df.get("Saldo (₡)", pd.Series()), errors="coerce").fillna(0).sum())
    st.metric("Subtotal Caja y Bancos", f"₡{caja_total:,.0f}")

    st.markdown("---")

    # 2) Cuentas por cobrar a clientes (detalle) + verificación
    st.markdown("**Cuentas por cobrar a clientes**")
    cxc_cols = [
        "Cliente/Descripción", "Monto (₡)", "Verificado por asesor", "Tipo de evidencia", "Comentario"
    ]
    cxc_placeholder = pd.DataFrame([{
        "Cliente/Descripción": "", "Monto (₡)": 0, "Verificado por asesor": False,
        "Tipo de evidencia": "", "Comentario": ""
    } for _ in range(3)])

    cxc_df = st.data_editor(
        cxc_placeholder,
        use_container_width=True,
        num_rows="dynamic",
        hide_index=True,
        key="bg_cxc_clientes",
        column_config={
            "Cliente/Descripción": st.column_config.TextColumn("Cliente/Descripción"),
            "Monto (₡)": st.column_config.NumberColumn("Monto (₡)", min_value=0, step=10000, format="₡ %d"),
            "Verificado por asesor": st.column_config.CheckboxColumn("Verificado por asesor", default=False),
            "Tipo de evidencia": st.column_config.SelectboxColumn("Tipo de evidencia", options=evidencias, required=False),
            "Comentario": st.column_config.TextColumn("Comentario"),
        },
    )
    cxc_total = int(pd.to_numeric(cxc_df.get("Monto (₡)", pd.Series()), errors="coerce").fillna(0).sum())
    st.metric("Subtotal Cuentas por Cobrar a Clientes", f"₡{cxc_total:,.0f}")

    st.markdown("---")

    # 3) Inventarios (tres tablas con subtotales y total)
    st.markdown("**Inventarios**")

    inv_cols = ["Detalle", "Valor (₡)", "Verificado por asesor", "Tipo de evidencia", "Comentario"]
    inv_opts = {
        "Materia prima": "bg_inv_mp",
        "Producto en proceso": "bg_inv_pp",
        "Producto terminado": "bg_inv_pt",
    }

    subtotales_inv = {}

    for titulo, keyname in inv_opts.items():
        st.markdown(f"*{titulo}*")
        inv_placeholder = pd.DataFrame([{
            "Detalle": "", "Valor (₡)": 0, "Verificado por asesor": False,
            "Tipo de evidencia": "", "Comentario": ""
        } for _ in range(3)])

        df_inv = st.data_editor(
            inv_placeholder,
            use_container_width=True,
            num_rows="dynamic",
            hide_index=True,
            key=keyname,
            column_config={
                "Detalle": st.column_config.TextColumn("Detalle"),
                "Valor (₡)": st.column_config.NumberColumn("Valor (₡)", min_value=0, step=10000, format="₡ %d"),
                "Verificado por asesor": st.column_config.CheckboxColumn("Verificado por asesor", default=False),
                "Tipo de evidencia": st.column_config.SelectboxColumn("Tipo de evidencia", options=evidencias, required=False),
                "Comentario": st.column_config.TextColumn("Comentario"),
            },
        )
        subtotal = int(pd.to_numeric(df_inv.get("Valor (₡)", pd.Series()), errors="coerce").fillna(0).sum())
        subtotales_inv[titulo] = subtotal
        st.caption(f"Subtotal {titulo}: **₡{subtotal:,.0f}**")
        st.markdown("")

    total_inventarios = int(sum(subtotales_inv.values()))
    st.metric("**Total Inventarios**", f"₡{total_inventarios:,.0f}")

    st.markdown("---")

    # Total Activo Circulante
    activo_circulante = int(caja_total + cxc_total + total_inventarios)
    st.metric("💼 **Total Activo Circulante**", f"₡{activo_circulante:,.0f}")

    st.divider()

    # ========= Activo Fijo Neto =========
    st.subheader("II. Activo Fijo Neto")
    st.caption("Ingrese cada activo fijo; se calcula neto = valor bruto – depreciación acumulada.")

    af_cols = [
        "Activo", "Valor bruto (₡)", "Depreciación acum. (₡)",
        "Verificado por asesor", "Tipo de evidencia", "Comentario"
    ]
    af_placeholder = pd.DataFrame([{
        "Activo": "",
        "Valor bruto (₡)": 0,
        "Depreciación acum. (₡)": 0,
        "Verificado por asesor": False,
        "Tipo de evidencia": "",
        "Comentario": "",
    } for _ in range(4)])

    with st.expander("Agregar/editar activos fijos"):
        af_df = st.data_editor(
            af_placeholder,
            use_container_width=True,
            num_rows="dynamic",
            hide_index=True,
            key="bg_activo_fijo",
            column_config={
                "Activo": st.column_config.TextColumn("Activo"),
                "Valor bruto (₡)": st.column_config.NumberColumn("Valor bruto (₡)", min_value=0, step=25000, format="₡ %d"),
                "Depreciación acum. (₡)": st.column_config.NumberColumn("Depreciación acum. (₡)", min_value=0, step=25000, format="₡ %d"),
                "Verificado por asesor": st.column_config.CheckboxColumn("Verificado por asesor", default=False),
                "Tipo de evidencia": st.column_config.SelectboxColumn("Tipo de evidencia", options=evidencias, required=False),
                "Comentario": st.column_config.TextColumn("Comentario"),
            },
        )
    af_bruto = pd.to_numeric(af_df.get("Valor bruto (₡)", pd.Series()), errors="coerce").fillna(0)
    af_depr  = pd.to_numeric(af_df.get("Depreciación acum. (₡)", pd.Series()), errors="coerce").fillna(0)
    af_neto_series = (af_bruto - af_depr).clip(lower=0)
    af_neto_total = int(af_neto_series.sum())
    st.metric("🏭 **Activo Fijo Neto**", f"₡{af_neto_total:,.0f}")

    st.divider()

    # ========= Totales de Activo =========
    total_activos = int(activo_circulante + af_neto_total)
    st.metric("🧮 **Total Activos**", f"₡{total_activos:,.0f}")

    st.divider()

    # ========= Pasivo =========
    st.subheader("III. Pasivo")

    # A) Pasivo circulante
    st.markdown("**Pasivo circulante**")

    # Cuentas por pagar a proveedores (detalle) + verificación
    st.markdown("*Cuentas por pagar a proveedores*")
    cpp_cols = ["Proveedor", "Monto (₡)", "Verificado por asesor", "Tipo de evidencia", "Comentario"]
    cpp_placeholder = pd.DataFrame([{
        "Proveedor": "", "Monto (₡)": 0, "Verificado por asesor": False,
        "Tipo de evidencia": "", "Comentario": ""
    } for _ in range(3)])

    cpp_df = st.data_editor(
        cpp_placeholder,
        use_container_width=True,
        num_rows="dynamic",
        hide_index=True,
        key="bg_cpp",
        column_config={
            "Proveedor": st.column_config.TextColumn("Proveedor"),
            "Monto (₡)": st.column_config.NumberColumn("Monto (₡)", min_value=0, step=10000, format="₡ %d"),
            "Verificado por asesor": st.column_config.CheckboxColumn("Verificado por asesor", default=False),
            "Tipo de evidencia": st.column_config.SelectboxColumn("Tipo de evidencia", options=evidencias, required=False),
            "Comentario": st.column_config.TextColumn("Comentario"),
        },
    )
    cpp_total = int(pd.to_numeric(cpp_df.get("Monto (₡)", pd.Series()), errors="coerce").fillna(0).sum())
    st.caption(f"Subtotal CxP Proveedores: **₡{cpp_total:,.0f}**")

    # Anticipos de clientes (pasivo)
    st.markdown("*Anticipos de clientes*")
    antic_cols = ["Cliente/Descripción", "Monto (₡)", "Verificado por asesor", "Tipo de evidencia", "Comentario"]
    antic_placeholder = pd.DataFrame([{
        "Cliente/Descripción": "", "Monto (₡)": 0, "Verificado por asesor": False,
        "Tipo de evidencia": "", "Comentario": ""
    } for _ in range(2)])

    antic_df = st.data_editor(
        antic_placeholder,
        use_container_width=True,
        num_rows="dynamic",
        hide_index=True,
        key="bg_anticipos",
        column_config={
            "Cliente/Descripción": st.column_config.TextColumn("Cliente/Descripción"),
            "Monto (₡)": st.column_config.NumberColumn("Monto (₡)", min_value=0, step=10000, format="₡ %d"),
            "Verificado por asesor": st.column_config.CheckboxColumn("Verificado por asesor", default=False),
            "Tipo de evidencia": st.column_config.SelectboxColumn("Tipo de evidencia", options=evidencias, required=False),
            "Comentario": st.column_config.TextColumn("Comentario"),
        },
    )
    antic_total = int(pd.to_numeric(antic_df.get("Monto (₡)", pd.Series()), errors="coerce").fillna(0).sum())
    st.caption(f"Subtotal Anticipos de clientes: **₡{antic_total:,.0f}**")

    # Cuentas por pagar a corto plazo (traídas de Deudas – corto)
    st.markdown("*Cuentas por pagar a corto plazo (de Deudas Paso 6)*")
    st.info(f"Total de corto plazo desde Deudas: **₡{tot_corto:,.0f}**")

    pasivo_circulante = int(cpp_total + antic_total + tot_corto)
    st.metric("💳 **Total Pasivo Circulante**", f"₡{pasivo_circulante:,.0f}")

    st.markdown("---")

    # B) Pasivo a largo plazo (de Deudas)
    st.markdown("**Pasivo a largo plazo**")
    st.info(f"Total de largo plazo desde Deudas: **₡{tot_largo:,.0f}**")
    pasivo_largo = int(tot_largo)

    # ========= Total Pasivo =========
    total_pasivo = int(pasivo_circulante + pasivo_largo)
    st.metric("📉 **Total Pasivos**", f"₡{total_pasivo:,.0f}")

    st.divider()

    # ========= Patrimonio y Capital de Trabajo =========
    patrimonio = int(total_activos - total_pasivo)
    capital_trabajo = int(activo_circulante - pasivo_circulante)

    colA, colB = st.columns(2)
    with colA:
        st.metric("📈 **Patrimonio (Activo - Pasivo)**", f"₡{patrimonio:,.0f}")
    with colB:
        st.metric("🧰 **Capital de trabajo (AC - PC)**", f"₡{capital_trabajo:,.0f}")

    st.divider()

    # ========= Comentarios del asesor =========
    st.subheader("Comentarios del asesor")
    comentarios = st.text_area("Observaciones, aclaraciones o notas relevantes para el análisis:", key="bg_comentarios", height=140)

    st.divider()

    # ========= Guardar / Navegación =========
    c1, c2 = st.columns([0.5, 0.5])
    with c1:
        if st.button("⬅️ Volver a Gastos operativos", key="bg_back_go", use_container_width=True):
            st.session_state.step = 6
            st.rerun()
    with c2:
        if st.button("Guardar Balance y continuar ➡️", key="bg_save_next", use_container_width=True):
            # --- Helper local: asegurar DataFrame ---
            def _as_df(obj, cols=None):
                if isinstance(obj, pd.DataFrame):
                    return obj.copy()
                return pd.DataFrame(obj or [], columns=cols)

            st.session_state.setdefault("reporte", {})

            # Coerciones seguras desde session_state (pueden venir como DF o lista)
            inv_mp_df  = _as_df(st.session_state.get("bg_inv_mp"))
            inv_pp_df  = _as_df(st.session_state.get("bg_inv_pp"))
            inv_pt_df  = _as_df(st.session_state.get("bg_inv_pt"))
            af_df_save = _as_df(st.session_state.get("bg_activo_fijo"))

            # También convertimos los que ya están en memoria (por consistencia)
            caja_save  = _as_df(caja_df)
            cxc_save   = _as_df(cxc_df)
            cpp_save   = _as_df(cpp_df)
            antic_save = _as_df(antic_df)

            st.session_state["reporte"]["balance_general"] = {
                "activo_circulante": {
                    "caja_bancos": caja_save.fillna("").to_dict(orient="records"),
                    "cxc_clientes": cxc_save.fillna("").to_dict(orient="records"),
                    "inventarios": {
                        "materia_prima":      inv_mp_df.fillna("").to_dict(orient="records"),
                        "producto_proceso":   inv_pp_df.fillna("").to_dict(orient="records"),
                        "producto_terminado": inv_pt_df.fillna("").to_dict(orient="records"),
                        "subtotales": {
                            "materia_prima":        int(subtotales_inv.get("Materia prima", 0)),
                            "producto_proceso":     int(subtotales_inv.get("Producto en proceso", 0)),
                            "producto_terminado":   int(subtotales_inv.get("Producto terminado", 0)),
                            "total_inventarios":    int(total_inventarios),
                        }
                    },
                    "totales": {
                        "caja_bancos":       int(caja_total),
                        "cxc_clientes":      int(cxc_total),
                        "total_inventarios": int(total_inventarios),
                        "activo_circulante": int(activo_circulante),
                    }
                },
                "activo_fijo_neto": {
                    "detalle":    af_df_save.fillna("").to_dict(orient="records"),
                    "total_neto": int(af_neto_total),
                },
                "activos_totales": int(total_activos),
                "pasivo": {
                    "pasivo_circulante": {
                        "cxp_proveedores":         cpp_save.fillna("").to_dict(orient="records"),
                        "anticipos_clientes":      antic_save.fillna("").to_dict(orient="records"),
                        "deudas_corto_plazo":      int(tot_corto),
                        "total_pasivo_circulante": int(pasivo_circulante),
                    },
                    "pasivo_largo_plazo": int(pasivo_largo),
                    "pasivo_total":       int(total_pasivo),
                },
                "patrimonio":      int(patrimonio),
                "capital_trabajo": int(capital_trabajo),
                "comentarios_asesor": str(comentarios or ""),
            }
            st.success("Balance general guardado. Avanzando…")
            st.session_state.step = 9  # <-- avanzar al paso siguiente
            st.rerun()

    st.stop()


##############################################################################################################################



# informe_portada.py — Etapa 1: Asesor, fecha/hora y GPS
import datetime as dt
from zoneinfo import ZoneInfo
import streamlit as st

# Evitar conflicto si otra página ya llamó set_page_config
if not st.session_state.get("_page_config_set"):
    st.set_page_config(page_title="Informe – Portada", page_icon="📑", layout="centered")
    st.session_state["_page_config_set"] = True

TZ = ZoneInfo("America/Costa_Rica")

# ---------- Helpers robustos ----------
def _fmt_dt(x):
    """Devuelve fecha/hora como 'dd/mm/YYYY HH:MM:SS' o None si no puede formatear."""
    try:
        if x is None:
            return None
        if isinstance(x, str):
            return x  # ya viene formateada desde el Paso 1 (reporte.asesor.fecha_hora)
        # datetime / pandas.Timestamp
        if hasattr(x, "tzinfo") and x.tzinfo is not None:
            x = x.astimezone(TZ)
        return dt.datetime.fromtimestamp(x.timestamp(), tz=TZ).strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        try:
            # último intento: parsear string ISO
            return dt.datetime.fromisoformat(str(x)).astimezone(TZ).strftime("%d/%m/%Y %H:%M:%S")
        except Exception:
            return None

def _parse_gps_str(s):
    """Convierte 'lat, lon' en (lat, lon) floats."""
    try:
        if not s:
            return None, None
        parts = [p.strip() for p in str(s).split(",")]
        if len(parts) >= 2:
            return float(parts[0]), float(parts[1])
    except Exception:
        pass
    return None, None

def _maps_links(lat, lon):
    lat_s = f"{lat:.6f}"
    lon_s = f"{lon:.6f}"
    g = f"https://www.google.com/maps/search/?api=1&query={lat_s},{lon_s}"
    g_at = f"https://www.google.com/maps/@{lat_s},{lon_s},18z"
    osm = f"https://www.openstreetmap.org/?mlat={lat_s}&mlon={lon_s}#map=18/{lat_s}/{lon_s}"
    return g, g_at, osm

# ---------- Lectura desde session_state ----------
ases = st.session_state.get("asesor", {}) or {}
rep_ases = (st.session_state.get("reporte", {}) or {}).get("asesor", {}) or {}

# Nombre del asesor
nombre = rep_ases.get("nombre") or ases.get("nombre") or "(sin registrar)"

# Fecha y hora de visita + fuente
fecha_str = rep_ases.get("fecha_hora")
if not fecha_str:
    fecha_str = _fmt_dt(ases.get("fecha_hora")) or dt.datetime.now(TZ).strftime("%d/%m/%Y %H:%M:%S")
fuente = rep_ases.get("hora_fuente") or (
    "Internet" if ases.get("timestamp_source") == "internet"
    else ("Dispositivo" if ases.get("timestamp_source") else "—")
)

# GPS (lat, lon)
lat = ases.get("lat"); lon = ases.get("lon")
if lat is None or lon is None:
    lat, lon = _parse_gps_str(rep_ases.get("gps"))

# Enlaces de mapa (preferir los guardados en reporte)
gmap = rep_ases.get("google_maps")
gview = rep_ases.get("google_maps_vista")
osm  = rep_ases.get("openstreetmap")
if (not gmap or not osm) and (lat is not None and lon is not None):
    gmap_gen, gview_gen, osm_gen = _maps_links(float(lat), float(lon))
    gmap = gmap or gmap_gen
    gview = gview or gview_gen
    osm = osm or osm_gen

# ---------- UI ----------
st.title("🧭 Encabezado de visita")
st.caption("Datos del **Paso 1**: asesor, fecha/hora y ubicación GPS del negocio.")

col1, col2 = st.columns([0.55, 0.45])
with col1:
    st.write(f"**Asesor:** {nombre}")
    st.write(f"**Fecha y hora de visita:** {fecha_str} ({fuente})")

with col2:
    if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
        st.write(f"**GPS negocio:** {float(lat):.6f}, {float(lon):.6f}")
        links = []
        if gmap:  links.append(f"[Google Maps]({gmap})")
        if gview: links.append(f"[Vista @18z]({gview})")
        if osm:   links.append(f"[OpenStreetMap]({osm})")
        if links:
            st.markdown(" · ".join(links))
    else:
        st.info("GPS no disponible aún.")

# === Etapa 2: Cliente y Negocio (detalle + comentario del asesor) ===
import streamlit as st

def _fmt_antiguedad(anios, meses):
    try:
        a = int(anios or 0); m = int(meses or 0)
        if a == 0 and m == 0:
            return ""
        return f"{a} año(s) y {m} mes(es)"
    except Exception:
        return ""

# Preferir lo guardado en reporte -> cliente_negocio
cn = (st.session_state.get("reporte", {}) or {}).get("cliente_negocio", {}) or {}
cli_live = st.session_state.get("cliente", {}) or {}
neg_live = st.session_state.get("negocio", {}) or {}

cliente_nombre = cn.get("cliente_nombre") or cli_live.get("nombre_completo") or "(sin registrar)"
cliente_cedula = cn.get("cliente_identificacion") or cli_live.get("identificacion") or "(sin registrar)"

nombre_comercial = cn.get("nombre_comercial") or neg_live.get("nombre_comercial") or "—"
sector = cn.get("sector_economico") or neg_live.get("sector_economico") or "—"
actividad = cn.get("actividad_principal") or neg_live.get("actividad_principal") or "—"
ubicacion = cn.get("ubicacion") or neg_live.get("ubicacion") or "—"
persona_juridica = cn.get("persona_juridica") or ("Sí" if neg_live.get("persona_juridica") else "No")
patente = cn.get("patente_municipal") or ("Sí" if neg_live.get("patente_municipal") else "No")
registros = cn.get("registros_contables") or ("Sí" if neg_live.get("registros_contables") else "No")
tipo_local = cn.get("tipo_local") or neg_live.get("tipo_local") or "—"
antiguedad = cn.get("antiguedad") or _fmt_antiguedad(
    neg_live.get("antiguedad_anios"), neg_live.get("antiguedad_meses")
) or "—"

# Comentario del asesor: preferir el de la valoración 3VAL; si no, obs_general
coment_asesor = (
    ((st.session_state.get("reporte", {}) or {}).get("valoracion_asesor", {}) or {}).get("comentario")
    or st.session_state.get("obs_general", "")
    or "—"
)

st.subheader("👤 Cliente y negocio")

colL, colR = st.columns([0.55, 0.45], vertical_alignment="top")
with colL:
    st.markdown(
        f"""
**Cliente:** {cliente_nombre}  
**Identificación:** {cliente_cedula}  

**Nombre comercial:** {nombre_comercial}  
**Actividad principal:** {actividad}  
**Sector económico:** {sector}  
**Tipo de local:** {tipo_local}  
**Persona jurídica:** {persona_juridica}  
**Patente municipal:** {patente}  
**Registros contables:** {registros}  
**Antigüedad del negocio:** {antiguedad}
        """.strip()
    )

with colR:
    st.markdown("**Ubicación / señas del negocio**")
    st.info(ubicacion or "—")

st.markdown("**Comentario del asesor**")
st.info(coment_asesor)


# =========================
# III. Valoración del asesor de crédito
# (insertar este bloque antes del "IV. Estado de Resultados")
# =========================

def _leer_valoracion_asesor():
    """Devuelve (dict_valoracion, fuente_str). Tolera faltantes."""
    # 1) Preferir lo guardado por Paso 3VAL en el reporte
    rep_val = st.session_state.get("reporte", {}).get("valoracion_asesor")
    if isinstance(rep_val, dict) and rep_val:
        return rep_val, "reporte.valoracion_asesor"
    # 2) Fallback: estado en vivo
    live_val = st.session_state.get("valoracion_asesor")
    if isinstance(live_val, dict) and live_val:
        return live_val, "session_state.valoracion_asesor"
    # 3) Nada
    return {}, "—"

val, val_src = _leer_valoracion_asesor()

# Campos con defaults seguros
conoc = int((val.get("conocimiento_0a10") or 0) if str(val.get("conocimiento_0a10") or "").strip() != "" else 0)
cred  = int((val.get("credibilidad_0a10") or 0) if str(val.get("credibilidad_0a10") or "").strip() != "" else 0)
dudas = (val.get("dudas_declaracion") or "Sin dudas")
clas  = (val.get("clasificacion") or "—")
fact  = float(val.get("factor_asesor_0a1") or 0.0)

ev_raw = val.get("evidencia", [])
if isinstance(ev_raw, str):
    evidencia = [s.strip() for s in ev_raw.split(",") if s.strip()]
elif isinstance(ev_raw, list):
    evidencia = [str(x).strip() for x in ev_raw if str(x).strip()]
else:
    evidencia = []
coment = (val.get("comentario") or "").strip()

# (Opcional) Detalle del cálculo del factor, si aplica
avg = (conoc + cred) / 2.0
base_calc = 0.6 + 0.04 * avg
mult_dudas_map = {"Sin dudas": 1.00, "Dudas leves": 0.85, "Dudas serias": 0.60}
mult_dudas = mult_dudas_map.get(dudas, 1.00)

st.subheader("III. Valoración del asesor de crédito")

colV1, colV2, colV3 = st.columns(3)
with colV1:
    st.metric("Conocimiento (0–10)", f"{conoc}")
with colV2:
    st.metric("Credibilidad (0–10)", f"{cred}")
with colV3:
    st.metric("Factor de confiabilidad", f"{fact:.2f}")

colV4, colV5 = st.columns(2)
with colV4:
    st.write(f"**Percepción de veracidad:** {dudas}")
with colV5:
    st.write(f"**Clasificación del caso:** {clas}")

# Evidencia observada
st.markdown("**Evidencia observada:**")
if evidencia:
    st.markdown("\n".join([f"- {e}" for e in evidencia]))
else:
    st.caption("—")

# Comentario del asesor
st.markdown("**Comentario del asesor:**")
st.info(coment or "—")

# Glosa del factor (si hay datos)
if (conoc or cred) and fact > 0:
    st.caption(
        f"Glosa del factor: base={base_calc:.2f} (0.60 + 0.04×promedio de conocimiento/credibilidad={avg:.1f}) × "
        f"ajuste por dudas={mult_dudas:.2f} → {base_calc * mult_dudas:.2f}"
        + (" (redondeado/limitado a [0.40–1.00])" if abs((base_calc * mult_dudas) - fact) > 1e-6 else "")
    )
# st.caption(f"Fuente de valoración: {val_src}")  # útil para depurar; dejar comentado si no quieres mostrarlo




# =========================
# III-b. Análisis de ventas
# (pegar después de la "Valoración del asesor" y antes del ER)
# =========================

def _num(x):
    try:
        if x is None: return 0.0
        return float(str(x).replace(",", ""))
    except Exception:
        return 0.0

def _fmt_col(x):
    try:
        return f"₡ {int(round(_num(x))):,}".replace(",", ".")
    except Exception:
        return "₡ 0"

def _ajuste_tipicidad(valor, tipicidad):
    """Regla simple como en 3A: Alto -10%, Bajo +10%, Típico sin ajuste."""
    if valor is None: 
        return None, "—"
    v = _num(valor)
    if tipicidad == "Alto":  return v * 0.90, "Alto → −10%"
    if tipicidad == "Bajo":  return v * 1.10, "Bajo → +10%"
    return v, "Típico (sin ajuste)"

def _desv_pct(a, b):
    """Desviación relativa promedio; None si no se puede."""
    a, b = _num(a), _num(b)
    if a <= 0 or b <= 0: 
        return None
    base = (a + b) / 2.0
    return abs(a - b) / base

def _precision_label(ape):
    """Clasifica precisión de la clienta según el APE (error porcentual absoluto)."""
    if ape is None: 
        return "Indefinida"
    if ape <= 0.20: 
        return "Alta (≤20%)"
    if ape <= 0.40: 
        return "Media (20–40%)"
    return "Baja (>40%)"

rep = st.session_state.get("reporte", {})

# 3A Top-down (declaración de la clienta)
vtd = rep.get("ventas_topdown", {}) or {}
top_raw      = vtd.get("monto_colones")
tipicidad    = vtd.get("tipicidad")
fuente       = vtd.get("fuente")
conf_cli     = vtd.get("confianza_cliente_0a10")
coment_td    = (vtd.get("comentario") or "").strip()
top_ajustado, txt_ajuste = _ajuste_tipicidad(top_raw, tipicidad) if top_raw else (None, "—")

# 3B Bottom-up
vbu = rep.get("ventas_bottomup", {}) or {}
bottom_val   = vbu.get("ventas_estimadas_colones")
coment_bu    = (vbu.get("comentario") or "").strip()

# 3C Insumos/Margen
vin = rep.get("ventas_insumos_simple", rep.get("ventas_insumos", {})) or {}
insumos_val  = None if vin.get("no_aplica") else vin.get("ventas_estimadas_colones")
coment_ins   = (vin.get("comentario") or "").strip()
tiene_regs   = vin.get("tiene_registros_compras", "")

# Conciliación (si existe)
vcon = rep.get("ventas_conciliacion", {}) or {}
ventas_conc  = vcon.get("ventas_conciliadas_colones")
max_dev      = vcon.get("desviacion_max_pct")   # ya viene como fracción (0–1) si usaste el código previo
pesos        = vcon.get("pesos", {})
det_conc     = vcon.get("detalle", {}) or {}

# Factor/confiabilidad del asesor (contexto)
val = rep.get("valoracion_asesor", {}) or {}
factor_asesor = val.get("factor_asesor_0a1")
dudas = val.get("dudas_declaracion")
coment_asesor = (val.get("comentario") or "").strip()

# Tabla de estimaciones
filas = [
    {"Ángulo": "Top-down (clienta)", "Monto bruto": _fmt_col(top_raw), "Ajuste": txt_ajuste if top_ajustado else "—", "Usado": _fmt_col(top_ajustado) if top_ajustado else "—"},
    {"Ángulo": "Bottom-up (operativa)", "Monto bruto": _fmt_col(bottom_val), "Ajuste": "—", "Usado": _fmt_col(bottom_val) if bottom_val else "—"},
    {"Ángulo": "Insumos/Margen", "Monto bruto": ("No aplica" if vin.get("no_aplica") else _fmt_col(insumos_val)), "Ajuste": "—", "Usado": "—" if vin.get("no_aplica") else (_fmt_col(insumos_val) if insumos_val else "—")},
]
st.subheader("III-b. Análisis de ventas")
st.caption("Comparativa de ángulos y precisión declarativa de la clienta.")

st.dataframe(
    pd.DataFrame(filas),
    use_container_width=True,
    hide_index=True
)

# Si hay conciliación, mostrar resultado y métricas de precisión
if ventas_conc:
    ventas_conc = _num(ventas_conc)
    # Error porcentual absoluto de la clienta (declaración ajustada vs conciliado)
    ape = None
    if top_ajustado and ventas_conc > 0:
        ape = abs(_num(top_ajustado) - ventas_conc) / ventas_conc
    # Desviación máxima entre métodos (si no viene precalculada, la calculamos)
    if max_dev is None:
        pares = []
        for a, b in [(top_ajustado, bottom_val), (top_ajustado, insumos_val), (bottom_val, insumos_val)]:
            d = _desv_pct(a, b)
            if d is not None:
                pares.append(d)
        max_dev = max(pares) if pares else None

    colS1, colS2, colS3 = st.columns(3)
    with colS1:
        st.metric("Ventas conciliadas", _fmt_col(ventas_conc))
    with colS2:
        st.metric("Precisión de la clienta", ("—" if ape is None else f"{(1-ape):.0%}"))
    with colS3:
        st.metric("Desviación máx. entre métodos", ("—" if max_dev is None else f"{max_dev:.0%}"))

    # Calidad de la fuente declarativa y confianza
    fuente_formal = fuente in ["Facturación electrónica", "POS/Datáfono", "Extractos bancarios/SINPE"]
    colQ1, colQ2, colQ3 = st.columns(3)
    with colQ1:
        st.write(f"**Fuente Top-down:** {fuente or '—'}")
        st.caption("Clasificación: " + ("Formal" if fuente_formal else ("—" if not fuente else "Informal")))
    with colQ2:
        st.write(f"**Confianza declarada por clienta:** {conf_cli if conf_cli is not None else '—'}/10")
    with colQ3:
        st.write(f"**Factor del asesor:** {f'{factor_asesor:.2f}' if factor_asesor else '—'}  ·  **Dudas:** {dudas or '—'}")

    # Pesos (si existen)
    if pesos:
        st.markdown("**Ponderaciones en conciliación (Top/Bottom/Insumos):** "
                    f"{pesos.get('top_down', 0):.2f} / {pesos.get('bottom_up', 0):.2f} / {pesos.get('insumos', 0):.2f}")

# Comentarios específicos
st.markdown("**Comentarios específicos de ventas:**")
comentarios = []
if coment_td:  comentarios.append(f"- Top-down (clienta): {coment_td}")
if coment_bu:  comentarios.append(f"- Bottom-up: {coment_bu}")
if coment_ins: comentarios.append(f"- Insumos/Margen: {coment_ins}")
if comentarios:
    st.markdown("\n".join(comentarios))
else:
    st.caption("—")

# Comentario del asesor (si no lo mostraste ya en la sección anterior y quieres reiterarlo aquí)
if coment_asesor:
    st.markdown("**Comentario del asesor:**")
    st.info(coment_asesor)

# Etiqueta cualitativa de precisión (si hay APE)
if ventas_conc and top_ajustado:
    etiqueta = _precision_label(ape)
    st.caption(f"**Etiqueta de precisión declarativa de la clienta:** {etiqueta}")





# estado_resultados.py
# ---------------------------------------------------------
# Lee del st.session_state["reporte"] generado por tus pasos
# y calcula el Estado de Resultados. Al final muestra
# una valoración de verificación (% verificado vs no).

import streamlit as st
import pandas as pd
import datetime as dt
from zoneinfo import ZoneInfo

# Evitar choque si otra página ya configuró page_config
if not st.session_state.get("_page_config_set"):
    st.set_page_config(page_title="Estado de Resultados", page_icon="📑", layout="centered")
    st.session_state["_page_config_set"] = True

TZ = ZoneInfo("America/Costa_Rica")

# ========= Helpers =========
def _getr(path, default=None):
    cur = st.session_state.get("reporte", {}) or {}
    try:
        for p in path:
            cur = cur[p]
        return cur
    except Exception:
        return default

def _num(x, default=0.0):
    try:
        if x is None: return float(default)
        return float(x)
    except Exception:
        try:
            s = str(x).strip().replace(",", "")
            return float(s)
        except Exception:
            return float(default)

def _fmt_col(x):
    try:
        return f"₡{int(round(_num(x))):,}".replace(",", ".")
    except Exception:
        return "₡0"

def _mult_mensualizacion(per):
    per = (str(per) or "").strip().lower()
    if per == "diario":       return 30.0
    if per == "semanal":      return 52.0 / 12.0
    if per == "quincenal":    return 2.0
    if per == "mensual":      return 1.0
    if per == "bimestral":    return 0.5
    if per == "trimestral":   return 1.0 / 3.0
    if per == "semestral":    return 1.0 / 6.0
    if per == "anual":        return 1.0 / 12.0
    return 0.0

def _sum_from_table(df, value_col, verif_col=None):
    """Suma segura de una tabla con columna de valor y opcional de verificación."""
    if df is None or len(df) == 0:
        return 0.0, 0.0
    df = pd.DataFrame(df).copy()
    # Normaliza nombres a minúsculas
    df.columns = [str(c).strip() for c in df.columns]
    lower = {c: c.lower() for c in df.columns}
    df = df.rename(columns=lower)

    # Mapear posibles nombres
    candidates_val = [value_col.lower(), "monto por período (₡)".lower(), "gasto mensualizado (₡)".lower(),
                      "cuota mensualizada (₡)".lower(), "ingreso mensualizado (₡)".lower()]
    col_val = next((c for c in candidates_val if c in df.columns), None)

    if col_val is None:
        # Intento: mensualizar si hay "monto por período (₡)" + "periodicidad"
        if "monto por período (₡)".lower() in df.columns and "periodicidad" in df.columns:
            montos = pd.to_numeric(df["monto por período (₡)".lower()], errors="coerce").fillna(0)
            mults = df["periodicidad"].map(_mult_mensualizacion)
            total = float((montos * mults).sum())
            verif_total = 0.0
            if verif_col:
                col_v = verif_col.lower()
                if col_v in df.columns:
                    mask = df[col_v].fillna(False).astype(bool)
                    verif_total = float((montos[mask] * df.loc[mask, "periodicidad"].map(_mult_mensualizacion)).sum())
            return total, verif_total
        return 0.0, 0.0

    total = float(pd.to_numeric(df[col_val], errors="coerce").fillna(0).sum())

    verif_total = 0.0
    if verif_col:
        col_v = verif_col.lower()
        if col_v in df.columns:
            mask = df[col_v].fillna(False).astype(bool)
            verif_total = float(pd.to_numeric(df.loc[mask, col_val], errors="coerce").fillna(0).sum())

    return total, verif_total

# ========= Recolecta valores del reporte (con fallbacks) =========
src = {}  # para mostrar origen de algunos valores (opcional)

# 1) Ventas (preferir conciliadas)
ventas_total = _getr(["ventas_conciliacion", "ventas_conciliadas_colones"])
if ventas_total:
    src["ventas"] = "reporte.ventas_conciliacion.ventas_conciliadas_colones"
else:
    ventas_total = (
        _getr(["ventas_topdown", "monto_colones"]) or
        _getr(["ventas_bottomup", "ventas_estimadas_colones"]) or
        _getr(["ventas_insumos_simple", "ventas_estimadas_colones"]) or
        _getr(["ventas_insumos", "ventas_estimadas_colones"])
    )
ventas_total = _num(ventas_total, 0)

# 2) Compras/costo (si usas el método 3C simple)
compras_total = _getr(["ventas_insumos_simple", "compras_mes_colones"], 0)
compras_total = _num(compras_total, 0)

# 3) Margen (opcional: solo para mostrar en métrica)
tipo_margen = _getr(["ventas_insumos_simple", "tipo_margen"])
margen_pct = _getr(["ventas_insumos_simple", "margen_pct"])

# 4) Gastos operativos (mensualizado) + verificado
gop_total = _getr(["gastos_operativos", "totales", "total_gasto_operativo_mensualizado_colones"])
gop_verif = _getr(["gastos_operativos", "totales", "total_gasto_operativo_verificado_colones"])
if gop_total is None:
    # Fallback desde tabla
    gop_total, gop_verif = _sum_from_table(
        _getr(["gastos_operativos", "tabla"], []),
        value_col="Gasto mensualizado (₡)",
        verif_col="Verificado por asesor",
    )
gop_total = _num(gop_total, 0)
gop_verif = _num(gop_verif, 0)

# 5) Otros ingresos (usar ponderado si existe; verificación desde mensualizado verificado)
oi_pond = _getr(["otros_ingresos", "totales", "total_ponderado_colones"])
oi_mens = _getr(["otros_ingresos", "totales", "total_mensualizado_colones"])
oi_verif_mens = _getr(["otros_ingresos", "totales", "total_verificado_mensualizado_colones"])
# Total para ER:
otros_ing_total = _num(oi_pond if oi_pond else oi_mens, 0)
# Totales para cobertura de verificación:
oi_base_para_cobertura = _num(oi_mens, 0) if _num(oi_mens, 0) > 0 else _num(oi_pond, 0)
oi_verif = min(_num(oi_verif_mens, 0), oi_base_para_cobertura)

# 6) Gastos familiares (mensualizado) + verificado
gf_total = _getr(["gastos_familiares", "totales", "total_gastos_familiares_mensualizado_colones"])
gf_verif = _getr(["gastos_familiares", "totales", "total_gastos_familiares_verificado_colones"])
if gf_total is None:
    # Fallback desde tabla
    gf_total, gf_verif = _sum_from_table(
        _getr(["gastos_familiares", "tabla"], []),
        value_col="Gasto mensualizado (₡)",
        verif_col="Verificado por asesor",
    )
gf_total = _num(gf_total, 0)
gf_verif = _num(gf_verif, 0)

# 7) Pago de deudas (mensualizado) + verificado
deu_total = _getr(["deudas_activas", "totales", "total_pago_mensual_colones"], 0)
deu_verif = _getr(["deudas_activas", "totales", "total_pago_mensual_verificado_colones"], 0)
deu_total = _num(deu_total, 0)
deu_verif = _num(deu_verif, 0)

# ========= Cálculos de ER =========
# Utilidad bruta (si hay % de margen y base, se podría usar; por simplicidad usamos ventas - compras)
utilidad_bruta = max(0.0, ventas_total - compras_total)
utilidad_neta_ope = utilidad_bruta - gop_total
subtotal_post_otros = utilidad_neta_ope + otros_ing_total
disponible_final = subtotal_post_otros - gf_total - deu_total

# ========= UI =========
st.header("📑 Estado de Resultados (mensualizado)")

# Orígenes (opcional)
with st.expander("🔎 Origen rápido (rutas detectadas)"):
    st.json({
        "ventas": src.get("ventas", "conciliadas o fallback 3A/3B/3C"),
        "gastos_operativos": "reporte.gastos_operativos.totales (o tabla)",
        "otros_ingresos": "reporte.otros_ingresos.totales (ponderado/mens.)",
        "gastos_familiares": "reporte.gastos_familiares.totales (o tabla)",
        "deudas_activas": "reporte.deudas_activas.totales",
    })

# Cabecera con ventas / compras / margen
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Ventas", _fmt_col(ventas_total))
with col2:
    st.metric("Compras/Costos", _fmt_col(compras_total))
with col3:
    if tipo_margen and margen_pct is not None:
        base_txt = ("ventas" if (tipo_margen == "Sobre ventas") else ("compras" if (tipo_margen == "Sobre compras (markup)") else "—"))
        pct = float(margen_pct)
        pct = pct if pct <= 1 else pct/100.0
        st.metric("Margen (base)", f"{pct:.0%} sobre {base_txt}")
    else:
        st.metric("Margen (base)", "—")

st.divider()

# Bloque principal
col4, col5 = st.columns(2)
with col4:
    st.metric("🧮 Utilidad Bruta", _fmt_col(utilidad_bruta))
with col5:
    st.metric("🧾 Gastos operativos", _fmt_col(gop_total))

st.metric("📌 Utilidad Neta Operativa", _fmt_col(utilidad_neta_ope))

st.divider()

col6, col7 = st.columns(2)
with col6:
    st.metric("➕ Otros ingresos", _fmt_col(otros_ing_total))
with col7:
    st.metric("Subtotal post-otros", _fmt_col(subtotal_post_otros))

st.divider()

col8, col9 = st.columns(2)
with col8:
    st.metric("👪 Gastos familiares", _fmt_col(gf_total))
with col9:
    st.metric("💳 Pago de deudas", _fmt_col(deu_total))

st.success(f"💰 **Disponible para el préstamo:** {_fmt_col(disponible_final)}")

# ========= Valoración de verificación =========
st.divider()
st.subheader("✅ Cobertura de verificación de la información")

# Tabla por rubro
verif_rows = [
    {
        "Concepto": "Otros ingresos",
        "Total (₡)": int(round(oi_base_para_cobertura)),
        "Verificado (₡)": int(round(oi_verif)),
        "% Verificado": f"{(oi_verif / oi_base_para_cobertura * 100):.0f}%" if oi_base_para_cobertura > 0 else "—",
    },
    {
        "Concepto": "Gastos operativos",
        "Total (₡)": int(round(gop_total)),
        "Verificado (₡)": int(round(gop_verif)),
        "% Verificado": f"{(gop_verif / gop_total * 100):.0f}%" if gop_total > 0 else "—",
    },
    {
        "Concepto": "Gastos familiares",
        "Total (₡)": int(round(gf_total)),
        "Verificado (₡)": int(round(gf_verif)),
        "% Verificado": f"{(gf_verif / gf_total * 100):.0f}%" if gf_total > 0 else "—",
    },
    {
        "Concepto": "Pago de deudas",
        "Total (₡)": int(round(deu_total)),
        "Verificado (₡)": int(round(deu_verif)),
        "% Verificado": f"{(deu_verif / deu_total * 100):.0f}%" if deu_total > 0 else "—",
    },
]
st.dataframe(pd.DataFrame(verif_rows), use_container_width=True, hide_index=True)

# Resumen global (% verificado sobre la suma absoluta de montos considerados)
glob_total = oi_base_para_cobertura + gop_total + gf_total + deu_total
glob_verif = oi_verif + gop_verif + gf_verif + deu_verif
pct_glob = (glob_verif / glob_total * 100) if glob_total > 0 else None

st.info(
    f"**Cobertura verificada global:** "
    f"{(pct_glob and f'{pct_glob:.0f}%') or '—'}  "
    f"({ _fmt_col(glob_verif) } verificados de { _fmt_col(glob_total) })."
)

# (Opcional) Ver tablas de origen
with st.expander("Ver tablas de origen (si están disponibles)"):
    rep = st.session_state.get("reporte", {})
    st.subheader("Otros ingresos")
    st.dataframe(pd.DataFrame(rep.get("otros_ingresos", {}).get("tabla", [])), use_container_width=True)
    st.subheader("Gastos operativos")
    st.dataframe(pd.DataFrame(rep.get("gastos_operativos", {}).get("tabla", [])), use_container_width=True)
    st.subheader("Gastos familiares")
    st.dataframe(pd.DataFrame(rep.get("gastos_familiares", {}).get("tabla", [])), use_container_width=True)
    st.subheader("Deudas activas")
    st.dataframe(pd.DataFrame(rep.get("deudas_activas", {}).get("tabla", [])), use_container_width=True)



# balance_general.py
# ---------------------------------------------------------
# Balance General (resumen) + Tabla de Verificación
# Lee los datos de st.session_state (pasos previos) y calcula:
# - Activo Circulante, Activo Fijo Neto, Total Activos
# - Pasivo Circulante, Pasivo Largo Plazo, Total Pasivos
# - Patrimonio y Capital de Trabajo
# Además muestra una tabla de "Total / Verificado / %Verificado" por rubro.

import streamlit as st
import pandas as pd

# Evitar duplicar configuración si ya se hizo en otra página
if not st.session_state.get("_page_config_set"):
    st.set_page_config(page_title="Balance General", page_icon="📊", layout="centered")
    st.session_state["_page_config_set"] = True

# ---------- Helpers robustos ----------
def _coerce_df(obj, cols_hint=None) -> pd.DataFrame:
    """Convierte obj a DataFrame y normaliza nombres de columnas a minúsculas."""
    if isinstance(obj, pd.DataFrame):
        df = obj.copy()
    elif isinstance(obj, list):
        df = pd.DataFrame(obj)
    elif isinstance(obj, dict):
        # dict de filas -> df con 1 fila | dict de columnas -> DataFrame(dict)
        try:
            df = pd.DataFrame(obj)
            # si salió con shape rara, intenta como lista
            if df.shape[0] == 0 and obj:
                df = pd.DataFrame([obj])
        except Exception:
            df = pd.DataFrame([obj])
    elif obj is None:
        df = pd.DataFrame()
    else:
        df = pd.DataFrame()

    if df.empty and cols_hint:
        df = pd.DataFrame(columns=cols_hint)

    # normaliza nombres a str/lower
    if not df.empty:
        df.columns = [str(c).strip().lower() for c in df.columns]
    return df

def _find_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """Devuelve el nombre de columna que exista en df (comparando en minúsculas)."""
    if df is None or df.empty:
        return None
    cols = list(df.columns)
    for cand in candidates:
        c = cand.lower()
        if c in cols:
            return c
    return None

def _verified_mask(df: pd.DataFrame):
    """Devuelve Serie booleana de verificación si existe; si no, None."""
    if df is None or df.empty:
        return None
    col = _find_col(df, ["verificado por asesor", "verificado_por_asesor", "verificado"])
    if col is None:
        return None
    try:
        return df[col].fillna(False).astype(bool)
    except Exception:
        return None

def _sum_amounts(df: pd.DataFrame, value_cands: list[str]) -> float:
    """Suma una columna numérica indicada por candidatos; 0 si nada existe."""
    if df is None or df.empty:
        return 0.0
    col = _find_col(df, value_cands)
    if col is None:
        return 0.0
    return float(pd.to_numeric(df[col], errors="coerce").fillna(0).sum())

def _sum_amounts_verified(df: pd.DataFrame, value_cands: list[str]) -> float:
    """Suma solo las filas verificadas si existe una columna de verificación."""
    if df is None or df.empty:
        return 0.0
    col = _find_col(df, value_cands)
    if col is None:
        return 0.0
    mask = _verified_mask(df)
    if mask is None:
        return 0.0
    col_series = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    return float(col_series[mask].sum())

def _pct(v, total):
    if total and total != 0:
        return round(100.0 * float(v) / float(total), 1)
    return 0.0

# ---------- Lectura de tablas desde session_state ----------
# Activo circulante
caja_df = _coerce_df(st.session_state.get("bg_caja_bancos"))
cxc_df  = _coerce_df(st.session_state.get("bg_cxc_clientes"))
inv_mp  = _coerce_df(st.session_state.get("bg_inv_mp"))
inv_pp  = _coerce_df(st.session_state.get("bg_inv_pp"))
inv_pt  = _coerce_df(st.session_state.get("bg_inv_pt"))

# Activo fijo
af_df   = _coerce_df(st.session_state.get("bg_activo_fijo"))

# Pasivos propios de esta página
cpp_df   = _coerce_df(st.session_state.get("bg_cpp"))
anticip  = _coerce_df(st.session_state.get("bg_anticipos"))

# Deudas (Paso 6) – preferimos lo guardado en reporte, si estuviera
deu_tab = None
try:
    deu_tab = _coerce_df(st.session_state["reporte"]["deudas_activas"]["tabla"])
except Exception:
    # Si no está en reporte, intenta leer un posible editor vivo
    deu_tab = _coerce_df(st.session_state.get("de_deudas_activas_calc")) or _coerce_df(st.session_state.get("de_deudas_activas"))

# ---------- Cálculos: ACTIVO ----------
# Caja/Bancos
caja_total = _sum_amounts(caja_df, ["saldo (₡)", "saldo", "monto", "valor (₡)", "valor"])
caja_verif = _sum_amounts_verified(caja_df, ["saldo (₡)", "saldo", "monto", "valor (₡)", "valor"])

# Cuentas por Cobrar
cxc_total = _sum_amounts(cxc_df, ["monto (₡)", "monto", "valor (₡)", "valor"])
cxc_verif = _sum_amounts_verified(cxc_df, ["monto (₡)", "monto", "valor (₡)", "valor"])

# Inventarios
inv_mp_total = _sum_amounts(inv_mp, ["valor (₡)", "monto"])
inv_mp_verif = _sum_amounts_verified(inv_mp, ["valor (₡)", "monto"])

inv_pp_total = _sum_amounts(inv_pp, ["valor (₡)", "monto"])
inv_pp_verif = _sum_amounts_verified(inv_pp, ["valor (₡)", "monto"])

inv_pt_total = _sum_amounts(inv_pt, ["valor (₡)", "monto"])
inv_pt_verif = _sum_amounts_verified(inv_pt, ["valor (₡)", "monto"])

inv_total = inv_mp_total + inv_pp_total + inv_pt_total
inv_verif = inv_mp_verif + inv_pp_verif + inv_pt_verif

activo_circulante = caja_total + cxc_total + inv_total
ac_verif = caja_verif + cxc_verif + inv_verif

# Activo Fijo Neto (Valor Bruto - Depreciación)
# Intentamos columnas típicas; si no existen, tratamos de sumar "monto"
af_vb_col = _find_col(af_df, ["valor bruto (₡)", "valor bruto", "valor_bruto (₡)", "valor_bruto"])
af_da_col = _find_col(af_df, ["depreciación acum. (₡)", "depreciacion acum. (₡)", "depreciación", "depreciacion", "dep_acum (₡)"])

if af_vb_col:
    vb_total = float(pd.to_numeric(af_df[af_vb_col], errors="coerce").fillna(0).sum())
else:
    vb_total = _sum_amounts(af_df, ["monto", "valor (₡)", "valor"])

if af_da_col:
    da_total = float(pd.to_numeric(af_df[af_da_col], errors="coerce").fillna(0).sum())
else:
    da_total = 0.0  # si no hay columna de dep, asumimos 0

af_neto = max(0.0, vb_total - da_total)

# Verificado en AF (si existe columna de verificación)
mask_af = _verified_mask(af_df)
if mask_af is not None and af_vb_col:
    vb_ver = float(pd.to_numeric(af_df.loc[mask_af, af_vb_col], errors="coerce").fillna(0).sum())
    if af_da_col:
        da_ver = float(pd.to_numeric(af_df.loc[mask_af, af_da_col], errors="coerce").fillna(0).sum())
    else:
        da_ver = 0.0
    af_verif = max(0.0, vb_ver - da_ver)
else:
    af_verif = 0.0

total_activos = activo_circulante + af_neto
activos_verif = ac_verif + af_verif

# ---------- Cálculos: PASIVO ----------
# CxP y Anticipos (capturados aquí)
cxp_total = _sum_amounts(cpp_df, ["monto (₡)", "monto"])
cxp_verif = _sum_amounts_verified(cpp_df, ["monto (₡)", "monto"])

anticip_total = _sum_amounts(anticip, ["monto (₡)", "monto"])
anticip_verif = _sum_amounts_verified(anticip, ["monto (₡)", "monto"])

# Deudas CP/LP
deu_cp_total = 0.0
deu_lp_total = 0.0
deu_cp_verif = 0.0
deu_lp_verif = 0.0

if deu_tab is not None and not deu_tab.empty:
    # columnas típicas en paso 6
    deu_tab.columns = [str(c).strip().lower() for c in deu_tab.columns]
    col_saldo = _find_col(deu_tab, ["saldo adeudado (₡)", "saldo", "monto"])
    col_plazo = _find_col(deu_tab, ["plazo (clasificación)", "plazo", "clasificación", "clasificacion"])
    mask_ver = _verified_mask(deu_tab)

    if col_saldo:
        s = pd.to_numeric(deu_tab[col_saldo], errors="coerce").fillna(0.0)
        if col_plazo:
            cp_mask = deu_tab[col_plazo].str.contains("corto", case=False, na=False)
            lp_mask = deu_tab[col_plazo].str.contains("largo", case=False, na=False)
            deu_cp_total = float(s[cp_mask].sum())
            deu_lp_total = float(s[lp_mask].sum())

            if mask_ver is not None:
                deu_cp_verif = float(s[cp_mask & mask_ver].sum())
                deu_lp_verif = float(s[lp_mask & mask_ver].sum())
        else:
            # sin clasificación, todo a corto por defecto
            deu_cp_total = float(s.sum())
            if mask_ver is not None:
                deu_cp_verif = float(s[mask_ver].sum())
else:
    # Fallback a totales consolidados guardados en reporte
    try:
        tot = st.session_state["reporte"]["deudas_activas"]["totales"]
        deu_cp_total = float(tot.get("total_adeudado_corto_plazo_colones", 0))
        deu_lp_total = float(tot.get("total_adeudado_largo_plazo_colones", 0))
    except Exception:
        pass
    # sin tabla, no podemos distinguir verificados → 0

pasivo_circulante = cxp_total + anticip_total + deu_cp_total
pasivo_circulante_verif = cxp_verif + anticip_verif + deu_cp_verif

pasivo_largo = deu_lp_total
pasivo_largo_verif = deu_lp_verif

total_pasivos = pasivo_circulante + pasivo_largo
pasivos_verif = pasivo_circulante_verif + pasivo_largo_verif

# ---------- Patrimonio / CT ----------
patrimonio = total_activos - total_pasivos
capital_trabajo = activo_circulante - pasivo_circulante

# ---------- UI ----------
st.title("📊 Balance General (mensualizado)")

# Activo
st.subheader("Activo")
act_tab = pd.DataFrame([
    {"Concepto": "Caja y Bancos", "Monto (₡)": int(round(caja_total))},
    {"Concepto": "Cuentas por Cobrar a Clientes", "Monto (₡)": int(round(cxc_total))},
    {"Concepto": "Inventario – Materia prima", "Monto (₡)": int(round(inv_mp_total))},
    {"Concepto": "Inventario – Producto en proceso", "Monto (₡)": int(round(inv_pp_total))},
    {"Concepto": "Inventario – Producto terminado", "Monto (₡)": int(round(inv_pt_total))},
    {"Concepto": "Total Inventarios", "Monto (₡)": int(round(inv_total))},
    {"Concepto": "Total Activo Circulante", "Monto (₡)": int(round(activo_circulante))},
    {"Concepto": "Activo Fijo Neto", "Monto (₡)": int(round(af_neto))},
    {"Concepto": "TOTAL ACTIVOS", "Monto (₡)": int(round(total_activos))},
])
st.dataframe(act_tab, use_container_width=True, hide_index=True)

# Pasivo y patrimonio
st.subheader("Pasivo y Patrimonio")
pas_tab = pd.DataFrame([
    {"Concepto": "CxP Proveedores", "Monto (₡)": int(round(cxp_total))},
    {"Concepto": "Anticipos de clientes", "Monto (₡)": int(round(anticip_total))},
    {"Concepto": "Deudas corto plazo", "Monto (₡)": int(round(deu_cp_total))},
    {"Concepto": "Total Pasivo Circulante", "Monto (₡)": int(round(pasivo_circulante))},
    {"Concepto": "Deudas largo plazo", "Monto (₡)": int(round(deu_lp_total))},
    {"Concepto": "Pasivo a largo plazo", "Monto (₡)": int(round(pasivo_largo))},
    {"Concepto": "TOTAL PASIVOS", "Monto (₡)": int(round(total_pasivos))},
    {"Concepto": "Patrimonio (Activos - Pasivos)", "Monto (₡)": int(round(patrimonio))},
    {"Concepto": "Capital de trabajo (AC - PC)", "Monto (₡)": int(round(capital_trabajo))},
])
st.dataframe(pas_tab, use_container_width=True, hide_index=True)

st.divider()

# ---------- Tabla de verificados ----------
st.subheader("🔎 Verificación del Balance")

verif_rows = [
    {"Concepto": "Caja y Bancos",
     "Total (₡)": int(round(caja_total)),
     "Verificado (₡)": int(round(caja_verif)),
     "% Verificado": _pct(caja_verif, caja_total)},
    {"Concepto": "Cuentas por Cobrar",
     "Total (₡)": int(round(cxc_total)),
     "Verificado (₡)": int(round(cxc_verif)),
     "% Verificado": _pct(cxc_verif, cxc_total)},
    {"Concepto": "Inventario MP",
     "Total (₡)": int(round(inv_mp_total)),
     "Verificado (₡)": int(round(inv_mp_verif)),
     "% Verificado": _pct(inv_mp_verif, inv_mp_total)},
    {"Concepto": "Inventario PP",
     "Total (₡)": int(round(inv_pp_total)),
     "Verificado (₡)": int(round(inv_pp_verif)),
     "% Verificado": _pct(inv_pp_verif, inv_pp_total)},
    {"Concepto": "Inventario PT",
     "Total (₡)": int(round(inv_pt_total)),
     "Verificado (₡)": int(round(inv_pt_verif)),
     "% Verificado": _pct(inv_pt_verif, inv_pt_total)},
    {"Concepto": "Total Inventarios",
     "Total (₡)": int(round(inv_total)),
     "Verificado (₡)": int(round(inv_verif)),
     "% Verificado": _pct(inv_verif, inv_total)},
    {"Concepto": "Activo Circulante",
     "Total (₡)": int(round(activo_circulante)),
     "Verificado (₡)": int(round(ac_verif)),
     "% Verificado": _pct(ac_verif, activo_circulante)},
    {"Concepto": "Activo Fijo Neto",
     "Total (₡)": int(round(af_neto)),
     "Verificado (₡)": int(round(af_verif)),
     "% Verificado": _pct(af_verif, af_neto)},
    {"Concepto": "TOTAL ACTIVOS",
     "Total (₡)": int(round(total_activos)),
     "Verificado (₡)": int(round(activos_verif)),
     "% Verificado": _pct(activos_verif, total_activos)},
    {"Concepto": "CxP Proveedores",
     "Total (₡)": int(round(cxp_total)),
     "Verificado (₡)": int(round(cxp_verif)),
     "% Verificado": _pct(cxp_verif, cxp_total)},
    {"Concepto": "Anticipos de clientes",
     "Total (₡)": int(round(anticip_total)),
     "Verificado (₡)": int(round(anticip_verif)),
     "% Verificado": _pct(anticip_verif, anticip_total)},
    {"Concepto": "Deudas corto plazo",
     "Total (₡)": int(round(deu_cp_total)),
     "Verificado (₡)": int(round(deu_cp_verif)),
     "% Verificado": _pct(deu_cp_verif, deu_cp_total)},
    {"Concepto": "Pasivo Circulante",
     "Total (₡)": int(round(pasivo_circulante)),
     "Verificado (₡)": int(round(pasivo_circulante_verif)),
     "% Verificado": _pct(pasivo_circulante_verif, pasivo_circulante)},
    {"Concepto": "Deudas largo plazo",
     "Total (₡)": int(round(deu_lp_total)),
     "Verificado (₡)": int(round(deu_lp_verif)),
     "% Verificado": _pct(deu_lp_verif, deu_lp_total)},
    {"Concepto": "Pasivo a largo plazo",
     "Total (₡)": int(round(pasivo_largo)),
     "Verificado (₡)": int(round(pasivo_largo_verif)),
     "% Verificado": _pct(pasivo_largo_verif, pasivo_largo)},
    {"Concepto": "TOTAL PASIVOS",
     "Total (₡)": int(round(total_pasivos)),
     "Verificado (₡)": int(round(pasivos_verif)),
     "% Verificado": _pct(pasivos_verif, total_pasivos)},
]

verif_df = pd.DataFrame(verif_rows)
st.dataframe(verif_df, use_container_width=True, hide_index=True)

colA, colB = st.columns(2)
with colA:
    st.metric("✅ % Verificado del ACTIVO", f"{_pct(activos_verif, total_activos)}%")
with colB:
    st.metric("✅ % Verificado del PASIVO", f"{_pct(pasivos_verif, total_pasivos)}%")

# (Opcional) guardar resumen en session_state["reporte"]
st.session_state.setdefault("reporte", {})
st.session_state["reporte"]["balance_general"] = {
    "activo": {
        "caja_bancos": int(round(caja_total)),
        "cxc_clientes": int(round(cxc_total)),
        "inventarios": {
            "materia_prima": int(round(inv_mp_total)),
            "producto_proceso": int(round(inv_pp_total)),
            "producto_terminado": int(round(inv_pt_total)),
            "total_inventarios": int(round(inv_total)),
        },
        "activo_circulante": int(round(activo_circulante)),
        "activo_fijo_neto": int(round(af_neto)),
        "total_activos": int(round(total_activos)),
        "verificados": {
            "ac_verificado": int(round(ac_verif)),
            "af_verificado": int(round(af_verif)),
            "activos_verificado_total": int(round(activos_verif)),
        }
    },
    "pasivo": {
        "cxp_proveedores": int(round(cxp_total)),
        "anticipos_clientes": int(round(anticip_total)),
        "deudas_corto_plazo": int(round(deu_cp_total)),
        "pasivo_circulante": int(round(pasivo_circulante)),
        "deudas_largo_plazo": int(round(deu_lp_total)),
        "pasivo_largo_plazo": int(round(pasivo_largo)),
        "total_pasivos": int(round(total_pasivos)),
        "verificados": {
            "pc_verificado": int(round(pasivo_circulante_verif)),
            "pl_verificado": int(round(pasivo_largo_verif)),
            "pasivos_verificado_total": int(round(pasivos_verif)),
        }
    },
    "patrimonio": int(round(patrimonio)),
    "capital_trabajo": int(round(capital_trabajo)),
}





















