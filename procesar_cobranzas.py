import requests
import pandas as pd
from datetime import datetime

ORQUESTADOR_URL = "https://orquestador.senderosderaza.com.ar/api/v1"
API_KEY = "sr_f23256ffa63cc4257efa077fc4efbc129525e9272a8b39bfbfd88e7c0c286266"
FECHA_DESDE = "2026-08-01"

# Lista maestra exacta de las 58 Empresas
EMPRESAS_CARTERA = [
    "ALONSO LUIS SEBASTIAN", "AGS S.R.L", "AÑELO FOODS AND DRINKS S.A.S", "BASE 2 SRL",
    "BEERSEBA SRL", "BETOS LOMOS (CHIARO SRL)", "BIGNERT, CESAR ADRIAN,JULIO Y DANIEL",
    "BUTACO SRL", "CASINO MAGIC NEUQUEN S.A", "COLEAL SOCIEDAD ANONIMA", "CONFLUENCIA DE SABORES SAS",
    "CONSEJO PROVINCIAL DE EDUCACION DEL NQN", "COSTA NQN SRL", "DISTRITO 220 S.R.L",
    "DREST EMPRENDIMIENTOS S.A", "EL ORIGEN BEER HOUSE SRL", "EL RINCON DE PIEDRA DEL AGUILA SRL",
    "EPICURO SMA S.A.S.", "EQUIPADOS SAS", "FCH S. A. S.", "FOOD SERVICE S.A.",
    "GARCIA OTERO ESTEBAN JAVIER", "GINALLI SRL", "GOURMET LAB S.A.S.", "HOTEL LAND EXPRESS",
    "HUMO SAPIENS S.R.L.", "IDRIS PATAGONIA SA", "INDUX S.A.", "INN S.A.", "JUANITO SRL",
    "KOMPASS SRL", "KUK S.A.S.", "LA MALEVA SMA", "LUIS ARCEO SRL", "LUNCH S.A.S",
    "MARFA S.R.L", "MARSHA S.R.L", "MAXIMIA SA", "MAYCAR SOCIEDAD ANONIMA", "MUCA S.A.S",
    "OFFICE GOURMET", "PELUDO BARFERO S. A. S.", "PITIO S.A", "PIZZERIA POPULAR PATAGONIA S.A.S",
    "R.C. ALBA S.G. S. A. S.", "REYMON SOCIAL CLUB S.A.S", "RYM.COM S.A.S.", "SAIGRO S.A",
    "SALUZZO S.R.L", "SIMPLIFICADA", "SERVICIOS NASER SRL", "TRUCKS VIAL SAS",
    "V&D SOCIEDAD DE RESPONSABILIDAD LIMITADA", "VANOLI & DURAND SRL", "WENELEN (ADMINVER S.A)",
    "WENVIL S.A.", "SOTO SERVICIOS INDUSTRIALES S.R.L", "DOGMA SRL"
]

def obtener_token_respaldo():
    """Obtiene token de autenticación si la API Key aún no está dada de alta en la base."""
    try:
        data = {"username": "alejandra", "password": "vV7apCBlD0O0p3pAXs8y"}
        resp = requests.post(f"{ORQUESTADOR_URL}/auth/login", data=data, timeout=10)
        if resp.status_code == 200:
            return resp.json().get("access_token")
    except Exception as e:
        print(f"Error login respaldo: {e}")
    return None

def realizar_request(endpoint_url):
    """Ejecuta consulta HTTP con API Key o Token de respaldo."""
    headers = {"X-API-Key": API_KEY}
    try:
        resp = requests.get(endpoint_url, headers=headers, timeout=15)
        if resp.status_code == 401:
            token = obtener_token_respaldo()
            if token:
                headers = {"Authorization": f"Bearer {token}"}
                resp = requests.get(endpoint_url, headers=headers, timeout=15)
        return resp
    except Exception as e:
        print(f"Error en request: {e}")
        return None

def obtener_datos_orquestador():
    """Consulta facturas y movimientos bancarios filtrando EXCLUSIVAMENTE la cartera de 58 empresas."""
    url_facturas = f"{ORQUESTADOR_URL}/facturas?limit=1000&solo_pendientes=true"
    resp_facturas = realizar_request(url_facturas)
    
    df_facturas = pd.DataFrame()
    if resp_facturas and resp_facturas.status_code == 200:
        df_raw = pd.DataFrame(resp_facturas.json())
        if not df_raw.empty and 'cliente' in df_raw.columns:
            # Filtro estricto por los nombres de las 58 empresas
            patron = '|'.join([e.replace('(', r'\(').replace(')', r'\)').replace('.', r'\.') for e in EMPRESAS_CARTERA])
            df_facturas = df_raw[df_raw['cliente'].str.contains(patron, case=False, na=False)].copy()

    # Consultar últimos cobros de Interbanking para la alerta de días
    url_cobros = f"{ORQUESTADOR_URL}/interbanking/movimientos?limit=1000&debit_credit_type=C&fecha_desde={FECHA_DESDE}"
    resp_cobros = realizar_request(url_cobros)
    
    dict_ultimos_cobros = {}
    if resp_cobros and resp_cobros.status_code == 200:
        df_cobros = pd.DataFrame(resp_cobros.json())
        if not df_cobros.empty and 'customer_cuit' in df_cobros.columns and 'movement_date' in df_cobros.columns:
            df_cobros['movement_date'] = pd.to_datetime(df_cobros['movement_date'])
            ultimos = df_cobros.groupby('customer_cuit')['movement_date'].max().reset_index()
            dict_ultimos_cobros = dict(zip(ultimos['customer_cuit'], ultimos['movement_date']))

    if not df_facturas.empty:
        if 'id_fiscal' in df_facturas.columns:
            df_facturas['cuit_limpio'] = df_facturas['id_fiscal'].astype(str).str.replace(r'\D', '', regex=True)
            df_facturas['fecha_ultimo_cobro'] = df_facturas['cuit_limpio'].map(dict_ultimos_cobros)
        else:
            df_facturas['fecha_ultimo_cobro'] = None

    return df_facturas

def calcular_semaforo(fecha_pago):
    """Calcula el estado del semáforo según días transcurridos desde el último pago."""
    if pd.isna(fecha_pago) or str(fecha_pago).strip() in ["", "None", "NaT"]:
        return "🔴 +15 días"
    try:
        ts_pago = pd.to_datetime(fecha_pago)
        dias = (pd.Timestamp.now() - ts_pago).days
        if dias <= 7:
            return "🟢 0-7 días"
        elif 7 < dias <= 14:
            return "🟡 7-14 días"
        else:
            return "🔴 +15 días"
    except Exception:
        return "🔴 +15 días"
