# ==========================================
# Página 17 — Estados de cuenta financieros
# ==========================================

import streamlit as st
import pyodbc
import fitz

st.set_page_config(
    page_title="Paso 17: Estados de cuenta bancarios",
    page_icon="🏦"
)

st.title("🏦 Paso 17 — Estados de cuenta bancarios")

# ==============================
# FUNCIÓN CONEXIÓN SQL
# ==============================

def get_connection():
    return pyodbc.connect(
        f"DRIVER={{{st.secrets['azure_sql']['driver']}}};"
        f"SERVER={st.secrets['azure_sql']['server']};"
        f"DATABASE={st.secrets['azure_sql']['database']};"
        f"UID={st.secrets['azure_sql']['username']};"
        f"PWD={st.secrets['azure_sql']['password']};"
        "TrustServerCertificate=yes;"
    )

# ==============================
# 1️⃣ DETECTAR ASESOR
# ==============================

usuario = (
    st.session_state.get("asesor", {}).get("nombre")
    or "Aplicacion"
)

# ==============================
# 2️⃣ IDENTIFICACIÓN CLIENTE
# ==============================

cliente_id = st.session_state.get("cliente", {}).get("identificacion")
if not cliente_id:
    st.warning("Cargá un cliente antes de gestionar sus estados de cuenta.")
    st.stop()

# ==============================
# 3️⃣ CARGA ESTADOS DE CUENTA
# ==============================

st.subheader("Carga de estados de cuenta")

tipo_documento = st.selectbox(
    "Tipo de estado",
    ["BANCARIO", "TARJETA"]
)

uploaded_file = st.file_uploader(
    "Subir estado de cuenta PDF",
    type=["pdf"]
)

if st.button("Guardar estado de cuenta"):

    if not cliente_id or uploaded_file is None:
        st.error("Complete los datos requeridos")
        st.stop()

    try:

        file_bytes = uploaded_file.read()
        file_name = uploaded_file.name

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO DocumentosFinancierosCliente
            (CedulaCliente, TipoDocumento, NombreArchivo,
             ArchivoPDF, UsuarioCarga, Asesor)
            VALUES (?,?,?,?,?,?)
        """,
        cliente_id,
        tipo_documento,
        file_name,
        file_bytes,
        usuario,
        usuario
        )

        conn.commit()
        conn.close()

        st.success("Estado de cuenta guardado correctamente")
        st.rerun()

    except Exception as e:
        st.error(f"Error al guardar: {e}")

# ==============================
# 4️⃣ LISTADO + VER + DESCARGAR + ELIMINAR
# ==============================

if cliente_id:

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT IdDocumento, TipoDocumento,
                   NombreArchivo, ArchivoPDF, FechaCarga, UsuarioCarga
            FROM DocumentosFinancierosCliente
            WHERE CedulaCliente = ?
              AND Activo = 1
            ORDER BY FechaCarga DESC
        """, cliente_id)

        rows = cursor.fetchall()
        conn.close()

        if rows:

            st.subheader("📂 Estados de cuenta cargados")

            for r in rows:
                doc_id = int(r.IdDocumento)
                pdf_bytes = bytes(r.ArchivoPDF)
                documento_actual = (cliente_id, doc_id)

                col1, col2, col3, col4 = st.columns(
                    [5, 1.4, 1.7, 1.7]
                )

                col1.markdown(
                    f"**{r.TipoDocumento}**  \n"
                    f"Archivo: {r.NombreArchivo}  \n"
                    f"Fecha: {r.FechaCarga}"
                )

                # 👁️ VER
                if col2.button(
                    "👁️ Ver",
                    key=f"ver_estado_{doc_id}",
                    use_container_width=True,
                ):
                    if (
                        st.session_state.get("estado_pdf_abierto")
                        == documento_actual
                    ):
                        st.session_state.pop(
                            "estado_pdf_abierto",
                            None,
                        )
                    else:
                        st.session_state["estado_pdf_abierto"] = (
                            documento_actual
                        )

                # ⬇️ DESCARGAR
                col3.download_button(
                    "⬇️ Descargar",
                    data=pdf_bytes,
                    file_name=r.NombreArchivo,
                    mime="application/pdf",
                    key=f"descargar_estado_{doc_id}",
                    use_container_width=True,
                )

                # 🗑️ ELIMINAR
                if col4.button(
                    "🗑️ Eliminar",
                    key=f"eliminar_estado_{doc_id}",
                    use_container_width=True,
                ):
                    st.session_state["estado_confirmar_eliminar"] = documento_actual

                if st.session_state.get("estado_confirmar_eliminar") == documento_actual:
                    st.warning(
                        f"¿Eliminar el estado {r.TipoDocumento}: {r.NombreArchivo}?"
                    )

                    col_confirmar, col_cancelar = st.columns(2)

                    with col_confirmar:
                        if st.button(
                            "Sí, eliminar",
                            key=f"confirmar_estado_{doc_id}",
                            use_container_width=True,
                        ):
                            conn = get_connection()
                            cursor = conn.cursor()
                            cursor.execute("""
                                UPDATE DocumentosFinancierosCliente
                                SET Activo = 0
                                WHERE IdDocumento = ?
                                  AND CedulaCliente = ?
                            """, doc_id, cliente_id)
                            conn.commit()
                            conn.close()

                            st.session_state.pop(
                                "estado_confirmar_eliminar",
                                None,
                            )

                            if (
                                st.session_state.get("estado_pdf_abierto")
                                == documento_actual
                            ):
                                st.session_state.pop(
                                    "estado_pdf_abierto",
                                    None,
                                )

                            st.rerun()

                    with col_cancelar:
                        if st.button(
                            "Cancelar",
                            key=f"cancelar_estado_{doc_id}",
                            use_container_width=True,
                        ):
                            st.session_state.pop(
                                "estado_confirmar_eliminar",
                                None,
                            )
                            st.rerun()

                # 👁️ VISUALIZACIÓN DEL PDF
                if st.session_state.get("estado_pdf_abierto") == documento_actual:
                    try:
                        with fitz.open(
                            stream=pdf_bytes,
                            filetype="pdf",
                        ) as pdf:
                            total_paginas = len(pdf)
                            clave_pagina = (
                                f"pagina_estado_{cliente_id}_{doc_id}"
                            )

                            st.session_state.setdefault(clave_pagina, 1)

                            pagina = min(
                                max(
                                    st.session_state[clave_pagina],
                                    1,
                                ),
                                total_paginas,
                            )

                            col_anterior, col_numero, col_siguiente = st.columns(
                                [1, 2, 1]
                            )

                            with col_anterior:
                                if st.button(
                                    "⬅️ Anterior",
                                    key=f"anterior_estado_{doc_id}",
                                    disabled=pagina <= 1,
                                    use_container_width=True,
                                ):
                                    pagina -= 1
                                    st.session_state[clave_pagina] = pagina

                            with col_numero:
                                st.markdown(
                                    f"<p style='text-align:center'>"
                                    f"Página {pagina} de {total_paginas}"
                                    f"</p>",
                                    unsafe_allow_html=True,
                                )

                            with col_siguiente:
                                if st.button(
                                    "Siguiente ➡️",
                                    key=f"siguiente_estado_{doc_id}",
                                    disabled=pagina >= total_paginas,
                                    use_container_width=True,
                                ):
                                    pagina += 1
                                    st.session_state[clave_pagina] = pagina

                            imagen = pdf[pagina - 1].get_pixmap(
                                matrix=fitz.Matrix(1.5, 1.5)
                            ).tobytes("png")

                            st.image(
                                imagen,
                                use_container_width=True,
                            )

                    except Exception as e:
                        st.error(f"No se pudo mostrar el PDF: {e}")

        else:
            st.info("Este cliente no tiene estados de cuenta cargados.")

    except Exception as e:
        st.error(e)

