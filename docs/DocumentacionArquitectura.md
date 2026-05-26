# Documentación de Arquitectura  
# Data Lake AWS/TMDb para Gestión de Catálogo de Streaming

**Cliente:** Plataforma de Streaming  
**Proyecto:** Analítica de catálogo audiovisual con TMDb y AWS  
**Fecha:** Mayo 2026  
**Versión:** 2.0

---

## 1. Resumen ejecutivo

Este documento describe la arquitectura de datos implementada para una plataforma de streaming que necesita analizar información reciente de películas populares y usarla como apoyo para decisiones de catálogo.

La solución utiliza una arquitectura Medallion con capas Bronze, Silver y Gold sobre Amazon S3. El flujo está automatizado de punta a punta mediante EventBridge, S3 Event Notification y AWS Lambda. Amazon Athena crea y consulta tablas analíticas Gold, y Power BI consume estos resultados para presentar un dashboard ejecutivo.

---

## 2. Objetivo de la arquitectura

La arquitectura tiene como objetivo convertir datos externos de TMDb en información accionable para decisiones de catálogo, incluyendo:

- Identificación de géneros con mejor desempeño reciente.
- Priorización de películas recomendables o promocionables.
- Detección de películas populares con baja calificación.
- Identificación de géneros con crecimiento reciente.
- Visualización ejecutiva de indicadores en Power BI.

---

## 3. Diagrama conceptual

```text
TMDb API
↓
Amazon EventBridge Scheduler
↓
Lambda tmdb_to_bronze
↓
Amazon S3 - 1bronce/tmdb/popular/
↓ S3 Event Notification
Lambda bronce_tmdb_to_silver
↓
Amazon S3 - 2silver/movies/
↓ invocación automática
Lambda silver_tmdb_to_gold
↓
Amazon Athena CTAS
↓
Amazon S3 - 3gold/
↓
Athena Query Editor / ODBC
↓
Power BI Desktop - Dashboard ejecutivo
```

---

## 4. Stack tecnológico

| Componente | Servicio / herramienta | Función |
|---|---|---|
| Fuente externa | TMDb API | Provee datos de películas populares. |
| Orquestación inicial | EventBridge Scheduler | Programa la ingesta lunes y viernes a las 8:00 a.m. |
| Ingesta | AWS Lambda | Consulta TMDb y guarda datos en Bronze. |
| Almacenamiento | Amazon S3 | Guarda las capas Bronze, Silver y Gold. |
| Automatización intermedia | S3 Event Notification | Dispara Silver al detectar nuevos archivos en Bronze. |
| Transformación | AWS Lambda | Limpia datos y genera Silver. |
| Generación analítica | AWS Lambda + Athena CTAS | Recrea tablas Gold orientadas a negocio. |
| Catálogo | AWS Glue Data Catalog | Registra metadatos consultables por Athena. |
| Descubrimiento de esquema | AWS Glue Crawler | Detecta esquema y particiones de Silver. |
| Consulta | Amazon Athena | Consulta Silver/Gold y genera tablas CTAS. |
| Visualización | Power BI Desktop | Dashboard ejecutivo conectado a Athena por ODBC. |
| Seguridad | IAM + Secrets Manager | Manejo de permisos y secretos. |
| Desarrollo | Amazon EC2 | Ambiente de pruebas; no forma parte del pipeline productivo. |

---

## 5. Arquitectura Medallion

### 5.1 Bronze

La capa Bronze conserva los datos crudos obtenidos desde TMDb. Su valor principal es la trazabilidad: permite mantener snapshots de cada ingesta y reprocesar datos si es necesario.

Ruta:

```text
1bronce/tmdb/popular/
```

Características:

- Formato NDJSON.
- Datos por fecha de ingesta.
- Aproximadamente 100 películas por ejecución.
- Incluye `source_page`, `ingestion_timestamp` e `ingestion_date`.

---

### 5.2 Silver

La capa Silver contiene datos limpios, filtrados y listos para consulta estructurada.

Ruta:

```text
2silver/movies/
```

Características:

- Formato Parquet.
- Histórico limpio.
- Filtro `vote_count >= 100`.
- Mapeo de géneros.
- Conversión de fechas y tipos numéricos.
- Eliminación de duplicados del lote.
- Reconocimiento mediante Glue Crawler y Glue Data Catalog.

---

### 5.3 Gold

La capa Gold contiene tablas analíticas orientadas al negocio de streaming.

Ruta:

```text
3gold/
```

Tablas:

| Tabla | Uso |
|---|---|
| `gold_performance_genero` | Identificar géneros con mejor desempeño reciente. |
| `gold_ranking_peliculas` | Priorizar películas para recomendación o promoción. |
| `gold_peliculas_sobreexpuestas` | Detectar películas populares con baja calificación. |
| `gold_tendencia_generos` | Identificar géneros con crecimiento reciente. |

Características:

- Creada mediante Athena CTAS.
- Ventana móvil de 30 días.
- Registro más reciente por película.
- Limpieza automática de carpetas S3 Gold antes de recrear tablas.
- Separación de géneros múltiples con `UNNEST(split(...))`.

---

## 6. Flujo de datos

1. EventBridge ejecuta `tmdb_to_bronze` lunes y viernes a las 8:00 a.m.
2. La Lambda consulta `/movie/popular` de TMDb, páginas 1 a 5.
3. Los datos se guardan en Bronze en formato NDJSON.
4. S3 Event Notification detecta el nuevo archivo y activa `bronce_tmdb_to_silver`.
5. Silver limpia, filtra, mapea géneros y escribe Parquet en `2silver/movies/`.
6. Al terminar correctamente, Silver invoca `silver_tmdb_to_gold`.
7. Gold elimina tablas anteriores y limpia rutas S3 Gold.
8. Athena CTAS recrea las cuatro tablas analíticas.
9. Athena expone las tablas Gold para consulta.
10. Power BI Desktop consume las tablas mediante ODBC.
11. El dashboard presenta resultados ejecutivos de catálogo.

---

## 7. Capa de visualización

La capa de visualización se implementa con Power BI Desktop conectado a Athena mediante ODBC.

Fuente de datos:

```text
db_movies_tmdb.gold_performance_genero
db_movies_tmdb.gold_ranking_peliculas
db_movies_tmdb.gold_peliculas_sobreexpuestas
db_movies_tmdb.gold_tendencia_generos
```

El dashboard permite analizar:

- KPIs generales.
- Desempeño por género.
- Tendencia de géneros.
- Ranking de películas recomendables.
- Películas sobreexpuestas.

En un escenario productivo, el reporte puede publicarse en Power BI Service y actualizarse mediante Power BI Gateway después de cada ejecución del pipeline.

---

## 8. Seguridad

La arquitectura considera:

- Uso de Secrets Manager para API Key de TMDb.
- IAM Roles con principio de menor privilegio.
- Separación de permisos por Lambda.
- Control de lectura y escritura por ruta S3.
- Permisos específicos para Athena, Glue y S3 Gold.
- No exposición de secretos en GitHub.
- Capturas de evidencia sin mostrar claves o credenciales.

---

## 9. Decisiones de arquitectura

| Decisión | Justificación |
|---|---|
| Usar S3 como Data Lake | Escalable, económico y compatible con Athena. |
| Usar arquitectura Bronze/Silver/Gold | Facilita trazabilidad, limpieza y análisis de negocio. |
| Usar Lambda | Evita servidores permanentes y reduce costos. |
| Usar EventBridge | Permite ingesta programada y controlada. |
| Usar S3 Event Notification | Automatiza el paso de Bronze a Silver. |
| Usar Athena CTAS para Gold | Permite generar tablas analíticas sin motor de base de datos dedicado. |
| Usar Power BI | Facilita visualización ejecutiva y consumo por usuarios de negocio. |
| No usar EMR/Redshift/RDS | El volumen no justifica servicios más pesados o costosos. |

---

## 10. Consideraciones de costo

El diseño se mantiene en servicios serverless o bajo demanda:

- Lambda cobra por ejecución.
- S3 cobra por almacenamiento.
- Athena cobra por datos escaneados.
- EventBridge tiene costo bajo para programación.
- Glue Crawler se ejecuta solo cuando es necesario.
- Power BI se usa como herramienta externa de visualización.

La programación lunes y viernes reduce ejecuciones innecesarias y mantiene un balance razonable entre actualización y costo.

---

## 11. Limitaciones

- TMDb es una fuente externa y no refleja consumo interno real de la plataforma.
- El análisis no incluye costos de licenciamiento ni disponibilidad legal de títulos.
- Power BI Desktop requiere actualización manual.
- La actualización productiva requiere Power BI Service y Gateway.
- No se implementa personalización por usuario.
- La solución está optimizada para volúmenes bajos o moderados.

---

## 12. Mejoras futuras

- Automatizar infraestructura con CloudFormation.
- Agregar pruebas automáticas de calidad de datos.
- Incorporar más endpoints de TMDb.
- Publicar dashboard en Power BI Service.
- Programar refresh con Power BI Gateway.
- Agregar métricas de costo de licenciamiento si estuvieran disponibles.
- Combinar datos TMDb con métricas internas de visualización de la plataforma.
- Implementar un modelo de recomendación en una fase posterior.

---

## 13. Conclusión

La arquitectura permite a una plataforma de streaming transformar datos externos de TMDb en indicadores útiles para gestión de catálogo. El flujo automatizado Bronze, Silver y Gold permite trazabilidad, limpieza, análisis y visualización ejecutiva sin utilizar servicios pesados o infraestructura permanente innecesaria.
