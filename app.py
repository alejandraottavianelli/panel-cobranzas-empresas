import streamlit as st
import pandas as pd
from procesar_cobranzas import obtener_datos_orquestador, calcular_semaforo

st.set_page_config(page_title="Panel de Cobranzas Empresas", layout="wide")

st.title("📊 Conciliación & Ruta de Cobranzas - Cartera Empresas")

tab1, tab2, tab3, tab4 = st.tabs([
    "1. Cargar Archivos & Sincronización", 
    "2. Resumen Ejecutivo", 
    "3. Ruta de Cobranzas & CRM", 
    "4. Alertas & Cash Flow"
])

with tab1:
    st.subheader("Conexión con Orquestador API")
    if st.button("🔄 Sincronizar Datos en Vivo"):
        st.cache_data.clear()
        st.success("¡Datos actualizados desde el Orquestador!")

with tab3:
    st.subheader("Ruta de Cobranzas & Seguimiento con Semáforo")
    
    df = obtener_datos_orquestador()
    
    if not df.empty:
        df['Semáforo'] = df['last_update_date'].apply(calcular_semaforo)
        
        # Columnas de gestión CRM editables
        if 'Estado Contacto' not in df.columns:
            df['Estado Contacto'] = "Sin contactar"
        if 'Observación' not in df.columns:
            df['Observación'] = ""
        if 'Promesa de Pago' not in df.columns:
            df['Promesa de Pago'] = None

        edited_df = st.data_editor(
            df[['cliente', 'id_fiscal', 'comprobante', 'total', 'balance', 'Semáforo', 'Estado Contacto', 'Observación', 'Promesa de Pago']],
            column_config={
                "cliente": "Empresa",
                "id_fiscal": "CUIT",
                "comprobante": "Factura",
                "total": "Total Facturado",
                "balance": "Saldo Pendiente",
                "Semáforo": "Estado Pago",
                "Estado Contacto": st.column_config.SelectboxColumn(
                    "Estado Contacto",
                    options=["Sin contactar", "Se llamó", "Mail enviado", "Promesa de pago"],
                    required=True
                ),
                "Observación": st.column_config.TextColumn("Última Observación", width="large"),
                "Promesa de Pago": st.column_config.DateColumn("Fecha Promesa")
            },
            hide_index=True,
            use_container_width=True
        )

        st.download_button(
            label="💾 Exportar Copia de Seguridad con Anotaciones (Excel/CSV)",
            data=edited_df.to_csv(index=False).encode('utf-8'),
            file_name="Copia_Seguridad_Cobranzas.csv",
            mime="text/csv"
        )
    else:
        st.info("Hacé clic en Sincronizar o aguardá la carga de datos del Orquestador...")
