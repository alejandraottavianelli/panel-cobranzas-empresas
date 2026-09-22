import pandas as pd
import datetime

def buscar_columna(df, posibles_nombres):
    """Busca una columna en el DataFrame ignorando mayúsculas, minúsculas y espacios."""
    cols_lower = {str(col).strip().lower(): col for col in df.columns}
    for nombre in posibles_nombres:
        n_clean = nombre.strip().lower()
        if n_clean in cols_lower:
            return cols_lower[n_clean]
    return None

def procesar_panel_cobranzas(file_facturas, file_cobranzas, file_limite, df_contactos=None):
    df_facturas = pd.read_excel(file_facturas)
    df_cobranzas = pd.read_excel(file_cobranzas)
    df_limite = pd.read_excel(file_limite)
    
    # 1. Normalizar columna 'Cliente' / 'Organización'
    for df in [df_facturas, df_cobranzas, df_limite]:
        col_cliente = buscar_columna(df, ['Cliente', 'Organización', 'Organizacion', 'Cuenta corriente', 'Razon Social'])
        if col_cliente:
            df.rename(columns={col_cliente: 'Cliente'}, inplace=True)

    # 2. Identificar columnas clave en Facturas
    col_venc = buscar_columna(df_facturas, ['Vencimiento', 'Fecha vencimiento', 'Fecha de vencimiento', 'F.Vencimiento'])
    col_saldo = buscar_columna(df_facturas, ['Saldo', 'Saldo pendiente', 'Importe saldo', 'Total', 'Importe total'])
    col_numero = buscar_columna(df_facturas, ['Número', 'Numero', 'Nro', 'Comprobante'])

    # Convertir fechas y saldos numéricos
    if col_venc:
        df_facturas['Vencimiento'] = pd.to_datetime(df_facturas[col_venc], errors='coerce')
    else:
        df_facturas['Vencimiento'] = pd.NaT

    if col_saldo:
        # Limpieza de valores numéricos si vienen como texto
        df_facturas['Saldo'] = df_facturas[col_saldo].astype(str).str.replace('$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        df_facturas['Saldo'] = pd.to_numeric(df_facturas['Saldo'], errors='coerce').fillna(0)
    else:
        df_facturas['Saldo'] = 0

    df_facturas['Número'] = df_facturas[col_numero] if col_numero else 1

    # 3. Identificar columnas en Cobranzas
    col_fecha_cob = buscar_columna(df_cobranzas, ['Fecha', 'Fecha cobranza', 'Fecha de pago'])
    col_total_cob = buscar_columna(df_cobranzas, ['Total', 'Importe', 'Monto'])

    if col_fecha_cob:
        df_cobranzas['Fecha'] = pd.to_datetime(df_cobranzas[col_fecha_cob], errors='coerce')
    else:
        df_cobranzas['Fecha'] = pd.NaT

    if col_total_cob:
        df_cobranzas['Total'] = df_cobranzas[col_total_cob].astype(str).str.replace('$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        df_cobranzas['Total'] = pd.to_numeric(df_cobranzas['Total'], errors='coerce').fillna(0)
    else:
        df_cobranzas['Total'] = 0

    hoy = pd.to_datetime(datetime.date.today())
    
    # 4. Agrupación por Cliente
    # Si hay saldos mayores a 0, toma esos; si no, procesa todas las facturas del archivo
    df_pendientes = df_facturas[df_facturas['Saldo'] > 0] if (df_facturas['Saldo'] > 0).any() else df_facturas
    
    resumen_facturas = df_pendientes.groupby('Cliente').agg(
        Deuda_Total=('Saldo', 'sum'),
        Facturas_Pendientes=('Número', 'count')
    ).reset_index()
    
    # Deuda Vencida
    df_vencidas = df_pendientes[df_pendientes['Vencimiento'] < hoy]
    if not df_vencidas.empty:
        resumen_vencidas = df_vencidas.groupby('Cliente').agg(
            Deuda_Vencida=('Saldo', 'sum')
        ).reset_index()
    else:
        resumen_vencidas = pd.DataFrame(columns=['Cliente', 'Deuda_Vencida'])
    
    # 5. Último Pago
    if not df_cobranzas.empty and 'Fecha' in df_cobranzas.columns:
        df_cobranzas_ord = df_cobranzas.sort_values(by=['Cliente', 'Fecha'], ascending=[True, False])
        ultimo_pago = df_cobranzas_ord.groupby('Cliente').first().reset_index()
        ultimo_pago = ultimo_pago[['Cliente', 'Fecha', 'Total']].rename(
            columns={'Fecha': 'Fecha_Ultimo_Pago', 'Total': 'Monto_Ultimo_Pago'}
        )
        ultimo_pago['Fecha_Ultimo_Pago'] = ultimo_pago['Fecha_Ultimo_Pago'].dt.strftime('%Y-%m-%d')
    else:
        ultimo_pago = pd.DataFrame(columns=['Cliente', 'Fecha_Ultimo_Pago', 'Monto_Ultimo_Pago'])
    
    # 6. Condición de Venta y Límite
    cols_limite = [c for c in ['Condición de venta', 'Límite de crédito'] if c in df_limite.columns]
    resumen_limite = df_limite[['Cliente'] + cols_limite].drop_duplicates('Cliente') if cols_limite else pd.DataFrame(columns=['Cliente'])
    
    # 7. Consolidar
    consolidado = pd.merge(resumen_facturas, resumen_vencidas, on='Cliente', how='left')
    consolidado['Deuda_Vencida'] = consolidado['Deuda_Vencida'].fillna(0)
    consolidado = pd.merge(consolidado, ultimo_pago, on='Cliente', how='left')
    consolidado = pd.merge(consolidado, resumen_limite, on='Cliente', how='left')
    
    def calcular_semaforo(row):
        if row['Deuda_Vencida'] > 0:
            return '🔴 Vencido'
        elif row['Deuda_Total'] > 0:
            return '🟡 En Seguimiento'
        else:
            return '🟢 Al Día'
            
    consolidado['Estado'] = consolidado.apply(calcular_semaforo, axis=1)
    
    if df_contactos is not None and not df_contactos.empty:
        consolidado = pd.merge(consolidado, df_contactos, on='Cliente', how='left')
        
    return consolidado
