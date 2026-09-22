import pandas as pd
import datetime

def procesar_panel_cobranzas(file_facturas, file_cobranzas, file_limite, df_contactos=None):
    df_facturas = pd.read_excel(file_facturas)
    df_cobranzas = pd.read_excel(file_cobranzas)
    df_limite = pd.read_excel(file_limite)
    
    for df in [df_facturas, df_cobranzas, df_limite]:
        if 'Organización' in df.columns and 'Cliente' not in df.columns:
            df.rename(columns={'Organización': 'Cliente'}, inplace=True)
            
    df_facturas['Vencimiento'] = pd.to_datetime(df_facturas['Vencimiento'], errors='coerce')
    df_cobranzas['Fecha'] = pd.to_datetime(df_cobranzas['Fecha'], errors='coerce')
    
    hoy = pd.to_datetime(datetime.date.today())
    
    # Pendientes
    df_pendientes = df_facturas[df_facturas['Saldo'] > 0]
    resumen_facturas = df_pendientes.groupby('Cliente').agg(
        Deuda_Total=('Saldo', 'sum'),
        Facturas_Pendientes=('Número', 'count')
    ).reset_index()
    
    # Vencidas
    df_vencidas = df_pendientes[df_pendientes['Vencimiento'] < hoy]
    resumen_vencidas = df_vencidas.groupby('Cliente').agg(
        Deuda_Vencida=('Saldo', 'sum')
    ).reset_index()
    
    # Último Pago
    df_cobranzas_ord = df_cobranzas.sort_values(by=['Cliente', 'Fecha'], ascending=[True, False])
    ultimo_pago = df_cobranzas_ord.groupby('Cliente').first().reset_index()
    ultimo_pago = ultimo_pago[['Cliente', 'Fecha', 'Total']].rename(
        columns={'Fecha': 'Fecha_Ultimo_Pago', 'Total': 'Monto_Ultimo_Pago'}
    )
    
    # Condición de venta
    resumen_limite = df_limite[['Cliente', 'Condición de venta', 'Límite de crédito']].drop_duplicates('Cliente')
    
    # Consolidado
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
