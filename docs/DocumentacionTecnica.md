# Documentación Técnica  
# Pipeline de Datos AWS/TMDb

**Proyecto:** AWS/TMDb Data Lake  
**Fecha:** Mayo 2026  
**Versión:** 1.0

---

## 1. Objetivo del documento

Este documento describe los componentes técnicos, configuración general, flujo de procesamiento y operación del pipeline de datos implementado para el proyecto AWS/TMDb.

La documentación está orientada a integrantes técnicos del equipo, evaluadores o cualquier persona que necesite entender cómo se implementó y cómo se puede replicar o mantener la solución.

---

## 2. Descripción general de la solución

El pipeline extrae información de películas desde TMDb API, la almacena en Amazon S3, la organiza en capas Bronze, Silver y Gold, la cataloga mediante AWS Glue y permite consultarla desde Amazon Athena. Finalmente, los datos pueden visualizarse en Power BI mediante conexión ODBC hacia Athena.

El flujo general es:

```text
TMDb API -> Lambda -> S3 Bronze -> S3 Silver -> S3 Gold -> Glue Data Catalog -> Athena -> Power BI
```

---

## 3. Inventario técnico de recursos

| Recurso | Servicio | Función |
|---|---|---|
| Función de ingesta | AWS Lambda | Consume TMDb API y escribe datos en S3. |
| Configuración | AWS Secrets Manager | Guarda API Key y parámetros de conexión/configuración. |
| Data Lake | Amazon S3 | Almacena datos en capas Bronze, Silver y Gold. |
| Catálogo | AWS Glue Data Catalog | Registra tablas consultables desde Athena. |
| Crawler | AWS Glue Crawler | Detecta esquemas y particiones en S3. |
| Motor SQL | Amazon Athena | Consulta datos sobre S3. |
| Programación | Amazon EventBridge | Ejecuta Lambda con frecuencia programada. |
| Visualización | Power BI | Consume datos consultados desde Athena. |
| Driver/conexión | ODBC genérico / Athena ODBC | Permite conexión entre Power BI y Athena. |

---

## 4. Configuración del entorno

### 4.1 Requisitos

- Cuenta de AWS con permisos para:
  - Lambda.
  - S3.
  - Secrets Manager.
  - Glue.
  - Athena.
  - EventBridge.
  - IAM.
- API Key válida de TMDb.
- Power BI Desktop instalado si se desea replicar la visualización.
- Driver ODBC compatible con Athena o conexión ODBC genérica funcional.
- Python para desarrollo local, si se ejecutan scripts fuera de AWS.

### 4.2 Variables y secretos

La solución no debe almacenar secretos en código fuente. Los siguientes valores deben estar en Secrets Manager o configuraciones equivalentes:

| Parámetro | Descripción |
|---|---|
| `TMDB_API_KEY` | Llave de acceso a TMDb API. |
| `BASE_URL` | URL base de TMDb API. |
| `ENDPOINT` | Endpoint consultado, por ejemplo películas populares. |
| `S3_BUCKET` | Bucket destino del Data Lake. |
| `BRONZE_PREFIX` | Prefijo de capa Bronze. |
| `SILVER_PREFIX` | Prefijo de capa Silver. |
| `GOLD_PREFIX` | Prefijo de capa Gold. |

---

## 5. Estructura de almacenamiento en S3

La estructura lógica utilizada es:

```text
s3://<bucket>/
│
├── 1bronce/
│   └── tmdb/
│       └── popular/
│
├── 2silver/
│
└── 3gold/
```

También puede existir una ruta para resultados de Athena:

```text
s3://<bucket>/athena/results/
```

Y, si se crean tablas mediante CTAS, puede existir una ruta para tablas derivadas:

```text
s3://<bucket>/athena/tables/
```

---

## 6. Pipeline de ingesta

### 6.1 Componente principal

La ingesta se realiza mediante AWS Lambda. La función ejecuta los siguientes pasos:

1. Lee configuración desde Secrets Manager.
2. Construye la URL de consulta hacia TMDb API.
3. Solicita datos de películas populares.
4. Valida la respuesta.
5. Agrega metadatos de ingesta cuando aplica.
6. Escribe el resultado en S3 Bronze.

### 6.2 Datos obtenidos

El endpoint de películas populares de TMDb contiene información como:

- Identificador de película.
- Título.
- Título original.
- Idioma original.
- Fecha de estreno.
- Popularidad.
- Promedio de votos.
- Conteo de votos.
- Resumen.
- Indicador de contenido adulto.
- Géneros o identificadores de género, según la respuesta usada.

### 6.3 Frecuencia de ejecución

La ejecución puede ser manual o programada. En el proyecto se trabajó con Amazon EventBridge para automatizar la ingesta con una frecuencia controlada. Esta decisión permite reducir costos y evita llamadas innecesarias a la API.

---

## 7. Transformación Bronze a Silver

La capa Silver busca convertir los datos crudos en datos estructurados y confiables.

Transformaciones aplicadas o esperadas:

- Lectura de datos desde Bronze.
- Selección de columnas relevantes.
- Normalización de nombres de columnas.
- Conversión de tipos:
  - fechas a tipo fecha o timestamp.
  - popularidad y promedios a numérico.
  - votos a entero.
- Eliminación o control de registros duplicados.
- Inclusión de metadatos:
  - `source_page`
  - `ingestion_timestamp`
  - `ingestion_date`
- Escritura en formato Parquet cuando aplique.

Campos utilizados en la capa Silver:

| Campo | Descripción |
|---|---|
| `id` | Identificador de película en TMDb, si se conserva. |
| `title` | Título de la película. |
| `original_title` | Título original. |
| `original_language` | Idioma original. |
| `release_date` | Fecha de estreno. |
| `popularity` | Métrica de popularidad de TMDb. |
| `vote_average` | Calificación promedio. |
| `vote_count` | Número de votos. |
| `genres` | Géneros o descripción equivalente. |
| `audience_score` | Métrica derivada o renombrada cuando aplique. |
| `adult` | Indicador de contenido adulto. |
| `overview` | Resumen de la película. |
| `source_page` | Página de origen consultada en la API. |
| `ingestion_timestamp` | Momento exacto de ingesta. |
| `ingestion_date` | Fecha de ingesta. |

---

## 8. Transformación Silver a Gold

La capa Gold se orienta a consultas de negocio y visualización. Su objetivo es preparar datasets analíticos listos para Athena y Power BI.

Ejemplos de salidas Gold:

- Métricas por género.
- Ranking de películas por popularidad.
- Ranking por promedio de voto.
- Conteo de películas por idioma.
- Análisis por fecha de estreno.
- Comparación entre popularidad y calificación.

Ejemplo de consulta analítica:

```sql
SELECT
    original_language,
    COUNT(*) AS total_movies,
    AVG(popularity) AS avg_popularity,
    AVG(vote_average) AS avg_vote_average
FROM db_movies_tmdb.<tabla_silver_o_gold>
GROUP BY original_language
ORDER BY avg_popularity DESC;
```

> Ajustar el nombre de tabla según el catálogo real creado por Glue.

---

## 9. Glue Crawler y Data Catalog

### 9.1 Glue Crawler

El crawler se utiliza para detectar los archivos almacenados en S3 y registrar su esquema. Debe apuntar a las rutas de Silver y Gold que se quieran consultar desde Athena.

### 9.2 Glue Data Catalog

El catálogo contiene la base de datos y tablas consultables desde Athena. En el proyecto se trabajó con una base de datos asociada a TMDb, por ejemplo:

```text
db_movies_tmdb
```

Las tablas pueden tomar nombres generados por Glue según los prefijos de S3. En caso de nombres poco descriptivos, se recomienda documentarlos o renombrarlos si el flujo lo permite.

---

## 10. Consultas en Athena

Athena permite validar la existencia y calidad de los datos. Consultas básicas recomendadas:

```sql
SELECT *
FROM db_movies_tmdb.<tabla>
LIMIT 10;
```

```sql
SELECT COUNT(*) AS total_registros
FROM db_movies_tmdb.<tabla>;
```

```sql
SELECT
    original_language,
    COUNT(*) AS total
FROM db_movies_tmdb.<tabla>
GROUP BY original_language
ORDER BY total DESC;
```

```sql
SELECT
    title,
    popularity,
    vote_average,
    vote_count
FROM db_movies_tmdb.<tabla>
ORDER BY popularity DESC
LIMIT 20;
```

---

## 11. Conexión con Power BI

La conexión con Power BI se realizó mediante ODBC hacia Athena. El flujo general es:

1. Configurar driver ODBC compatible.
2. Crear o seleccionar DSN.
3. Configurar región AWS.
4. Configurar ubicación de resultados de Athena en S3.
5. Autenticarse con credenciales AWS autorizadas.
6. Seleccionar base de datos y tabla de Athena.
7. Cargar datos en Power BI.
8. Construir visualizaciones.

La actualización automática no queda garantizada por defecto en Power BI Desktop. Para un escenario productivo sería necesario configurar Power BI Service, gateway, credenciales y programación de actualización.

---

## 12. Automatización con EventBridge

EventBridge permite ejecutar Lambda automáticamente. La regla debe apuntar a la función de ingesta y usar una expresión `rate` o `cron`.

Ejemplo conceptual:

```text
EventBridge rule -> Lambda ingesta TMDb -> S3 Bronze
```

La frecuencia debe definirse con base en:

- Necesidad de actualización.
- Costo.
- Límites de TMDb API.
- Volumen de datos esperado.
- Tiempo disponible para el proyecto.

---

## 13. Monitoreo y validación

La validación técnica puede realizarse con:

- Logs de Lambda en CloudWatch.
- Archivos creados en S3 Bronze.
- Archivos transformados en Silver y Gold.
- Ejecución correcta de Glue Crawler.
- Tablas visibles en Glue Data Catalog.
- Consultas exitosas en Athena.
- Conexión funcional desde Power BI.

Evidencias recomendadas para `img/`:

- Captura de Lambda.
- Captura de Secrets Manager sin revelar secretos.
- Captura de S3 con capas.
- Captura de Glue Crawler.
- Captura de Glue Data Catalog.
- Captura de Athena con consulta exitosa.
- Captura de Power BI conectado a Athena.

---

## 14. Manejo de errores

| Error posible | Causa probable | Acción recomendada |
|---|---|---|
| Lambda falla al consultar API | API Key inválida o endpoint incorrecto | Revisar Secrets Manager y logs. |
| No aparecen archivos en S3 | Permisos insuficientes o prefijo incorrecto | Revisar rol IAM y bucket destino. |
| Athena no ve datos nuevos | Crawler no ejecutado o particiones no actualizadas | Ejecutar Glue Crawler. |
| Error de ruta existente en CTAS | Athena intenta escribir en una ruta ya ocupada | Cambiar ruta, limpiar carpeta destino o recrear tabla. |
| Power BI no conecta | DSN, región o credenciales incorrectas | Validar configuración ODBC. |
| Columnas faltantes | Esquema anterior o crawler desactualizado | Reprocesar datos y actualizar catálogo. |

---

## 15. Pruebas recomendadas

### 15.1 Pruebas de configuración

- Verificar que Secrets Manager contiene los parámetros requeridos.
- Verificar permisos IAM de Lambda sobre S3 y Secrets Manager.
- Verificar ubicación de resultados de Athena.

### 15.2 Pruebas de integración

- Ejecutar Lambda manualmente.
- Confirmar creación de archivos en Bronze.
- Ejecutar transformación a Silver.
- Ejecutar crawler.
- Consultar datos desde Athena.
- Conectar Power BI a Athena.

### 15.3 Pruebas unitarias

Si se separa el código en funciones, se pueden probar:

- Construcción de URL de TMDb.
- Validación de respuesta de API.
- Conversión de tipos.
- Limpieza de registros.
- Construcción de rutas S3.

---

## 16. Consideraciones de despliegue

Para replicar el proyecto se recomienda documentar en `deploy/INSTRUCTIVO_REPLICACION.md`:

1. Crear bucket S3.
2. Crear secreto en Secrets Manager.
3. Crear rol IAM para Lambda.
4. Crear función Lambda.
5. Probar ingesta.
6. Crear crawler de Glue.
7. Configurar Athena.
8. Crear consultas Gold.
9. Configurar EventBridge.
10. Conectar Power BI.

---

## 17. Conclusión

El pipeline AWS/TMDb implementa un flujo de datos completo usando servicios administrados de AWS. La solución permite extraer datos desde una API externa, almacenarlos en un Data Lake, transformarlos en capas analíticas, consultarlos mediante SQL y conectarlos con Power BI para visualización.
