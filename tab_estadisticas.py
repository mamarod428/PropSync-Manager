import customtkinter as ctk

# [CRITERIO ACADEMICO: 2e - Implicacion en entorno de negocio]
# Permite realizar backtesting e inteligencia de negocio analizando estadisticas de la estrategia
# para la toma de decisiones basada en datos (Data-Driven Decision Making).
class TabEstadisticas(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.cache_historial_len = -1
        self.construir_ui()

    def construir_ui(self):
        self.frame_stats = ctk.CTkFrame(self, fg_color="#1e272e")
        self.frame_stats.pack(fill="x", pady=10, padx=10)
        
        ctk.CTkLabel(self.frame_stats, text="Analisis de Rendimiento - Backtesting", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        self.grid_stats = ctk.CTkFrame(self.frame_stats, fg_color="transparent")
        self.grid_stats.pack(pady=10, padx=20, fill="x")
        self.grid_stats.columnconfigure((0, 1, 2, 3), weight=1)

        self.lbl_stat_ops = ctk.CTkLabel(self.grid_stats, text="Total Ops:\n0", font=ctk.CTkFont(size=18))
        self.lbl_stat_ops.grid(row=0, column=0, padx=10)
        self.lbl_stat_win = ctk.CTkLabel(self.grid_stats, text="Win Rate:\n0.0%", font=ctk.CTkFont(size=18))
        self.lbl_stat_win.grid(row=0, column=1, padx=10)
        self.lbl_stat_profit = ctk.CTkLabel(self.grid_stats, text="Beneficio Neto:\n$0.00", font=ctk.CTkFont(size=18, weight="bold"))
        self.lbl_stat_profit.grid(row=0, column=2, padx=10)
        self.lbl_stat_pf = ctk.CTkLabel(self.grid_stats, text="Profit Factor:\n0.00", font=ctk.CTkFont(size=18))
        self.lbl_stat_pf.grid(row=0, column=3, padx=10)

        self.frame_historial = ctk.CTkFrame(self, fg_color="#111111")
        self.frame_historial.pack(fill="both", expand=True, pady=10, padx=10)
        
        ctk.CTkLabel(self.frame_historial, text="Registro Historico de Operaciones Cerradas", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
        
        self.hist_header = ctk.CTkFrame(self.frame_historial, fg_color="#1e272e", corner_radius=5)
        self.hist_header.pack(fill="x", padx=15, pady=(0,5))
        self.hist_header.columnconfigure((0,1,2,3), weight=1, uniform="hist")
        
        ctk.CTkLabel(self.hist_header, text="Ticket Maestro", font=ctk.CTkFont(weight="bold", size=12), text_color="#a4b0be").grid(row=0, column=0, pady=8)
        ctk.CTkLabel(self.hist_header, text="Simbolo", font=ctk.CTkFont(weight="bold", size=12), text_color="#a4b0be").grid(row=0, column=1, pady=8)
        ctk.CTkLabel(self.hist_header, text="Direccion", font=ctk.CTkFont(weight="bold", size=12), text_color="#a4b0be").grid(row=0, column=2, pady=8)
        ctk.CTkLabel(self.hist_header, text="P/L Final ($)", font=ctk.CTkFont(weight="bold", size=12), text_color="#a4b0be").grid(row=0, column=3, pady=8)

        self.scroll_historial = ctk.CTkScrollableFrame(self.frame_historial, fg_color="transparent")
        self.scroll_historial.pack(fill="both", expand=True, padx=10, pady=5)

    def actualizar_datos(self, historial):
        total_ops = len(historial)
        
        if self.cache_historial_len != total_ops:
            self.cache_historial_len = total_ops
            
            ganadoras = []
            perdedoras = []
            net_profit = 0.0
            
            for op in historial:
                net_profit += op['profit']
                if op['profit'] > 0: ganadoras.append(op)
                else: perdedoras.append(op)
                    
            win_rate = 0.0
            if total_ops > 0: win_rate = (len(ganadoras) / total_ops) * 100
            
            gross_profit = 0.0
            for op in ganadoras: gross_profit += op['profit']
                
            gross_loss = 0.0
            for op in perdedoras: gross_loss += abs(op['profit'])
                
            profit_factor = gross_profit
            if gross_loss > 0: profit_factor = gross_profit / gross_loss
                
            color_profit = "#2ecc71" if net_profit >= 0 else "#e74c3c"
            
            self.lbl_stat_ops.configure(text=f"Total Ops:\n{total_ops}")
            self.lbl_stat_win.configure(text=f"Win Rate:\n{win_rate:.1f}%")
            self.lbl_stat_profit.configure(text=f"Beneficio Neto:\n${net_profit:,.2f}", text_color=color_profit)
            self.lbl_stat_pf.configure(text=f"Profit Factor:\n{profit_factor:.2f}")

            for widget in self.scroll_historial.winfo_children(): widget.destroy()
            
            for i, op in enumerate(reversed(historial)):
                bg_color = "#1a202c" if i % 2 == 0 else "#222b38"
                f_fila = ctk.CTkFrame(self.scroll_historial, fg_color=bg_color, corner_radius=0)
                f_fila.pack(fill="x", pady=1)
                f_fila.columnconfigure((0,1,2,3), weight=1, uniform="hist")
                
                c_pnl = "#2ecc71" if op['profit'] > 0 else "#e74c3c"
                dir_op = op.get('type', 'N/A')
                c_dir = "#2ecc71" if "BUY" in dir_op else "#e74c3c"
                
                ctk.CTkLabel(f_fila, text=str(op['ticket'])).grid(row=0, column=0, pady=4)
                ctk.CTkLabel(f_fila, text=op['symbol'], font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, pady=4)
                ctk.CTkLabel(f_fila, text=dir_op, text_color=c_dir, font=ctk.CTkFont(weight="bold")).grid(row=0, column=2, pady=4)
                ctk.CTkLabel(f_fila, text=f"${op['profit']:.2f}", text_color=c_pnl, font=ctk.CTkFont(weight="bold")).grid(row=0, column=3, pady=4)