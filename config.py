import json
import os

FILE_SECRETS = 'secrets.json'
FILE_DB = 'mapa_operaciones.json'
FILE_HISTORY = 'historial_operaciones.json'
FILE_FIRMS = 'prop_firms.json'

def cargar_credenciales():
    config_cargada = None
    if os.path.exists(FILE_SECRETS): 
        with open(FILE_SECRETS, 'r') as f: 
            config_cargada = json.load(f)
    return config_cargada

def guardar_credenciales(nueva_config):
    with open(FILE_SECRETS, 'w') as f:
        json.dump(nueva_config, f, indent=4)

def cargar_empresas():
    if os.path.exists(FILE_FIRMS):
        with open(FILE_FIRMS, 'r') as f:
            return json.load(f)
            
    # Empresas predeterminadas con sus limites y objetivos
    default_firms = {
        "FTMO": {"dd_diario": 5.0, "dd_total": 10.0, "target_f1": 10.0, "target_f2": 5.0},
        "WSF": {"dd_diario": 4.0, "dd_total": 8.0, "target_f1": 8.0, "target_f2": 5.0},
        "Axi": {"dd_diario": 5.0, "dd_total": 10.0, "target_f1": 8.0, "target_f2": 5.0}
    }
    guardar_empresas(default_firms)
    return default_firms

def guardar_empresas(data):
    with open(FILE_FIRMS, 'w') as f:
        json.dump(data, f, indent=4)