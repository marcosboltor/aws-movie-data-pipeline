# Solicitud de Propuesta (RFP)  
# Implementación de Infraestructura de Datos para Analítica de TMDb en AWS

**Proyecto:** Data Lake AWS/TMDb  
**Fuente de datos:** TMDb API  
**Fecha:** Mayo 2026  
**Repositorio sugerido:** `aws-tmdb-data-lake`

---

## 1. Introducción y antecedentes

El proyecto AWS/TMDb tiene como propósito construir una infraestructura de datos en la nube para extraer, almacenar, transformar, consultar y visualizar información de películas provenientes de la API de TMDb.

El sistema busca resolver una necesidad analítica concreta: disponer de un flujo reproducible y automatizado que permita consultar información histórica y actualizada sobre películas populares, métricas de audiencia, popularidad, votos, géneros, fechas de estreno e idioma original.

La solución se plantea bajo una arquitectura tipo Data Lake con capas Medallion: Bronze, Silver y Gold. El diseño prioriza servicios administrados de AWS, bajo costo operativo y uso eficiente de recursos, procurando mantenerse dentro de un enfoque compatible con Free Tier cuando sea posible.

---

## 2. Objetivo del RFP

Solicitar una propuesta técnica para diseñar e implementar una solución de datos en AWS que permita:

- Extraer datos desde la API de TMDb.
- Almacenar datos crudos en Amazon S3.
- Transformar y limpiar la información en capas intermedias.
- Generar datasets analíticos en una capa Gold.
- Consultar la información mediante Amazon Athena.
- Visualizar resultados en Power BI.
- Automatizar la ingesta mediante Amazon EventBridge y AWS Lambda.

---

## 3. Alcance técnico requerido

La propuesta debe cubrir los siguientes elementos técnicos.

### 3.1 Arquitectura de datos

La solución debe implementar una arquitectura por capas:

- **Bronze:** almacenamiento de datos crudos provenientes de TMDb.
- **Silver:** datos limpios, tipados y normalizados.
- **Gold:** datos refinados para consulta analítica y visualización.

### 3.2 Ingesta de datos

La ingesta debe realizarse desde la API de TMDb utilizando una función AWS Lambda. La configuración sensible, como API Key, URL base, endpoint y bucket de destino, debe gestionarse mediante AWS Secrets Manager o variables configurables de entorno.

### 3.3 Almacenamiento

Los datos deben almacenarse en Amazon S3, organizados por prefijos o carpetas lógicas para separar las capas del Data Lake. La estructura utilizada en el proyecto contempla rutas equivalentes a:

- `1bronce/`
- `2silver/`
- `3gold/`

Cuando aplique, los datos deben escribirse en formato Parquet para mejorar eficiencia de consulta en Athena.

### 3.4 Catálogo y consulta

La solución debe utilizar AWS Glue Crawler y AWS Glue Data Catalog para registrar tablas y metadatos consultables desde Amazon Athena. Athena será el motor principal de consulta SQL sobre los archivos almacenados en S3.

### 3.5 Automatización

La ejecución periódica de la ingesta debe automatizarse con Amazon EventBridge, disparando la función Lambda en la frecuencia definida por el equipo. En el proyecto se trabajó con una programación controlada para reducir costos y evitar ejecuciones innecesarias.

### 3.6 Visualización

La capa de consumo debe permitir conexión con Power BI. En la implementación se validó una conexión mediante ODBC genérico hacia Amazon Athena, permitiendo consultar resultados analíticos desde Power BI.

### 3.7 Seguridad y gobernanza

La solución debe considerar:

- Uso de IAM con principio de menor privilegio.
- Manejo seguro de credenciales mediante Secrets Manager.
- Separación lógica de capas en S3.
- Control de acceso a consultas y resultados de Athena.
- Evitar exponer la API Key en código fuente.

---

## 4. Requerimientos de la propuesta

La propuesta deberá incluir:

| Sección | Contenido esperado |
|---|---|
| Perfil del equipo | Experiencia del equipo en AWS, Python, SQL, almacenamiento en S3 y analítica de datos. |
| Metodología de trabajo | Fases de diseño, implementación, validación, documentación y entrega. |
| Arquitectura propuesta | Servicios AWS utilizados y justificación técnica. |
| Procesamiento de datos | Descripción del flujo Bronze, Silver y Gold. |
| Seguridad | Gestión de secretos, permisos IAM y protección de credenciales. |
| Entregables | Código, documentación, diagramas, evidencias, presentación y pruebas. |
| Costos y tiempos | Estimación general de ejecución, considerando uso eficiente de recursos. |

---

## 5. Criterios de evaluación

La propuesta será evaluada con base en los siguientes criterios:

- **Comprensión técnica del problema:** 40%.
- **Viabilidad de la arquitectura propuesta:** 25%.
- **Automatización y reproducibilidad:** 15%.
- **Claridad de documentación y evidencias:** 10%.
- **Control de costos y uso responsable de recursos:** 10%.

---

## 6. Entregables esperados

Los entregables mínimos del proyecto son:

- Código fuente de ingesta y transformación.
- Scripts SQL utilizados en Athena.
- Documentación funcional.
- Documentación técnica.
- Documentación de arquitectura.
- SOW.
- RFP.
- Diagrama de arquitectura.
- Diagrama de flujo o secuencia del pipeline.
- Capturas de evidencia de implementación en AWS.
- Presentación ejecutiva.
- Instructivo para replicar el proyecto.
- Pruebas realizadas, cuando apliquen.

---

## 7. Condiciones de entrega

El proyecto deberá entregarse en un repositorio de GitHub con estructura clara. Se recomienda mantener la documentación en formato Markdown para que sea visible directamente desde GitHub, y opcionalmente exportarla a PDF si el profesor lo solicita.

Estructura sugerida:

```text
deploy/
docs/
iac/
img/
ppt/
src/
tests/
README.md
```

---

## 8. Restricciones y supuestos

- La solución se construye con fines académicos.
- Se prioriza el uso de servicios administrados de AWS.
- Se evita incluir credenciales, API Keys o secretos en el repositorio.
- El procesamiento se diseña para un volumen manejable de datos de TMDb.
- Power BI funciona como herramienta externa de visualización conectada a Athena.
- La infraestructura puede documentarse aunque no todos los recursos se desplieguen mediante CloudFormation, si el alcance real del proyecto fue implementado manualmente desde consola.

---

## 9. Conclusión

El proyecto solicitado debe demostrar un flujo integral de datos en AWS: desde la ingesta de información desde TMDb hasta la consulta y visualización de indicadores analíticos. La propuesta debe ser técnicamente defendible, reproducible, segura y suficientemente documentada para permitir su revisión en GitHub.
