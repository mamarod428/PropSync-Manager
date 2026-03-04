# PropSync Manager - Enterprise Edition

## Descripcion del Proyecto
PropSync Manager es una solucion de software avanzada para la automatizacion de procesos roboticos (RPA) dentro del ecosistema de los mercados financieros. Su funcion principal es actuar como un orquestador transaccional que sincroniza, en tiempo real, las operaciones ejecutadas en una cuenta maestra hacia multiples cuentas esclavas o nodos.

El software resuelve el problema de la escalabilidad y la precision en la gestion de carteras distribuidas. Mediante el uso de tecnologias de baja latencia, permite que un operador humano o un sistema automatizado gestione un capital global diversificado en multiples terminales MetaTrader 5 sin incurrir en errores de calculo de riesgo manual.

## Arquitectura Modular del Sistema
El software ha sido desarrollado siguiendo patrones de ingenieria de software modernos, dividiendo la logica en modulos independientes para garantizar la mantenibilidad y escalabilidad:

* **main.py**: Controlador principal que orquesta el bucle de trading y la sincronizacion IT/OT.
* **interfaz.py**: Orquestador visual que gestiona la carga de modulos UI.
* **ui_tabs.py**: Componentes especificos de cada pestana del programa.
* **ui_components.py**: Elementos visuales reutilizables y sistemas de ayuda al usuario.
* **trading.py**: Capa de Tecnologia de Operaciones (OT) que interactua con la API de MetaTrader 5.
* **database.py**: Gestion del ciclo de vida del dato y persistencia en disco local.
* **config.py**: Manejo de credenciales y parametros de seguridad del sistema.

## Requisitos del Sistema
* Sistema Operativo: Windows 10/11.
* Software de Terceros: Terminal MetaTrader 5 instalado y configurado.
* Lenguaje: Python 3.11 o superior.

## Instalacion y Puesta en Marcha
1. Descargue el codigo fuente en su directorio local.
2. Instale las dependencias necesarias mediante la consola de comandos:
   ```bash
   pip install MetaTrader5 customtkinter pillow
3. Asegurese de que su terminal MetaTrader 5 este abierta y con sesion iniciada en la cuenta que desea utilizar.

## Guia de Puesta en Marcha

Para poner en funcionamiento el sistema de sincronizacion, siga este procedimiento:

1. **Configuracion Maestra**: Acceda a la pestana **Configuracion de Red** y complete los datos de su cuenta lider. Indique el balance inicial para un calculo correcto del riesgo.
2. **Definicion de Reglas**: En la subpestana **Base de Datos de Firmas**, registre los limites de perdida (Drawdown) permitidos por su empresa de fondeo o su gestion personal.
3. **Registro de Nodos**: Anada las cuentas esclavas indicando sus credenciales. Utilice la herramienta **Calcular Factor** para establecer la proporcion de riesgo adecuada.
4. **Activacion**: En el panel lateral izquierdo, pulse el boton **Iniciar Servicio**. El sistema realizara una validacion de conexion y comenzara la vigilancia activa de la red.

## Licencia

Este software se distribuye bajo la licencia Open Source MIT.