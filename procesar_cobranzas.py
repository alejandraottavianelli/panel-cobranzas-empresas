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

def obtener_datos_orquestador():
    headers = {"X-API-Key": API_KEY}
    url = f"{ORQUESTADOR_URL}/facturas?solo_pendientes=true&last_update_date={FECHA_DESDE}T00:00:00"
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            df = pd.DataFrame(response.json())
            if not df.empty and 'cliente' in df.columns:
                pattern = '|'.join(EMPRESAS_CARTERA)
                return df[df['cliente'].str.contains(pattern, case=False, na=False)]
        return pd.DataFrame()
    except Exception as e:
        print(f"Error de conexión: {e}")
        return pd.DataFrame()

def calcular_semaforo(fecha_pago):
    if not fecha_pago or pd.isna(fecha_pago):
        return "🔴 +15 días"
    dias = (datetime.now() - pd.to_datetime(fecha_pago)).days
    if dias <= 7:
        return "🟢 0-7 días"
    elif 7 < dias <= 14:
        return "🟡 7-14 días"
    else:
        return "🔴 +15 días"
