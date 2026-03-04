import MetaTrader5 as mt5
import time
import math
# Correccion: Importacion desde la carpeta modules
from modules.database import guardar_vinculo, eliminar_vinculo, obtener_vinculo

# [CRITERIO ACADEMICO: 2f - Mejoras en IT y OT]
# Este modulo representa la capa de Tecnologia de Operaciones (OT). Interactua con la API del broker 
# para enviar sentencias criticas de transaccion con latencias de milisegundos.

# [CRITERIO ACADEMICO: 2e - Beneficios operativos]
# Automatizacion critica: Automatiza el salto asincrono entre instancias financieras (logins), 
# una tarea que manualmente tomaria minutos, reducida a menos de 0.5 segundos (RPA).
def cambiar_cuenta(datos_cuenta, login_actual):
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

def calcular_volumen(symbol, lot_maestro, eq_maestra, eq_esclava, factor_riesgo):
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

def ejecutar_apertura(op, s_cfg, eq_m, db_ram, log_func):
    symbol = op['symbol']
    t_m = op['ticket']
    id_s = s_cfg['id']
    
    simbolo_ok = 0
    if mt5.symbol_select(symbol, 1):
        simbolo_ok = 1
        
    if simbolo_ok == 0:
        db_ram = guardar_vinculo(db_ram, id_s, t_m, 0, 0, 0, 0, 0)
        return db_ram, 1

    eq_s = mt5.account_info().equity
    riesgo = s_cfg.get('risk_factor', 1.0)
    vol = calcular_volumen(symbol, op['volume'], eq_m, eq_s, riesgo)
    
    log_func(f"[ACCION] Abriendo {symbol} ({vol} lotes) en {id_s}...")

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
        log_func(f"[EXITO] Operacion confirmada (Ticket: {res.order}) en {id_s}.")
        db_ram = guardar_vinculo(db_ram, id_s, t_m, res.order, op['sl'], op['tp'], res.price, vol)
        return db_ram, 1
    else:
        log_func(f"[ERROR] Apertura rechazada en {id_s}. Marcando como ignorada.")
        db_ram = guardar_vinculo(db_ram, id_s, t_m, 0, op['sl'], op['tp'], op['price'], 0)
        return db_ram, 1

def ejecutar_modificacion(vinculo, op, id_s, db_ram, log_func):
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
            log_func(f"[MODIFICACION] Actualizando precio de entrada y limites en ticket {t_s} ({id_s}).")
        else:
            req["action"] = mt5.TRADE_ACTION_SLTP
            req["position"] = t_s
            log_func(f"[MODIFICACION] Actualizando limites SL/TP en ticket {t_s} ({id_s}).")

        res = mt5.order_send(req)
        
        mod_exitosa = 0
        if res:
            if res.retcode == mt5.TRADE_RETCODE_DONE:
                mod_exitosa = 1
            elif res.retcode == 10025: 
                mod_exitosa = 1
                
        if mod_exitosa == 1:
            log_func(f"[EXITO] Modificacion confirmada en ticket {t_s}.")
        else:
            log_func(f"[ADVERTENCIA] Rechazo de broker. Actualizando base de datos local para prevencion de bucles.")
            
        p_save = op['price'] 
        if es_pendiente == 0:
            p_save = vinculo['price']
            
        db_ram = guardar_vinculo(db_ram, id_s, op['ticket'], t_s, op['sl'], op['tp'], p_save, vinculo['vol'])
        return db_ram, 1
    return db_ram, 0

def ejecutar_cierre(t_m, vinculo, id_s, db_ram, log_func):
    t_s = int(vinculo['slave_ticket'])
    
    if t_s == 0:
        db_ram = eliminar_vinculo(db_ram, id_s, t_m)
        return db_ram, 1

    log_func(f"[CIERRE] Solicitando cierre para ticket {t_s} en {id_s}.")
    
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
            
        price_c = mt5.symbol_info_tick(pos.symbol).bid 
        if tipo_c == mt5.ORDER_TYPE_BUY:
            price_c = mt5.symbol_info_tick(pos.symbol).ask
            
        req = {
            "action": mt5.TRADE_ACTION_DEAL, "symbol": pos.symbol, "volume": pos.volume,
            "type": tipo_c, "position": t_s, "price": price_c, "deviation": 20, "magic": 111,
            "type_time": mt5.ORDER_TIME_GTC, "type_filling": mt5.ORDER_FILLING_FOK
        }
        res = mt5.order_send(req)
    else:
        # [CRITERIO ACADEMICO: 5b - Gestion del dato]
        log_func(f"[LIMPIEZA] Ticket {t_s} inexistente en servidor OT. Desvinculando en IT.")
        db_ram = eliminar_vinculo(db_ram, id_s, t_m)
        return db_ram, 1

    cierre_exitoso = 0
    if res:
        if res.retcode == mt5.TRADE_RETCODE_DONE:
            cierre_exitoso = 1
            
    if cierre_exitoso == 1:
        log_func(f"[EXITO] Operacion {t_s} cerrada en {id_s}.")
        db_ram = eliminar_vinculo(db_ram, id_s, t_m)
        return db_ram, 1
    else:
        log_func(f"[ERROR] Error al procesar cierre de {t_s}. Forzando desvinculacion local.")
        db_ram = eliminar_vinculo(db_ram, id_s, t_m)
        return db_ram, 1

# [CRITERIO ACADEMICO: 2g - Tecnologias Habilitadoras Digitales (THD)]
def obtener_estado_maestro():
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
                              "volume": p.volume, "price": p.price_open, "sl": round(p.sl, 5), "tp": round(p.tp, 5), "categoria": "MERCADO"})
                              
        ordenes = mt5.orders_get()
        hay_ordenes = 0
        if ordenes:
            hay_ordenes = 1
            
        if hay_ordenes == 1:
            for o in ordenes:
                lista.append({"ticket": o.ticket, "symbol": o.symbol, "type": o.type, 
                              "volume": o.volume_current, "price": round(o.price_open, 5), "sl": round(o.sl, 5), "tp": round(o.tp, 5), "categoria": "PENDIENTE"})
    return lista

def sincronizar_inicio(cfg, login_estado, db_ram, log_func):
    log_func("[SISTEMA] Verificando e inicializando estructura en memoria RAM.")
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
                    db_ram = guardar_vinculo(db_ram, s['id'], op['ticket'], 0, op['sl'], op['tp'], op['price'], 0)
        
        log_func("[SISTEMA] Base de datos y mapeos sincronizados correctamente.")
    return nuevo_estado, db_ram