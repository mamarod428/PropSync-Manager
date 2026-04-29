"""
Database management module — dual-tier persistence layer.

This module handles all data persistence for PropSync Manager using two
complementary backends:

* **Local JSON (Tier 1):** Zero-latency edge storage for operational data
  (live trade map and closed trade history). All reads/writes during the
  trading loop operate on in-memory structures; disk writes happen only
  when a change is detected.

* **Supabase Cloud (Tier 2):** Asynchronous backup and analytics. Cloud
  operations are always attempted but never block local execution.

Typical usage example::

    db = cargar_mapa_a_ram()
    db = guardar_vinculo(db, 'slave_A', 98765, 12345, 1.0800, 1.0900, 1.0850, 0.5)
    guardar_ram_a_disco(db)
"""
import json
import os
from supabase import create_client
from modules.config import cargar_secrets

# --- DYNAMIC ABSOLUTE PATHS ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_DATA = os.path.join(BASE_DIR, "data")

FILE_DB = os.path.join(DIR_DATA, "mapa_operaciones.json")
FILE_HISTORY = os.path.join(DIR_DATA, "historial_operaciones.json")

# --- CLOUD CONFIGURATION (CENTRALIZED) ---
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

def cargar_mapa_a_ram() -> dict:
    """Loads the live trade map from disk into a RAM dictionary.

    Reads ``data/mapa_operaciones.json``. If the file does not exist or is
    corrupt, returns an empty dict so the trading loop can start fresh.

    Returns:
        A nested dict mapping slave IDs to their active trade links::

            {
                "slave_A": {
                    "98765": {"slave_ticket": 12345, "sl": 1.08, "tp": 1.09, ...}
                }
            }
    """
    mapa = {}
    if os.path.exists(FILE_DB): 
        try:
            with open(FILE_DB, 'r') as f: 
                mapa = json.load(f)
        except Exception:
            mapa = {}
    return mapa

def guardar_ram_a_disco(db_ram: dict) -> None:
    """Flushes the in-memory trade map to ``data/mapa_operaciones.json``.

    Creates the ``data/`` directory if it does not exist. On write failure,
    the error is silently ignored to prevent the trading loop from crashing.

    Args:
        db_ram: The in-memory trade map dict as managed by the trading loop.
    """
    if not os.path.exists(DIR_DATA): os.makedirs(DIR_DATA)
    try:
        with open(FILE_DB, 'w') as f: 
            json.dump(db_ram, f, indent=4)
    except Exception:
        error_guardado = 1

def guardar_vinculo(db_ram: dict, id_esclava: str, ticket_maestro: int,
                    ticket_esclavo: int, sl: float, tp: float,
                    price: float, volumen: float) -> dict:
    """Creates or updates a master-to-slave trade link in the RAM map.

    Stores the relationship between a master account position and its
    corresponding slave account order, including order parameters needed
    for future modification detection.

    Args:
        db_ram: The current in-memory trade map.
        id_esclava: The unique identifier of the slave node (e.g., 'slave_A').
        ticket_maestro: The ticket number of the master position.
        ticket_esclavo: The ticket number of the slave order (0 if rejected).
        sl: Stop Loss level, rounded to 5 decimal places.
        tp: Take Profit level, rounded to 5 decimal places.
        price: Entry price or pending order price.
        volumen: Lot size executed on the slave account.

    Returns:
        The updated RAM map with the new link recorded.
    """
    t_str = str(ticket_maestro)
    
    if id_esclava not in db_ram:
        db_ram[id_esclava] = {}
    
    db_ram[id_esclava][t_str] = {
        "slave_ticket": int(ticket_esclavo),
        "sl": round(float(sl), 5),
        "tp": round(float(tp), 5),
        "price": round(float(price), 5),
        "vol": float(volumen)
    }
    return db_ram

def eliminar_vinculo(db_ram: dict, id_esclava: str, ticket_maestro) -> dict:
    """Removes a master-to-slave trade link from the RAM map.

    Called when a master position is detected as closed. Cleans up the
    in-memory state so the slave entry is no longer tracked.

    Args:
        db_ram: The current in-memory trade map.
        id_esclava: The unique identifier of the slave node.
        ticket_maestro: The ticket number of the closed master position.

    Returns:
        The updated RAM map with the link removed.
    """
    t_str = str(ticket_maestro)
    if id_esclava in db_ram:
        if t_str in db_ram[id_esclava]:
            del db_ram[id_esclava][t_str]
    return db_ram

def obtener_vinculo(db_ram: dict, id_esclava: str, ticket_maestro) -> dict | None:
    """Retrieves the trade link for a given slave and master ticket pair.

    Args:
        db_ram: The current in-memory trade map.
        id_esclava: The unique identifier of the slave node.
        ticket_maestro: The ticket number of the master position to look up.

    Returns:
        A dict with keys ``slave_ticket``, ``sl``, ``tp``, ``price``, ``vol``
        if the link exists, or ``None`` if no link is found.
    """
    t_str = str(ticket_maestro)
    if id_esclava in db_ram:
        if isinstance(db_ram[id_esclava], dict):
            return db_ram[id_esclava].get(t_str)
    return None

def cargar_historial() -> list:
    """Loads the closed trade history from disk.

    Returns:
        A list of closed trade records. Each record is a dict with keys:
        ``ticket``, ``symbol``, ``type``, ``profit``, ``time_close``.
        Returns an empty list if the file does not exist or is corrupt.
    """
    if not os.path.exists(FILE_HISTORY): 
        return []
    try:
        with open(FILE_HISTORY, 'r') as f: 
            return json.load(f)
    except Exception: 
        return []

def agregar_a_historial(registro: dict) -> None:
    """Appends a closed trade record to the local history and syncs to Supabase.

    Writes the record to ``data/historial_operaciones.json`` first (always),
    then attempts to insert it into the Supabase ``trades`` table. Cloud
    failure does not affect local persistence.

    Args:
        registro: A dict describing the closed trade::

            {
                "ticket": str,
                "symbol": str,
                "type": "BUY" | "SELL",
                "profit": float,
                "time_close": float  # Unix timestamp
            }
    """
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

def obtener_tickets_nube(user_email: str) -> list:
    """Fetches the set of trade ticket IDs already stored in Supabase for a user.

    Used by :func:`sincronizar_historial_con_nube` to determine which local
    trades are missing from the cloud record.

    Args:
        user_email: The authenticated user's email address (used as the
            row identifier in the ``trades`` table).

    Returns:
        A list of ticket ID strings. Returns an empty list if Supabase is
        unavailable or the query fails.
    """
    """Obtains a list of all tickets already registered in the cloud for this user"""
    tickets = []
    if estado_conexion == 1:
        try:
            # We bring only the 'ticket' column to save bandwidth
            res = cliente_nube.table("trades").select("ticket").eq("user_email", user_email).execute()
            # We use a list comprehension to extract the IDs
            tickets = [str(item['ticket']) for item in res.data]
        except Exception:
            error_nube = 1
    return tickets

def sincronizar_historial_con_nube() -> None:
    """Uploads any locally stored trades that are missing from the Supabase cloud.

    Compares the local ``historial_operaciones.json`` against the cloud
    ``trades`` table for the current user, then bulk-uploads the difference.
    This ensures eventual consistency between the local edge store and the
    cloud analytics layer without uploading duplicates.
    """
    """Compares the local history with the cloud history and uploads what is missing"""
    if estado_conexion == 1:
        user_email = os.environ.get("PROPSYNC_USER_EMAIL", "default@propsync.com")
        historial_local = cargar_historial()
        tickets_en_nube = obtener_tickets_nube(user_email)
        
        # We filter operations that are NOT in the cloud
        # We don't use 'continue' or 'break', we use filtering logic
        operaciones_pendientes = [
            op for op in historial_local 
            if str(op.get("ticket")) not in tickets_en_nube
        ]
        
        # If there are pending items, we upload them one by one
        if len(operaciones_pendientes) > 0:
            registrar_en_lote_nube(operaciones_pendientes, user_email)

def registrar_en_lote_nube(lista_ops: list, email: str) -> None:
    """Uploads a list of trade records to Supabase in sequence.

    Individual insert failures are silently ignored so that one bad record
    does not prevent the rest from being uploaded.

    Args:
        lista_ops: A list of trade record dicts (same format as
            :func:`agregar_a_historial`).
        email: The authenticated user's email to tag each record with.
    """
    """Uploads a list of operations to Supabase"""
    for op in lista_ops:
        try:
            data_nube = {
                "user_email": email,
                "ticket": str(op.get("ticket", "0")),
                "symbol": op.get("symbol", "N/A"),
                "type": op.get("type", "BUY"),
                "profit": float(op.get("profit", 0.0)),
                "time_close": str(op.get("time_close", "0"))
            }
            cliente_nube.table("trades").insert(data_nube).execute()
        except Exception:
            error_subida = 1

# --- NEW PROP FIRM OPERATIONS & CLOUD CONFIG ---
def fetch_prop_firms() -> list:
    """Fetches all prop firm records from the Supabase ``prop_firms`` table.

    Returns:
        A list of prop firm dicts from Supabase, or an empty list if
        the cloud is unavailable.
    """
    if estado_conexion == 1:
        try:
            res = cliente_nube.table("prop_firms").select("*").execute()
            return res.data
        except Exception:
            return []
    return []

def add_prop_firm(data: dict) -> dict:
    """Inserts a new prop firm record into the Supabase ``prop_firms`` table.

    Args:
        data: A dict containing the prop firm configuration fields
            (e.g., ``name``, ``dd_diario``, ``dd_total``, ``target_f1``).

    Returns:
        A result dict with ``status`` set to ``'success'`` and ``data`` on
        success, or ``status`` set to ``'error'`` with a ``message`` on failure.
    """
    if estado_conexion == 1:
        try:
            res = cliente_nube.table("prop_firms").insert(data).execute()
            return {"status": "success", "data": res.data}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    return {"status": "error", "message": "No cloud connection"}

def upload_user_config(email: str, config_dict: dict) -> None:
    """Upserts the user's application configuration to the Supabase cloud.

    Serialises ``config_dict`` to a JSON string and stores it in the
    ``user_configs`` table, keyed by ``email``. This provides cloud backup
    and enables configuration restore on a new machine.

    Args:
        email: The authenticated user's email address.
        config_dict: The full application configuration dict (master + slaves).
    """
    if estado_conexion == 1:
        try:
            cliente_nube.table("user_configs").upsert({
                "user_email": email,
                "config_json": json.dumps(config_dict)
            }).execute()
        except Exception:
            pass

def download_user_config(email: str) -> dict | None:
    """Downloads the user's application configuration from the Supabase cloud.

    Args:
        email: The authenticated user's email address.

    Returns:
        The configuration dict if found in Supabase, or ``None`` if the user
        has no cloud backup or the cloud is unavailable.
    """
    if estado_conexion == 1:
        try:
            res = cliente_nube.table("user_configs").select("config_json").eq("user_email", email).execute()
            if res.data and len(res.data) > 0:
                return json.loads(res.data[0]["config_json"])
        except Exception:
            pass
    return None