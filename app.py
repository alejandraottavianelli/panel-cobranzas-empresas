import streamlit as st
import pandas as pd
from procesar_cobranzas import obtener_datos_orquestador, calcular_semaforo

st.set_page_config(page_title="Panel de Cobranzas Empresas", layout="wide")

st.title("📊 Conciliación & Ruta de Cobranzas - Cartera Empresas")

@st.cache_data(ttl=300)
def cargar_datos():
    return obtener_datos_orquestador()

df = cargar_datos()

tab1, tab2, tab3, tab4 = st.tabs([
    "1. Cargar Archivos & Sincronización", 
    "2. Resumen Ejecutivo", 
    "3. Ruta de Cobranzas & CRM", 
    "4. Alertas & Cash Flow"
])

# --- PESTAÑA 1 ---
with tab1:
    st.subheader("Conexión con Orquestador API")
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("🔄 Sincronizar Datos en Vivo"):
            st.cache_data.clear()
            st.rerun()
    with col2:
        if not df.empty:
            st.success(f"¡Sincronización Exitosa! Facturas vivas cargadas: {len(df)}")
        else:
            st.warning("No se obtuvieron registros o la API está reconectando...")

# --- PESTAÑA 2: RESUMEN EJECUTIVO ---
with tab2:
    st.subheader("📈 Resumen Ejecutivo y Métricas Principales")
    if not df.empty:
        col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
        total_facturado = df['total'].sum() if 'total' in df.columns else 0
        total_deuda = df['balance'].sum() if 'balance' in df.columns else 0
        cant_empresas = df['cliente'].nunique() if 'cliente' in df.columns else 0

        col_kpi1.metric("Total Facturado", f"${total_facturado:,.2f}")
        col_kpi2.metric("Deuda Viva (Saldo Pendiente)", f"${total_deuda:,.2f}")
        col_kpi3.metric("Empresas Activas en Cartera", cant_empresas)

        st.markdown("---")
        st.subheader("Resumen por Cliente")
        if 'cliente' in df.columns and 'balance' in df.columns:
            resumen = df.groupby('cliente')[['total', 'balance']].sum().reset_index()
            st.dataframe(resumen, use_container_width=True)

# --- PESTAÑA 3: RUTA DE COBRANZAS & CRM ---
with tab3:
    st.subheader("📋 Ruta de Cobranzas & CRM con Semáforo de Pagos Reales")
    
    if not df.empty:
        df_crm = df.copy()
        
        # Calcular semáforo según la fecha del último cobro registrado en Interbanking
        df_crm['Semáforo'] = df_crm['fecha_ultimo_cobro'].apply(calcular_semaforo) if 'fecha_ultimo_cobro' in df_crm.columns else "🔴 +15 días"
        
        # Formatear la fecha visible de último cobro
        if 'fecha_ultimo_cobro' in df_crm.columns:
            df_crm['Último Cobro'] = pd.to_datetime(df_crm['fecha_ultimo_cobro']).dt.strftime('%Y-%m-%d').fillna('Sin registros')
        else:
            df_crm['Último Cobro'] = 'Sin registros'

        # Columnas CRM editables
        df_crm['Estado Contacto'] = "Sin contactar"
        df_crm['Observación'] = ""
        df_crm['Promesa de Pago'] = None

        columnas_mostrar = [c for c in ['cliente', 'id_fiscal', 'comprobante', 'total', 'balance', 'Último Cobro', 'Semáforo', 'Estado Contacto', 'Observación', 'Promesa de Pago'] if c in df_crm.columns]

        edited_df = st.data_editor(
            df_crm[columnas_mostrar],
            column_config={
                "cliente": "Empresa",
                "id_fiscal": "CUIT",
                "comprobante": "Factura",
                "total": "Total Facturado",
                "balance": "Saldo Pendiente",
                "Último Cobro": "Fecha Último Pago",
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
            label="💾 Exportar Copia de Seguridad con Anotaciones (CSV)",
            data=edited_df.to_csv(index=False).encode('utf-8'),
            file_name="Copia_Seguridad_Cobranzas.csv",
            mime="text/csv"
        )

# --- PESTAÑA 4: ALERTAS ---
with tab4:
    st.subheader("🔔 Alertas de Cobranza & Ranking de Deudores")
    if not df.empty and 'cliente' in df.columns and 'balance' in df.columns:
        top_deudores = df.groupby('cliente')['balance'].sum().reset_index().sort_values(by='balance', ascending=False).head(10)
        st.write("Top 10 Empresas con Mayor Saldo Pendiente:")
        st.bar_chart(top_deudores.set_index('cliente'))
