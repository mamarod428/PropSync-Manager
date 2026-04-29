"""
PropSync Manager — application entry point and pywebview bridge.

This module serves two roles:

1. **Application bootstrap:** Loads credentials, creates the ``BridgeAPI``
   instance, and launches the pywebview window that renders the local
   web interface.

2. **JS ←→ Python bridge:** The ``BridgeAPI`` class exposes all Python
   capabilities (MT5 engine lifecycle, configuration persistence, telemetry)
   to the JavaScript frontend via the pywebview ``js_api`` mechanism.

Typical entry::

    python main.py

The trading engine runs in a daemon thread (:func:`ciclo_trading_recursivo`)
and does not block the UI. All shared state is managed via module-level globals.
"""
import MetaTrader5 as mt5
import time
import os
import threading
import webview
from supabase import create_client

from modules.config import cargar_credenciales, cargar_secrets, guardar_credenciales
from modules.database import cargar_mapa_a_ram, guardar_ram_a_disco, cargar_historial, agregar_a_historial, obtener_vinculo, eliminar_vinculo
from modules.trading import (cambiar_cuenta, obtener_estado_maestro, sincronizar_inicio,
                             ejecutar_apertura, ejecutar_modificacion, ejecutar_cierre,
                             verificar_credenciales_mt5)

# --- CLOUD CONFIGURATION ---
secrets = cargar_secrets()
URL_NUBE = secrets.get("SUPABASE_URL", "")
KEY_NUBE = secrets.get("SUPABASE_KEY", "")

supabase = None
if URL_NUBE != "":
    try:
        supabase = create_client(URL_NUBE, KEY_NUBE)
    except Exception:
        error_conexion = 1

# --- GLOBAL STATE VARIABLES ---
bot_activo = 0
cuenta_conectada = 0
memoria_db = {}
tickets_maestros_abiertos = []
app_config = None
window = None
hilo_motor = None  # Thread handle for the trading loop

# Floating variables for the Dashboard
eq_master_global = 0.0
bal_master_global = 0.0
profit_master_global = 0.0

# ──────────────────────────────────────────────────────────────────────────────
# Log category icons used by the JS terminal parser
# ──────────────────────────────────────────────────────────────────────────────
# Stat counters exposed to BridgeAPI.obtener_estado_motor()
_stat_ciclos = 0
_stat_replicaciones = 0
_stat_errores = 0
_stat_ultimo_sync = ""

def registrar_log(mensaje: str) -> None:
    """Sends a timestamped log message to both the terminal and the web UI console.

    Prepends an ``HH:MM:SS`` timestamp so the terminal panel can display it.
    Escapes single quotes to prevent JavaScript syntax errors. Silently ignores
    failures if the pywebview window is not yet initialised.

    Args:
        mensaje: The log message string to display.
    """
    import datetime
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    mensaje_ts = f"[{ts}] {mensaje}"
    print(mensaje_ts)
    global _stat_errores
    if "[ERROR]" in mensaje or "[CREDENCIAL]" in mensaje:
        _stat_errores += 1
    if window:
        msg_seguro = mensaje_ts.replace("\\", "\\\\").replace("'", "\\'")
        try:
            window.evaluate_js(f"if(typeof window.log_sys==='function') window.log_sys('{msg_seguro}');")
        except Exception:
            pass

def iniciar_motor_trading() -> dict:
    """Initialises the MT5 connection and starts the trading loop thread.

    Validates master credentials with :func:`verificar_credenciales_mt5` before
    starting the loop, surfacing a specific error type (wrong login number,
    wrong password, unreachable server, terminal not running).

    Returns:
        A dict with a ``status`` key:

        * ``{'status': 'ok'}`` — engine started.
        * ``{'status': 'config_error', 'message': str}`` — credentials missing.
        * ``{'status': 'mt5_error', 'tipo': str, 'message': str}`` — MT5 failure with category.
    """
    global bot_activo, cuenta_conectada, memoria_db, tickets_maestros_abiertos, app_config, hilo_motor
    global _stat_ciclos, _stat_replicaciones, _stat_errores, _stat_ultimo_sync

    # Prevent starting if already active
    if bot_activo == 1:
        return {"status": "ok"}

    # Reset statistics
    _stat_ciclos = 0
    _stat_replicaciones = 0
    _stat_errores = 0
    _stat_ultimo_sync = ""

    # ── 1. Validate config ────────────────────────────────────────────────────────────
    if not app_config or not app_config.get('master') or app_config['master'].get('login') == "":
        registrar_log("[ERROR] Master account parameters missing in configuration.")
        return {"status": "config_error", "message": "Master account credentials not configured."}

    m = app_config['master']

    # ── 2. Verify credentials precisely ──────────────────────────────────────────────
    registrar_log(f"[SYSTEM] Verifying MT5 credentials for account {m['login']} on {m['server']}...")
    resultado_ver = verificar_credenciales_mt5(
        login=int(m['login']),
        password=m['password'],
        server=m['server']
    )

    if not resultado_ver['valido']:
        tipo  = resultado_ver['tipo']
        msg   = resultado_ver['mensaje']
        registrar_log(f"[CREDENTIAL] ✗ MT5 Authentication failed ({tipo}): {msg}")
        mt5.shutdown()
        return {"status": "mt5_error", "tipo": tipo, "message": msg}

    registrar_log(f"[SYSTEM] ✓ Valid credentials. Account {m['login']} authenticated on {m['server']}.")

    # ── 3. Boot the engine ─────────────────────────────────────────────────────────────
    bot_activo = 1
    registrar_log("[SYSTEM] Starting Edge sync routines...")

    registrar_log("[CLOUD] Verifying data integrity with Supabase...")
    from modules.database import sincronizar_historial_con_nube
    sincronizar_historial_con_nube()
    registrar_log("[CLOUD] Sync completed.")

    memoria_db = cargar_mapa_a_ram()
    cuenta_conectada, memoria_db = sincronizar_inicio(app_config, cuenta_conectada, memoria_db, registrar_log)
    guardar_ram_a_disco(memoria_db)

    ops_iniciales = obtener_estado_maestro()
    tickets_maestros_abiertos = [str(op['ticket']) for op in ops_iniciales]

    n_ops = len(tickets_maestros_abiertos)
    registrar_log(f"[SYSTEM] RPA Engine started. {n_ops} operation(s) detected on master.")

    hilo_motor = threading.Thread(target=ciclo_trading_recursivo, daemon=True)
    hilo_motor.start()
    return {"status": "ok"}

def detener_motor_trading() -> None:
    """Stops the trading loop and shuts down the MT5 connection.

    Sets ``bot_activo`` to 0, which causes :func:`ciclo_trading_recursivo`
    to exit its ``while`` loop on the next iteration, then waits for the
    thread to finish before calling ``mt5.shutdown()``.
    """
    global bot_activo, cuenta_conectada, hilo_motor
    if bot_activo == 0:
        return

    bot_activo = 0
    registrar_log("[SYSTEM] Stopping RPA Engine...")

    # Wait for the thread to exit gracefully (max 3s)
    if hilo_motor and hilo_motor.is_alive():
        hilo_motor.join(timeout=3.0)
    
    mt5.shutdown()
    cuenta_conectada = 0  # Important: Reset so next start forces re-login
    registrar_log("[SYSTEM] RPA Engine stopped.")

def ciclo_trading_recursivo() -> None:
    """Event-driven trading synchronisation loop (runs in a daemon thread).

    **Architecture:** The loop stays connected to the master account at all
    times. Slave accounts are only accessed when a concrete change is detected
    (new position, modification, or closure). After all slave operations are
    completed, the loop switches back to master immediately — no time is
    wasted cycling accounts when nothing has changed.

    **Latency:** When a change is detected, replication to all slaves happens
    in the same iteration with no artificial delay. An idle poll (no changes)
    waits 150ms before re-checking master state.

    The loop exits when :func:`detener_motor_trading` sets ``bot_activo`` to 0.
    """
    global bot_activo, cuenta_conectada, memoria_db, tickets_maestros_abiertos, app_config
    global eq_master_global, bal_master_global, profit_master_global
    global _stat_ciclos, _stat_replicaciones, _stat_ultimo_sync

    POLL_IDLE_S  = 0.15   # 150ms master-only poll when nothing changed
    RECONNECT_S  = 2.0    # wait before retry on master connection loss
    master_login = int(app_config['master']['login'])

    registrar_log("[SYSTEM] ▶ Event-driven replication cycle started.")

    while bot_activo == 1:
        _stat_ciclos += 1

        # ── 1. Ensure active MASTER session ─────────────────────────────────────
        if cuenta_conectada != master_login:
            cuenta_conectada = cambiar_cuenta(app_config['master'], cuenta_conectada)
        if cuenta_conectada == 0:
            registrar_log("[WARN] Master connection lost. Retrying in 2s...")
            time.sleep(RECONNECT_S)
            continue

        # ── 2. Read MASTER state (without account switch) ──────────────────────────
        inf = mt5.account_info()
        if inf:
            eq_master_global     = inf.equity
            bal_master_global    = inf.balance
            profit_master_global = inf.profit

        ops_actuales = obtener_estado_maestro()
        t_acts = [str(op['ticket']) for op in ops_actuales]

        # ── 3. Detect CLOSED operations on master ────────────────────────────
        for t_ant in tickets_maestros_abiertos:
            if t_ant not in t_acts:
                deals = mt5.history_deals_get(position=int(t_ant))
                if deals and len(deals) > 0:
                    beneficio_total = sum(d.profit + d.swap + d.commission + d.fee for d in deals)
                    simbolo  = deals[0].symbol
                    tipo_str = "SELL" if deals[0].type == 1 else "BUY"
                    registro = {
                        "ticket":     t_ant,
                        "symbol":     simbolo,
                        "type":       tipo_str,
                        "profit":     beneficio_total,
                        "time_close": time.time()
                    }
                    agregar_a_historial(registro)
                    signo = "+" if beneficio_total >= 0 else ""
                    registrar_log(f"[ACTION] OP {t_ant} ({tipo_str} {simbolo}) CLOSED. P/L: {signo}${beneficio_total:.2f}")

        tickets_maestros_abiertos = t_acts

        # ── 4. Calculate tasks for slaves ────────────────────────────────────────
        hay_trabajo = 0
        c_ram       = 0
        tareas = {s['id']: [] for s in app_config['slaves']}

        # 4a. New openings or modifications detected on master
        for op in ops_actuales:
            for s in app_config['slaves']:
                s_id = s['id']
                vin  = obtener_vinculo(memoria_db, s_id, op['ticket'])

                if not vin:
                    # Ticket without record — genuinely new operation (opened WHILE the bot is running)
                    tareas[s_id].append({"tipo": "NUEVA", "datos": op, "cfg": s})
                    hay_trabajo = 1
                elif vin['slave_ticket'] == 0:
                    # Pending replication (pre-existing pending order or previous failed opening)
                    tareas[s_id].append({"tipo": "NUEVA", "datos": op, "cfg": s})
                    hay_trabajo = 1
                elif vin['slave_ticket'] == -1:
                    # Pre-existing at startup (MARKET). DO NOT replicate opening.
                    # Only detect SL/TP changes to synchronize them
                    pass
                elif vin['slave_ticket'] > 0:
                    # Already successfully replicated — check if SL/TP/price modification occurred
                    d_sl = abs(op['sl']    - vin['sl'])    > 0.00001
                    d_tp = abs(op['tp']    - vin['tp'])    > 0.00001
                    d_pr = abs(op['price'] - vin['price']) > 0.00001 if op['categoria'] == "PENDIENTE" else False
                    if d_sl or d_tp or d_pr:
                        tareas[s_id].append({"tipo": "MOD", "datos": op, "vinculo": vin})
                        hay_trabajo = 1

        # 4b. Operations closed on master that still have a link on slaves
        for s in app_config['slaves']:
            s_id = s['id']
            if s_id in memoria_db:
                for t_g in list(memoria_db[s_id].keys()):
                    if t_g not in t_acts:
                        datos   = memoria_db[s_id][t_g]
                        t_esc   = datos.get('slave_ticket', 0)
                        if t_esc != 0:
                            tareas[s_id].append({"tipo": "CERRAR", "t_maestro": t_g, "vinculo": datos})
                            hay_trabajo = 1
                        else:
                            memoria_db = eliminar_vinculo(memoria_db, s_id, t_g)
                            c_ram = 1

        # ── 5. Execute tasks on slaves ——— ONLY if there is work ───────────────
        if hay_trabajo == 1:
            for s_cfg in app_config['slaves']:
                s_id  = s_cfg['id']
                
                # Ignore isolated nodes
                if s_cfg.get('aislado', False):
                    continue

                m_tar = tareas[s_id]
                if not m_tar:
                    continue

                # Change to this slave
                cuenta_conectada = cambiar_cuenta(s_cfg, cuenta_conectada)

                if cuenta_conectada == int(s_cfg['login']):
                    s_cfg['fallos_conexion'] = 0 # Reset counter
                    for t in m_tar:
                        ex = 0
                        if   t['tipo'] == "NUEVA":
                            memoria_db, ex = ejecutar_apertura(t['datos'], s_cfg, eq_master_global, memoria_db, registrar_log)
                        elif t['tipo'] == "MOD":
                            memoria_db, ex = ejecutar_modificacion(t['vinculo'], t['datos'], s_id, memoria_db, registrar_log)
                        elif t['tipo'] == "CERRAR":
                            memoria_db, ex = ejecutar_cierre(t['t_maestro'], t['vinculo'], s_id, memoria_db, registrar_log)
                        if ex == 1:
                            c_ram = 1
                else:
                    fallos = s_cfg.get('fallos_conexion', 0) + 1
                    s_cfg['fallos_conexion'] = fallos
                    if fallos >= 3:
                        s_cfg['aislado'] = True
                        registrar_log(f"[CRITICAL] Node {s_id} isolated from the network after multiple failures. Check MT5 credentials.")
                    else:
                        registrar_log(f"[ERROR] Could not connect to node {s_id} (attempt {fallos}/3). Invalid credentials or unreachable server.")

            # Switch back to master IMMEDIATELY after finishing with slaves
            cuenta_conectada = cambiar_cuenta(app_config['master'], cuenta_conectada)

            if c_ram == 1:
                guardar_ram_a_disco(memoria_db)

            _stat_replicaciones += 1
            import datetime
            _stat_ultimo_sync = datetime.datetime.now().strftime("%H:%M:%S")

            # No pause — we re-poll master immediately to detect more cascading changes

        else:
            # No changes: low latency pause before next poll
            if c_ram == 1:
                guardar_ram_a_disco(memoria_db)
            time.sleep(POLL_IDLE_S)


# --- JAVASCRIPT API CLASS ---
class BridgeAPI:
    """JavaScript-to-Python API bridge exposed via pywebview.

    All public methods of this class are callable from the web frontend
    using ``await window.pywebview.api.method_name(args)``. Methods run
    synchronously in the Python main process and their return values are
    automatically serialised to JSON for the JavaScript caller.

    Attributes:
        None (all state is managed via module-level globals).
    """
    def obtener_claves_js(self) -> dict:
        """Returns Supabase credentials to the JavaScript frontend at runtime.

        Credentials are never hardcoded in JS files; they are passed through
        this bridge method after being loaded from the gitignored ``secrets.json``.

        Returns:
            A dict with keys ``url`` and ``key`` containing the Supabase
            project URL and anonymous API key respectively.
        """
        return {"url": URL_NUBE, "key": KEY_NUBE}
        
    def conectar(self, email: str, password: str) -> dict:
        """Authenticates the user against Supabase and starts the trading engine.

        Attempts Supabase email/password authentication, stores the user email
        in an environment variable for session-scoped cloud operations, then
        calls :func:`iniciar_motor_trading`. Returns a structured result so
        the frontend can handle partial failures (e.g., auth OK but MT5 down).

        Args:
            email: The user's Supabase account email address.
            password: The user's Supabase account password.

        Returns:
            A dict with a ``status`` key:

            * ``{'status': 'success', 'email': str}`` — fully operational.
            * ``{'status': 'mt5_error', 'email': str, 'message': str}`` — auth OK, MT5 failed.
            * ``{'status': 'error', 'message': str}`` — Supabase auth failed.
        """
        global supabase, URL_NUBE, KEY_NUBE
        try:
            # 1. We force reading to see if the JSON actually reaches Python
            s_dict = cargar_secrets()
            URL_NUBE = s_dict.get("SUPABASE_URL", "")
            KEY_NUBE = s_dict.get("SUPABASE_KEY", "")
            
            if URL_NUBE == "" or KEY_NUBE == "":
                return {"status": "error", "message": "Python detected the JSON but did not find the 'SUPABASE_URL' keys. Is there an extra comma?"}
            
            # 2. We force the creation of the client to capture URL errors
            if not supabase:
                supabase = create_client(URL_NUBE, KEY_NUBE)
                
            # 3. We attempt Login
            res = supabase.auth.sign_in_with_password({"email": email, "password": password})
            os.environ["PROPSYNC_USER_EMAIL"] = res.user.email
            
            # 4. We attempt to start the trading engine
            resultado_motor = iniciar_motor_trading()
            
            if resultado_motor["status"] == "ok":
                return {"status": "success", "email": res.user.email}
            elif resultado_motor["status"] == "mt5_error":
                # Cloud auth OK but MT5 failed — inform the frontend
                return {
                    "status": "mt5_error",
                    "email": res.user.email,
                    "message": resultado_motor["message"]
                }
            else:
                # config_error or other
                return {
                    "status": "mt5_error",
                    "email": res.user.email,
                    "message": resultado_motor.get("message", "Engine configuration error.")
                }
                
        except Exception as e:
            return {"status": "error", "message": f"DEBUG ROOT: {str(e)}"}

    def registrar(self, email: str, password: str) -> dict:
        """Registers a new user account in Supabase Auth.

        Args:
            email: The desired email address for the new account.
            password: The desired password (Supabase enforces a minimum length).

        Returns:
            ``{'status': 'success'}`` on success, or
            ``{'status': 'error', 'message': str}`` on failure.
        """
        global supabase, URL_NUBE, KEY_NUBE
        try:
            if not supabase:
                s_dict = cargar_secrets()
                supabase = create_client(s_dict.get("SUPABASE_URL", ""), s_dict.get("SUPABASE_KEY", ""))
                
            supabase.auth.sign_up({"email": email, "password": password})
            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "message": f"DEBUG ROOT: {str(e)}"}

    def apagar_motor(self) -> str:
        """Stops the trading engine from the frontend.

        Returns:
            The string ``'ok'`` after :func:`detener_motor_trading` completes.
        """
        detener_motor_trading()
        return "ok"
    
    def encender_motor(self) -> dict:
        """Restarts the trading engine without requiring re-authentication.

        Useful when the user stops the service temporarily and wants to
        resume without logging out. Calls :func:`iniciar_motor_trading`
        and passes its result dict directly to the frontend.

        Returns:
            The result dict from :func:`iniciar_motor_trading`.
        """
        resultado = iniciar_motor_trading()
        return resultado

    def obtener_configuracion(self) -> dict:
        """Returns the current application configuration to the frontend.

        Returns:
            The ``app_config`` dict (master + slaves), or a default empty
            structure if no configuration has been loaded.
        """
        global app_config
        if not app_config:
            return {"master": {}, "slaves": []}
        return app_config
    
    def obtener_telemetria(self) -> dict:
        """Returns live telemetry data for the dashboard.

        Combines the closed trade history from disk with the current
        floating P&L metrics captured from the last trading loop iteration.

        Returns:
            A dict with keys:

            * ``historial``: list of closed trade records.
            * ``flotante``: dict with ``equity``, ``balance``, ``profit``
              floats from the master account.
        """
        try:
            historial = cargar_historial()
            return {
                "historial": historial,
                "flotante": {
                    "equity": eq_master_global,
                    "balance": bal_master_global,
                    "profit": profit_master_global
                }
            }
        except Exception as e:
            return {"historial": [], "flotante": {"equity": 0, "balance": 0, "profit": 0}}

    def guardar_maestra(self, datos_master: dict) -> str:
        """Saves the master account configuration and syncs it to the cloud.

        Updates the in-memory ``app_config`` with the new master parameters,
        persists to disk via :func:`guardar_credenciales`, and triggers a
        cloud config upload via :meth:`db_push_user_config`.

        Args:
            datos_master: A dict with master account fields
                (``login``, ``password``, ``server``, ``initial_balance``).

        Returns:
            The string ``'ok'`` on success.
        """
        global app_config
        app_config['master'] = datos_master
        guardar_credenciales(app_config)
        self.db_push_user_config()
        registrar_log("[INFO] Main Master configuration updated and sent to the cloud.")
        return "ok"

    def guardar_esclava(self, datos_slave: dict) -> str:
        """Adds or updates a slave node in the configuration.

        If a slave with the same ``id`` already exists, it is replaced.
        Otherwise, the new slave is appended to the list. Persists to disk
        and syncs to the cloud.

        Args:
            datos_slave: A dict with slave node fields
                (``id``, ``login``, ``password``, ``server``, ``risk_factor``,
                ``initial_balance``).

        Returns:
            The string ``'ok'`` on success.
        """
        global app_config
        ind_actualizar = -1
        for i in range(len(app_config['slaves'])):
            if app_config['slaves'][i]['id'] == datos_slave['id']:
                ind_actualizar = i
                
        if ind_actualizar != -1:
            app_config['slaves'][ind_actualizar] = datos_slave
            registrar_log(f"[INFO] Slave node '{datos_slave['id']}' updated.")
        else:
            app_config['slaves'].append(datos_slave)
            registrar_log(f"[INFO] Slave node '{datos_slave['id']}' attached to the network.")
            
        guardar_credenciales(app_config)
        self.db_push_user_config()
        return "ok"

    def eliminar_esclava(self, id_borrar: str) -> str:
        """Removes a slave node from the configuration.

        Filters the slave list to exclude the node with the given ID and
        persists the updated configuration to disk.

        Args:
            id_borrar: The unique identifier of the slave node to remove.

        Returns:
            The string ``'ok'`` on success.
        """
        global app_config
        n_lista = []
        for s in app_config['slaves']:
            if s['id'] != id_borrar: n_lista.append(s)
        app_config['slaves'] = n_lista
        guardar_credenciales(app_config)
        registrar_log(f"[INFO] Node '{id_borrar}' removed from the network.")
        return "ok"

    def db_get_prop_firms(self) -> list:
        """Fetches all prop firm records from Supabase via the database module.

        Returns:
            A list of prop firm dicts, or an empty list if unavailable.
        """
        from modules.database import fetch_prop_firms
        return fetch_prop_firms()

    def db_add_prop_firm(self, firm_data: dict) -> dict:
        """Inserts a new prop firm record into Supabase.

        Args:
            firm_data: The prop firm configuration dict.

        Returns:
            A result dict with ``status`` and optional ``data`` or ``message``.
        """
        from modules.database import add_prop_firm
        return add_prop_firm(firm_data)

    def verificar_cuenta_mt5(self, login: int, password: str, server: str) -> dict:
        """Validates MT5 credentials on-demand from the configuration panel.

        Calls :func:`verificar_credenciales_mt5` and returns the structured
        result so the frontend can display a precise, actionable error message
        (e.g., 'wrong password' vs 'server not found' vs 'terminal not running').

        Args:
            login: Numeric MT5 account number.
            password: Plaintext account password.
            server: Broker server name.

        Returns:
            ``{'valido': True}`` on success, or
            ``{'valido': False, 'tipo': str, 'mensaje': str}`` on failure.
        """
        resultado = verificar_credenciales_mt5(
            login=int(login), password=password, server=server
        )
        if resultado['valido']:
            registrar_log(f"[SYSTEM] ✓ Manual verification: account {login} valid on {server}.")
        else:
            registrar_log(f"[CREDENTIAL] ✗ Manual verification failed ({resultado['tipo']}): {resultado['mensaje']}")
        return resultado

    def obtener_estado_motor(self) -> dict:
        """Returns live engine statistics for the terminal status bar.

        Returns:
            A dict with keys ``activo`` (bool), ``ciclos`` (int),
            ``replicaciones`` (int), ``errores`` (int), ``ultimo_sync`` (str).
        """
        return {
            "activo":        bot_activo == 1,
            "ciclos":        _stat_ciclos,
            "replicaciones": _stat_replicaciones,
            "errores":       _stat_errores,
            "ultimo_sync":   _stat_ultimo_sync
        }

    def guardar_logs_en_archivo(self, texto_logs: str) -> dict:
        """Opens a save file dialog and writes the provided log text to disk.

        Used as a fallback for the JavaScript 'Exportar' button to ensure
        reliable file saving across all pywebview platforms.

        Args:
            texto_logs: The full block of log text to be saved.

        Returns:
            A result dict with a ``status`` key ('success' or 'error').
        """
        try:
            # pywebview has a built-in file dialog
            file_path = window.create_file_dialog(
                webview.SAVE_DIALOG, 
                directory=os.path.expanduser("~"), 
                save_filename='PropSync_Terminal_Logs.txt'
            )
            if file_path:
                # If the list of paths is returned, take the first one
                target = file_path[0] if isinstance(file_path, (list, tuple)) else file_path
                with open(target, 'w', encoding='utf-8') as f:
                    f.write(texto_logs)
                registrar_log(f"[SYSTEM] Logs exported successfully to: {target}")
                return {"status": "success"}
            return {"status": "cancelled"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def db_push_user_config(self) -> None:
        """Uploads the current ``app_config`` to Supabase for the authenticated user.

        Uses the ``PROPSYNC_USER_EMAIL`` environment variable set during
        :meth:`conectar` to identify the target cloud record. Silently skips
        if no user is currently authenticated.
        """
        from modules.database import upload_user_config
        import os
        email = os.environ.get("PROPSYNC_USER_EMAIL", "")
        if email != "":
            upload_user_config(email, app_config)
            registrar_log("[CLOUD] Edge configuration synced to Supabase.")

# --- LAUNCH ---
if __name__ == "__main__":
    app_config = cargar_credenciales()
    config_null = 0
    if not app_config: config_null = 1
        
    if config_null == 1:
        app_config = {
            "master": {"login": "", "password": "", "server": "", "initial_balance": 100000}, 
            "slaves": []
        }
        
    api = BridgeAPI()
    
    # Create and launch the local web window
    window = webview.create_window(
            'PropSync Edge Engine', 
            'web_local/index.html', 
            js_api=api,
            width=1280,
            height=800,
            resizable=True,
            min_size=(900, 600)
        )
    
    webview.start()