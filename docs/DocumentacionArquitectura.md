# Documentación de Arquitectura  
# Implementación de Data Lake AWS/TMDb

**Proyecto:** AWS/TMDb Data Lake  
**Fecha:** Mayo 2026  
**Versión:** 1.0

---

## 1. Resumen ejecutivo

Este documento describe la arquitectura del sistema de datos implementado para analizar información de películas obtenida desde TMDb API.

La solución sigue una arquitectura Medallion con tres capas principales: Bronze, Silver y Gold. Amazon S3 funciona como almacenamiento central del Data Lake. AWS Lambda realiza la ingesta desde TMDb API. AWS Glue Crawler y Glue Data Catalog permiten registrar los metadatos. Amazon Athena permite ejecutar consultas SQL sobre los datos almacenados en S3. Finalmente, Power BI se conecta a Athena mediante ODBC para la visualización de información.

La arquitectura fue diseñada para ser simple, reproducible, de bajo costo y adecuada para un proyecto académico de analítica en AWS.

---

## 2. Objetivo de la arquitectura

Diseñar un flujo de datos que permita:

- Ingerir datos desde TMDb API.
- Almacenar datos crudos y transformados en Amazon S3.
- Separar la información por capas de procesamiento.
- Consultar los datos con SQL mediante Athena.
- Generar una capa Gold para análisis.
- Conectar la información con Power BI.
- Automatizar la ingesta mediante EventBridge.
- Mantener credenciales fuera del código fuente.

---

## 3. Stack tecnológico

| Componente | Servicio / herramienta | Uso dentro del proyecto |
|---|---|---|
| Fuente de datos | TMDb API | Origen de datos de películas populares. |
| Ingesta | AWS Lambda | Extracción de datos desde la API. |
| Configuración segura | AWS Secrets Manager | Almacenamiento de API Key y parámetros configurables. |
| Almacenamiento | Amazon S3 | Data Lake con capas Bronze, Silver y Gold. |
| Catálogo | AWS Glue Data Catalog | Registro de tablas y metadatos. |
| Descubrimiento de esquema | AWS Glue Crawler | Detección de archivos, esquemas y particiones. |
| Consulta | Amazon Athena | Motor SQL sobre S3. |
| Automatización | Amazon EventBridge | Programación de ejecuciones de ingesta. |
| Visualización | Power BI | Tableros y análisis conectados a Athena. |
| Conectividad BI | ODBC genérico / Athena ODBC | Conexión entre Power BI y Athena. |

---

## 4. Vista conceptual de la arquitectura

```text
TMDb API
   |
   v
AWS Lambda
   |
   | obtiene configuración desde
   v
AWS Secrets Manager
   |
   v
Amazon S3 - Bronze
   |
   v
Transformación / limpieza
   |
   v
Amazon S3 - Silver
   |
   v
Agregación / refinamiento
   |
   v
Amazon S3 - Gold
   |
   v
AWS Glue Crawler + Glue Data Catalog
   |
   v
Amazon Athena
   |
   v
Power BI
```

---

## 5. Descripción de capas Medallion

### 5.1 Capa Bronze

La capa Bronze almacena los datos crudos obtenidos desde TMDb API. Su objetivo es conservar la información de origen con el menor procesamiento posible.

Características:

- Contiene respuestas originales o semiestructuradas de TMDb.
- Permite reprocesamiento en caso de errores.
- Conserva evidencia histórica de ingestas.
- Puede organizarse por fecha de ingesta, página o timestamp.

Ejemplo de ruta:

```text
s3://<bucket>/1bronce/tmdb/popular/
```

### 5.2 Capa Silver

La capa Silver contiene datos limpios y estructurados. En esta capa se aplican transformaciones básicas para que la información pueda consultarse de forma confiable.

Transformaciones esperadas:

- Selección de campos relevantes.
- Conversión de tipos de datos.
- Normalización de fechas.
- Control de duplicados.
- Inclusión de campos de trazabilidad como fecha o timestamp de ingesta.
- Escritura en formato Parquet cuando aplique.

Campos trabajados en el proyecto incluyen, entre otros:

- `release_date`
- `popularity`
- `vote_average`
- `vote_count`
- `genres`
- `audience_score`
- `original_title`
- `original_language`
- `adult`
- `overview`
- `source_page`
- `ingestion_timestamp`
- `ingestion_date`

Ejemplo de ruta:

```text
s3://<bucket>/2silver/
```

### 5.3 Capa Gold

La capa Gold contiene datos refinados para análisis y visualización. En esta capa se preparan consultas, agregaciones o tablas finales que responden preguntas de negocio.

Ejemplos de análisis:

- Popularidad promedio por género.
- Promedio de votos por género.
- Películas con mayor puntuación.
- Comparación por idioma original.
- Evolución por fecha de estreno.
- Detección de películas populares con alto o bajo volumen de votos.

Ejemplo de ruta:

```text
s3://<bucket>/3gold/
```

---

## 6. Flujo de datos

1. EventBridge activa la función Lambda de acuerdo con la programación definida.
2. Lambda consulta TMDb API usando parámetros almacenados en Secrets Manager.
3. Lambda guarda los datos obtenidos en Amazon S3 dentro de la capa Bronze.
4. Los datos se transforman para generar una capa Silver limpia y estructurada.
5. A partir de Silver se generan datasets o tablas Gold para consumo analítico.
6. Glue Crawler detecta esquemas, archivos y particiones.
7. Glue Data Catalog registra las tablas disponibles.
8. Athena consulta los datos usando SQL.
9. Power BI se conecta a Athena mediante ODBC para crear reportes.

---

## 7. Componentes principales

### 7.1 TMDb API

Es la fuente externa de datos. Se utilizó para obtener información de películas populares. La API requiere una llave de acceso que no debe almacenarse directamente en el repositorio.

### 7.2 AWS Lambda

Ejecuta el proceso de ingesta. Su función principal es conectarse a TMDb API, recuperar datos y almacenarlos en S3.

### 7.3 AWS Secrets Manager

Se usa para almacenar parámetros sensibles o configurables, como:

- API Key.
- URL base.
- Endpoint.
- Bucket de destino.
- Prefijos de almacenamiento.

### 7.4 Amazon S3

Es el repositorio central del Data Lake. Separa los datos en capas Bronze, Silver y Gold.

### 7.5 AWS Glue Crawler

Identifica estructura, columnas y particiones de los datos almacenados en S3. Permite que Athena consulte los datos mediante tablas del catálogo.

### 7.6 AWS Glue Data Catalog

Funciona como catálogo de metadatos. En el proyecto se trabajó con una base de datos asociada a películas TMDb, por ejemplo `db_movies_tmdb`.

### 7.7 Amazon Athena

Permite ejecutar SQL sobre archivos almacenados en S3. Se utiliza para validar datos, consultar Silver y generar o consultar resultados Gold.

### 7.8 Amazon EventBridge

Automatiza la ejecución periódica de la ingesta. La frecuencia debe definirse considerando costos, límites de API y necesidades de actualización.

### 7.9 Power BI

Herramienta de visualización conectada a Athena mediante ODBC. Permite construir reportes y tableros a partir de los datos procesados.

---

## 8. Seguridad

La arquitectura considera los siguientes controles:

- Uso de Secrets Manager para no exponer la API Key.
- Políticas IAM con permisos mínimos necesarios.
- Separación de responsabilidades por servicio.
- Evitar subir archivos `.env`, credenciales o claves al repositorio.
- Controlar permisos sobre S3, Lambda, Glue y Athena.
- Definir una ubicación específica para resultados de consultas Athena.

---

## 9. Consideraciones de costo

Para reducir costos:

- Se usa una arquitectura serverless cuando es posible.
- Lambda se ejecuta bajo demanda o por programación.
- EventBridge evita ejecuciones manuales innecesarias.
- Athena cobra por datos escaneados, por lo que se recomienda usar Parquet y particiones.
- Se limita el número de páginas consultadas de TMDb.
- No se utilizan servicios de cómputo permanente si no son necesarios.

---

## 10. Decisiones de diseño

| Decisión | Justificación |
|---|---|
| Usar S3 como Data Lake | Permite almacenamiento barato, escalable y compatible con Athena. |
| Separar Bronze, Silver y Gold | Facilita trazabilidad, limpieza y consumo analítico. |
| Usar Lambda para ingesta | Evita mantener servidores y reduce complejidad. |
| Usar Secrets Manager | Protege la API Key y parámetros sensibles. |
| Usar Athena | Permite SQL directo sobre S3 sin levantar base de datos dedicada. |
| Usar Power BI | Facilita visualización y presentación ejecutiva. |
| Usar EventBridge | Automatiza ejecuciones con bajo costo operativo. |

---

## 11. Limitaciones

- La solución depende de disponibilidad y límites de TMDb API.
- No se implementó necesariamente un ambiente productivo multiusuario.
- El gobierno de datos avanzado no forma parte del alcance base.
- La capa Gold depende de las consultas y reglas definidas por el equipo.
- El rendimiento de Power BI depende de la configuración ODBC y de Athena.
- Las capturas y evidencias deben agregarse en la carpeta `img/`.

---

## 12. Mejoras futuras

- Crear infraestructura con CloudFormation o Terraform.
- Agregar pruebas automáticas de calidad de datos.
- Implementar particionamiento más robusto.
- Agregar monitoreo con alarmas de CloudWatch.
- Automatizar transformación Silver y Gold.
- Incorporar más endpoints de TMDb.
- Implementar dashboards más completos en Power BI.
- Usar Lake Formation para gobierno de datos si el proyecto crece.

---

## 13. Conclusión

La arquitectura implementada permite demostrar un flujo moderno de analítica en AWS usando servicios serverless y administrados. El sistema cubre ingesta, almacenamiento, transformación, catálogo, consulta y visualización, manteniendo una separación clara por capas y una estructura adecuada para documentación y entrega en GitHub.
