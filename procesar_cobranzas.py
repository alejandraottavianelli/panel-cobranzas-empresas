import requests
import pandas as pd
from datetime import datetime

ORQUESTADOR_URL = "https://orquestador.senderosderaza.com.ar/api/v1"
API_KEY = "sr_f23256ffa63cc4257efa077fc4efbc129525e9272a8b39bfbfd88e7c0c286266"
FECHA_DESDE = "2026-08-01"

# Las 58 empresas de tu cartera
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
    """Genera un token dinamico usando usuario y contraseña si la API Key falla."""
    try:
        data = {"username": "alejandra", "password": "vV7apCBlD0O0p3pAXs8y"}
        resp = requests.post(f"{ORQUESTADOR_URL}/auth/login", data=data, timeout=10)
        if resp.status_code == 200:
            return resp.json().get("access_token")
    except Exception as e:
        print(f"Error al obtener token de respaldo: {e}")
    return None

def obtener_datos_orquestador():
    """Trae las facturas pendientes intentando primero API Key y luego Token de respaldo."""
    url = f"{ORQUESTADOR_URL}/facturas?limit=1000&solo_pendientes=true"
    headers = {"X-API-Key": API_KEY}
    
    response = None
    try:
        response = requests.get(url, headers=headers, timeout=12)
        if response.status_code == 401:
            token = obtener_token_respaldo()
            if token:
                headers = {"Authorization": f"Bearer {token}"}
                response = requests.get(url, headers=headers, timeout=12)
    except Exception as e:
        print(f"Error en request facturas: {e}")

    if response and response.status_code == 200:
        df = pd.DataFrame(response.json())
        if not df.empty and 'cliente' in df.columns:
            palabras_clave = ["AGS", "AÑELO", "ALONSO", "BASE", "BEERSEBA", "BETOS", "BUTACO", "CASINO", "COLEAL", "CONFLUENCIA", "COSTA", "DISTRITO", "DREST", "ORIGEN", "EQUIPADOS", "FOOD", "GINALLI", "GOURMET", "HOTEL", "HUMO", "IDRIS", "INDUX", "INN", "JUANITO", "KOMPASS", "KUK", "MALEVA", "MARFA", "MARSHA", "MAXIMIA", "MAYCAR", "MUCA", "OFFICE", "PELUDO", "PITIO", "PIZZERIA", "SAIGRO", "SALUZZO", "SIMPLIFICADA", "NASER", "TRUCKS", "VANOLI", "WENELEN", "WENVIL", "SOTO", "DOGMA"]
            pattern = '|'.join(palabras_clave)
            df_filtrado = df[df['cliente'].str.contains(pattern, case=False, na=False)]
            return df_filtrado if not df_filtrado.empty else df
        return df
    
    return pd.DataFrame()

def calcular_semaforo(fecha_pago):
    """Calcula los días transcurridos evitando errores de tipo (TypeError)."""
    if pd.isna(fecha_pago) or str(fecha_pago).strip() in ["", "None", "NaT"]:
        return "🔴 +15 días"
    
    try:
        ts_pago = pd.to_datetime(fecha_pago)
        if pd.isna(ts_pago):
            return "🔴 +15 días"
            
        dias = (pd.Timestamp.now() - ts_pago).days
        if dias <= 7:
            return "🟢 0-7 días"
        elif 7 < dias <= 14:
            return "🟡 7-14 días"
        else:
            return "🔴 +15 días"
    except Exception:
        return "🔴 +15 días"
