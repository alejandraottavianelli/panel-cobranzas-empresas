import streamlit as st
import pandas as pd
import io
from procesar_cobranzas import obtener_datos_orquestador, calcular_semaforo

st.set_page_config(page_title="Panel de Cobranzas Empresas", layout="wide")

st.title("📊 Control & Seguimiento Semanal de Cobranzas Corporativas")

@st.cache_data(ttl=300)
def cargar_datos():
    return obtener_datos_orquestador()

df = cargar_datos()

# Nueva estructura de pestañas focalizada
tab1, tab2, tab3, tab4 = st.tabs([
    "1. Sincronización Automática API", 
    "2. Resumen Ejecutivo Matriz", 
    "3. Seguimiento Semanal & Alertas", 
    "4. Alertas & Ranking Cash Flow"
])

# --- PESTAÑA 1: SINCRONIZACIÓN ---
with tab1:
    st.subheader("Sincronización en Tiempo Real (Orquestador & Interbanking)")
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("🔄 Sincronizar Datos Ahora"):
            st.cache_data.clear()
            st.rerun()
    with col2:
        if not df.empty:
            st.success(f"¡Conexión Exitosa! Registros vivos procesados para las 58 empresas: {len(df)}")
        else:
            st.warning("Conectando con la API del Orquestador...")

# --- PESTAÑA 2: RESUMEN EJECUTIVO ---
with tab2:
    st.subheader("📈 Resumen Ejecutivo - Cartera Empresas Matriz")
    if not df.empty:
        col1, col2, col3 = st.columns(3)
        total_facturado = df['total'].sum() if 'total' in df.columns else 0
        total_deuda = df['balance'].sum() if 'balance' in df.columns else 0
        empresas_unicas = df['cliente'].nunique() if 'cliente' in df.columns else 0

        col1.metric("Total Facturado", f"${total_facturado:,.2f}")
        col2.metric("Deuda Viva (Saldo Pendiente)", f"${total_deuda:,.2f}")
        col3.metric("Empresas Filtradas", empresas_unicas)

        st.markdown("---")
        st.subheader("Consolidado por Empresa")
        if 'cliente' in df.columns and 'balance' in df.columns:
            resumen = df.groupby('cliente')[['total', 'balance']].sum().reset_index()
            st.dataframe(resumen, use_container_width=True)

# --- PESTAÑA 3: SEGUIMIENTO SEMANAL & ALERTAS ---
with tab3:
    st.subheader("📅 Seguimiento Semanal de Cobranzas & Matriz de Alertas")
    
    if not df.empty:
        df_semanal = df.copy()
        
        # Calcular Alerta Semanal
        df_semanal['Alerta Semanal'] = df_semanal['fecha_ultimo_cobro'].apply(calcular_semaforo) if 'fecha_ultimo_cobro' in df_semanal.columns else "🔴 +15 días"
        
        if 'fecha_ultimo_cobro' in df_semanal.columns:
            df_semanal['Fecha Último Cobro'] = pd.to_datetime(df_semanal['fecha_ultimo_cobro']).dt.strftime('%Y-%m-%d').fillna('Sin pagos recientes')
        else:
            df_semanal['Fecha Último Cobro'] = 'Sin pagos recientes'

        # Columnas editables para la gestión de los chicos
        df_semanal['Estado Gestión'] = "Sin contactar"
        df_semanal['Observación Semanal'] = ""
        df_semanal['Promesa de Pago'] = None

        cols_mostrar = [c for c in ['cliente', 'id_fiscal', 'comprobante', 'total', 'balance', 'Fecha Último Cobro', 'Alerta Semanal', 'Estado Gestión', 'Observación Semanal', 'Promesa de Pago'] if c in df_semanal.columns]

        edited_df = st.data_editor(
            df_semanal[cols_mostrar],
            column_config={
                "cliente": "Empresa Matriz",
                "id_fiscal": "CUIT",
                "comprobante": "Comprobante",
                "total": "Facturado ($)",
                "balance": "Saldo Pendiente ($)",
                "Fecha Último Cobro": "Último Pago Registrado",
                "Alerta Semanal": "Alerta Cobro",
                "Estado Gestión": st.column_config.SelectboxColumn(
                    "Estado Contacto",
                    options=["Sin contactar", "Se llamó", "Mail enviado", "Promesa de pago", "En conflicto"],
                    required=True
                ),
                "Observación Semanal": st.column_config.TextColumn("Seguimiento / Notas", width="large"),
                "Promesa de Pago": st.column_config.DateColumn("Fecha Compromiso")
            },
            hide_index=True,
            use_container_width=True
        )

        # Botón para descargar reporte en Excel nativo (.xlsx)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            edited_df.to_excel(writer, sheet_name='Seguimiento Semanal Matriz', index=False)
        buffer.seek(0)

        st.download_button(
            label="📊 Exportar Reporte Semanal (Excel .xlsx)",
            data=buffer,
            file_name="Seguimiento_Semanal_Cobranzas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# --- PESTAÑA 4: ALERTAS & CASH FLOW ---
with tab4:
    st.subheader("🔔 Ranking de Deudores & Alertas de Cash Flow")
    if not df.empty and 'cliente' in df.columns and 'balance' in df.columns:
        top_deudores = df.groupby('cliente')['balance'].sum().reset_index().sort_values(by='balance', ascending=False).head(10)
        st.write("Top 10 Empresas con Mayor Saldo Pendiente:")
        st.bar_chart(top_deudores.set_index('cliente'))
