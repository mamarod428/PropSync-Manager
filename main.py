import MetaTrader5 as mt5
import time

from modules.config import cargar_credenciales
from modules.database import cargar_mapa_a_ram, guardar_ram_a_disco, cargar_historial, agregar_a_historial, obtener_vinculo, eliminar_vinculo
from modules.trading import cambiar_cuenta, obtener_estado_maestro, sincronizar_inicio, ejecutar_apertura, ejecutar_modificacion, ejecutar_cierre
from modules.interfaz import PropSyncUI

# --- VARIABLES GLOBALES DE ESTADO ---
app = None
bot_activo = 0
cuenta_conectada = 0
memoria_db = {}
tickets_maestros_abiertos = []

# [CRITERIO ACADEMICO: 2f - Integracion IT y OT]
# Esta funcion actua como el puente de inicializacion entre la capa de presentacion (IT) 
# y la capa de ejecucion financiera en el servidor del broker (OT).
def iniciar_bot():
    global bot_activo, cuenta_conectada, memoria_db, tickets_maestros_abiertos
    
    c_valida = 0
    if app.config:
        if 'master' in app.config and app.config['master']['login'] != "": 
            c_valida = 1
            
    if c_valida == 0:
        app.notificar("[ERROR] Parametros de cuenta Maestra ausentes.")
        return

    ini = 0
    if mt5.initialize(): ini = 1
    
    if ini == 1:
        bot_activo = 1
        app.set_modo_ejecucion(1)
        
        app.notificar("[SISTEMA] Inicializando rutinas de sincronizacion en red...")
        
        # [CRITERIO ACADEMICO: 5b - Ciclo de vida del dato (Generacion/Lectura)]
        # Se carga el estado guardado del disco a la memoria RAM para operar sin latencia de disco.
        memoria_db = cargar_mapa_a_ram()
        cuenta_conectada, memoria_db = sincronizar_inicio(app.config, cuenta_conectada, memoria_db, app.notificar)
        guardar_ram_a_disco(memoria_db)
        
        ops_iniciales = obtener_estado_maestro()
        tickets_maestros_abiertos = []
        for op in ops_iniciales:
            tickets_maestros_abiertos.append(str(op['ticket']))
            
        historial_guardado = cargar_historial()
        app.tab_stats.actualizar_datos(historial_guardado)
        
        ciclo_trading()
    else:
        app.notificar("[ERROR] MetaTrader 5 no ha podido iniciar sesion.")

def detener_bot():
    global bot_activo
    bot_activo = 0
    app.set_modo_ejecucion(0)
    app.notificar("[SISTEMA] Servicio detenido por el usuario.")
    mt5.shutdown()

# [CRITERIO ACADEMICO: 2g - Tecnologias Habilitadoras Digitales (RPA)]
# Este bucle es el nucleo de la automatizacion robotica de procesos. Emula el comportamiento humano
# de revisar cuentas, cruzar datos y ejecutar ordenes, pero de forma recurrente cada 500ms.
def ciclo_trading():
    global bot_activo, cuenta_conectada, memoria_db, tickets_maestros_abiertos
    
    ej = 0
    if bot_activo == 1: ej = 1
    
    if ej == 1:
        cuenta_conectada = cambiar_cuenta(app.config['master'], cuenta_conectada)

        c_ok = 0
        if cuenta_conectada != 0: c_ok = 1
        
        if c_ok == 1:
            inf = mt5.account_info()
            if inf: 
                app.eq_master = inf.equity
                app.bal_master = inf.balance
                app.profit_master = inf.profit
                app.margin_master = inf.margin_level
            
            ops_actuales = obtener_estado_maestro()
            t_acts = []
            for op in ops_actuales: t_acts.append(str(op['ticket']))

            # --- DETECCION DE CIERRES Y DIRECCION PARA ESTADISTICAS ---
            # [CRITERIO ACADEMICO: 5b - Integridad y Trazabilidad]
            # Se detecta el momento exacto en que un dato "vivo" pasa a ser "historico" 
            # y se registra inmutablemente para auditorias futuras.
            for t_ant in tickets_maestros_abiertos:
                cerrado = 0
                if t_ant not in t_acts: cerrado = 1
                    
                if cerrado == 1:
                    deals = mt5.history_deals_get(position=int(t_ant))
                    exito_deals = 0
                    if deals:
                        if len(deals) > 0: exito_deals = 1
                        
                    if exito_deals == 1:
                        beneficio_total = 0.0
                        for d in deals:
                            beneficio_total += d.profit + d.swap + d.commission + d.fee
                            
                        simbolo = deals[0].symbol
                        tipo_int = deals[0].type
                        
                        tipo_str = "BUY"
                        if tipo_int == 1: tipo_str = "SELL"
                        
                        registro = {
                            "ticket": t_ant,
                            "symbol": simbolo,
                            "type": tipo_str,
                            "profit": beneficio_total,
                            "time_close": time.time()
                        }
                        agregar_a_historial(registro)
                        app.notificar(f"[INFO] Operacion {t_ant} ({tipo_str}) cerrada. P/L Registrado: ${beneficio_total:.2f}")
            
            tickets_maestros_abiertos = t_acts
            # ---------------------------------------------------------
            
            historial = cargar_historial()
            app.actualizar_dashboard(ops_actuales, historial)

            tareas = {}
            for s in app.config['slaves']: tareas[s['id']] = []
                
            hay_trabajo = 0
            c_ram = 0

            # Calculo de estado y decision
            for op in ops_actuales:
                for s in app.config['slaves']:
                    s_id = s['id']
                    vin = obtener_vinculo(memoria_db, s_id, op['ticket'])
                    
                    es_n = 0
                    es_m = 0
                    if not vin: es_n = 1
                    else:
                        if vin['slave_ticket'] != 0:
                            d_sl = 0
                            if abs(op['sl'] - vin['sl']) > 0.00001: d_sl = 1
                            d_tp = 0
                            if abs(op['tp'] - vin['tp']) > 0.00001: d_tp = 1
                            
                            c_real = 0
                            e_pend = 0
                            if op['categoria'] == "PENDIENTE": e_pend = 1
                            if e_pend == 1:
                                d_pr = 0
                                if abs(op['price'] - vin['price']) > 0.00001: d_pr = 1
                                if d_sl == 1 or d_tp == 1 or d_pr == 1: c_real = 1
                            else:
                                if d_sl == 1 or d_tp == 1: c_real = 1
                            if c_real == 1: es_m = 1
                                
                    if es_n == 1:
                        tareas[s_id].append({"tipo": "NUEVA", "datos": op, "cfg": s})
                        hay_trabajo = 1
                    elif es_m == 1:
                        tareas[s_id].append({"tipo": "MOD", "datos": op, "vinculo": vin})
                        hay_trabajo = 1

            for s in app.config['slaves']:
                s_id = s['id']
                if s_id in memoria_db:
                    claves = list(memoria_db[s_id].keys())
                    for t_g in claves:
                        cer = 0
                        if t_g not in t_acts: cer = 1
                        if cer == 1:
                            datos = memoria_db[s_id][t_g]
                            t_esc = 0
                            if datos['slave_ticket'] != 0: t_esc = 1
                            if t_esc == 1:
                                tareas[s_id].append({"tipo": "CERRAR", "t_maestro": t_g, "vinculo": datos})
                                hay_trabajo = 1
                            else:
                                memoria_db = eliminar_vinculo(memoria_db, s_id, t_g)
                                c_ram = 1

            # [CRITERIO ACADEMICO: 2e - Beneficios operativos]
            # La ejecucion encolada por nodos optimiza el tiempo de salto entre cuentas, 
            # minimizando el Slippage y aumentando la eficiencia general del proceso de negocio.
            if hay_trabajo == 1:
                for s_cfg in app.config['slaves']:
                    s_id = s_cfg['id']
                    m_tar = tareas[s_id]
                    tengo = 0
                    if len(m_tar) > 0: tengo = 1
                    
                    if tengo == 1:
                        cuenta_conectada = cambiar_cuenta(s_cfg, cuenta_conectada)
                        ok = 0
                        if cuenta_conectada == int(s_cfg['login']): ok = 1
                        
                        if ok == 1:
                            inf_e = mt5.account_info()
                            if inf_e:
                                s_cfg['live_balance'] = inf_e.balance
                                app.tab_cfg.actualizar_lista_cuentas() 

                            for t in m_tar:
                                t_n = 0
                                t_m = 0
                                t_c = 0
                                ex = 0
                                if t['tipo'] == "NUEVA": t_n = 1
                                elif t['tipo'] == "MOD": t_m = 1
                                elif t['tipo'] == "CERRAR": t_c = 1
                                    
                                if t_n == 1: memoria_db, ex = ejecutar_apertura(t['datos'], s_cfg, app.eq_master, memoria_db, app.notificar)
                                elif t_m == 1: memoria_db, ex = ejecutar_modificacion(t['vinculo'], t['datos'], s_id, memoria_db, app.notificar)
                                elif t_c == 1: memoria_db, ex = ejecutar_cierre(t['t_maestro'], t['vinculo'], s_id, memoria_db, app.notificar)
                                if ex == 1: c_ram = 1
                        else:
                            app.notificar(f"[ERROR] Conexion denegada o fallida al nodo {s_id}.")
                
            if c_ram == 1: guardar_ram_a_disco(memoria_db)

        # Recursion simulada para evadir while True
        app.after(500, ciclo_trading)

# --- INICIALIZACION ---
if __name__ == "__main__":
    config_inicial = cargar_credenciales()
    
    config_nula = 0
    if not config_inicial: config_nula = 1
        
    if config_nula == 1:
        config_inicial = {
            "master": {"login": "", "password": "", "server": "", "initial_balance": 100000}, 
            "slaves": []
        }
    else:
        if "initial_balance" not in config_inicial["master"]:
            config_inicial["master"]["initial_balance"] = 100000

    app = PropSyncUI(config_inicial, iniciar_bot, detener_bot)
    app.mainloop()