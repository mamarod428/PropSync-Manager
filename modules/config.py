import json
import os
import base64

# --- RUTAS ABSOLUTAS DINÁMICAS ---
# __file__ es config.py. Subimos dos niveles: modules/ -> PropSync-Manager/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_DATA = os.path.join(BASE_DIR, "data")

FILE_CREDS = os.path.join(DIR_DATA, "credenciales.json")
FILE_FIRMS = os.path.join(DIR_DATA, "prop_firms.json")
FILE_SECRETS_NUBE = os.path.join(BASE_DIR, "secrets.json")

def codificar(texto):
    return base64.b64encode(texto.encode('utf-8')).decode('utf-8')

def decodificar(texto_codificado):
    try:
        return base64.b64decode(texto_codificado.encode('utf-8')).decode('utf-8')
    except Exception:
        error_ignorado = 1
        return texto_codificado

def cargar_credenciales():
    config_cargada = None
    if os.path.exists(FILE_CREDS): 
        try:
            with open(FILE_CREDS, 'r') as f: 
                config_cargada = json.load(f)
                
            if 'master' in config_cargada and 'password' in config_cargada:
                config_cargada = decodificar(config_cargada)
                
            if 'slaves' in config_cargada:
                for s in config_cargada:
                    if 'password' in s:
                        s = decodificar(s)
        except Exception:
            error_lectura = 1
                        
    return config_cargada

def guardar_credenciales(nueva_config):
    if not os.path.exists(DIR_DATA): os.makedirs(DIR_DATA)
    
    config_segura = json.loads(json.dumps(nueva_config))
    
    if 'master' in config_segura and 'password' in config_segura:
        config_segura = codificar(config_segura)
        
    if 'slaves' in config_segura:
        for s in config_segura:
            if 'password' in s:
                s = codificar(s)

    try:
        with open(FILE_CREDS, 'w') as f:
            json.dump(config_segura, f, indent=4)
    except Exception:
        error_escritura = 1

def cargar_empresas():
    if os.path.exists(FILE_FIRMS):
        try:
            with open(FILE_FIRMS, 'r') as f:
                return json.load(f)
        except Exception:
            error_lectura = 1
            
    default_firms = {
        "FTMO": {"dd_diario": 5.0, "dd_total": 10.0, "target_f1": 10.0, "target_f2": 5.0},
        "WSF": {"dd_diario": 4.0, "dd_total": 8.0, "target_f1": 8.0, "target_f2": 5.0},
        "Axi Select": {"dd_diario": 10.0, "dd_total": 10.0, "target_f1": 7.0, "target_f2": 7.0}
    }
    guardar_empresas(default_firms)
    return default_firms

def guardar_empresas(data):
    if not os.path.exists(DIR_DATA): os.makedirs(DIR_DATA)
    try:
        with open(FILE_FIRMS, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception:
        error_escritura = 1

def cargar_secrets():
    if os.path.exists(FILE_SECRETS_NUBE):
        try:
            with open(FILE_SECRETS_NUBE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f">>> Fallo al leer secrets.json: {str(e)}")
            return {"SUPABASE_URL": "", "SUPABASE_KEY": ""}
    else:
        print(f">>> No se encuentra secrets.json en: {FILE_SECRETS_NUBE}")
        
    return {"SUPABASE_URL": "", "SUPABASE_KEY": ""}