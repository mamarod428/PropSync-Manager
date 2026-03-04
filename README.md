# PropSync Manager - Enterprise Edition

## 1. Descripcion del Proyecto
PropSync Manager es una solucion avanzada de automatizacion de procesos roboticos (RPA) diseñada para la gestion sincronizada de terminales financieras MetaTrader 5. El software captura eventos de mercado en una cuenta **Maestra** y los replica instantaneamente en multiples cuentas **Esclavas**.

Este proyecto permite gestionar grandes capitales distribuidos manteniendo una gestion de riesgo proporcional y cumpliendo las reglas de preservacion de capital de las empresas de fondeo (Prop Firms).

## 2. Arquitectura Modular del Sistema
El software divide su logica en componentes especializados para garantizar la escalabilidad y el orden (Grado Enterprise):

* **Raiz (`/`):** Contiene el punto de entrada `main.py` y archivos de configuracion.
* **Modulos (`/modules`):** Contiene la logica de trading (`trading.py`), base de datos (`database.py`) y los componentes visuales (`interfaz.py`, `tab_*.py`).
* **Datos (`/data`):** Almacenamiento local de credenciales e historial en formato JSON.
* **Recursos (`/assets`):** Iconos y elementos graficos del sistema.

## 3. Requisitos Previos (Antes de empezar)
1.  **Sistema Operativo:** Windows 10 o 11.
2.  **MetaTrader 5 (MT5):** Debe estar instalado. Si no lo tiene, descarguelo gratis desde [metatrader5.com](https://www.metatrader5.com/).
3.  **Python:** Descargue la version 3.11 o superior desde [python.org](https://www.python.org/). 
    * **IMPORTANTE:** Durante la instalacion de Python, marque la casilla que dice **"Add Python to PATH"**.

---

## 4. Configuracion Critica de MetaTrader 5
Para que el software pueda "hablar" con su cuenta de trading, debe activar este permiso:
1.  Abra su terminal **MetaTrader 5**.
2.  Vaya al menu superior: **Herramientas (Tools)** > **Opciones (Options)**.
3.  Haga clic en la pestaña **Asesores Expertos (Expert Advisors)**.
4.  Marque la casilla **Permitir el trading algoritmico (Allow Algo Trading)**.
5.  Haga clic en **Aceptar**.
6.  **Asegurese de tener la sesion iniciada en su cuenta de trading.**

---

## 5. Instalacion Paso a Paso (Mediante VS Code)

Siga estos pasos exactamente para poner el programa en marcha:

### Paso 1: Descargar el Proyecto
1.  En la pagina de este repositorio en GitHub, haga clic en el boton verde **"Code"**.
2.  Seleccione **"Download ZIP"**.
3.  Extraiga el contenido del archivo en una carpeta de su escritorio.

### Paso 2: Preparar Visual Studio Code
1.  Abra **Visual Studio Code**.
2.  Instale la extension oficial de **Python** (busquela en el icono de cuadrados en la barra izquierda).
3.  Vaya a **Archivo** > **Abrir carpeta...** y seleccione la carpeta donde extrajo el proyecto.

### Paso 3: Instalar librerias necesarias
1.  Abra una terminal dentro de VS Code (Menu **Terminal** > **Nueva terminal**).
2.  Copie, pegue y presione Enter para ejecutar este comando:
    ```bash
    pip install MetaTrader5 customtkinter pillow matplotlib
    ```

### Paso 4: Ejecucion
1.  En el listado de archivos de la izquierda, busque y haga clic en `main.py`.
2.  Presione la tecla **F5** o haga clic en el boton de **Play** (triangulo) en la esquina superior derecha.

---

## 6. Guia de Puesta en Marcha (Uso del Programa)

Una vez que la ventana de **PropSync Manager** se abra, siga este orden:

1.  **Configuracion Maestra:** * Vaya a la pestaña **Configuracion de Red**.
    * Introduzca su numero de cuenta (Login), su contraseña y el servidor de su broker.
    * Escriba su **Balance Inicial** (el dinero que tiene la cuenta actualmente).
    * Haga clic en **Aplicar Cambios**.

2.  **Base de Datos de Firmas:** * En la subpestaña de firmas, registre los limites de su cuenta (ej: introduzca **5.0** si su limite de perdida diaria es del 5%). Esto sirve para que el programa vigile su riesgo.

3.  **Registro de Cuentas Esclavas:** * Añada los datos de las cuentas donde quiere que se copien las operaciones. 
    * Use el boton **Calcular Factor** para que el sistema asigne automaticamente el tamaño de las operaciones segun el capital de cada cuenta.
    * Haga clic en **Registrar Nodo**.

4.  **Activacion Final:** * En el panel oscuro de la izquierda, haga clic en el boton verde **Iniciar Servicio**.
    * El programa confirmara la conexion y aparecera un mensaje: `[SISTEMA EN EJECUCION]`. A partir de este momento, todo lo que haga en la cuenta Maestra se replicara en las demas.

---

## 7. Indice de Correccion para el Evaluador
Este proyecto cumple con los siguientes criterios academicos localizables en el codigo:

* **Criterio 2e (Beneficios):** Automatizacion RPA en `modules/trading.py`.
* **Criterio 2f (IT/OT):** Integracion de API financiera en `modules/tab_dashboard.py`.
* **Criterio 5b (Dato):** Gestion del ciclo de vida en `modules/database.py`.
* **Criterio 5i (Seguridad):** Ofuscacion de credenciales en `modules/tab_configuracion.py`.

## Licencia
Este software se distribuye bajo la licencia Open Source **MIT**.