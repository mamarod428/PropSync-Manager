# PropSync Manager - Enterprise Edition

## Descripcion del Proyecto
PropSync Manager es una solucion avanzada de automatizacion de procesos roboticos (RPA) diseñada especificamente para la gestion sincronizada de terminales financieras MetaTrader 5. El software funciona como un orquestador transaccional que captura eventos de mercado en una cuenta Maestra (fuente de señales) y los replica de forma asincrona en multiples cuentas Esclavas (nodos receptores).

Este proyecto permite la gestion unificada de grandes capitales distribuidos en diferentes cuentas, manteniendo siempre una gestion de riesgo proporcional y el cumplimiento estricto de las reglas de preservacion de capital exigidas por las empresas de fondeo (Prop Firms).

## Arquitectura Modular del Sistema
El software utiliza patrones de ingenieria modernos para garantizar la separacion entre la Capa de Presentacion (IT) y la Capa de Operaciones (OT):

* **main.py**: Controlador principal y ejecutor del bucle de sincronizacion.
* **trading.py**: Capa OT que interactua con la API de MetaTrader 5.
* **database.py**: Gestion del ciclo de vida y persistencia de los datos.
* **config.py**: Seguridad y manejo de archivos de configuracion.
* **interfaz.py** y **tab_*.py**: Modulos de la interfaz grafica y analitica.

## Requisitos Previos
* **Sistema Operativo**: Microsoft Windows 10 o Windows 11.
* **Plataforma Financiera**: Terminal MetaTrader 5 instalada (descargable desde metatrader5.com).



### Configuracion Critica en MetaTrader 5
Independientemente del metodo de instalacion elegido, debe activar el acceso algoritmico en MT5 para permitir la comunicacion con el software:
1. Abra su terminal **MetaTrader 5**.
2. Acceda al menu **Herramientas** (Tools) > **Opciones** (Options).
3. En la pestaña **Asesores Expertos** (Expert Advisors), marque la casilla **Permitir el trading algoritmico** (Allow Algo Trading).
4. Haga clic en **Aceptar**.

---

## Metodos de Instalacion

El evaluador puede optar por cualquiera de las siguientes dos vias para ejecutar el software:

### Metodo A: Ejecucion mediante Visual Studio Code (Entorno de Desarrollo)
Recomendado para revisar la arquitectura, el codigo fuente y la estructura de modulos.

1. **Instalacion de Python**: Descargue e instale Python 3.11+ desde `python.org` (Es fundamental marcar la casilla **Add Python to PATH** durante el proceso).
2. **Preparacion de VS Code**:
   - Abra **Visual Studio Code**.
   - Instale la extension oficial de **Python** (Microsoft).
   - Abra la carpeta del proyecto: **Archivo** > **Abrir carpeta...**
3. **Instalacion de Dependencias**: Abra una nueva terminal en VS Code (**Terminal** > **Nueva terminal**) y ejecute:
   ```bash
   pip install MetaTrader5 customtkinter pillow
4.  **Ejecucion**: En el explorador de archivos de la izquierda, abra **main.py** y presione el boton **Play** (ejecutar) en la esquina superior derecha o presione `F5`.

### Metodo B: Ejecucion mediante Archivo Portable (.exe)

Recomendado para una evaluacion funcional directa sin configurar entornos de programacion.

1.  Localice el archivo **PropSync_Manager.exe** en la carpeta raiz de la entrega.

2.  Asegurese de que la terminal **MetaTrader 5** este abierta.

3.  Haga doble clic sobre el ejecutable. El programa cargara todas las dependencias internamente y mostrara la interfaz de control de forma automatica.

------------------------
## Guia de Puesta en Marcha

Una vez iniciada la aplicacion, siga este procedimiento para iniciar la sincronizacion:

1.  **Configuracion Maestra**: En la pestaña **Configuracion de Red**, introduzca el **Login**, **Contraseña** y **Servidor** de su cuenta de MetaTrader 5. Indique el **Balance Inicial** real y pulse **Aplicar Cambios**.

2.  **Reglas de Firma**: En la subpestaña **Base de Datos de Firmas**, registre los limites de perdida permitidos (ejemplo: **5.0** para un 5% de Drawdown diario).

3.  **Registro de Nodos**: Añada los datos de una cuenta esclava. Utilice el boton **Calcular Factor** para que el sistema asigne el riesgo proporcional de forma automatica. Pulse **Registrar Nodo**.

4.  **Activacion**: En el panel lateral, pulse el boton verde **Iniciar Servicio**. El sistema validara la conexion y comenzara la vigilancia de la red en tiempo real.

Licencia
--------

Este software se distribuye bajo la licencia Open Source **MIT**.