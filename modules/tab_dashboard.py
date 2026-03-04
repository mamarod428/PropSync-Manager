import customtkinter as ctk
from modules.ui_components import ToolTip

def obtener_nombre_tipo(tipo_int):
    if tipo_int == 0: return "BUY"
    if tipo_int == 1: return "SELL"
    if tipo_int == 2: return "BUY LIMIT"
    if tipo_int == 3: return "SELL LIMIT"
    if tipo_int == 4: return "BUY STOP"
    if tipo_int == 5: return "SELL STOP"
    return "OTRO"

# [CRITERIO ACADEMICO: 2f - Integracion IT y OT]
# Este modulo traduce datos operativos crudos (OT) provenientes de la terminal de trading
# en un panel de monitorizacion estructurado (IT), mejorando la visibilidad del proceso.
class TabDashboard(ctk.CTkScrollableFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        
        self.refs_ops = {}
        self.current_tickets = []
        self.refs_slaves = {}
        self.current_slaves = []
        self.refs_master_prog = {}
        self.cache_master_cfg_str = ""

        self.construir_ui()

    def construir_ui(self):
        self.frame_master = ctk.CTkFrame(self, fg_color="#1e272e")
        self.frame_master.pack(fill="x", pady=5, padx=5)
        
        lbl_master_title = ctk.CTkLabel(self.frame_master, text="Cuenta Maestra (Fuente de Senales)", font=ctk.CTkFont(size=14, weight="bold"))
        lbl_master_title.pack(pady=(10,5))
        ToolTip(lbl_master_title, "El motor financiero principal. Sus acciones dictan el comportamiento de la red.")
        
        self.grid_metricas = ctk.CTkFrame(self.frame_master, fg_color="transparent")
        self.grid_metricas.pack(pady=5, padx=15, fill="x")
        self.grid_metricas.columnconfigure((0, 1, 2, 3), weight=1, uniform="m_metrics")

        f_m1 = ctk.CTkFrame(self.grid_metricas, fg_color="#2f3640", corner_radius=8)
        f_m1.grid(row=0, column=0, padx=8, pady=5, sticky="nsew")
        ctk.CTkLabel(f_m1, text="Balance Fijo", font=ctk.CTkFont(size=12), text_color="#a4b0be").pack(pady=(10,0))
        self.lbl_bal_master = ctk.CTkLabel(f_m1, text="$0.00", font=ctk.CTkFont(size=18, weight="bold"))
        self.lbl_bal_master.pack(pady=(0,10))

        f_m2 = ctk.CTkFrame(self.grid_metricas, fg_color="#2f3640", corner_radius=8)
        f_m2.grid(row=0, column=1, padx=8, pady=5, sticky="nsew")
        ctk.CTkLabel(f_m2, text="Equidad Dinamica", font=ctk.CTkFont(size=12), text_color="#a4b0be").pack(pady=(10,0))
        self.lbl_eq_master = ctk.CTkLabel(f_m2, text="$0.00", font=ctk.CTkFont(size=18, weight="bold"))
        self.lbl_eq_master.pack(pady=(0,10))

        f_m3 = ctk.CTkFrame(self.grid_metricas, fg_color="#2f3640", corner_radius=8)
        f_m3.grid(row=0, column=2, padx=8, pady=5, sticky="nsew")
        ctk.CTkLabel(f_m3, text="P/L Flotante", font=ctk.CTkFont(size=12), text_color="#a4b0be").pack(pady=(10,0))
        self.lbl_profit_master = ctk.CTkLabel(f_m3, text="$0.00", font=ctk.CTkFont(size=18, weight="bold"))
        self.lbl_profit_master.pack(pady=(0,10))

        f_m4 = ctk.CTkFrame(self.grid_metricas, fg_color="#2f3640", corner_radius=8)
        f_m4.grid(row=0, column=3, padx=8, pady=5, sticky="nsew")
        ctk.CTkLabel(f_m4, text="Nivel de Margen", font=ctk.CTkFont(size=12), text_color="#a4b0be").pack(pady=(10,0))
        self.lbl_margin_master = ctk.CTkLabel(f_m4, text="0.00%", font=ctk.CTkFont(size=18, weight="bold"))
        self.lbl_margin_master.pack(pady=(0,10))

        self.frame_progreso_master = ctk.CTkFrame(self.frame_master, fg_color="transparent")
        self.frame_progreso_master.pack(fill="x", padx=15, pady=(5, 10))

        self.frame_virtual = ctk.CTkFrame(self, fg_color="#2f3640")
        self.frame_virtual.pack(fill="x", pady=10, padx=5)
        
        lbl_virtual = ctk.CTkLabel(self.frame_virtual, text="Monitor de Red: Control de Riesgo y Nodos", font=ctk.CTkFont(size=14, weight="bold"), text_color="#3498db")
        lbl_virtual.pack(pady=(10,5))
        
        self.v_header = ctk.CTkFrame(self.frame_virtual, fg_color="#1e272e", corner_radius=5)
        self.v_header.pack(fill="x", padx=15, pady=(0,5))
        self.v_header.columnconfigure((0,1,2,3,4,5), weight=1, uniform="v_col")
        
        ctk.CTkLabel(self.v_header, text="Identificador Nodo", font=ctk.CTkFont(weight="bold", size=12), text_color="#a4b0be").grid(row=0, column=0, pady=8)
        ctk.CTkLabel(self.v_header, text="Tipo / Empresa", font=ctk.CTkFont(weight="bold", size=12), text_color="#a4b0be").grid(row=0, column=1, pady=8)
        ctk.CTkLabel(self.v_header, text="Finanzas Calc.", font=ctk.CTkFont(weight="bold", size=12), text_color="#a4b0be").grid(row=0, column=2, pady=8)
        ctk.CTkLabel(self.v_header, text="Drawdown Diario", font=ctk.CTkFont(weight="bold", size=12), text_color="#a4b0be").grid(row=0, column=3, pady=8)
        ctk.CTkLabel(self.v_header, text="Drawdown Total", font=ctk.CTkFont(weight="bold", size=12), text_color="#a4b0be").grid(row=0, column=4, pady=8)
        ctk.CTkLabel(self.v_header, text="Rentabilidad Target", font=ctk.CTkFont(weight="bold", size=12), text_color="#a4b0be").grid(row=0, column=5, pady=8)

        self.container_slaves = ctk.CTkFrame(self.frame_virtual, fg_color="transparent")
        self.container_slaves.pack(fill="x", expand=True, padx=15, pady=(0, 10))

        self.frame_ops = ctk.CTkFrame(self, fg_color="#111111")
        self.frame_ops.pack(fill="x", pady=5, padx=5)
        
        ctk.CTkLabel(self.frame_ops, text="Terminal de Posiciones Activas", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(10,5))
        
        self.frame_header = ctk.CTkFrame(self.frame_ops, fg_color="#1e272e", corner_radius=5)
        self.frame_header.pack(fill="x", padx=15, pady=(0,5))
        self.frame_header.columnconfigure((0,1,2,3,4,5,6), weight=1, uniform="col")
        
        ctk.CTkLabel(self.frame_header, text="Ticket", font=ctk.CTkFont(weight="bold", size=12), text_color="#a4b0be").grid(row=0, column=0, pady=8)
        ctk.CTkLabel(self.frame_header, text="Simbolo", font=ctk.CTkFont(weight="bold", size=12), text_color="#a4b0be").grid(row=0, column=1, pady=8)
        ctk.CTkLabel(self.frame_header, text="Tipo", font=ctk.CTkFont(weight="bold", size=12), text_color="#a4b0be").grid(row=0, column=2, pady=8)
        ctk.CTkLabel(self.frame_header, text="Volumen", font=ctk.CTkFont(weight="bold", size=12), text_color="#a4b0be").grid(row=0, column=3, pady=8)
        ctk.CTkLabel(self.frame_header, text="Precio Entrada", font=ctk.CTkFont(weight="bold", size=12), text_color="#a4b0be").grid(row=0, column=4, pady=8)
        ctk.CTkLabel(self.frame_header, text="Stop Loss", font=ctk.CTkFont(weight="bold", size=12), text_color="#a4b0be").grid(row=0, column=5, pady=8)
        ctk.CTkLabel(self.frame_header, text="Take Profit", font=ctk.CTkFont(weight="bold", size=12), text_color="#a4b0be").grid(row=0, column=6, pady=8)

        self.container_ops = ctk.CTkFrame(self.frame_ops, fg_color="transparent")
        self.container_ops.pack(fill="x", expand=True, padx=15, pady=(0, 10))

    def actualizar_datos(self, ops_actuales):
        c_prof = "#2ecc71" if self.app.profit_master >= 0 else "#e74c3c"
        self.lbl_bal_master.configure(text=f"${self.app.bal_master:,.2f}")
        self.lbl_eq_master.configure(text=f"${self.app.eq_master:,.2f}")
        self.lbl_profit_master.configure(text=f"${self.app.profit_master:,.2f}", text_color=c_prof)
        self.lbl_margin_master.configure(text=f"{self.app.margin_master:,.2f}%")
        
        self._dibujar_progreso_maestra()
        self._dibujar_monitor_virtual()
        self._dibujar_tabla_operaciones(ops_actuales)

    def _dibujar_progreso_maestra(self):
        cfg_m = self.app.config.get('master', {})
        tipo_cap = cfg_m.get('capital_type', 'Capital Propio')
        nom_empresa = cfg_m.get('prop_firm', '')
        bal_inicial = float(cfg_m.get('initial_balance', 0.1))
        if bal_inicial <= 0: bal_inicial = 0.1

        estado_master_cfg = f"{tipo_cap}-{nom_empresa}-{bal_inicial}"
        es_fondeo = 1 if tipo_cap in ["Fondeada", "Fase 1", "Fase 2"] else 0

        if self.cache_master_cfg_str != estado_master_cfg:
            self.cache_master_cfg_str = estado_master_cfg
            for widget in self.frame_progreso_master.winfo_children(): widget.destroy()
            self.refs_master_prog.clear()

            if es_fondeo == 1 and nom_empresa in self.app.empresas_fondeo:
                self.frame_progreso_master.columnconfigure((0,1,2), weight=1, uniform="m_prog")
                
                f_dd_d = ctk.CTkFrame(self.frame_progreso_master, fg_color="transparent")
                f_dd_d.grid(row=0, column=0, sticky="ew", padx=10)
                l_dd_d = ctk.CTkLabel(f_dd_d, text="DD Diario:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#a4b0be")
                l_dd_d.pack(anchor="w", pady=(0,4))
                b_dd_d = ctk.CTkProgressBar(f_dd_d, height=10, progress_color="#e74c3c")
                b_dd_d.set(0)
                b_dd_d.pack(fill="x")
                self.refs_master_prog['lbl_dd_d'] = l_dd_d
                self.refs_master_prog['bar_dd_d'] = b_dd_d

                f_dd_t = ctk.CTkFrame(self.frame_progreso_master, fg_color="transparent")
                f_dd_t.grid(row=0, column=1, sticky="ew", padx=10)
                l_dd_t = ctk.CTkLabel(f_dd_t, text="DD Total:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#a4b0be")
                l_dd_t.pack(anchor="w", pady=(0,4))
                b_dd_t = ctk.CTkProgressBar(f_dd_t, height=10, progress_color="#e74c3c")
                b_dd_t.set(0)
                b_dd_t.pack(fill="x")
                self.refs_master_prog['lbl_dd_t'] = l_dd_t
                self.refs_master_prog['bar_dd_t'] = b_dd_t

                if tipo_cap in ["Fase 1", "Fase 2"]:
                    f_obj = ctk.CTkFrame(self.frame_progreso_master, fg_color="transparent")
                    f_obj.grid(row=0, column=2, sticky="ew", padx=10)
                    l_obj = ctk.CTkLabel(f_obj, text="Rentabilidad Target:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#a4b0be")
                    l_obj.pack(anchor="w", pady=(0,4))
                    b_obj = ctk.CTkProgressBar(f_obj, height=10, progress_color="#2ecc71")
                    b_obj.set(0)
                    b_obj.pack(fill="x")
                    self.refs_master_prog['lbl_obj'] = l_obj
                    self.refs_master_prog['bar_obj'] = b_obj

        if es_fondeo == 1 and nom_empresa in self.app.empresas_fondeo and self.refs_master_prog:
            sim_equity = self.app.eq_master
            datos_emp = self.app.empresas_fondeo[nom_empresa]

            dd_diario_max_pct = datos_emp.get("dd_diario", 5.0)
            max_dd_d_usd = bal_inicial * (dd_diario_max_pct / 100.0)
            act_dd_d_usd = bal_inicial - sim_equity if sim_equity < bal_inicial else 0.0
            
            p_d = act_dd_d_usd / max_dd_d_usd if max_dd_d_usd > 0 else 0
            p_d = max(0.0, min(1.0, p_d))
            self.refs_master_prog['lbl_dd_d'].configure(text=f"DD Diario: ${act_dd_d_usd:,.2f} / ${max_dd_d_usd:,.2f}")
            self.refs_master_prog['bar_dd_d'].set(p_d)

            dd_total_max_pct = datos_emp.get("dd_total", 10.0)
            max_dd_t_usd = bal_inicial * (dd_total_max_pct / 100.0)
            act_dd_t_usd = bal_inicial - sim_equity if sim_equity < bal_inicial else 0.0

            p_t = act_dd_t_usd / max_dd_t_usd if max_dd_t_usd > 0 else 0
            p_t = max(0.0, min(1.0, p_t))
            self.refs_master_prog['lbl_dd_t'].configure(text=f"DD Total: ${act_dd_t_usd:,.2f} / ${max_dd_t_usd:,.2f}")
            self.refs_master_prog['bar_dd_t'].set(p_t)

            if tipo_cap in ["Fase 1", "Fase 2"]:
                pct_objetivo = datos_emp.get("target_f1", 8.0) if tipo_cap == "Fase 1" else datos_emp.get("target_f2", 5.0)
                dinero_objetivo = bal_inicial * (pct_objetivo / 100.0)
                act_obj_usd = sim_equity - bal_inicial if sim_equity > bal_inicial else 0.0
                
                p_o = act_obj_usd / dinero_objetivo if dinero_objetivo > 0 else 0
                p_o = max(0.0, min(1.0, p_o))
                self.refs_master_prog['lbl_obj'].configure(text=f"Rentabilidad Target: ${act_obj_usd:,.2f} / ${dinero_objetivo:,.2f}")
                self.refs_master_prog['bar_obj'].set(p_o)

    def _dibujar_monitor_virtual(self):
        slaves_sig = []
        for s in self.app.config.get('slaves', []):
            slaves_sig.append(f"{s['id']}-{s.get('capital_type')}-{s.get('prop_firm')}-{s.get('risk_factor')}-{s.get('initial_balance')}")
            
        if slaves_sig != self.current_slaves:
            self.current_slaves = slaves_sig
            for widget in self.container_slaves.winfo_children(): widget.destroy()
            self.refs_slaves.clear()
            
            for i, s in enumerate(self.app.config.get('slaves', [])):
                s_id = s['id']
                tipo_cap = s.get('capital_type', 'Capital Propio')
                nom_empresa = s.get('prop_firm', '')
                es_fondeo = 1 if tipo_cap in ["Fondeada", "Fase 1", "Fase 2"] else 0

                bg_color = "#222b38" if i % 2 == 0 else "#1a202c"
                f_fila = ctk.CTkFrame(self.container_slaves, fg_color=bg_color, corner_radius=0)
                f_fila.pack(fill="x", pady=1)
                f_fila.columnconfigure((0,1,2,3,4,5), weight=1, uniform="v_col")

                f_c0 = ctk.CTkFrame(f_fila, fg_color="transparent")
                f_c0.grid(row=0, column=0, sticky="nsew", padx=10, pady=8)
                ctk.CTkLabel(f_c0, text=s_id, font=ctk.CTkFont(weight="bold", size=13)).pack(anchor="w")
                ctk.CTkLabel(f_c0, text=f"Riesgo: {s.get('risk_factor', 1.0)}x", font=ctk.CTkFont(size=11), text_color="#f39c12").pack(anchor="w")

                f_c1 = ctk.CTkFrame(f_fila, fg_color="transparent")
                f_c1.grid(row=0, column=1, sticky="nsew", padx=10, pady=8)
                ctk.CTkLabel(f_c1, text=tipo_cap, font=ctk.CTkFont(weight="bold", size=12)).pack(anchor="w")
                if es_fondeo == 1 and nom_empresa != "":
                    ctk.CTkLabel(f_c1, text=nom_empresa, font=ctk.CTkFont(size=11), text_color="#a4b0be").pack(anchor="w")

                f_c2 = ctk.CTkFrame(f_fila, fg_color="transparent")
                f_c2.grid(row=0, column=2, sticky="nsew", padx=10, pady=8)
                l_eq = ctk.CTkLabel(f_c2, text="Eq: $0.00", font=ctk.CTkFont(size=12))
                l_eq.pack(anchor="w")
                l_pnl = ctk.CTkLabel(f_c2, text="P/L: $0.00", font=ctk.CTkFont(weight="bold", size=12))
                l_pnl.pack(anchor="w")

                self.refs_slaves[s_id] = {'l_eq': l_eq, 'l_pnl': l_pnl}

                f_c3 = ctk.CTkFrame(f_fila, fg_color="transparent")
                f_c3.grid(row=0, column=3, sticky="nsew", padx=10, pady=8)
                if es_fondeo == 1 and nom_empresa in self.app.empresas_fondeo:
                    l_dd_d = ctk.CTkLabel(f_c3, text="$0.00 / $0.00", font=ctk.CTkFont(size=11))
                    l_dd_d.pack(anchor="w")
                    b_dd_d = ctk.CTkProgressBar(f_c3, height=6, progress_color="#e74c3c")
                    b_dd_d.set(0)
                    b_dd_d.pack(fill="x", pady=(2,0))
                    self.refs_slaves[s_id]['l_dd_d'] = l_dd_d
                    self.refs_slaves[s_id]['b_dd_d'] = b_dd_d
                else: ctk.CTkLabel(f_c3, text="N/A", text_color="#7f8c8d").pack(anchor="w", pady=10)

                f_c4 = ctk.CTkFrame(f_fila, fg_color="transparent")
                f_c4.grid(row=0, column=4, sticky="nsew", padx=10, pady=8)
                if es_fondeo == 1 and nom_empresa in self.app.empresas_fondeo:
                    l_dd_t = ctk.CTkLabel(f_c4, text="$0.00 / $0.00", font=ctk.CTkFont(size=11))
                    l_dd_t.pack(anchor="w")
                    b_dd_t = ctk.CTkProgressBar(f_c4, height=6, progress_color="#e74c3c")
                    b_dd_t.set(0)
                    b_dd_t.pack(fill="x", pady=(2,0))
                    self.refs_slaves[s_id]['l_dd_t'] = l_dd_t
                    self.refs_slaves[s_id]['b_dd_t'] = b_dd_t
                else: ctk.CTkLabel(f_c4, text="N/A", text_color="#7f8c8d").pack(anchor="w", pady=10)

                f_c5 = ctk.CTkFrame(f_fila, fg_color="transparent")
                f_c5.grid(row=0, column=5, sticky="nsew", padx=10, pady=8)
                if tipo_cap in ["Fase 1", "Fase 2"] and nom_empresa in self.app.empresas_fondeo:
                    l_obj = ctk.CTkLabel(f_c5, text="$0.00 / $0.00", font=ctk.CTkFont(size=11))
                    l_obj.pack(anchor="w")
                    b_obj = ctk.CTkProgressBar(f_c5, height=6, progress_color="#2ecc71")
                    b_obj.set(0)
                    b_obj.pack(fill="x", pady=(2,0))
                    self.refs_slaves[s_id]['l_obj'] = l_obj
                    self.refs_slaves[s_id]['b_obj'] = b_obj
                else: ctk.CTkLabel(f_c5, text="N/A", text_color="#7f8c8d").pack(anchor="w", pady=10)

        equidad_global_simulada = self.app.eq_master

        for s in self.app.config.get('slaves', []):
            s_id = s['id']
            if s_id in self.refs_slaves:
                riesgo = s.get('risk_factor', 1.0)
                bal_inicial = float(s.get('initial_balance', 0.1))
                bal_base = float(s.get('live_balance', bal_inicial))

                sim_profit = self.app.profit_master * riesgo
                sim_equity = bal_base + sim_profit
                equidad_global_simulada += sim_equity

                c_prof = "#2ecc71" if sim_profit >= 0 else "#e74c3c"

                self.refs_slaves[s_id]['l_eq'].configure(text=f"Eq: ${sim_equity:,.2f}")
                self.refs_slaves[s_id]['l_pnl'].configure(text=f"P/L: ${sim_profit:,.2f}", text_color=c_prof)

                tipo_cap = s.get('capital_type', 'Capital Propio')
                nom_empresa = s.get('prop_firm', '')
                if tipo_cap in ["Fondeada", "Fase 1", "Fase 2"] and nom_empresa in self.app.empresas_fondeo:
                    datos_emp = self.app.empresas_fondeo[nom_empresa]

                    dd_diario_max_pct = datos_emp.get("dd_diario", 5.0)
                    max_dd_d_usd = bal_base * (dd_diario_max_pct / 100.0)
                    act_dd_d_usd = bal_base - sim_equity if sim_equity < bal_base else 0.0

                    p_d = act_dd_d_usd / max_dd_d_usd if max_dd_d_usd > 0 else 0
                    p_d = max(0.0, min(1.0, p_d))
                    self.refs_slaves[s_id]['l_dd_d'].configure(text=f"${act_dd_d_usd:,.2f} / ${max_dd_d_usd:,.2f}")
                    self.refs_slaves[s_id]['b_dd_d'].set(p_d)

                    dd_total_max_pct = datos_emp.get("dd_total", 10.0)
                    max_dd_t_usd = bal_inicial * (dd_total_max_pct / 100.0)
                    act_dd_t_usd = bal_inicial - sim_equity if sim_equity < bal_inicial else 0.0

                    p_t = act_dd_t_usd / max_dd_t_usd if max_dd_t_usd > 0 else 0
                    p_t = max(0.0, min(1.0, p_t))
                    self.refs_slaves[s_id]['l_dd_t'].configure(text=f"${act_dd_t_usd:,.2f} / ${max_dd_t_usd:,.2f}")
                    self.refs_slaves[s_id]['b_dd_t'].set(p_t)

                    if tipo_cap in ["Fase 1", "Fase 2"]:
                        pct_objetivo = datos_emp.get("target_f1", 8.0) if tipo_cap == "Fase 1" else datos_emp.get("target_f2", 5.0)
                        dinero_objetivo = bal_inicial * (pct_objetivo / 100.0)
                        act_obj_usd = sim_equity - bal_inicial if sim_equity > bal_inicial else 0.0

                        p_o = act_obj_usd / dinero_objetivo if dinero_objetivo > 0 else 0
                        p_o = max(0.0, min(1.0, p_o))
                        self.refs_slaves[s_id]['l_obj'].configure(text=f"${act_obj_usd:,.2f} / ${dinero_objetivo:,.2f}")
                        self.refs_slaves[s_id]['b_obj'].set(p_o)

        prof_global = equidad_global_simulada - self.app.bal_master - sum([s.get('live_balance', s.get('initial_balance', 0)) for s in self.app.config.get('slaves', [])])
        c_prof_glob = "#2ecc71" if prof_global >= 0 else "#e74c3c"
        
        self.app.lbl_resumen_prof_global.configure(text=f"Beneficio Global:\n${prof_global:,.2f}", text_color=c_prof_glob)
        self.app.lbl_resumen_eq_global.configure(text=f"Equidad Global:\n${equidad_global_simulada:,.2f}")

    def _dibujar_tabla_operaciones(self, ops_actuales):
        tickets_now = [str(op['ticket']) for op in ops_actuales]
        
        if tickets_now != self.current_tickets:
            for widget in self.container_ops.winfo_children(): widget.destroy()
            self.refs_ops.clear()
            self.current_tickets = tickets_now
            
            for i, op in enumerate(ops_actuales):
                bg_color = "#1a202c" if i % 2 == 0 else "#222b38"
                f_fila = ctk.CTkFrame(self.container_ops, fg_color=bg_color, corner_radius=0)
                f_fila.pack(fill="x", pady=1)
                f_fila.columnconfigure((0,1,2,3,4,5,6), weight=1, uniform="col")
                
                t_tipo = obtener_nombre_tipo(op['type'])
                c_tipo = "#2ecc71" if "BUY" in t_tipo else "#e74c3c"
                
                ctk.CTkLabel(f_fila, text=str(op['ticket'])).grid(row=0, column=0, pady=4)
                ctk.CTkLabel(f_fila, text=op['symbol'], font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, pady=4)
                ctk.CTkLabel(f_fila, text=t_tipo, text_color=c_tipo, font=ctk.CTkFont(weight="bold")).grid(row=0, column=2, pady=4)
                
                l_vol = ctk.CTkLabel(f_fila, text=str(op['volume']))
                l_vol.grid(row=0, column=3, pady=4)
                
                l_pr = ctk.CTkLabel(f_fila, text=f"{op['price']:.5f}")
                l_pr.grid(row=0, column=4, pady=4)
                
                t_sl = f"{op['sl']:.5f}" if op['sl'] > 0 else "-"
                l_sl = ctk.CTkLabel(f_fila, text=t_sl, text_color="#e74c3c")
                l_sl.grid(row=0, column=5, pady=4)
                
                t_tp = f"{op['tp']:.5f}" if op['tp'] > 0 else "-"
                l_tp = ctk.CTkLabel(f_fila, text=t_tp, text_color="#2ecc71")
                l_tp.grid(row=0, column=6, pady=4)
                
                self.refs_ops[str(op['ticket'])] = {'vol': l_vol, 'pr': l_pr, 'sl': l_sl, 'tp': l_tp}
        else:
            for op in ops_actuales:
                t_id = str(op['ticket'])
                if t_id in self.refs_ops:
                    r = self.refs_ops[t_id]
                    r['vol'].configure(text=str(op['volume']))
                    r['pr'].configure(text=f"{op['price']:.5f}")
                    r['sl'].configure(text=f"{op['sl']:.5f}" if op['sl'] > 0 else "-")
                    r['tp'].configure(text=f"{op['tp']:.5f}" if op['tp'] > 0 else "-")