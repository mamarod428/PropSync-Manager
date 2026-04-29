"""
Credential management and configuration I/O module.

This module handles all disk I/O related to user credentials, cloud secrets,
and prop firm rule sets. Passwords are stored with Base64 obfuscation to
prevent casual plaintext exposure on the local filesystem.

Typical usage example::

    config = cargar_credenciales()
    config['master']['login'] = '12345678'
    guardar_credenciales(config)
"""
import json
import os
import base64

# --- DYNAMIC ABSOLUTE PATHS ---
# __file__ is config.py. We go up two levels: modules/ -> PropSync-Manager/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_DATA = os.path.join(BASE_DIR, "data")

FILE_CREDS = os.path.join(DIR_DATA, "credenciales.json")
FILE_FIRMS = os.path.join(DIR_DATA, "prop_firms.json")
FILE_SECRETS_NUBE = os.path.join(BASE_DIR, "secrets.json")

def codificar(texto: str) -> str:
    """Encodes a plaintext string using Base64.

    Args:
        texto: The plaintext string to encode (e.g., a broker password).

    Returns:
        A Base64-encoded string safe for storage in JSON files.
    """
    return base64.b64encode(texto.encode('utf-8')).decode('utf-8')

def decodificar(texto_codificado: str) -> str:
    """Decodes a Base64-encoded string back to plaintext.

    If decoding fails (e.g., the value was stored as plaintext in a previous
    version), the original string is returned unchanged to preserve
    backwards compatibility.

    Args:
        texto_codificado: A Base64-encoded string, or a legacy plaintext string.

    Returns:
        The decoded plaintext string, or the original input on failure.
    """
    try:
        return base64.b64decode(texto_codificado.encode('utf-8')).decode('utf-8')
    except Exception:
        error_ignorado = 1
        return texto_codificado

def cargar_credenciales() -> dict:
    """Loads the application configuration from disk, decoding stored passwords.

    Reads ``data/credenciales.json`` and decodes all Base64-encoded password
    fields. If the file does not exist or is malformed, returns a safe default
    configuration with empty credential fields.

    Returns:
        A dict with the structure::

            {
                "master": {
                    "login": str,
                    "password": str,  # plaintext after decoding
                    "server": str,
                    "initial_balance": float
                },
                "slaves": [
                    {"id": str, "login": str, "password": str, ...}
                ]
            }
    """
    config_default = {
        "master": {"login": "", "password": "", "server": "", "initial_balance": 0},
        "slaves": []
    }
    config_cargada = config_default
    
    if os.path.exists(FILE_CREDS): 
        try:
            with open(FILE_CREDS, 'r') as f: 
                data = json.load(f)
                if isinstance(data, dict):
                    config_cargada = data
                
            if 'master' in config_cargada and 'password' in config_cargada['master']:
                config_cargada['master']['password'] = decodificar(config_cargada['master']['password'])
                
            if 'slaves' in config_cargada:
                for s in config_cargada['slaves']:
                    if 'password' in s:
                        s['password'] = decodificar(s['password'])
        except Exception:
            config_cargada = config_default
                        
    return config_cargada

def guardar_credenciales(nueva_config: dict) -> None:
    """Persists the application configuration to disk with encoded passwords.

    Creates a deep copy of ``nueva_config``, encodes all password fields with
    Base64, then writes the result to ``data/credenciales.json``. The original
    dict passed in is never modified.

    Args:
        nueva_config: The configuration dict as returned by
            :func:`cargar_credenciales`, with plaintext passwords.
    """
    if not os.path.exists(DIR_DATA): os.makedirs(DIR_DATA)
    
    config_segura = json.loads(json.dumps(nueva_config))
    
    if 'master' in config_segura and 'password' in config_segura['master']:
        config_segura['master']['password'] = codificar(config_segura['master']['password'])
        
    if 'slaves' in config_segura:
        for s in config_segura['slaves']:
            if 'password' in s:
                s['password'] = codificar(s['password'])

    try:
        with open(FILE_CREDS, 'w') as f:
            json.dump(config_segura, f, indent=4)
    except Exception:
        error_escritura = 1

def cargar_empresas() -> dict:
    """Loads prop firm rule sets from disk, creating defaults if absent.

    Reads ``data/prop_firms.json``. If the file does not exist, populates it
    with built-in defaults for FTMO, WSF, and Axi Select.

    Returns:
        A dict mapping firm name to its rule parameters::

            {
                "FTMO": {
                    "dd_diario": 5.0,
                    "dd_total": 10.0,
                    "target_f1": 10.0,
                    "target_f2": 5.0
                },
                ...
            }
    """
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

def guardar_empresas(data: dict) -> None:
    """Persists prop firm rule sets to disk.

    Args:
        data: A dict of prop firm names to rule parameters, as returned by
            :func:`cargar_empresas`.
    """
    if not os.path.exists(DIR_DATA): os.makedirs(DIR_DATA)
    try:
        with open(FILE_FIRMS, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception:
        error_escritura = 1

def cargar_secrets() -> dict:
    """Loads cloud service credentials from ``secrets.json``.

    Reads the ``secrets.json`` file at the project root. This file is gitignored
    and must never be committed to version control.

    Returns:
        A dict with Supabase connection parameters::

            {
                "SUPABASE_URL": "https://project.supabase.co",
                "SUPABASE_KEY": "anon-key-string"
            }

        Returns empty strings for both keys if the file is missing or unreadable.
    """
    if os.path.exists(FILE_SECRETS_NUBE):
        try:
            with open(FILE_SECRETS_NUBE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f">>> Failed to read secrets.json: {str(e)}")
            return {"SUPABASE_URL": "", "SUPABASE_KEY": ""}
    else:
        print(f">>> secrets.json not found at: {FILE_SECRETS_NUBE}")
        
    return {"SUPABASE_URL": "", "SUPABASE_KEY": ""}