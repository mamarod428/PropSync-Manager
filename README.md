# PropSync Manager - Enterprise Edition

## Descripcion del Proyecto
PropSync Manager es una solucion avanzada de automatizacion de procesos roboticos (RPA) diseñada especificamente para la gestion sincronizada de terminales financieras MetaTrader 5. El software funciona como un orquestador transaccional que captura eventos de mercado en una cuenta Maestra (fuente de señales) y los replica de forma asincrona en multiples cuentas Esclavas (nodos receptores).

Este proyecto resuelve la limitacion de escalabilidad de los operadores individuales, permitiendo la gestion unificada de grandes capitales distribuidos en diferentes cuentas, manteniendo siempre una gestion de riesgo proporcional y el cumplimiento estricto de las reglas de preservacion de capital exigidas por las empresas de fondeo (Prop Firms).

## Arquitectura Modular del Sistema
El software ha sido desarrollado siguiendo patrones de ingenieria de software modernos, dividiendo la logica en componentes especializados para garantizar la mantenibilidad y escalabilidad. Esta estructura permite una separacion clara entre la Capa de Presentacion (IT) y la Capa de Operaciones (OT):

### Capa de Orquestacion y Logica (Backend)
* **main.py**: Controlador principal que gestiona el estado global y ejecuta el bucle de sincronizacion IT/OT.
* **trading.py**: Capa de Tecnologia de Operaciones (OT). Gestiona la comunicacion de baja latencia con la API de MetaTrader 5.
* **database.py**: Gestion del ciclo de vida del dato. Controla la integridad referencial de los tickets y la persistencia del historial.
* **config.py**: Gestor de seguridad y archivos de configuracion persistentes.

### Capa de Interfaz y Experiencia de Usuario (Frontend)
* **interfaz.py**: Orquestador visual principal que gestiona la carga de los diferentes modulos de la interfaz.
* **ui_components.py**: Elementos transversales como el sistema de ToolTips y el Manual de Usuario para principiantes.
* **tab_monitor.py**: Modulo especializado en la visualizacion de la red y control de riesgos en vivo.
* **tab_estadisticas.py**: Modulo analitico encargado del procesamiento y renderizado de datos historicos.
* **tab_configuracion.py**: Componente de gestion de nodos, credenciales y bases de datos de firmas.
* **tab_notificaciones.py**: Sistema de registros y trazabilidad de eventos del sistema en tiempo real.

## Requisitos del Sistema
* Sistema Operativo: Microsoft Windows 10 o Windows 11.
* Lenguaje de programacion: Python 3.11 o superior.
* Espacio en disco: 200 MB aprox.

## Guia de Instalacion Paso a Paso

### 1. Instalacion y Configuracion de MetaTrader 5 (Plataforma OT)
Dado que el software actua como un puente tecnologico, requiere que la terminal de ejecucion financiera este instalada:

1. Ingrese a la web oficial de MetaQuotes (`metatrader5.com`) y haga clic en el boton **Download MetaTrader 5 for Windows**.
2. Ejecute el archivo descargado (`mt5setup.exe`) haciendo doble clic sobre el.
3. En la ventana de instalacion, haga clic en **Siguiente** y espere a que finalice el proceso. Haga clic en **Finalizar**.
4. Una vez abierta la terminal MetaTrader 5, el sistema le pedira abrir una cuenta. Si no posee una, seleccione el broker por defecto, haga clic en **Siguiente**, elija **Abrir una cuenta demo** y complete los datos basicos.
5. **Configuracion Critica**: Para que el robot pueda comunicarse con la terminal, debe activar el acceso algoritmico:
   - En el menu superior, haga clic en **Herramientas** (Tools).
   - Haga clic en **Opciones** (Options).
   - Seleccione la pestaña **Asesores Expertos** (Expert Advisors).
   - Marque la casilla **Permitir el trading algoritmico** (Allow Algo Trading).
   - Haga clic en el boton **Aceptar**.

### 2. Instalacion de Python y Dependencias (Capa IT)
1. Descargue Python desde `python.org` (Version 3.11 o superior).
2. Durante la instalacion, es **obligatorio** marcar la casilla **Add Python to PATH**.
3. Una vez instalado, abra una terminal de Windows (CMD o PowerShell).
4. Navegue hasta la carpeta donde ha descargado este proyecto.
5. Ejecute el siguiente comando para instalar las librerias necesarias para la interfaz y la conexion financiera:
   ```bash
   pip install MetaTrader5 customtkinter pillow