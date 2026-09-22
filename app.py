import streamlit as st
import pandas as pd
from procesar_cobranzas import procesar_panel_cobranzas

st.set_page_config(page_title="Panel de Cobranzas", layout="wide")

st.title("📊 Panel de Cobranzas y Cuentas Corrientes - Empresas")

# Módulo de Carga de Archivos desde la pantalla web
st.sidebar.header("📁 Cargar Datos de Finnegans")
f_facturas = st.sidebar.file_uploader("Facturas empresas.xlsx", type=["xlsx"])
f_cobranzas = st.sidebar.file_uploader("Cobranzas empresas.xlsx", type=["xlsx"])
f_limite = st.sidebar.file_uploader("Limite de Credito.xlsx", type=["xlsx"])

if f_facturas and f_cobranzas and f_limite:
    df = procesar_panel_cobranzas(f_facturas, f_cobranzas, f_limite)

    # Tarjetas KPI
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Deuda Total Pendiente", f"${df['Deuda_Total'].sum():,.2f}")
    col2.metric("Deuda Vencida", f"${df['Deuda_Vencida'].sum():,.2f}")
    col3.metric("Facturas Pendientes", int(df['Facturas_Pendientes'].sum()))
    col4.metric("Empresas en Cartera", len(df))

    st.markdown("---")

    # Tabla interactiva
    st.subheader("📋 Estado de Cuentas por Empresa")
    st.dataframe(df, use_container_width=True)

else:
    st.info("👈 Por favor, carga los 3 archivos de Finnegans en el menú lateral para ver el panel.")
