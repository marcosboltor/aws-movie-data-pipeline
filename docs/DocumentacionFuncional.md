# Documentación Funcional  
# Sistema de Analítica de Películas TMDb en AWS

**Proyecto:** AWS/TMDb Data Lake  
**Fecha:** Mayo 2026  
**Versión:** 1.0

---

## 1. Objetivo del documento

Este documento describe el sistema desde una perspectiva funcional, es decir, qué hace la solución, qué usuarios la utilizan, qué procesos soporta y qué valor aporta. No profundiza en código ni configuración interna de infraestructura.

El sistema permite consultar y analizar información de películas populares obtenidas desde TMDb API, procesadas en AWS y visualizadas mediante herramientas analíticas como Athena y Power BI.

---

## 2. Descripción funcional del sistema

El sistema AWS/TMDb permite construir un flujo de datos para análisis de películas. Su función principal es obtener información periódica desde TMDb, almacenarla en un Data Lake, transformarla en datos confiables y exponerla para consultas y visualización.

La solución permite responder preguntas como:

- ¿Cuáles son las películas más populares?
- ¿Qué idiomas concentran más películas populares?
- ¿Qué películas tienen mejor promedio de voto?
- ¿Qué géneros presentan mayor popularidad?
- ¿Cómo se distribuyen las películas por fecha de estreno?
- ¿Qué películas tienen alta popularidad pero bajo volumen de votos?

---

## 3. Usuarios del sistema

| Rol | Responsabilidades |
|---|---|
| Analista de datos | Consulta datasets en Athena, valida resultados y genera análisis. |
| Data Engineer | Mantiene el flujo de ingesta, transformación, catálogo y automatización. |
| Usuario de negocio / Stakeholder | Consulta visualizaciones en Power BI para interpretar métricas. |
| Evaluador académico | Revisa funcionamiento, documentación, arquitectura y evidencias del proyecto. |

---

## 4. Procesos funcionales soportados

### 4.1 Ingesta de información de películas

El sistema obtiene datos desde TMDb API, específicamente información relacionada con películas populares. Este proceso puede ejecutarse manualmente o de forma programada mediante EventBridge.

Resultado esperado:

- Nuevos archivos almacenados en la capa Bronze de S3.
- Conservación de datos de origen para trazabilidad.

### 4.2 Centralización de datos

Los datos obtenidos desde TMDb se almacenan en Amazon S3 como repositorio central. Esto evita depender exclusivamente de llamadas directas a la API para cada análisis.

Resultado esperado:

- Datos disponibles en un Data Lake.
- Separación por capas de procesamiento.
- Organización por prefijos como Bronze, Silver y Gold.

### 4.3 Limpieza y estructuración

El sistema transforma los datos crudos en una versión limpia y consultable. En esta etapa se seleccionan campos relevantes, se ajustan tipos de datos y se preparan archivos para consulta eficiente.

Resultado esperado:

- Datos limpios en capa Silver.
- Columnas consistentes.
- Datos listos para consulta con Athena.

### 4.4 Generación de capa analítica

A partir de los datos Silver se crean datasets o consultas Gold orientadas a indicadores. Esta capa permite análisis más directo desde Athena y Power BI.

Resultado esperado:

- Tablas o resultados Gold.
- Consultas enfocadas en métricas de popularidad, votos, géneros, idioma y fechas.

### 4.5 Consulta SQL

El sistema permite que un analista ejecute consultas SQL sobre los datos almacenados en S3 mediante Athena.

Resultado esperado:

- Consultas sin necesidad de una base de datos tradicional.
- Validación rápida de datos procesados.
- Resultados exportables o conectables a BI.

### 4.6 Visualización en Power BI

El sistema permite consumir datos desde Power BI mediante conexión ODBC hacia Athena.

Resultado esperado:

- Tableros con métricas de películas.
- Visualizaciones para presentación ejecutiva.
- Análisis más accesible para usuarios no técnicos.

---

## 5. Casos de uso

### Caso de uso 1: Consultar películas más populares

**Actor principal:** Analista de datos.  
**Descripción:** El analista desea identificar las películas con mayor popularidad en el conjunto de datos procesado.  
**Flujo esperado:**

1. El analista consulta la tabla en Athena.
2. Ordena los datos por `popularity`.
3. Obtiene un ranking de películas.
4. Usa el resultado para visualización o análisis.

**Resultado:** Ranking de películas populares disponible para reporte.

---

### Caso de uso 2: Analizar popularidad por idioma

**Actor principal:** Analista de datos o stakeholder.  
**Descripción:** Se desea conocer qué idiomas concentran mayor número de películas populares o mayor popularidad promedio.  
**Flujo esperado:**

1. El usuario consulta datos por `original_language`.
2. El sistema agrupa películas por idioma.
3. Se calcula conteo, popularidad promedio y calificación promedio.
4. El resultado se visualiza en Athena o Power BI.

**Resultado:** Comparación analítica por idioma original.

---

### Caso de uso 3: Validar actualización de datos

**Actor principal:** Data Engineer.  
**Descripción:** El responsable técnico revisa si la ingesta programada generó datos nuevos.  
**Flujo esperado:**

1. Se revisa la ejecución de Lambda.
2. Se valida la existencia de archivos nuevos en S3 Bronze.
3. Se revisa que los datos aparezcan en Silver o Gold.
4. Se ejecuta consulta de conteo en Athena.

**Resultado:** Confirmación de actualización correcta del pipeline.

---

### Caso de uso 4: Crear tablero ejecutivo

**Actor principal:** Usuario de negocio o equipo del proyecto.  
**Descripción:** Se desea presentar métricas principales del conjunto de películas.  
**Flujo esperado:**

1. Power BI se conecta a Athena.
2. Se seleccionan tablas o consultas Gold.
3. Se construyen visualizaciones.
4. Se presentan KPIs principales.

**Resultado:** Tablero listo para exposición ejecutiva.

---

### Caso de uso 5: Reprocesar información

**Actor principal:** Data Engineer.  
**Descripción:** Si se detecta un error en datos procesados, el equipo puede usar Bronze como fuente histórica para reprocesar Silver o Gold.  
**Flujo esperado:**

1. Se identifica el archivo o partición afectada.
2. Se corrige el proceso de transformación.
3. Se vuelve a generar Silver o Gold.
4. Se actualiza catálogo y consultas.

**Resultado:** Datos corregidos sin depender de una nueva llamada a la API.

---

## 6. Reglas funcionales

- La API Key de TMDb no debe estar expuesta en el código fuente.
- Los datos crudos deben conservarse en Bronze antes de transformarse.
- La capa Silver debe contener datos estructurados y consultables.
- La capa Gold debe orientarse a análisis y visualización.
- Las consultas deben ejecutarse desde Athena sobre tablas registradas en Glue Data Catalog.
- La conexión con Power BI debe usar datos ya disponibles en Athena.
- El pipeline debe poder ejecutarse manualmente y, cuando aplique, mediante EventBridge.
- Las evidencias de implementación deben agregarse al repositorio sin mostrar secretos.
- Los nombres exactos de buckets, secretos o recursos deben documentarse solo si no comprometen seguridad.

---

## 7. Indicadores funcionales

Los indicadores que el sistema puede soportar incluyen:

| Indicador | Descripción |
|---|---|
| Total de películas procesadas | Número de registros disponibles para análisis. |
| Popularidad promedio | Promedio de la métrica `popularity`. |
| Calificación promedio | Promedio de `vote_average`. |
| Total de votos | Suma o análisis de `vote_count`. |
| Películas por idioma | Conteo por `original_language`. |
| Películas por género | Conteo o popularidad por género, si el dato fue transformado. |
| Ranking de popularidad | Lista ordenada por `popularity`. |
| Ranking de calificación | Lista ordenada por `vote_average`, considerando `vote_count`. |

---

## 8. Entradas y salidas del sistema

### 8.1 Entradas

- Datos obtenidos desde TMDb API.
- Parámetros configurados en Secrets Manager.
- Programación de EventBridge.
- Consultas SQL definidas por el equipo.
- Configuración ODBC para Power BI.

### 8.2 Salidas

- Archivos Bronze en S3.
- Archivos Silver limpios.
- Datasets o tablas Gold.
- Tablas registradas en Glue Data Catalog.
- Resultados de consulta en Athena.
- Visualizaciones en Power BI.
- Evidencias y documentación del proyecto.

---

## 9. Beneficios esperados

- Centralización de datos de TMDb en AWS.
- Separación clara entre datos crudos, limpios y analíticos.
- Consulta SQL sin necesidad de base de datos tradicional.
- Automatización de la ingesta.
- Visualización de datos desde Power BI.
- Repositorio documentado y defendible.
- Buenas prácticas básicas de seguridad al no exponer credenciales.

---

## 10. Limitaciones funcionales

- La calidad y disponibilidad de datos depende de TMDb API.
- El proyecto no garantiza actualización automática en Power BI Desktop por sí solo.
- La visualización depende de la conexión ODBC y configuración de Athena.
- La capa Gold depende de las consultas definidas por el equipo.
- No se contempla, dentro del alcance base, un sistema productivo multiusuario.
- No se incluyen modelos predictivos o machine learning como funcionalidad principal.

---

## 11. Glosario

| Término | Definición |
|---|---|
| TMDb | The Movie Database, fuente de datos de películas. |
| API | Interfaz que permite consultar datos desde una aplicación externa. |
| Data Lake | Repositorio central para almacenar datos en distintos formatos. |
| Bronze | Capa de datos crudos. |
| Silver | Capa de datos limpios y estructurados. |
| Gold | Capa de datos refinados para análisis. |
| Athena | Servicio AWS para consultar datos en S3 usando SQL. |
| Glue Data Catalog | Catálogo de metadatos para tablas y esquemas. |
| Glue Crawler | Servicio que detecta estructura de datos en S3. |
| Lambda | Servicio serverless para ejecutar código bajo demanda. |
| EventBridge | Servicio para programar o disparar eventos. |
| Secrets Manager | Servicio para almacenar secretos y configuraciones sensibles. |
| Power BI | Herramienta de visualización y análisis de datos. |
| ODBC | Estándar de conexión entre aplicaciones y fuentes de datos. |

---

## 12. Conclusión

El sistema AWS/TMDb permite construir un flujo funcional de analítica de películas utilizando servicios de AWS. Desde una perspectiva de usuario, la solución permite consultar, analizar y visualizar información de TMDb de forma centralizada, estructurada y defendible para una entrega académica.
