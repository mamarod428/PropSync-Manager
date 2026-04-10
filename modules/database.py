"""
Database Management Module.
"""
import json
import os
from supabase import create_client
from modules.config import cargar_secrets

# --- RUTAS ABSOLUTAS DINÁMICAS ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_DATA = os.path.join(BASE_DIR, "data")

FILE_DB = os.path.join(DIR_DATA, "mapa_operaciones.json")
FILE_HISTORY = os.path.join(DIR_DATA, "historial_operaciones.json")

# --- CONFIGURACIÓN CLOUD (CENTRALIZADA) ---
secrets = cargar_secrets()
URL_NUBE = secrets.get("SUPABASE_URL", "")
KEY_NUBE = secrets.get("SUPABASE_KEY", "")

cliente_nube = None
estado_conexion = 0
if URL_NUBE != "":
    try:
        cliente_nube = create_client(URL_NUBE, KEY_NUBE)
        estado_conexion = 1
    except Exception as e:
        error_init = str(e)

def cargar_mapa_a_ram():
    mapa = {}
    if os.path.exists(FILE_DB): 
        try:
            with open(FILE_DB, 'r') as f: 
                mapa = json.load(f)
        except Exception:
            mapa = {}
    return mapa

def guardar_ram_a_disco(db_ram):
    if not os.path.exists(DIR_DATA): os.makedirs(DIR_DATA)
    try:
        with open(FILE_DB, 'w') as f: 
            json.dump(db_ram, f, indent=4)
    except Exception:
        error_guardado = 1

def guardar_vinculo(db_ram, id_esclava, ticket_maestro, ticket_esclavo, sl, tp, price, volumen):
    t_str = str(ticket_maestro)
    
    esclava_existe = 0
    if id_esclava in db_ram:
        if isinstance(db_ram, dict):
            esclava_existe = 1
            
    if esclava_existe == 0:
        db_ram = {}
    
    db_ram = {
        "slave_ticket": int(ticket_esclavo),
        "sl": round(float(sl), 5),
        "tp": round(float(tp), 5),
        "price": round(float(price), 5),
        "vol": float(volumen)
    }
    return db_ram

def eliminar_vinculo(db_ram, id_esclava, ticket_maestro):
    t_str = str(ticket_maestro)
    registro_existe = 0
    if id_esclava in db_ram:
        if t_str in db_ram:
            registro_existe = 1
            
    if registro_existe == 1:
        del db_ram
    return db_ram

def obtener_vinculo(db_ram, id_esclava, ticket_maestro):
    t_str = str(ticket_maestro)
    vinculo_valido = 0
    if id_esclava in db_ram:
        if isinstance(db_ram, dict):
            vinculo_valido = 1
            
    if vinculo_valido == 1:
        return db_ram.get(t_str)
    return None

def cargar_historial():
    if not os.path.exists(FILE_HISTORY): 
        return []
    try:
        with open(FILE_HISTORY, 'r') as f: 
            return json.load(f)
    except Exception: 
        return []

def agregar_a_historial(registro):
    historial = cargar_historial()
    historial.append(registro)
    if not os.path.exists(DIR_DATA): os.makedirs(DIR_DATA)
    try:
        with open(FILE_HISTORY, 'w') as f: 
            json.dump(historial, f, indent=4)
    except Exception:
        error_local = 1
        
    if estado_conexion == 1:
        try:
            usuario_actual = os.environ.get("PROPSYNC_USER_EMAIL", "default@propsync.com")
            data_nube = {
                "user_email": usuario_actual,
                "ticket": str(registro.get("ticket", "0")),
                "symbol": registro.get("symbol", "N/A"),
                "type": registro.get("type", "BUY"),
                "profit": float(registro.get("profit", 0.0)),
                "time_close": str(registro.get("time_close", "0"))
            }
            cliente_nube.table("trades").insert(data_nube).execute()
        except Exception:
            error_sync = 1