import streamlit as st
from utils.db import get_connection, load_visita   # 👈 usamos helpers de conexión
import datetime as dt
from zoneinfo import ZoneInfo

# =========================
# PASO 2 – Datos del cliente y del negocio
# =========================
st.set_page_config(page_title="Paso 2: Cliente y negocio", page_icon="👤")

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

# --------- UI ----------
init_paso2_state()
c = st.session_state.cliente
n = st.session_state.negocio

# =========================
# Inicializar mes_iso
# =========================
TZ = ZoneInfo("America/Costa_Rica")
if "mes_iso" not in st.session_state:
    now = dt.datetime.now(TZ)
    st.session_state["mes_iso"] = now.strftime("%Y-%m")

st.title("👤 Paso 2: Datos del cliente y del negocio")
st.caption("Complete los campos. Los marcados con * son obligatorios.")

with st.container():
    st.subheader("Datos del cliente")
    col1, col2 = st.columns([0.7, 0.3])
    with col1:
        c["nombre_completo"] = st.text_input(
            "Nombre completo *",
            value=c["nombre_completo"],
            placeholder="Ej.: Juan Carlos Rodríguez"
        )
        c["identificacion"] = st.text_input(
            "Número de identificación (cédula, DIMEX, pasaporte) *",
            value=c["identificacion"],
            placeholder="Ej.: 1-2345-0678"
        )
    with col2:
        if st.button("📂 Cargar datos", use_container_width=True) and c["identificacion"].strip():
            datos = load_visita(c["identificacion"].strip())
            if datos:
                st.success("✅ Datos cargados desde la base de datos")

                # Cliente
                c["nombre_completo"] = datos["cliente_nombre"]
                n["nombre_comercial"] = datos["nombre_comercial"]
                n["persona_juridica"] = bool(datos["persona_juridica"])
                n["ubicacion"] = datos["ubicacion"]
                n["sector_economico"] = datos["sector_economico"]
                n["actividad_principal"] = datos["actividad_principal"]
                n["patente_municipal"] = bool(datos["patente_municipal"])
                n["registros_contables"] = bool(datos["registros_contables"])
                n["tipo_local"] = datos["tipo_local"]
                n["antiguedad_anios"] = datos["antiguedad_anios"]
                n["antiguedad_meses"] = datos["antiguedad_meses"]

                # Asesor
                asesor = st.session_state.get("asesor", {})
                asesor["nombre"] = datos["asesor_nombre"]
                asesor["fecha_hora"] = datos["fecha_hora"]
                asesor["timestamp_source"] = datos["hora_fuente"]
                asesor["lat"] = datos["lat"]
                asesor["lon"] = datos["lon"]
                asesor["maps_url"] = datos["maps_url"]

                st.session_state["asesor"] = asesor
            else:
                st.warning("⚠️ No se encontraron datos para esta cédula")



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
        st.switch_page("pages/01_Asesor.py")

with colNav2:
    if st.button("Siguiente ➡️", key="next_step_2", disabled=not obligatorios_ok, use_container_width=True):
        asesor = st.session_state.get("asesor", {})

        # 👇 Asegurar que fecha_hora siempre tenga valor
        if not asesor.get("fecha_hora"):
            asesor["fecha_hora"] = dt.datetime.now(TZ)

        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Verificar si ya existe registro
            cursor.execute("SELECT COUNT(*) FROM visitas_credito WHERE cliente_identificacion = ?", (c["identificacion"].strip(),))
            existe = cursor.fetchone()[0]

            if existe:
                # UPDATE
                cursor.execute("""
                    UPDATE visitas_credito SET
                        cliente_nombre=?, nombre_comercial=?, persona_juridica=?,
                        ubicacion=?, sector_economico=?, actividad_principal=?,
                        patente_municipal=?, registros_contables=?, tipo_local=?,
                        antiguedad_anios=?, antiguedad_meses=?,
                        asesor_nombre=?, fecha_hora=?, hora_fuente=?, lat=?, lon=?, maps_url=?,
                        mes_iso=?
                    WHERE cliente_identificacion=?
                """, (
                    c["nombre_completo"].strip(),
                    n["nombre_comercial"].strip(),
                    1 if n["persona_juridica"] else 0,
                    n["ubicacion"].strip(),
                    n["sector_economico"],
                    n["actividad_principal"].strip(),
                    1 if n["patente_municipal"] else 0,
                    1 if n["registros_contables"] else 0,
                    n["tipo_local"],
                    int(n["antiguedad_anios"]),
                    int(n["antiguedad_meses"]),
                    asesor.get("nombre", "N/A"),
                    asesor.get("fecha_hora"),
                    asesor.get("timestamp_source", "N/A"),
                    asesor.get("lat"),
                    asesor.get("lon"),
                    asesor.get("maps_url", "N/A"),
                    st.session_state["mes_iso"],
                    c["identificacion"].strip()
                ))
                mensaje = "♻️ Datos ACTUALIZADOS en Azure SQL"
            else:
                # INSERT
                cursor.execute("""
                    INSERT INTO visitas_credito (
                        cliente_identificacion, cliente_nombre, nombre_comercial,
                        persona_juridica, ubicacion, sector_economico, actividad_principal,
                        patente_municipal, registros_contables, tipo_local,
                        antiguedad_anios, antiguedad_meses,
                        asesor_nombre, fecha_hora, hora_fuente, lat, lon, maps_url,
                        mes_iso
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    c["identificacion"].strip(),
                    c["nombre_completo"].strip(),
                    n["nombre_comercial"].strip(),
                    1 if n["persona_juridica"] else 0,
                    n["ubicacion"].strip(),
                    n["sector_economico"],
                    n["actividad_principal"].strip(),
                    1 if n["patente_municipal"] else 0,
                    1 if n["registros_contables"] else 0,
                    n["tipo_local"],
                    int(n["antiguedad_anios"]),
                    int(n["antiguedad_meses"]),
                    asesor.get("nombre", "N/A"),
                    asesor.get("fecha_hora"),
                    asesor.get("timestamp_source", "N/A"),
                    asesor.get("lat"),
                    asesor.get("lon"),
                    asesor.get("maps_url", "N/A"),
                    st.session_state["mes_iso"]
                ))
                mensaje = "🆕 Datos INSERTADOS en Azure SQL"

            conn.commit()
            conn.close()

            st.success(mensaje)
            st.session_state["done_02"] = True

            # 🔀 Navegar automáticamente al Paso 3
            try:
                st.switch_page("pages/03_Ventas_top_down.py")
                st.stop()
            except Exception:
                st.info("✅ Datos guardados. Continúa con el Paso 3A desde el menú lateral.")
                st.stop()

        except Exception as e:
            st.error(f"❌ Error al guardar en la base de datos: {e}")


