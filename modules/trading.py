"""
MetaTrader 5 RPA trading engine — Operational Technology (OT) layer.

This module implements the Robotic Process Automation core of PropSync Manager.
It interacts directly with the MetaTrader 5 broker API to execute, modify, and
close positions on slave accounts in response to events on the master account.

**Latency target:** All MT5 API calls complete within 50–200ms.

**Account switching model:** MT5 supports only one active login at a time.
``cambiar_cuenta`` manages the login state and switches accounts as needed
between master reads and slave writes.
"""
import MetaTrader5 as mt5
import time
import math
from modules.database import guardar_vinculo, eliminar_vinculo, obtener_vinculo

# ─────────────────────────────────────────────────────────────────────────────
# Error code → human-readable message mapping
# ─────────────────────────────────────────────────────────────────────────────
_MT5_ERROR_MAP = {
    # Terminal / connection
    -1:  ("terminal",    "MetaTrader 5 is not running. Start it and try again."),
    -2:  ("terminal",    "MetaTrader 5 not found. Check the installation."),
    -5:  ("red",         "No connection to the broker server. Check your network and try again."),
    -6:  ("servidor",    "Cannot contact the specified server. Check the server name."),
    # Auth
    10013: ("credencial", "Login request rejected by server (invalid credentials)."),
    10014: ("credencial", "Invalid volume — possibly incorrect credentials."),
    10018: ("cuenta",    "Market is closed or the account does not have trading permissions."),
}

def interpretar_error_mt5() -> dict:
    """Reads ``mt5.last_error()`` and returns a structured error dict.

    Returns:
        A dict with keys:

        * ``codigo`` (int): raw MT5 error code.
        * ``tipo`` (str): category — ``'terminal'``, ``'red'``, ``'servidor'``,
          ``'credencial'``, ``'cuenta'``, or ``'desconocido'``.
        * ``mensaje`` (str): human-readable Spanish description.
    """
    err = mt5.last_error()
    if not err:
        return {"codigo": -99, "tipo": "desconocido", "mensaje": "Unknown MT5 error (no details available)."}
    code, desc = err[0], err[1] if len(err) > 1 else ""
    if code in _MT5_ERROR_MAP:
        tipo, mensaje = _MT5_ERROR_MAP[code]
    else:
        desc_low = desc.lower()
        if "password" in desc_low or "invalid account" in desc_low or "authorization" in desc_low:
            tipo, mensaje = "credencial", f"Incorrect password or account number. (MT5: {desc})"
        elif "connect" in desc_low or "network" in desc_low:
            tipo, mensaje = "red", f"Network failure connecting to server. (MT5: {desc})"
        elif "server" in desc_low:
            tipo, mensaje = "servidor", f"Server not found or unreachable. (MT5: {desc})"
        else:
            tipo, mensaje = "desconocido", f"MT5 Error {code}: {desc}"
    return {"codigo": code, "tipo": tipo, "mensaje": mensaje}


def verificar_credenciales_mt5(login: int, password: str, server: str) -> dict:
    """Validates MT5 account credentials without starting the replication loop.

    Args:
        login: Numeric MT5 account number.
        password: Account password (plaintext).
        server: Broker server name (e.g., ``'ICMarkets-Live'``).

    Returns:
        A dict with keys ``valido`` (bool), ``codigo``, ``tipo``, ``mensaje``.
    """
    if not mt5.initialize():
        err = interpretar_error_mt5()
        return {"valido": False, "codigo": err["codigo"], "tipo": err["tipo"], "mensaje": err["mensaje"]}

    ok = mt5.login(login=login, password=password, server=server)
    if ok:
        return {"valido": True, "codigo": 0, "tipo": "", "mensaje": ""}
    else:
        err = interpretar_error_mt5()
        if err["tipo"] == "desconocido" or err["codigo"] == 0:
            info_check = mt5.account_info()
            if info_check is None:
                err["tipo"] = "credencial"
                err["mensaje"] = (f"Account number {login} not recognized on server '{server}', "
                                  f"or incorrect password.")
        return {"valido": False, "codigo": err["codigo"], "tipo": err["tipo"], "mensaje": err["mensaje"]}


# [CRITERIO ACADEMICO: 2f - Mejoras en IT y OT]
# Este modulo representa la capa de Tecnologia de Operaciones (OT). Interactua con la API del broker
# para enviar sentencias criticas de transaccion con latencias de milisegundos.

# [CRITERIO ACADEMICO: 2e - Beneficios operativos]
# Automatizacion critica: Automatiza el salto asincrono entre instancias financieras (logins),
# una tarea que manualmente tomaria minutos, reducida a menos de 0.5 segundos (RPA).
def cambiar_cuenta(datos_cuenta: dict, login_actual: int) -> int:
    """Switches the active MT5 session to the specified account.

    Args:
        datos_cuenta: Dict with ``login``, ``password``, ``server``.
        login_actual: Currently logged-in account number (0 if none).

    Returns:
        The account number of the successfully logged-in account, or 0 on failure.
    """
    login_deseado = int(datos_cuenta['login'])
    estado_login = 0

    if login_actual == login_deseado:
        estado_login = login_actual

    if estado_login == 0:
        inicializado = 0
        if mt5.initialize():
            inicializado = 1

        if inicializado == 1:
            exito = mt5.login(login=login_deseado, password=datos_cuenta['password'], server=datos_cuenta['server'])
            if exito:
                time.sleep(0.3)
                estado_login = login_deseado

    return estado_login


def calcular_volumen(symbol: str, lot_maestro: float, eq_maestra: float,
                     eq_esclava: float, factor_riesgo: float) -> float:
    """Calculates the proportional lot size for a slave account.

    Args:
        symbol: The trading instrument symbol (e.g., ``'EURUSD'``).
        lot_maestro: The lot size of the master position.
        eq_maestra: The current equity of the master account.
        eq_esclava: The current equity of the slave account.
        factor_riesgo: A user-defined multiplier.

    Returns:
        The normalised lot size as a float.
    """
    if eq_maestra == 0:
        return lot_maestro

    ratio = eq_esclava / eq_maestra
    lot_calculado = lot_maestro * ratio * factor_riesgo

    info = mt5.symbol_info(symbol)
    if not info:
        return lot_maestro

    step = info.volume_step
    lot_normalizado = round(math.floor(lot_calculado / step) * step, 2)

    if lot_normalizado < info.volume_min:
        lot_normalizado = info.volume_min
    if lot_normalizado > info.volume_max:
        lot_normalizado = info.volume_max

    return lot_normalizado


def ejecutar_apertura(op: dict, s_cfg: dict, eq_m: float,
                      db_ram: dict, log_func) -> tuple:
    """Replicates the opening of a master position on a slave account.

    Args:
        op: Master operation dict (symbol, ticket, type, volume, price, sl, tp, categoria).
        s_cfg: Slave node config dict (id, login, password, server, risk_factor).
        eq_m: Master account equity.
        db_ram: Current in-memory trade map.
        log_func: Logging callable.

    Returns:
        Tuple ``(db_ram, changed)`` — changed is 1 if a write occurred.
    """
    symbol = op['symbol']
    t_m = op['ticket']
    id_s = s_cfg['id']

    simbolo_ok = 0
    if mt5.symbol_select(symbol, 1):
        simbolo_ok = 1

    if simbolo_ok == 0:
        db_ram = guardar_vinculo(db_ram, id_s, t_m, 0, 0, 0, 0, 0)
        return db_ram, 1

    inf = mt5.account_info()
    eq_s = 0.0
    if inf:
        eq_s = inf.equity

    riesgo = s_cfg.get('risk_factor', 1.0)
    vol = calcular_volumen(symbol, op['volume'], eq_m, eq_s, riesgo)

    log_func(f"[ACTION] Opening {symbol} ({vol} lots) on {id_s}...")

    tipo = op['type']
    precio = op['price']
    action = mt5.TRADE_ACTION_PENDING

    es_mercado = 0
    if op['categoria'] == "MERCADO":
        es_mercado = 1

    if es_mercado == 1:
        tick = mt5.symbol_info_tick(symbol)
        if tick:
            if tipo == 0:
                tipo = mt5.ORDER_TYPE_BUY
                precio = tick.ask
            else:
                tipo = mt5.ORDER_TYPE_SELL
                precio = tick.bid
            action = mt5.TRADE_ACTION_DEAL

    # [CRITERIO ACADEMICO: 5i - Seguridad y proteccion]
    req = {
        "action": action, "symbol": symbol, "volume": vol,
        "type": tipo, "price": precio,
        "sl": op['sl'], "tp": op['tp'],
        "deviation": 20, "magic": 111,
        "comment": f"Copy-{t_m}", "type_time": mt5.ORDER_TIME_GTC, "type_filling": mt5.ORDER_FILLING_FOK,
    }

    res = mt5.order_send(req)
    apertura_exitosa = 0
    if res:
        if res.retcode == mt5.TRADE_RETCODE_DONE:
            apertura_exitosa = 1

    if apertura_exitosa == 1:
        log_func(f"[SUCCESS] Operation confirmed (Ticket: {res.order}) on {id_s}.")
        db_ram = guardar_vinculo(db_ram, id_s, t_m, res.order, op['sl'], op['tp'], res.price, vol)
        return db_ram, 1
    else:
        if res is None:
            err = mt5.last_error()
            log_func(f"[ERROR] Open rejected on {id_s} (no response from broker, internal error: {err}).")
        else:
            log_func(f"[ERROR] Open rejected on {id_s} (MT5 retcode {res.retcode}: {res.comment}).")
        db_ram = guardar_vinculo(db_ram, id_s, t_m, 0, op['sl'], op['tp'], op['price'], 0)
        return db_ram, 1


def ejecutar_modificacion(vinculo: dict, op: dict, id_s: str,
                          db_ram: dict, log_func) -> tuple:
    """Replicates a SL/TP (or pending price) modification to a slave order.

    Args:
        vinculo: Current trade link record from the RAM map.
        op: Updated master operation dict.
        id_s: Slave node identifier.
        db_ram: Current in-memory trade map.
        log_func: Logging callable.

    Returns:
        Tuple ``(db_ram, changed)`` — changed is 1 if a write occurred.
    """
    t_s = int(vinculo['slave_ticket'])
    ticket_valido = 0
    if t_s != 0:
        ticket_valido = 1

    if ticket_valido == 1:
        req = {"symbol": op['symbol'], "sl": op['sl'], "tp": op['tp']}

        es_pendiente = 0
        if op['categoria'] == "PENDIENTE":
            es_pendiente = 1

        if es_pendiente == 1:
            req["action"] = mt5.TRADE_ACTION_MODIFY
            req["order"] = t_s
            req["price"] = op['price']
            log_func(f"[MODIFICATION] Updating entry price and limits on ticket {t_s} ({id_s}).")
        else:
            req["action"] = mt5.TRADE_ACTION_SLTP
            req["position"] = t_s
            log_func(f"[MODIFICATION] Updating SL/TP limits on ticket {t_s} ({id_s}).")

        res = mt5.order_send(req)

        mod_exitosa = 0
        if res:
            if res.retcode == mt5.TRADE_RETCODE_DONE:
                mod_exitosa = 1
            elif res.retcode == 10025:
                mod_exitosa = 1

        if mod_exitosa == 1:
            log_func(f"[SUCCESS] Modification confirmed on ticket {t_s}.")
        else:
            log_func(f"[WARNING] Broker rejection. Updating local database to prevent loops.")

        p_save = op['price']
        if es_pendiente == 0:
            p_save = vinculo['price']

        db_ram = guardar_vinculo(db_ram, id_s, op['ticket'], t_s, op['sl'], op['tp'], p_save, vinculo['vol'])
        return db_ram, 1
    return db_ram, 0


def ejecutar_cierre(t_m: str, vinculo: dict, id_s: str,
                    db_ram: dict, log_func) -> tuple:
    """Closes or removes a slave position when its master counterpart is closed.

    Args:
        t_m: Master ticket number as string (RAM map key).
        vinculo: Trade link record for this master ticket.
        id_s: Slave node identifier.
        db_ram: Current in-memory trade map.
        log_func: Logging callable.

    Returns:
        Tuple ``(db_ram, changed)`` — changed is always 1.
    """
    t_s = int(vinculo['slave_ticket'])

    # If the slave ticket is non‑positive (0 means never opened, -1 is sentinel for pre‑existing master position),
    # we should simply unlink the record without attempting any MT5 call that would raise an overflow.
    if t_s <= 0:
        db_ram = eliminar_vinculo(db_ram, id_s, t_m)
        log_func(f"[CLEANUP] Ticket {t_s} invalid or pre-existing, unlinking locally.")
        return db_ram, 1

    log_func(f"[CLOSE] Requesting close for ticket {t_s} on {id_s}.")

    es_orden = mt5.orders_get(ticket=t_s)
    es_pos = mt5.positions_get(ticket=t_s)

    res = None
    es_tipo_orden = 0
    es_tipo_posicion = 0

    if es_orden:
        es_tipo_orden = 1
    elif es_pos:
        es_tipo_posicion = 1

    if es_tipo_orden == 1:
        res = mt5.order_send({"action": mt5.TRADE_ACTION_REMOVE, "order": t_s})
    elif es_tipo_posicion == 1:
        pos = es_pos[0]
        tipo_c = mt5.ORDER_TYPE_SELL
        if pos.type == mt5.ORDER_TYPE_SELL:
            tipo_c = mt5.ORDER_TYPE_BUY

        tick_info = mt5.symbol_info_tick(pos.symbol)
        price_c = 0.0
        if tick_info:
            price_c = tick_info.bid
            if tipo_c == mt5.ORDER_TYPE_BUY:
                price_c = tick_info.ask

        req = {
            "action": mt5.TRADE_ACTION_DEAL, "symbol": pos.symbol, "volume": pos.volume,
            "type": tipo_c, "position": t_s, "price": price_c, "deviation": 20, "magic": 111,
            "type_time": mt5.ORDER_TIME_GTC, "type_filling": mt5.ORDER_FILLING_FOK
        }
        res = mt5.order_send(req)
    else:
        # [CRITERIO ACADEMICO: 5b - Gestion del dato]
        log_func(f"[CLEANUP] Ticket {t_s} does not exist on OT server. Unlinking in IT.")
        db_ram = eliminar_vinculo(db_ram, id_s, t_m)
        return db_ram, 1

    cierre_exitoso = 0
    if res:
        if res.retcode == mt5.TRADE_RETCODE_DONE:
            cierre_exitoso = 1

    if cierre_exitoso == 1:
        log_func(f"[SUCCESS] Operation {t_s} closed on {id_s}.")
        db_ram = eliminar_vinculo(db_ram, id_s, t_m)
        return db_ram, 1
    else:
        if res is None:
            err = mt5.last_error()
            log_func(f"[ERROR] Error closing {t_s} (internal error: {err}). Unlinking locally.")
        else:
            log_func(f"[ERROR] Error closing {t_s} (MT5 retcode {res.retcode}: {res.comment}). Unlinking.")
        db_ram = eliminar_vinculo(db_ram, id_s, t_m)
        return db_ram, 1


# [CRITERIO ACADEMICO: 2g - Tecnologias Habilitadoras Digitales (THD)]
def obtener_estado_maestro() -> list:
    """Retrieves all currently open positions and pending orders from the master account.

    Returns:
        List of operation dicts with keys: ticket, symbol, type, volume, price, sl, tp, categoria.
        Returns empty list if the terminal is not connected.
    """
    lista = []
    t_info = mt5.terminal_info()
    terminal_ok = 0
    if t_info:
        if t_info.connected:
            terminal_ok = 1

    if terminal_ok == 1:
        posiciones = mt5.positions_get()
        hay_posiciones = 0
        if posiciones:
            hay_posiciones = 1

        if hay_posiciones == 1:
            for p in posiciones:
                lista.append({"ticket": p.ticket, "symbol": p.symbol, "type": p.type,
                              "volume": p.volume, "price": p.price_open,
                              "sl": round(p.sl, 5), "tp": round(p.tp, 5), "categoria": "MERCADO"})

        ordenes = mt5.orders_get()
        hay_ordenes = 0
        if ordenes:
            hay_ordenes = 1

        if hay_ordenes == 1:
            for o in ordenes:
                lista.append({"ticket": o.ticket, "symbol": o.symbol, "type": o.type,
                              "volume": o.volume_current, "price": round(o.price_open, 5),
                              "sl": round(o.sl, 5), "tp": round(o.tp, 5), "categoria": "PENDIENTE"})
    return lista


def sincronizar_inicio(cfg: dict, login_estado: int, db_ram: dict, log_func) -> tuple:
    """Initialises the RAM trade map by cross-referencing the current master state.

    Called once when the trading engine starts to prevent duplicate opens on
    first iteration.

    Args:
        cfg: Full application configuration dict (master + slaves).
        login_estado: Current MT5 login state (0 if not connected).
        db_ram: Existing in-memory trade map.
        log_func: Logging callable.

    Returns:
        Tuple ``(login_estado, db_ram)`` with updated values.
    """
    log_func("[SYSTEM] Verifying and initializing RAM structure.")
    nuevo_estado = cambiar_cuenta(cfg['master'], login_estado)

    estado_ok = 0
    if nuevo_estado != 0:
        estado_ok = 1

    if estado_ok == 1:
        ops = obtener_estado_maestro()
        for op in ops:
            for s in cfg['slaves']:
                vinculo_actual = obtener_vinculo(db_ram, s['id'], op['ticket'])
                vinculo_nulo = 0
                if not vinculo_actual:
                    vinculo_nulo = 1
                if vinculo_nulo == 1:
                    # Pre-existing MARKET positions: mark with -1 so the loop
                    # knows they existed before startup and must NOT be replicated.
                    # Pre-existing PENDING orders: mark with 0 so they WILL be
                    # replicated (user requirement).
                    if op['categoria'] == "MERCADO":
                        sentinel = -1   # "already open, skip replication"
                    else:
                        sentinel = 0    # "pending order, replicate it"
                    db_ram = guardar_vinculo(db_ram, s['id'], op['ticket'], sentinel, op['sl'], op['tp'], op['price'], 0)

        log_func("[SYSTEM] Database and maps synced successfully.")
    return nuevo_estado, db_ram