import customtkinter as ctk

# [CRITERIO ACADÉMICO: 2e - Beneficios operativos]
# La implementación de ToolTips mejora la usabilidad (UX) del software, 
# reduciendo la curva de aprendizaje en entornos de negocio complejos.
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)

    def enter(self, event=None):
        self.schedule_id = self.widget.after(500, self.show)

    def leave(self, event=None):
        cancelar_id = 0
        if hasattr(self, 'schedule_id'): cancelar_id = 1
        if cancelar_id == 1: self.widget.after_cancel(self.schedule_id)
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

    def show(self):
        ventana_activa = 0
        if self.tooltip_window: ventana_activa = 1
            
        if ventana_activa == 0:
            x, y, cx, cy = self.widget.bbox("insert")
            x += self.widget.winfo_rootx() + 35
            y += self.widget.winfo_rooty() + 20
            
            self.tooltip_window = tw = ctk.CTkToplevel(self.widget)
            tw.wm_overrideredirect(True)
            tw.wm_geometry(f"+{x}+{y}")
            
            label = ctk.CTkLabel(tw, text=self.text, fg_color="#2c3e50", text_color="white", corner_radius=6, padx=10, pady=5, font=ctk.CTkFont(size=12))
            label.pack()

# [CRITERIO ACADÉMICO: 2g - Impacto de las THD]
# Esta ventana documenta el uso del software como una herramienta RPA (Robotic Process Automation), 
# explicando la tecnología subyacente a usuarios no técnicos.
class TutorialWindow(ctk.CTkToplevel):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.title("Guia para Principiantes - PropSync")
        self.geometry("650x550")
        self.attributes("-topmost", True)
        
        ctk.CTkLabel(self, text="¿Que es esto y como funciona?", font=ctk.CTkFont(size=22, weight="bold"), text_color="#3498db").pack(pady=(20, 10))
        
        texto = (
            "No te preocupes si no tienes conocimientos previos. Aqui tienes los conceptos basicos:\n\n"
            "1. Conceptos Clave:\n"
            " - MetaTrader: Es el programa estandar mundial donde se ejecutan las compras y ventas del mercado.\n"
            " - Cuentas de Fondeo (Prop Firms): Son empresas que te prestan miles de dolares para que operes, pero te imponen reglas muy estrictas de riesgo (Ejemplo: 'No pierdas mas de 500 dolares al dia').\n\n"
            "2. ¿Para que sirve PropSync?\n"
            "PropSync es un 'Robot de Automatizacion'. Si tienes varias cuentas conectadas, operar manualmente en todas a la vez es humanamente imposible. PropSync actua vigilando tu cuenta principal (Maestra) y clona instantaneamente tus movimientos en las demas cuentas (Esclavas).\n\n"
            "3. Pasos para arrancar:\n"
            " A) Ve a la pestana 'Configuracion de Red' e introduce los datos de tu cuenta Maestra.\n"
            " B) En 'Base de Datos de Firmas', registra tu empresa y sus limites de riesgo. El sistema usara esto para proteger tu cuenta visualmente.\n"
            " C) En 'Gestion de Nodos', anade tus cuentas Esclavas. Usa el boton 'Calcular Factor' para que el sistema decida automaticamente el tamano de las operaciones en base a tu dinero.\n"
            " D) Dale a 'Iniciar Servicio' en el panel izquierdo. El sistema comenzara a vigilar todo automaticamente."
        )
        
        caja = ctk.CTkTextbox(self, font=ctk.CTkFont(size=14), wrap="word", fg_color="#1e272e", text_color="#ecf0f1")
        caja.pack(fill="both", expand=True, padx=25, pady=10)
        caja.insert("0.0", texto)
        caja.configure(state="disabled") 
        
        ctk.CTkButton(self, text="Entendido, comenzar a operar", font=ctk.CTkFont(weight="bold"), fg_color="#2ecc71", hover_color="#27ae60", command=self.destroy).pack(pady=20)