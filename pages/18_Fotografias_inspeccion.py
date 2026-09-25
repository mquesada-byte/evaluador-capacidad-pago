import streamlit as st
from utils.db import get_connection
from PIL import Image
import io
import os
import pandas as pd

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="Paso 18: Fotografías de inspección",
    page_icon="📸",
)

st.title("📸 Paso 18: Fotografías de inspección")

# =========================
# CLIENTE
# =========================
cliente = st.session_state.get("cliente", {})

nombre_cliente = cliente.get("nombre_completo", "").strip()
identificacion_mostrar = cliente.get("identificacion", "").strip()

identificacion = (
    cliente.get("identificacion", "")
    .replace("-", "")
    .replace(" ", "")
    .strip()
)

if not identificacion:
    st.warning("⚠️ Primero complete el Paso 2.")
    st.stop()

asesor = st.session_state.get("asesor", {})
usuario_carga = asesor.get("nombre", "N/A")

st.info(f"""
Cliente: {nombre_cliente}

Identificación: {identificacion_mostrar}

Usuario: {usuario_carga}
""")

# =========================
# HELPERS
# =========================
def comprimir_imagen(uploaded_file, max_width=1600, quality=80):

    image = Image.open(uploaded_file)

    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")

    width, height = image.size

    if width > max_width:
        new_height = int((max_width / width) * height)
        image = image.resize((max_width, new_height))

    buffer = io.BytesIO()

    image.save(
        buffer,
        format="JPEG",
        quality=quality,
        optimize=True
    )

    return buffer.getvalue()


def guardar_foto(
    cliente_identificacion,
    tipo_foto,
    nombre_archivo,
    extension,
    peso_kb,
    archivo_bytes,
    usuario_carga,
    observaciones
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO dbo.FotosInspeccionCredito (
            ClienteIdentificacion,
            TipoFoto,
            NombreArchivo,
            ExtensionArchivo,
            PesoArchivoKB,
            ArchivoFoto,
            UsuarioCarga,
            Observaciones,
            Activo
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
    """, (
        cliente_identificacion,
        tipo_foto,
        nombre_archivo,
        extension,
        peso_kb,
        archivo_bytes,
        usuario_carga,
        observaciones
    ))

    conn.commit()
    conn.close()


def obtener_fotos(cliente_identificacion):

    conn = get_connection()

    query = """
        SELECT
            IdFoto,
            TipoFoto,
            NombreArchivo,
            PesoArchivoKB,
            ArchivoFoto,
            FechaCarga,
            UsuarioCarga,
            Observaciones
        FROM dbo.FotosInspeccionCredito
        WHERE ClienteIdentificacion = ?
          AND Activo = 1
        ORDER BY FechaCarga DESC
    """

    df = pd.read_sql(
        query,
        conn,
        params=[cliente_identificacion]
    )

    conn.close()

    return df


def eliminar_foto(id_foto):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE dbo.FotosInspeccionCredito
        SET Activo = 0
        WHERE IdFoto = ?
    """, (id_foto,))

    conn.commit()
    conn.close()


# =========================
# TIPOS FOTO
# =========================
tipos_foto = [
    ("clienta_negocio", "Clienta en el negocio"),
    ("inventario", "Inventario"),
    ("registros", "Registros contables"),
    ("patente_municipal", "Patente municipal"),
    ("formacion_acreditada", "Títulos, certificados y capacitaciones"),
    ("fachada", "Fachada de la vivienda donde reside"),
    ("local_negocio", "Foto del local (si aplica)"),
    ("trabajando", "Clienta trabajando"),
    ("herramientas", "Mobiliario y equipo")
]

# =========================
# CARGA
# =========================
st.subheader("📤 Cargar fotografías")

for codigo, descripcion in tipos_foto:

    with st.expander(descripcion, expanded=False):

        archivo = st.file_uploader(
            f"Seleccione fotografía: {descripcion}",
            type=["jpg", "jpeg", "png"],
            key=f"file_{codigo}"
        )

        observaciones = st.text_area(
            "Observaciones",
            key=f"obs_{codigo}"
        )

        if archivo is not None:

            try:

                bytes_imagen = comprimir_imagen(archivo)

                peso_kb = round(len(bytes_imagen) / 1024, 2)

                st.image(
                    bytes_imagen,
                    width=350
                )

                st.caption(f"Peso: {peso_kb} KB")

                if st.button(
                    f"💾 Guardar {descripcion}",
                    key=f"save_{codigo}"
                ):

                    nombre_original = archivo.name

                    extension = (
                        os.path.splitext(nombre_original)[1]
                        .replace(".", "")
                        .lower()
                    )

                    guardar_foto(
                        cliente_identificacion=identificacion,
                        tipo_foto=codigo,
                        nombre_archivo=nombre_original,
                        extension=extension,
                        peso_kb=peso_kb,
                        archivo_bytes=bytes_imagen,
                        usuario_carga=usuario_carga,
                        observaciones=observaciones.strip()
                    )

                    st.success("✅ Fotografía guardada")
                    st.rerun()

            except Exception as e:
                st.error(f"❌ Error: {e}")

st.divider()

# =========================
# GALERÍA
# =========================
st.subheader("🖼️ Fotografías cargadas")

df_fotos = obtener_fotos(identificacion)

if df_fotos.empty:

    st.warning("No hay fotografías cargadas.")

else:

    for _, row in df_fotos.iterrows():
        foto_id = int(row["IdFoto"])
        foto_bytes = bytes(row["ArchivoFoto"])

        col1, col2, col3 = st.columns([0.25, 0.55, 0.20])

        with col1:

            st.image(
                foto_bytes,
                width=220
            )

        with col2:

            st.markdown(f"**Tipo:** {row['TipoFoto']}")
            st.markdown(f"**Archivo:** {row['NombreArchivo']}")
            st.markdown(f"**Peso:** {row['PesoArchivoKB']} KB")
            st.markdown(f"**Fecha:** {row['FechaCarga']}")
            st.markdown(f"**Usuario:** {row['UsuarioCarga']}")

            if row["Observaciones"]:
                st.markdown(f"**Obs:** {row['Observaciones']}")

        with col3:

            if st.button(
                "👁️ Ver",
                key=f"ver_foto_{foto_id}",
                use_container_width=True
            ):
                if st.session_state.get("foto_ampliada") == foto_id:
                    st.session_state.pop("foto_ampliada", None)
                else:
                    st.session_state["foto_ampliada"] = foto_id

            st.download_button(
                "⬇️ Descargar",
                data=foto_bytes,
                file_name=row["NombreArchivo"],
                mime="image/jpeg",
                key=f"descargar_foto_{foto_id}",
                use_container_width=True
            )

            if st.button(
                "🗑️ Eliminar",
                key=f"eliminar_foto_{foto_id}",
                use_container_width=True
            ):
                st.session_state["confirmar_eliminar_foto"] = foto_id

                if st.session_state.get("foto_ampliada") == foto_id:
                    st.image(
                        foto_bytes,
                        caption=row["NombreArchivo"],
                        use_container_width=True
            )

        if st.session_state.get("confirmar_eliminar_foto") == foto_id:
            st.warning(
                f"¿Eliminar la fotografía {row['NombreArchivo']}?"
            )

            col_confirmar, col_cancelar = st.columns(2)

            with col_confirmar:
                if st.button(
                    "Sí, eliminar",
                    key=f"confirmar_foto_{foto_id}",
                    use_container_width=True
                ):
                    eliminar_foto(foto_id)

                    st.session_state.pop(
                        "confirmar_eliminar_foto",
                        None
                    )

                    if st.session_state.get("foto_ampliada") == foto_id:
                        st.session_state.pop("foto_ampliada", None)

                    st.rerun()

            with col_cancelar:
                if st.button(
                    "Cancelar",
                    key=f"cancelar_foto_{foto_id}",
                    use_container_width=True
                ):
                    st.session_state.pop(
                        "confirmar_eliminar_foto",
                        None
                    )
                    st.rerun()
        
        st.divider()

# ============================================================
# NAVEGACIÓN — PASO 18
# ============================================================

st.divider()

col_volver, col_continuar = st.columns(2)

with col_volver:
    if st.button(
        "⬅️ Volver a 17 – Estados de cuenta",
        use_container_width=True
    ):
        st.switch_page("pages/17_Estados_cuenta.py")

with col_continuar:
    if st.button(
        "Continuar a 19 – Hechos relevantes ➡️",
        type="primary",
        use_container_width=True
    ):
        st.session_state["done_18"] = True
        st.switch_page("pages/19_Hechos_relevantes.py")
