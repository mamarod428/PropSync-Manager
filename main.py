import MetaTrader5 as mt5
import time
import os
import threading
import webview
from supabase import create_client

from modules.config import cargar_credenciales, cargar_secrets, guardar_credenciales
from modules.database import cargar_mapa_a_ram, guardar_ram_a_disco, cargar_historial, agregar_a_historial, obtener_vinculo, eliminar_vinculo
from modules.trading import cambiar_cuenta, obtener_estado_maestro, sincronizar_inicio, ejecutar_apertura, ejecutar_modificacion, ejecutar_cierre

# --- CONFIGURACIÓN CLOUD ---
secrets = cargar_secrets()
URL_NUBE = secrets.get("SUPABASE_URL", "")
KEY_NUBE = secrets.get("SUPABASE_KEY", "")

supabase = None
if URL_NUBE != "":
    try:
        supabase = create_client(URL_NUBE, KEY_NUBE)
    except Exception:
        error_conexion = 1

# --- VARIABLES GLOBALES DE ESTADO ---
bot_activo = 0
cuenta_conectada = 0
memoria_db = {}
tickets_maestros_abiertos = []
app_config = None
window = None

# Variables flotantes para el Dashboard
eq_master_global = 0.0
bal_master_global = 0.0
profit_master_global = 0.0

def registrar_log(mensaje):
    """Envia un mensaje a la consola de la interfaz web (JS)"""
    print(mensaje) # Mantiene log en terminal
    if window:
        # Escapamos comillas simples para evitar errores en JS
        msg_seguro = mensaje.replace("'", "\\'")
        # Llamamos a una funcion de JS para mostrar logs si existe
        try:
            window.evaluate_js(f"if(typeof window.log_sys === 'function') window.log_sys('{msg_seguro}');")
        except Exception:
            error = 1

def iniciar_motor_trading():
    """Inicializa la conexion a MT5 y arranca el ciclo"""
    global bot_activo, cuenta_conectada, memoria_db, tickets_maestros_abiertos, app_config
    
    c_valida = 0
    if app_config:
        if 'master' in app_config and app_config['master']['login'] != "": 
            c_valida = 1
            
    if c_valida == 0:
        registrar_log("[ERROR] Parametros de cuenta Maestra ausentes en config.")
        return False

    ini = 0
    if mt5.initialize(): ini = 1
    
    if ini == 1:
        bot_activo = 1
        registrar_log("[SISTEMA] Inicializando rutinas de sincronizacion Edge...")
        
        memoria_db = cargar_mapa_a_ram()
        cuenta_conectada, memoria_db = sincronizar_inicio(app_config, cuenta_conectada, memoria_db, registrar_log)
        guardar_ram_a_disco(memoria_db)
        
        ops_iniciales = obtener_estado_maestro()
        tickets_maestros_abiertos = []
        for op in ops_iniciales:
            tickets_maestros_abiertos.append(str(op['ticket']))
            
        # Iniciamos el bucle en un hilo separado usando recursion controlada
        threading.Thread(target=ciclo_trading_recursivo, daemon=True).start()
        return True
    else:
        registrar_log("[ERROR] MetaTrader 5 no ha podido iniciar sesion.")
        return False

def detener_motor_trading():
    """Detiene el servicio OT"""
    global bot_activo
    bot_activo = 0
    registrar_log("[SISTEMA] Motor RPA detenido.")
    mt5.shutdown()

def ciclo_trading_recursivo():
    """
    Alternativa a 'while True' y 'app.after'. 
    Usa time.sleep() y recursión. Corre en su propio hilo (daemon).
    """
    global bot_activo, cuenta_conectada, memoria_db, tickets_maestros_abiertos, app_config
    
    ejecutar = 0
    if bot_activo == 1: ejecutar = 1
    
    if ejecutar == 1:
        # --- NUCLEO DEL TRADING ---
        cuenta_conectada = cambiar_cuenta(app_config['master'], cuenta_conectada)

        c_ok = 0
        if cuenta_conectada != 0: c_ok = 1
        
        if c_ok == 1:
            inf = mt5.account_info()
            global eq_master_global, bal_master_global, profit_master_global
            if inf: 
                eq_master_global = inf.equity
                bal_master_global = inf.balance
                profit_master_global = inf.profit
            
            ops_actuales = obtener_estado_maestro()
            t_acts = []
            for op in ops_actuales: t_acts.append(str(op['ticket']))

            # Cierres
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
                        registrar_log(f"[INFO] Operacion {t_ant} ({tipo_str}) cerrada. P/L Registrado: ${beneficio_total:.2f}")
            
            tickets_maestros_abiertos = t_acts
            
            # Gestion Esclavas
            tareas = {}
            for s in app_config['slaves']: tareas[s['id']] = []
                
            hay_trabajo = 0
            c_ram = 0

            for op in ops_actuales:
                for s in app_config['slaves']:
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

            for s in app_config['slaves']:
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

            if hay_trabajo == 1:
                for s_cfg in app_config['slaves']:
                    s_id = s_cfg['id']
                    m_tar = tareas[s_id]
                    tengo = 0
                    if len(m_tar) > 0: tengo = 1
                    
                    if tengo == 1:
                        cuenta_conectada = cambiar_cuenta(s_cfg, cuenta_conectada)
                        ok = 0
                        if cuenta_conectada == int(s_cfg['login']): ok = 1
                        
                        if ok == 1:
                            for t in m_tar:
                                t_n = 0
                                t_m = 0
                                t_c = 0
                                ex = 0
                                if t['tipo'] == "NUEVA": t_n = 1
                                elif t['tipo'] == "MOD": t_m = 1
                                elif t['tipo'] == "CERRAR": t_c = 1
                                    
                                # AQUI CORREGIMOS eq_master por eq_master_global
                                if t_n == 1: memoria_db, ex = ejecutar_apertura(t['datos'], s_cfg, eq_master_global, memoria_db, registrar_log)
                                elif t_m == 1: memoria_db, ex = ejecutar_modificacion(t['vinculo'], t['datos'], s_id, memoria_db, registrar_log)
                                elif t_c == 1: memoria_db, ex = ejecutar_cierre(t['t_maestro'], t['vinculo'], s_id, memoria_db, registrar_log)
                                if ex == 1: c_ram = 1
                        else:
                            registrar_log(f"[ERROR] Conexion denegada al nodo {s_id}.")
                
            if c_ram == 1: guardar_ram_a_disco(memoria_db)

        # Espera medio segundo y se llama a si misma
        time.sleep(0.5)
        ciclo_trading_recursivo()


# --- CLASE API PARA JAVASCRIPT ---
class BridgeAPI:
    def obtener_claves_js(self):
        """Devuelve las claves a JavaScript sin exponerlas en archivos JS"""
        return {"url": URL_NUBE, "key": KEY_NUBE}
        
    def conectar(self, email, password):
        """Llamado desde el login en HTML"""
        global supabase, URL_NUBE, KEY_NUBE
        try:
            # 1. Forzamos la lectura para ver si el JSON realmente pasa a Python
            s_dict = cargar_secrets()
            URL_NUBE = s_dict.get("SUPABASE_URL", "")
            KEY_NUBE = s_dict.get("SUPABASE_KEY", "")
            
            if URL_NUBE == "" or KEY_NUBE == "":
                return {"status": "error", "message": "Python detectó el JSON pero no encontró las claves 'SUPABASE_URL'. ¿Hay alguna coma extra?"}
            
            # 2. Forzamos la creación del cliente para capturar errores de URL
            if not supabase:
                supabase = create_client(URL_NUBE, KEY_NUBE)
                
            # 3. Intentamos el Login
            res = supabase.auth.sign_in_with_password({"email": email, "password": password})
            os.environ["PROPSYNC_USER_EMAIL"] = res.user.email
            
            exito = iniciar_motor_trading()
            if exito:
                return {"status": "success", "email": res.user.email}
            else:
                return {"status": "error", "message": "Fallo al iniciar motor MT5"}
                
        except Exception as e:
            return {"status": "error", "message": f"DEBUG ROOT: {str(e)}"}

    def registrar(self, email, password):
        global supabase, URL_NUBE, KEY_NUBE
        try:
            if not supabase:
                s_dict = cargar_secrets()
                supabase = create_client(s_dict.get("SUPABASE_URL", ""), s_dict.get("SUPABASE_KEY", ""))
                
            supabase.auth.sign_up({"email": email, "password": password})
            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "message": f"DEBUG ROOT: {str(e)}"}

    def apagar_motor(self):
        detener_motor_trading()
        return "ok"
    
    def encender_motor(self):
        """Llamado desde JS para reactivar el motor sin reloguear"""
        exito = iniciar_motor_trading()
        if exito:
            return "ok"
        return "error"

    def obtener_configuracion(self):
        global app_config
        if not app_config:
            return {"master": {}, "slaves": []}
        return app_config
    
    def obtener_telemetria(self):
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

    def guardar_maestra(self, datos_master):
        global app_config
        app_config['master'] = datos_master
        guardar_credenciales(app_config)
        registrar_log("[INFO] Configuracion Maestra principal actualizada.")
        return "ok"

    def guardar_esclava(self, datos_slave):
        global app_config
        ind_actualizar = -1
        for i in range(len(app_config['slaves'])):
            if app_config['slaves'][i]['id'] == datos_slave['id']:
                ind_actualizar = i
                
        if ind_actualizar != -1:
            app_config['slaves'][ind_actualizar] = datos_slave
            registrar_log(f"[INFO] Nodo esclavo '{datos_slave['id']}' actualizado.")
        else:
            app_config['slaves'].append(datos_slave)
            registrar_log(f"[INFO] Nodo esclavo '{datos_slave['id']}' acoplado a la red.")
            
        guardar_credenciales(app_config)
        return "ok"

    def eliminar_esclava(self, id_borrar):
        global app_config
        n_lista = []
        for s in app_config['slaves']:
            if s['id'] != id_borrar: n_lista.append(s)
        app_config['slaves'] = n_lista
        guardar_credenciales(app_config)
        registrar_log(f"[INFO] Nodo '{id_borrar}' eliminado de la red.")
        return "ok"

# --- LANZAMIENTO ---
if __name__ == "__main__":
    app_config = cargar_credenciales()
    config_nula = 0
    if not app_config: config_nula = 1
        
    if config_nula == 1:
        app_config = {
            "master": {"login": "", "password": "", "server": "", "initial_balance": 100000}, 
            "slaves": []
        }
        
    api = BridgeAPI()
    
    # Crear y lanzar la ventana web local
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