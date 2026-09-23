import requests
import pandas as pd
from datetime import datetime

ORQUESTADOR_URL = "https://orquestador.senderosderaza.com.ar/api/v1"
API_KEY = "sr_f23256ffa63cc4257efa077fc4efbc129525e9272a8b39bfbfd88e7c0c286266"
FECHA_DESDE = "2026-08-01"

def obtener_token_respaldo():
    """Genera un token dinamico usando usuario y contraseña si la API Key falla."""
    try:
        data = {"username": "alejandra", "password": "vV7apCBlD0O0p3pAXs8y"}
        resp = requests.post(f"{ORQUESTADOR_URL}/auth/login", data=data, timeout=10)
        if resp.status_code == 200:
            return resp.json().get("access_token")
    except Exception as e:
        print(f"Error al obtener token de respaldo: {e}")
    return None

def obtener_headers():
    return {"X-API-Key": API_KEY}

def realizar_request(endpoint_url):
    """Realiza una consulta intentando primero con API_KEY y luego con Token."""
    headers = obtener_headers()
    try:
        resp = requests.get(endpoint_url, headers=headers, timeout=12)
        if resp.status_code == 401:
            token = obtener_token_respaldo()
            if token:
                headers = {"Authorization": f"Bearer {token}"}
                resp = requests.get(endpoint_url, headers=headers, timeout=12)
        return resp
    except Exception as e:
        print(f"Error en request: {e}")
        return None

def obtener_datos_orquestador():
    """Trae facturas pendientes y las cruza con los últimos cobros de Interbanking."""
    url_facturas = f"{ORQUESTADOR_URL}/facturas?limit=1000&solo_pendientes=true"
    resp_facturas = realizar_request(url_facturas)
    
    df_facturas = pd.DataFrame()
    if resp_facturas and resp_facturas.status_code == 200:
        df_facturas = pd.DataFrame(resp_facturas.json())

    # Traer movimientos de cobranzas (créditos) de Interbanking
    url_cobros = f"{ORQUESTADOR_URL}/interbanking/movimientos?limit=1000&debit_credit_type=C&fecha_desde={FECHA_DESDE}"
    resp_cobros = realizar_request(url_cobros)
    
    dict_ultimos_cobros = {}
    if resp_cobros and resp_cobros.status_code == 200:
        df_cobros = pd.DataFrame(resp_cobros.json())
        if not df_cobros.empty and 'customer_cuit' in df_cobros.columns and 'movement_date' in df_cobros.columns:
            # Obtener el último pago registrado por CUIT
            df_cobros['movement_date'] = pd.to_datetime(df_cobros['movement_date'])
            ultimos = df_cobros.groupby('customer_cuit')['movement_date'].max().reset_index()
            dict_ultimos_cobros = dict(zip(ultimos['customer_cuit'], ultimos['movement_date']))

    if not df_facturas.empty:
        # Limpiar y normalizar CUIT para el cruce
        if 'id_fiscal' in df_facturas.columns:
            df_facturas['cuit_limpio'] = df_facturas['id_fiscal'].astype(str).str.replace(r'\D', '', regex=True)
            df_facturas['fecha_ultimo_cobro'] = df_facturas['cuit_limpio'].map(dict_ultimos_cobros)
        else:
            df_facturas['fecha_ultimo_cobro'] = None

    return df_facturas

def calcular_semaforo(fecha_pago):
    """Calcula el semáforo basado en días sin recibir pago."""
    if pd.isna(fecha_pago) or str(fecha_pago).strip() in ["", "None", "NaT"]:
        return "🔴 +15 días (Sin Cobros)"
    
    try:
        ts_pago = pd.to_datetime(fecha_pago)
        dias = (pd.Timestamp.now() - ts_pago).days
        if dias <= 7:
            return "🟢 0-7 días (Cobro Reciente)"
        elif 7 < dias <= 14:
            return "🟡 7-14 días (Alerta)"
        else:
            return "🔴 +15 días (Atención)"
    except Exception:
        return "🔴 +15 días"
