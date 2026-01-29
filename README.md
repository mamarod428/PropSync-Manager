# PropSync Manager
### Propuesta de Proyecto: Orquestación y Gestión de Riesgos en Entornos Financieros

## Resumen de la Propuesta
Este documento presenta el plan de desarrollo para **PropSync Manager**, un software diseñado para automatizar la gestión simultánea de múltiples cuentas de inversión. El proyecto se centrará en la creación de un sistema que replique operaciones financieras en tiempo real y vigile el cumplimiento de normativas de riesgo, eliminando la falibilidad de la gestión manual.

## Justificación del Proyecto
En el contexto de las inversiones profesionales, es común gestionar capital de terceros bajo reglas estrictas de "pérdida máxima diaria". Si una cuenta supera un límite de pérdidas, se bloquea. Gestionar manualmente cinco o diez cuentas, calculando el riesgo para cada una mientras se opera en el mercado, es una tarea ineficiente y peligrosa. Este software busca actuar como un intermediario tecnológico que garantice la seguridad y escalabilidad de la operativa.

## Objetivos Funcionales
El desarrollo del software se estructurará en torno a tres pilares fundamentales:

1.  **Replicación Proporcional:** Se implementará un algoritmo capaz de detectar operaciones en una cuenta principal y replicarlas en las cuentas secundarias. El sistema ajustará matemáticamente el volumen de la operación según el capital disponible en cada cuenta, asegurando una exposición al riesgo idéntica.
2.  **Seguridad Activa:** Se desarrollará un módulo de validación que, antes de ejecutar una orden, verificará si esta infringe los límites de pérdida permitidos. Si la operación supone un riesgo de incumplimiento normativo, el sistema la bloqueará automáticamente.
3.  **Monitorización Unificada:** Se creará un panel de control web (Dashboard) para visualizar en tiempo real el estado de conexión y la salud financiera de todas las cuentas desde una única interfaz.

## Metodología y Stack Tecnológico
El proyecto se construirá utilizando **Python** como lenguaje principal debido a su capacidad de integración y análisis de datos.

* **Conectividad:** Se utilizará la librería `MetaTrader5` para interactuar directamente con los terminales de operación instalados localmente.
* **Interfaz:** El dashboard se desarrollará sobre `Streamlit` para permitir una visualización de datos ágil y accesible.
* **Arquitectura:** El sistema seguirá un modelo maestro-esclavo, procesando los datos en local para garantizar la mínima latencia posible en la ejecución.

## Resultados Esperados
Al finalizar el proyecto, se entregará un prototipo funcional que demuestre cómo la automatización de procesos (IT) aplicada a la operativa de mercados (OT) puede proteger el capital y optimizar la toma de decisiones en entornos de alta presión.
