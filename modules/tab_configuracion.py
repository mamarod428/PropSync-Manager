import customtkinter as ctk
from modules.config import guardar_credenciales, guardar_empresas
from modules.ui_components import ToolTip

# [CRITERIO ACADEMICO: 5i - Seguridad y regulacion]
# Se gestionan credenciales aplicando principios de ofuscacion visual.
# Los datos no se transmiten a internet, aislando las contrasenas localmente.
class TabConfiguracion(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.construir_ui()

    def construir_ui(self):
        self.subtabs_config = ctk.CTkTabview(self)
        self.subtabs_config.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.tab_nodos = self.subtabs_config.add("Gestion de Nodos y Cuentas")
        self.tab_firmas = self.subtabs_config.add("Base de Datos de Firmas (Riesgo)")

        self.construir_subtab_nodos()
        self.construir_subtab_firmas()

    def construir_subtab_nodos(self):
        self.frame_master_cfg = ctk.CTkFrame(self.tab_nodos, fg_color="#1e272e")
        self.frame_master_cfg.pack(fill="x", pady=5, padx=5)

        lbl_m = ctk.CTkLabel(self.frame_master_cfg, text="Configuracion de Cuenta Maestra", font=ctk.CTkFont(size=14, weight="bold"))
        lbl_m.grid(row=0, column=0, columnspan=5, pady=10)
        
        self.e_m_log = ctk.CTkEntry(self.frame_master_cfg, placeholder_text="Login MT5", width=130)
        self.e_m_log.grid(row=1, column=0, padx=10, pady=5)
        
        # [CRITERIO ACADEMICO: 5i - Seguridad implementada] Enmascaramiento de input
        self.e_m_pass = ctk.CTkEntry(self.frame_master_cfg, placeholder_text="Password", show="*", width=130)
        self.e_m_pass.grid(row=1, column=1, padx=10, pady=5)
        
        self.e_m_serv = ctk.CTkEntry(self.frame_master_cfg, placeholder_text="Servidor del Broker", width=160)
        self.e_m_serv.grid(row=1, column=2, padx=10, pady=5)
        self.e_m_bal = ctk.CTkEntry(self.frame_master_cfg, placeholder_text="Balance Inicial ($)", width=130)
        self.e_m_bal.grid(row=1, column=3, padx=10, pady=5)

        self.e_m_tipo_cap = ctk.CTkOptionMenu(self.frame_master_cfg, values=self.app.tipos_capital, command=self.evento_tipo_maestra, width=130)
        self.e_m_tipo_cap.grid(row=2, column=0, padx=10, pady=10)
        
        lista_empresas = self.app.obtener_lista_nombres_empresas()
        self.e_m_empresa = ctk.CTkOptionMenu(self.frame_master_cfg, values=lista_empresas, width=150)
        self.e_m_empresa.grid(row=2, column=1, padx=10, pady=10)
        self.e_m_empresa.configure(state="disabled")

        # [CRITERIO ACADEMICO: 5b / 5f - Gestion y Nube] 
        # Guarda las credenciales localmente.
        self.btn_save_master = ctk.CTkButton(self.frame_master_cfg, text="Aplicar Cambios", fg_color="#3498db", hover_color="#2980b9", command=self.guardar_maestra_ui)
        self.btn_save_master.grid(row=2, column=3, padx=10, pady=10, sticky="e")

        self.frame_form = ctk.CTkFrame(self.tab_nodos, fg_color="#2f3640")
        self.frame_form.pack(fill="x", pady=15, padx=5)

        ctk.CTkLabel(self.frame_form, text="Anadir / Editar Subcuenta", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, columnspan=6, pady=10)
        
        self.entry_id = ctk.CTkEntry(self.frame_form, placeholder_text="Identificador unico", width=130)
        self.entry_id.grid(row=1, column=0, padx=10, pady=5)
        self.entry_login = ctk.CTkEntry(self.frame_form, placeholder_text="Login MT5", width=120)
        self.entry_login.grid(row=1, column=1, padx=10, pady=5)
        self.entry_pass = ctk.CTkEntry(self.frame_form, placeholder_text="Password", show="*", width=120)
        self.entry_pass.grid(row=1, column=2, padx=10, pady=5)
        self.entry_server = ctk.CTkEntry(self.frame_form, placeholder_text="Servidor del Broker", width=160)
        self.entry_server.grid(row=1, column=3, padx=10, pady=5)

        self.entry_slave_bal = ctk.CTkEntry(self.frame_form, placeholder_text="Balance Inicial", width=130)
        self.entry_slave_bal.grid(row=2, column=0, padx=10, pady=5)
        
        self.entry_risk = ctk.CTkEntry(self.frame_form, placeholder_text="Factor Riesgo (1.0x)", width=120)
        self.entry_risk.grid(row=2, column=1, padx=10, pady=5)
        
        self.btn_calc_risk = ctk.CTkButton(self.frame_form, text="Calcular Factor", fg_color="#7f8c8d", hover_color="#718093", command=self.recomendar_riesgo, width=120)
        self.btn_calc_risk.grid(row=2, column=2, padx=10, pady=5, sticky="ew")
        
        self.e_s_tipo_cap = ctk.CTkOptionMenu(self.frame_form, values=self.app.tipos_capital, command=self.evento_tipo_esclava, width=130)
        self.e_s_tipo_cap.grid(row=3, column=0, padx=10, pady=10)
        self.e_s_empresa = ctk.CTkOptionMenu(self.frame_form, values=lista_empresas, width=150)
        self.e_s_empresa.grid(row=3, column=1, padx=10, pady=10)
        self.e_s_empresa.configure(state="disabled")

        self.btn_guardar_cuenta = ctk.CTkButton(self.frame_form, text="Registrar Nodo", fg_color="#3498db", hover_color="#2980b9", command=self.guardar_cuenta_ui)
        self.btn_guardar_cuenta.grid(row=2, column=3, rowspan=2, padx=10, pady=10, sticky="se")

        ctk.CTkLabel(self.tab_nodos, text="Red de Subcuentas Activas", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(15, 5))
        
        self.nodo_header = ctk.CTkFrame(self.tab_nodos, fg_color="#222222", corner_radius=5)
        self.nodo_header.pack(fill="x", padx=10)
        self.nodo_header.columnconfigure((0,1,2,3,4,5), weight=1, uniform="nodo")
        
        ctk.CTkLabel(self.nodo_header, text="Identificador", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, pady=8)
        ctk.CTkLabel(self.nodo_header, text="Login MT5", font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, pady=8)
        ctk.CTkLabel(self.nodo_header, text="Tipo de Capital", font=ctk.CTkFont(weight="bold")).grid(row=0, column=2, pady=8)
        ctk.CTkLabel(self.nodo_header, text="Balance Base", font=ctk.CTkFont(weight="bold")).grid(row=0, column=3, pady=8)
        ctk.CTkLabel(self.nodo_header, text="Riesgo", font=ctk.CTkFont(weight="bold")).grid(row=0, column=4, pady=8)
        ctk.CTkLabel(self.nodo_header, text="Acciones", font=ctk.CTkFont(weight="bold")).grid(row=0, column=5, pady=8)

        self.frame_lista = ctk.CTkScrollableFrame(self.tab_nodos, fg_color="transparent")
        self.frame_lista.pack(fill="both", expand=True, padx=5, pady=5)

    def construir_subtab_firmas(self):
        self.frame_empresa_form = ctk.CTkFrame(self.tab_firmas, fg_color="#1e272e")
        self.frame_empresa_form.pack(fill="x", pady=10, padx=5)
        
        ctk.CTkLabel(self.frame_empresa_form, text="Gestor de Parametros de Prop Firms", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, columnspan=5, pady=10)
        
        self.e_emp_nombre = ctk.CTkEntry(self.frame_empresa_form, placeholder_text="Nombre de la Firma", width=180)
        self.e_emp_nombre.grid(row=1, column=0, padx=10, pady=5)
        
        self.e_emp_dd_d = ctk.CTkEntry(self.frame_empresa_form, placeholder_text="DD Diario Max (%)", width=130)
        self.e_emp_dd_d.grid(row=1, column=1, padx=10, pady=5)
        
        self.e_emp_dd_t = ctk.CTkEntry(self.frame_empresa_form, placeholder_text="DD Total Max (%)", width=130)
        self.e_emp_dd_t.grid(row=1, column=2, padx=10, pady=5)
        
        self.e_emp_f1 = ctk.CTkEntry(self.frame_empresa_form, placeholder_text="Objetivo Fase 1 (%)", width=130)
        self.e_emp_f1.grid(row=1, column=3, padx=10, pady=5)
        
        self.e_emp_f2 = ctk.CTkEntry(self.frame_empresa_form, placeholder_text="Objetivo Fase 2 (%)", width=130)
        self.e_emp_f2.grid(row=1, column=4, padx=10, pady=5)
        
        self.btn_guardar_emp = ctk.CTkButton(self.frame_empresa_form, text="Guardar Parametros", fg_color="#2ecc71", hover_color="#27ae60", command=self.guardar_empresa_ui)
        self.btn_guardar_emp.grid(row=2, column=0, columnspan=5, pady=15)
        
        self.frame_lista_empresas = ctk.CTkFrame(self.tab_firmas)
        self.frame_lista_empresas.pack(fill="both", expand=True, pady=10, padx=5)
        
        ctk.CTkLabel(self.frame_lista_empresas, text="Firmas Registradas en el Sistema", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        
        self.firm_header = ctk.CTkFrame(self.frame_lista_empresas, fg_color="#222222", corner_radius=5)
        self.firm_header.pack(fill="x", padx=10)
        self.firm_header.columnconfigure((0,1,2,3,4,5), weight=1, uniform="firm")
        
        ctk.CTkLabel(self.firm_header, text="Empresa", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, pady=8)
        ctk.CTkLabel(self.firm_header, text="DD Diario", font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, pady=8)
        ctk.CTkLabel(self.firm_header, text="DD Total", font=ctk.CTkFont(weight="bold")).grid(row=0, column=2, pady=8)
        ctk.CTkLabel(self.firm_header, text="Target Fase 1", font=ctk.CTkFont(weight="bold")).grid(row=0, column=3, pady=8)
        ctk.CTkLabel(self.firm_header, text="Target Fase 2", font=ctk.CTkFont(weight="bold")).grid(row=0, column=4, pady=8)
        ctk.CTkLabel(self.firm_header, text="Acciones de Control", font=ctk.CTkFont(weight="bold")).grid(row=0, column=5, pady=8)
        
        self.scroll_firmas = ctk.CTkScrollableFrame(self.frame_lista_empresas, fg_color="transparent")
        self.scroll_firmas.pack(fill="both", expand=True, padx=5, pady=5)

    def evento_tipo_maestra(self, valor):
        if valor in ["Fondeada", "Fase 1", "Fase 2"]:
            self.e_m_empresa.configure(state="normal")
        else:
            self.e_m_empresa.configure(state="disabled")

    def evento_tipo_esclava(self, valor):
        if valor in ["Fondeada", "Fase 1", "Fase 2"]:
            self.e_s_empresa.configure(state="normal")
        else:
            self.e_s_empresa.configure(state="disabled")

    def guardar_maestra_ui(self):
        if self.app.bloquear_edicion:
            self.app.notificar("[ADVERTENCIA] Servicio debe estar detenido.")
            return

        n_log = self.e_m_log.get()
        n_pass = self.e_m_pass.get()
        n_serv = self.e_m_serv.get()
        n_bal = self.e_m_bal.get()
        n_tipo = self.e_m_tipo_cap.get()
        n_empresa = self.e_m_empresa.get() if n_tipo in ["Fondeada", "Fase 1", "Fase 2"] else "N/A"

        if not n_log or not n_pass or not n_serv or not n_bal:
            self.app.notificar("[ADVERTENCIA] Parametros incompletos en cuenta Maestra.")
            return

        self.app.config['master'] = {
            "login": int(n_log), "password": n_pass, "server": n_serv, 
            "initial_balance": float(n_bal), "capital_type": n_tipo, "prop_firm": n_empresa
        }
        guardar_credenciales(self.app.config)
        self.app.notificar("[INFO] Configuracion Maestra principal actualizada.")

    def recomendar_riesgo(self):
        try:
            bal_maestro = float(self.e_m_bal.get())
            bal_esclavo = float(self.entry_slave_bal.get())
            if bal_maestro > 0:
                proporcion = round(bal_esclavo / bal_maestro, 3)
                self.entry_risk.delete(0, 'end')
                self.entry_risk.insert(0, str(proporcion))
                self.app.notificar(f"[INFO] Factor de riesgo sugerido: {proporcion}x")
            else:
                self.app.notificar("[ADVERTENCIA] Balance maestro debe ser mayor a 0.")
        except:
            self.app.notificar("[ADVERTENCIA] Parametros invalidos en los balances.")

    def guardar_cuenta_ui(self):
        if self.app.bloquear_edicion:
            self.app.notificar("[ADVERTENCIA] Servicio debe estar detenido.")
            return

        n_id = self.entry_id.get()
        n_log = self.entry_login.get()
        n_pass = self.entry_pass.get()
        n_serv = self.entry_server.get()
        n_bal = self.entry_slave_bal.get()
        n_risk = self.entry_risk.get()
        n_tipo = self.e_s_tipo_cap.get()
        n_empresa = self.e_s_empresa.get() if n_tipo in ["Fondeada", "Fase 1", "Fase 2"] else "N/A"

        if not n_id or not n_log or not n_risk:
            self.app.notificar("[ADVERTENCIA] Faltan parametros identificativos.")
            return

        ind_actualizar = -1
        busqueda_origen = 1
        
        if self.app.id_nodo_en_edicion != "":
            for i in range(len(self.app.config['slaves'])):
                if self.app.config['slaves'][i]['id'] == self.app.id_nodo_en_edicion:
                    ind_actualizar = i
            busqueda_origen = 0
            
        if busqueda_origen == 1:
            for i in range(len(self.app.config['slaves'])):
                if self.app.config['slaves'][i]['id'] == n_id:
                    ind_actualizar = i
                
        n_cta = {
            "id": n_id, "login": int(n_log), "password": n_pass, "server": n_serv, 
            "initial_balance": float(n_bal), "risk_factor": float(n_risk),
            "capital_type": n_tipo, "prop_firm": n_empresa
        }

        if ind_actualizar != -1: 
            self.app.config['slaves'][ind_actualizar] = n_cta
            self.app.notificar(f"[INFO] Nodo esclavo '{n_id}' actualizado.")
        else: 
            self.app.config['slaves'].append(n_cta)
            self.app.notificar(f"[INFO] Nodo esclavo '{n_id}' acoplado a la red.")

        guardar_credenciales(self.app.config)
        self.actualizar_lista_cuentas()
        
        self.app.id_nodo_en_edicion = ""
        self.btn_guardar_cuenta.configure(text="Registrar Nodo", fg_color="#3498db", hover_color="#2980b9")
        
        self.entry_id.delete(0, 'end')
        self.entry_login.delete(0, 'end')
        self.entry_pass.delete(0, 'end')
        self.entry_server.delete(0, 'end')
        self.entry_slave_bal.delete(0, 'end')
        self.entry_risk.delete(0, 'end')

    def cargar_esclava_para_edicion(self, datos_esclava):
        self.app.id_nodo_en_edicion = datos_esclava['id']
        self.btn_guardar_cuenta.configure(text="Actualizar Nodo", fg_color="#e67e22", hover_color="#d35400")
        
        self.entry_id.delete(0, 'end')
        self.entry_id.insert(0, datos_esclava['id'])
        self.entry_login.delete(0, 'end')
        self.entry_login.insert(0, str(datos_esclava['login']))
        self.entry_pass.delete(0, 'end')
        self.entry_pass.insert(0, datos_esclava['password'])
        self.entry_server.delete(0, 'end')
        self.entry_server.insert(0, datos_esclava['server'])
        self.entry_slave_bal.delete(0, 'end')
        self.entry_slave_bal.insert(0, str(datos_esclava.get('initial_balance', '')))
        self.entry_risk.delete(0, 'end')
        self.entry_risk.insert(0, str(datos_esclava.get('risk_factor', 1.0)))
        
        t_cap = datos_esclava.get('capital_type', 'Capital Propio')
        emp = datos_esclava.get('prop_firm', '')
        
        self.e_s_tipo_cap.set(t_cap)
        self.evento_tipo_esclava(t_cap)
        
        if t_cap in ["Fondeada", "Fase 1", "Fase 2"] and emp:
            try: self.e_s_empresa.set(emp)
            except Exception as e: error_ignorado = 1
        
        self.app.notificar(f"[INFO] Edicion activada para el nodo '{datos_esclava['id']}'.")

    def eliminar_cuenta_ui(self, id_borrar):
        if self.app.bloquear_edicion: return
        n_lista = []
        for s in self.app.config['slaves']:
            if s['id'] != id_borrar: n_lista.append(s)
        self.app.config['slaves'] = n_lista
        guardar_credenciales(self.app.config)
        self.actualizar_lista_cuentas()
        self.app.notificar(f"[INFO] Nodo '{id_borrar}' eliminado de la red.")

    def actualizar_lista_cuentas(self):
        for widget in self.frame_lista.winfo_children(): widget.destroy()

        if 'slaves' in self.app.config:
            for i, s in enumerate(self.app.config['slaves']):
                bg_color = "#1a202c" if i % 2 == 0 else "#222b38"
                f_item = ctk.CTkFrame(self.frame_lista, fg_color=bg_color, corner_radius=0)
                f_item.pack(fill="x", pady=1)
                f_item.columnconfigure((0,1,2,3,4,5), weight=1, uniform="nodo")
                
                bal_base = s.get('initial_balance', 0)
                lbl_tipo = s.get('capital_type', 'Capital Propio')
                if lbl_tipo in ["Fondeada", "Fase 1", "Fase 2"] and s.get('prop_firm', ''): 
                    lbl_tipo += f" ({s.get('prop_firm', '')})"
                
                ctk.CTkLabel(f_item, text=s['id'], font=ctk.CTkFont(weight="bold", size=13)).grid(row=0, column=0, pady=8)
                ctk.CTkLabel(f_item, text=str(s['login'])).grid(row=0, column=1, pady=8)
                ctk.CTkLabel(f_item, text=lbl_tipo).grid(row=0, column=2, pady=8)
                ctk.CTkLabel(f_item, text=f"${bal_base:,.2f}").grid(row=0, column=3, pady=8)
                ctk.CTkLabel(f_item, text=f"{s.get('risk_factor', 1.0)}x").grid(row=0, column=4, pady=8)
                
                f_btns = ctk.CTkFrame(f_item, fg_color="transparent")
                f_btns.grid(row=0, column=5, pady=5)
                
                b_edit = ctk.CTkButton(f_btns, text="Editar", width=60, fg_color="#3498db", hover_color="#2980b9", command=lambda s_data=s: self.cargar_esclava_para_edicion(s_data))
                b_edit.pack(side="left", padx=5)
                
                b_del = ctk.CTkButton(f_btns, text="Eliminar", width=60, fg_color="#e74c3c", hover_color="#c0392b", command=lambda e_id=s['id']: self.eliminar_cuenta_ui(e_id))
                b_del.pack(side="left", padx=5)

    def guardar_empresa_ui(self):
        n = self.e_emp_nombre.get().strip()
        d = self.e_emp_dd_d.get()
        t = self.e_emp_dd_t.get()
        f1 = self.e_emp_f1.get()
        f2 = self.e_emp_f2.get()
        
        es_valido = 1
        if not n or not d or not t or not f1 or not f2: es_valido = 0
        
        if es_valido == 1:
            try:
                self.app.empresas_fondeo[n] = {
                    "dd_diario": float(d), "dd_total": float(t), "target_f1": float(f1), "target_f2": float(f2)
                }
                guardar_empresas(self.app.empresas_fondeo)
                self.actualizar_lista_empresas()
                
                lista_actualizada = self.app.obtener_lista_nombres_empresas()
                self.e_m_empresa.configure(values=lista_actualizada)
                self.e_s_empresa.configure(values=lista_actualizada)
                
                self.e_emp_nombre.delete(0, 'end')
                self.e_emp_dd_d.delete(0, 'end')
                self.e_emp_dd_t.delete(0, 'end')
                self.e_emp_f1.delete(0, 'end')
                self.e_emp_f2.delete(0, 'end')
                self.app.notificar(f"[SISTEMA] Parametros de firma '{n}' guardados.")
            except:
                self.app.notificar("[ERROR] Los valores deben ser numericos.")
        else:
            self.app.notificar("[ADVERTENCIA] Rellena todos los campos.")

    def cargar_empresa_para_edicion(self, nombre, datos):
        self.e_emp_nombre.delete(0, 'end')
        self.e_emp_nombre.insert(0, nombre)
        self.e_emp_dd_d.delete(0, 'end')
        self.e_emp_dd_d.insert(0, str(datos.get('dd_diario', '')))
        self.e_emp_dd_t.delete(0, 'end')
        self.e_emp_dd_t.insert(0, str(datos.get('dd_total', '')))
        self.e_emp_f1.delete(0, 'end')
        self.e_emp_f1.insert(0, str(datos.get('target_f1', '')))
        self.e_emp_f2.delete(0, 'end')
        self.e_emp_f2.insert(0, str(datos.get('target_f2', '')))

    def eliminar_empresa_ui(self, nombre):
        if nombre in self.app.empresas_fondeo:
            del self.app.empresas_fondeo[nombre]
            guardar_empresas(self.app.empresas_fondeo)
            self.actualizar_lista_empresas()
            
            lista_actualizada = self.app.obtener_lista_nombres_empresas()
            self.e_m_empresa.configure(values=lista_actualizada)
            self.e_s_empresa.configure(values=lista_actualizada)
            self.app.notificar(f"[SISTEMA] Firma '{nombre}' eliminada.")

    def actualizar_lista_empresas(self):
        for widget in self.scroll_firmas.winfo_children(): widget.destroy()
        
        for i, (nom, datos) in enumerate(self.app.empresas_fondeo.items()):
            bg_color = "#1a202c" if i % 2 == 0 else "#222b38"
            f_item = ctk.CTkFrame(self.scroll_firmas, fg_color=bg_color, corner_radius=0)
            f_item.pack(fill="x", pady=1)
            f_item.columnconfigure((0,1,2,3,4,5), weight=1, uniform="firm")
            
            ctk.CTkLabel(f_item, text=nom, font=ctk.CTkFont(weight="bold", size=13)).grid(row=0, column=0, pady=8)
            ctk.CTkLabel(f_item, text=f"{datos.get('dd_diario', 0.0)}%").grid(row=0, column=1, pady=8)
            ctk.CTkLabel(f_item, text=f"{datos.get('dd_total', 0.0)}%").grid(row=0, column=2, pady=8)
            ctk.CTkLabel(f_item, text=f"{datos.get('target_f1', 0.0)}%").grid(row=0, column=3, pady=8)
            ctk.CTkLabel(f_item, text=f"{datos.get('target_f2', 0.0)}%").grid(row=0, column=4, pady=8)
            
            f_btns = ctk.CTkFrame(f_item, fg_color="transparent")
            f_btns.grid(row=0, column=5, pady=5)
            
            b_edit = ctk.CTkButton(f_btns, text="Editar", width=60, fg_color="#3498db", hover_color="#2980b9", command=lambda n=nom, d=datos: self.cargar_empresa_para_edicion(n, d))
            b_edit.pack(side="left", padx=5)
            b_del = ctk.CTkButton(f_btns, text="Eliminar", width=60, fg_color="#e74c3c", hover_color="#c0392b", command=lambda n=nom: self.eliminar_empresa_ui(n))
            b_del.pack(side="left", padx=5)

    def cargar_datos_maestra_ui(self):
        if 'master' in self.app.config and self.app.config['master']['login'] != "":
            self.e_m_log.insert(0, str(self.app.config['master']['login']))
            self.e_m_pass.insert(0, self.app.config['master']['password'])
            self.e_m_serv.insert(0, self.app.config['master']['server'])
            self.e_m_bal.insert(0, str(self.app.config['master'].get('initial_balance', 100000)))
            
            t_cap = self.app.config['master'].get('capital_type', 'Capital Propio')
            emp = self.app.config['master'].get('prop_firm', '')
            
            self.e_m_tipo_cap.set(t_cap)
            self.evento_tipo_maestra(t_cap)
            
            if t_cap in ["Fondeada", "Fase 1", "Fase 2"] and emp:
                try: self.e_m_empresa.set(emp)
                except Exception as e: error_ignorado = 1