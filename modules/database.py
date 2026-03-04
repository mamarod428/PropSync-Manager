import json
import os

FILE_DB = os.path.join("data", "mapa_operaciones.json")
FILE_HISTORY = os.path.join("data", "historial_operaciones.json")

# [CRITERIO ACADEMICO: 5b - Ciclo de vida del dato (Generacion y Extraccion)]
def cargar_mapa_a_ram():
    mapa = {}
    if os.path.exists(FILE_DB): 
        try:
            with open(FILE_DB, 'r') as f: 
                mapa = json.load(f)
        except Exception as e:
            mapa = {}
    return mapa

# [CRITERIO ACADEMICO: 5f - Almacenamiento local (Edge Computing)]
def guardar_ram_a_disco(db_ram):
    if not os.path.exists("data"): os.makedirs("data")
    with open(FILE_DB, 'w') as f: 
        json.dump(db_ram, f, indent=4)

# [CRITERIO ACADEMICO: 5b - Consistencia e integridad de los datos]
def guardar_vinculo(db_ram, id_esclava, ticket_maestro, ticket_esclavo, sl, tp, price, volumen):
    t_str = str(ticket_maestro)
    
    esclava_existe = 0
    if id_esclava in db_ram:
        if isinstance(db_ram[id_esclava], dict):
            esclava_existe = 1
            
    if esclava_existe == 0:
        db_ram[id_esclava] = {}
    
    db_ram[id_esclava][t_str] = {
        "slave_ticket": int(ticket_esclavo),
        "sl": round(float(sl), 5),
        "tp": round(float(tp), 5),
        "price": round(float(price), 5),
        "vol": float(volumen)
    }
    return db_ram

# [CRITERIO ACADEMICO: 5b - Ciclo de vida del dato (Eliminacion)]
def eliminar_vinculo(db_ram, id_esclava, ticket_maestro):
    t_str = str(ticket_maestro)
    registro_existe = 0
    if id_esclava in db_ram:
        if t_str in db_ram[id_esclava]:
            registro_existe = 1
            
    if registro_existe == 1:
        del db_ram[id_esclava][t_str]
    return db_ram

def obtener_vinculo(db_ram, id_esclava, ticket_maestro):
    t_str = str(ticket_maestro)
    vinculo_valido = 0
    if id_esclava in db_ram:
        if isinstance(db_ram[id_esclava], dict):
            vinculo_valido = 1
            
    if vinculo_valido == 1:
        return db_ram[id_esclava].get(t_str)
    return None

# [CRITERIO ACADEMICO: 5b - Ciclo de vida del dato (Archivo e Historico)]
def cargar_historial():
    if not os.path.exists(FILE_HISTORY): 
        return []
    try:
        with open(FILE_HISTORY, 'r') as f: 
            return json.load(f)
    except: 
        return []

def agregar_a_historial(registro):
    historial = cargar_historial()
    historial.append(registro)
    if not os.path.exists("data"): os.makedirs("data")
    with open(FILE_HISTORY, 'w') as f: 
        json.dump(historial, f, indent=4)