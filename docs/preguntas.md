# Proyecto 2: Software para la Transformacion Digital - Analisis Teorico

## 1. Ciclo de vida del dato (5b)

**¿Como se gestionan los datos desde su generacion hasta su eliminacion en tu proyecto?**
La gestion de datos en PropSync Manager sigue un flujo estricto para garantizar la velocidad de ejecucion:
* **Generacion:** Los datos se generan en el entorno OT (Broker) y son capturados mediante el modulo `trading.py`.
* **Procesamiento:** Los datos crudos se normalizan en la memoria RAM para realizar calculos de riesgo dinamico.
* **Persistencia:** Los vinculos entre ordenes se guardan en archivos JSON localmente para permitir la recuperacion ante fallos del sistema.
* **Eliminacion:** Al detectarse el cierre de una operacion en el mercado real, el registro activo se purga de la base de datos viva (`mapa_operaciones.json`) y se traslada al archivo de historico.

**¿Que estrategia sigues para garantizar la consistencia e integridad de los datos?**
Se utiliza una estrategia de **Mapeo de Tickets Bidireccional**. Cada operacion maestra tiene un identificador unico vinculado a un identificador en cada nodo. El sistema realiza una validacion cruzada cada 500 milisegundos para asegurar que el estado en la base de datos local coincide exactamente con el estado del servidor del broker, eliminando cualquier discrepancia de forma automatica.

## 2. Almacenamiento en la nube (5f)

**¿Que alternativas consideraste para almacenar datos y por que elegiste tu solucion actual?**
Se considero el uso de bases de datos NoSQL en la nube (como Google Firebase). Sin embargo, se opto por un almacenamiento de **Edge Computing (Local JSON)** por una razon tecnica critica: la latencia. En el trading de alta frecuencia, un retraso de 200ms en la nube puede suponer perdidas financieras por deslizamiento de precios (Slippage). La ejecucion local garantiza una respuesta instantanea.

**Si no usas la nube, ¿como podrias integrarla en futuras versiones?**
La nube se integrara en la version 2.0 como una capa de **Backup y Analitica Asincrona**. Mientras que la ejecucion seguira siendo local, los datos del historial se sincronizaran con un bucket de AWS S3 para permitir al usuario consultar sus estadisticas desde una aplicacion movil o entorno web sin interferir con la ejecucion del bot.

## 3. Seguridad y regulacion (5i)

**¿Que medidas de seguridad implementaste para proteger los datos o procesos en tu proyecto?**
Se han implementado protocolos de **Seguridad Transaccional**. El software utiliza el parametro de desviacion maxima para rechazar ordenes si el precio de mercado ha cambiado bruscamente durante el proceso de copiado. Asimismo, la informacion sensible se almacena de forma local, evitando exposiciones en servidores externos.

**¿Que normativas (e.g., GDPR) podrian afectar el uso de tu software y como las has tenido en cuenta?**
El software cumple con los principios de **Privacidad desde el Diseno** de la GDPR. Al no recopilar, centralizar ni procesar datos personales o financieros en servidores externos al equipo del usuario, se garantiza que el operador mantiene la soberania absoluta sobre su informacion sensible.

## 4. Implicacion de las THD en negocio y planta (2e)

**¿Que impacto tendria tu software en un entorno de negocio o en una planta industrial?**
El impacto es la **Eliminacion de Cuellos de Botella Operativos**. En un entorno de gestion de fondos, un solo operador puede supervisar una red masiva de capital que antes requeriria un equipo de varias personas, optimizando los recursos humanos y financieros del negocio.

**¿Como crees que tu solucion podria mejorar procesos operativos o la toma de decisiones?**
Mejora la precision mediante la **Automatizacion de Reglas de Riesgo**. El sistema monitoriza los Drawdowns (niveles de perdida) de forma mas rapida y precisa que un humano, tomando decisiones de bloqueo de operativa en milisegundos para proteger el capital de la empresa ante volatilidades imprevistas.

## 5. Mejoras en IT y OT (2f)

**¿Como puede tu software facilitar la integracion entre entornos IT y OT?**
Actua como un **Middleware de Integracion**. Toma la tecnologia operativa (OT), que son las terminales de trading y los protocolos de ejecucion de ordenes, y los integra en un entorno IT (Interfaz CustomTkinter y Bases de Datos JSON), permitiendo una administracion centralizada y analitica del proceso.

**¿Que procesos especificos podrian beneficiarse de tu solucion en terminos de automatizacion o eficiencia?**
El proceso de **Sincronizacion de Carteras**. La replicacion manual de una estrategia en 10 cuentas distintas es ineficiente y propensa a errores de digitacion. Este software automatiza el 100% de ese flujo de trabajo.

## 6. Tecnologias Habilitadoras Digitales (2g)

**¿Que tecnologias habilitadoras digitales (THD) has utilizado o podrias integrar en tu proyecto?**
La THD principal utilizada es el **RPA (Robotic Process Automation)**, mediante algoritmos que emulan y optimizan la interaccion humana con las terminales financieras.

**¿Como mejoran estas tecnologias la funcionalidad o el alcance de tu software?**
El RPA permite la **Omnicanalidad Transaccional**. Sin esta tecnologia, el alcance del software estaria limitado a una sola cuenta. Al integrar automatizacion robotica, el alcance se vuelve virtualmente ilimitado, permitiendo gestionar redes de nodos de cualquier tamano con una sola fuente de datos.