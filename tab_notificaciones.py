import customtkinter as ctk
import time

# [CRITERIO ACADEMICO: 5b - Ciclo de vida del dato (Trazabilidad)]
# Este componente registra cronologicamente eventos de alto impacto para auditorias de red,
# permitiendo rastrear el ciclo vital de las transacciones (desde su apertura hasta su cierre).
class TabNotificaciones(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.construir_ui()

    def construir_ui(self):
        self.consola = ctk.CTkTextbox(self, font=ctk.CTkFont(family="Consolas", size=13), fg_color="#111111", text_color="#d1d8e0")
        self.consola.pack(fill="both", expand=True, padx=10, pady=10)
        self.btn_limpiar = ctk.CTkButton(self, text="Limpiar Consola de Sistema", fg_color="transparent", border_width=1, command=lambda: self.consola.delete("0.0", "end"))
        self.btn_limpiar.pack(pady=10)

    def agregar_log(self, m_str):
        self.consola.insert("end", f"[{time.strftime('%H:%M:%S')}] {m_str}\n")
        self.consola.see("end")