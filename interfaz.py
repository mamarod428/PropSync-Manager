import customtkinter as ctk
import os
from PIL import Image
from config import cargar_empresas
from ui_components import ToolTip, TutorialWindow
from tab_dashboard import TabDashboard
from tab_estadisticas import TabEstadisticas
from tab_configuracion import TabConfiguracion
from tab_notificaciones import TabNotificaciones

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# [CRITERIO ACADEMICO: Patrón MVC (Controlador Principal)] 
# Clase que orquesta la logica y actua de puente entre el motor OT (MT5) 
# y los componentes modulares de la interfaz IT.
class PropSyncUI(ctk.CTk):
    def __init__(self, config_inicial, cb_iniciar, cb_detener):
        super().__init__()

        self.title("PropSync Manager - Enterprise Edition Final")
        self.geometry("1280x850") 
        self.resizable(True, True)
        self.minsize(1150, 750)

        icono_nombre = 'propsync_icon.ico'
        if os.path.exists(icono_nombre):
            try: self.wm_iconbitmap(icono_nombre)
            except Exception as e: error_ignorado = 1

        self.config = config_inicial
        self.cb_iniciar = cb_iniciar
        self.cb_detener = cb_detener
        self.bloquear_edicion = False
        self.id_nodo_en_edicion = ""
        
        self.empresas_fondeo = cargar_empresas()
        self.tipos_capital = ["Capital Propio", "Demo", "Fondeada", "Fase 1", "Fase 2"]
        
        self.eq_master = 0.0
        self.bal_master = 0.0
        self.profit_master = 0.0
        self.margin_master = 0.0

        self.crear_interfaz_base()
        
        self.tab_cfg.cargar_datos_maestra_ui()
        self.tab_cfg.actualizar_lista_cuentas()
        self.tab_cfg.actualizar_lista_empresas()

    def set_modo_ejecucion(self, activo):
        self.bloquear_edicion = (activo == 1)
        if activo == 1:
            self.btn_iniciar.configure(state="disabled", fg_color="gray")
            self.btn_detener.configure(state="normal", fg_color="#e74c3c", hover_color="#c0392b")
            self.lbl_estado_badge.configure(text="[SISTEMA EN EJECUCION]", text_color="#2ecc71")
        else:
            self.btn_iniciar.configure(state="normal", fg_color="#2ecc71", hover_color="#27ae60")
            self.btn_detener.configure(state="disabled", fg_color="gray")
            self.lbl_estado_badge.configure(text="[SISTEMA DETENIDO]", text_color="#ff4d4d")

    def crear_interfaz_base(self):
        self.sidebar = ctk.CTkFrame(self, width=260, corner_radius=0, fg_color="#11151a")
        self.sidebar.pack(side="left", fill="y")

        ruta_icono = 'propsync_icon.ico'
        if os.path.exists(ruta_icono):
            try:
                img_logo = ctk.CTkImage(Image.open(ruta_icono), size=(90, 90))
                self.lbl_img_logo = ctk.CTkLabel(self.sidebar, text="", image=img_logo)
                self.lbl_img_logo.pack(pady=(30, 10))
            except Exception as e: error_img_ignorado = 1

        self.lbl_titulo = ctk.CTkLabel(self.sidebar, text="PropSync\nEnterprise", font=ctk.CTkFont(size=24, weight="bold"))
        self.lbl_titulo.pack(pady=(0, 20), padx=20)

        ctk.CTkFrame(self.sidebar, height=2, fg_color="#2f3640").pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(self.sidebar, text="CONTROL DE MOTORES", font=ctk.CTkFont(size=11, weight="bold"), text_color="#7f8c8d").pack(anchor="w", padx=20, pady=(10, 0))
        
        self.lbl_estado_badge = ctk.CTkLabel(self.sidebar, text="[SISTEMA DETENIDO]", font=ctk.CTkFont(size=14, weight="bold"), text_color="#ff4d4d")
        self.lbl_estado_badge.pack(pady=(5, 15))

        self.btn_iniciar = ctk.CTkButton(self.sidebar, text="Iniciar Servicio", fg_color="#2ecc71", hover_color="#27ae60", text_color="white", font=ctk.CTkFont(size=14, weight="bold"), height=45, command=self.cb_iniciar)
        self.btn_iniciar.pack(pady=5, padx=20, fill="x")

        self.btn_detener = ctk.CTkButton(self.sidebar, text="Detener Servicio", fg_color="gray", state="disabled", font=ctk.CTkFont(size=14, weight="bold"), height=45, command=self.cb_detener)
        self.btn_detener.pack(pady=5, padx=20, fill="x")

        ctk.CTkFrame(self.sidebar, height=2, fg_color="#2f3640").pack(fill="x", padx=20, pady=25)

        ctk.CTkLabel(self.sidebar, text="RESUMEN FINANCIERO RED", font=ctk.CTkFont(size=11, weight="bold"), text_color="#7f8c8d").pack(anchor="w", padx=20, pady=(0, 5))
        
        self.card_global = ctk.CTkFrame(self.sidebar, fg_color="#1e272e", corner_radius=10, border_width=1, border_color="#2f3640")
        self.card_global.pack(fill="x", padx=20, pady=5)
        
        self.lbl_resumen_prof_global = ctk.CTkLabel(self.card_global, text="Beneficio Flotante Global:\n$0.00", font=ctk.CTkFont(size=15, weight="bold"), text_color="#2ecc71")
        self.lbl_resumen_prof_global.pack(pady=(15, 10))
        
        self.lbl_resumen_eq_global = ctk.CTkLabel(self.card_global, text="Equidad Global:\n$0.00", font=ctk.CTkFont(size=15, weight="bold"), text_color="#f1c40f")
        self.lbl_resumen_eq_global.pack(pady=(10, 15))

        self.btn_tutorial = ctk.CTkButton(self.sidebar, text="Guia y Documentacion", fg_color="#8e44ad", hover_color="#9b59b6", font=ctk.CTkFont(weight="bold"), height=40, command=self.mostrar_tutorial)
        self.btn_tutorial.pack(side="bottom", pady=20, padx=20, fill="x")

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(side="right", fill="both", expand=True, padx=15, pady=15)

        tab_1 = self.tabview.add("Monitor Virtual")
        tab_2 = self.tabview.add("Estadisticas Analiticas")
        tab_3 = self.tabview.add("Configuracion de Red")
        tab_4 = self.tabview.add("Registro del Sistema")

        self.tab_dash = TabDashboard(tab_1, self)
        self.tab_dash.pack(fill="both", expand=True)

        self.tab_stats = TabEstadisticas(tab_2, self)
        self.tab_stats.pack(fill="both", expand=True)

        self.tab_cfg = TabConfiguracion(tab_3, self)
        self.tab_cfg.pack(fill="both", expand=True)

        self.tab_notif = TabNotificaciones(tab_4, self)
        self.tab_notif.pack(fill="both", expand=True)

    def mostrar_tutorial(self):
        TutorialWindow(self)

    def obtener_lista_nombres_empresas(self):
        lista = list(self.empresas_fondeo.keys())
        if len(lista) == 0: lista = ["Sin Empresas"]
        lista.append("Otra...")
        return lista

    def notificar(self, msg):
        etiquetas_validas = ["[SISTEMA]", "[ERROR]", "[INFO]", "[ADVERTENCIA]", "[ACCION]", "[EXITO]", "[MODIFICACION]", "[CIERRE]", "[LIMPIEZA]"]
        es_imp = 0
        for etiqueta in etiquetas_validas:
            if etiqueta in str(msg): es_imp = 1
                
        if es_imp == 1:
            self.tab_notif.agregar_log(msg)

    # [CRITERIO ACADEMICO: Rendimiento]
    def actualizar_dashboard(self, ops_actuales, historial):
        self.tab_dash.actualizar_datos(ops_actuales)
        self.tab_stats.actualizar_datos(historial)