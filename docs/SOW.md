# Statement of Work (SOW)  
# Proyecto AWS/TMDb Data Lake

**Proyecto:** Implementación de Data Lake para analítica de películas usando TMDb y AWS  
**Cliente académico:** Proyecto final de materia AWS/TMDb  
**Fecha:** Mayo 2026  
**Equipo:** Equipo de desarrollo del proyecto

---

## 1. Resumen del proyecto

El proyecto consiste en diseñar e implementar una arquitectura de datos en AWS para recolectar, almacenar, transformar y analizar información de películas obtenida desde la API de TMDb.

La solución utiliza una arquitectura Medallion con capas Bronze, Silver y Gold sobre Amazon S3. Los datos son consultados mediante Amazon Athena, catalogados con AWS Glue Data Catalog y visualizados desde Power BI mediante conexión ODBC hacia Athena.

El objetivo principal es demostrar un flujo de datos funcional, automatizado y defendible, utilizando servicios administrados de AWS y buenas prácticas básicas de seguridad, organización y documentación.

---

## 2. Objetivos

### 2.1 Objetivo general

Implementar un Data Lake en AWS para analizar información de películas populares de TMDb, permitiendo consultas analíticas y visualización de indicadores relevantes para toma de decisiones.

### 2.2 Objetivos específicos

- Extraer datos desde TMDb API mediante AWS Lambda.
- Almacenar datos crudos en Amazon S3.
- Organizar la información en capas Bronze, Silver y Gold.
- Transformar los datos a formatos analíticos, preferentemente Parquet.
- Registrar metadatos mediante AWS Glue Crawler y Glue Data Catalog.
- Consultar datos mediante Amazon Athena.
- Generar datasets Gold para análisis de negocio.
- Conectar Athena con Power BI para visualización.
- Documentar arquitectura, funcionamiento técnico, alcance y operación del sistema.

---

## 3. Alcance del trabajo

El alcance del proyecto incluye las siguientes actividades.

### 3.1 Ingesta de datos

- Configuración de una función AWS Lambda para consumir TMDb API.
- Uso de Secrets Manager para centralizar parámetros sensibles o configurables.
- Descarga de información de películas populares.
- Almacenamiento de los datos extraídos en S3, dentro de la capa Bronze.

### 3.2 Almacenamiento y organización

- Creación o uso de un bucket S3 para el Data Lake.
- Separación de datos por capas:
  - `1bronce/`
  - `2silver/`
  - `3gold/`
- Organización de archivos por fechas o particiones cuando aplique.

### 3.3 Transformación de datos

- Limpieza de registros.
- Selección de campos relevantes.
- Conversión de tipos de datos.
- Eliminación o control de duplicados.
- Escritura de datos transformados en Silver.
- Construcción de datasets analíticos en Gold.

### 3.4 Catálogo y consulta

- Ejecución de AWS Glue Crawler para descubrir esquemas.
- Registro de tablas en Glue Data Catalog.
- Consulta de tablas mediante Amazon Athena.
- Creación de consultas SQL para análisis de métricas de películas.

### 3.5 Automatización

- Programación de ejecuciones mediante Amazon EventBridge.
- Configuración de Lambda como proceso de ingesta programado.
- Control de frecuencia de ejecución para evitar costos innecesarios.

### 3.6 Visualización

- Conexión de Power BI con Athena mediante ODBC genérico.
- Validación de consulta desde Power BI.
- Preparación de visualizaciones o métricas a partir de los datos Gold.

### 3.7 Documentación

- Documentación funcional.
- Documentación técnica.
- Documentación de arquitectura.
- RFP.
- SOW.
- Instructivo de replicación.
- Evidencias y capturas de implementación.

---

## 4. Fuera de alcance

Quedan fuera del alcance, salvo que el equipo los haya implementado explícitamente:

- Implementación productiva multiambiente.
- Despliegue completo mediante CI/CD.
- Monitoreo avanzado con alarmas productivas.
- Gobierno de datos empresarial con Lake Formation.
- Control avanzado de calidad de datos con frameworks especializados.
- Entrenamiento de modelos de Machine Learning.
- Alta disponibilidad empresarial.
- Procesamiento de grandes volúmenes con EMR o Spark distribuido, salvo que se documente como posible mejora.

---

## 5. Entregables

| Entregable | Descripción |
|---|---|
| Repositorio GitHub | Estructura completa del proyecto con código, documentación y evidencias. |
| Código Lambda | Código de ingesta desde TMDb API hacia S3. |
| Scripts de transformación | Código o consultas utilizadas para generar Silver y Gold. |
| Scripts SQL Athena | Consultas para validación y análisis. |
| Documentación funcional | Descripción del sistema desde perspectiva de negocio y usuario. |
| Documentación técnica | Descripción de componentes, configuración y operación. |
| Documentación de arquitectura | Explicación del diseño, flujo de datos y servicios AWS. |
| RFP | Documento de solicitud de propuesta adaptado al proyecto. |
| SOW | Alcance formal de trabajo del proyecto. |
| Diagramas | Diagrama de arquitectura y diagrama de flujo o secuencia. |
| Evidencias | Capturas de S3, Lambda, Glue, Athena, EventBridge y Power BI cuando existan. |
| Presentación ejecutiva | Presentación final del proyecto. |
| Pruebas | Pruebas unitarias, integración o configuración si fueron realizadas. |

---

## 6. Cronograma estimado

| Fase | Actividades |
|---|---|
| Fase 1 | Diseño de arquitectura y definición de capas del Data Lake. |
| Fase 2 | Configuración de S3, Secrets Manager y Lambda. |
| Fase 3 | Ingesta de datos desde TMDb API hacia Bronze. |
| Fase 4 | Transformación de datos hacia Silver y Gold. |
| Fase 5 | Configuración de Glue Crawler, Glue Data Catalog y Athena. |
| Fase 6 | Conexión con Power BI y validación de consultas. |
| Fase 7 | Documentación, diagramas, evidencias y presentación final. |

---

## 7. Criterios de aceptación

El proyecto se considerará aceptado si cumple con los siguientes criterios:

- La función Lambda obtiene datos desde TMDb API.
- Los datos crudos se almacenan correctamente en S3 Bronze.
- Existe una capa Silver con datos limpios y estructurados.
- Existe una capa Gold con datos aptos para análisis.
- Glue Crawler reconoce los archivos y crea o actualiza tablas en el catálogo.
- Athena permite consultar los datos correctamente.
- Power BI puede conectarse a Athena y visualizar resultados.
- La ejecución periódica mediante EventBridge está documentada o implementada.
- El repositorio contiene código, documentación, diagramas y evidencias.
- No se exponen credenciales ni secretos en el código fuente.

---

## 8. Supuestos

- La API de TMDb está disponible durante las ejecuciones.
- La API Key se encuentra configurada fuera del código fuente.
- El volumen de datos consultado se mantiene dentro de límites razonables para un proyecto académico.
- La estructura de respuesta de TMDb se conserva sin cambios mayores.
- Los servicios AWS utilizados permanecen disponibles.
- El equipo cuenta con permisos suficientes en AWS para ejecutar Lambda, S3, Glue, Athena, EventBridge y Secrets Manager.

---

## 9. Riesgos

| Riesgo | Mitigación |
|---|---|
| Exposición accidental de la API Key | Usar Secrets Manager y excluir secretos del repositorio. |
| Costos inesperados en AWS | Limitar frecuencia de ejecución y evitar procesamiento innecesario. |
| Cambios en la API de TMDb | Documentar dependencias y validar respuestas antes de transformar. |
| Errores de esquema en Athena | Reejecutar Glue Crawler y validar tipos de datos. |
| Duplicidad de datos | Usar timestamps, particiones y lógica de selección de registros recientes. |
| Problemas de conexión con Power BI | Documentar el uso de ODBC genérico y validar DSN. |

---

## 10. Responsabilidades

### Equipo del proyecto

- Implementar la solución.
- Documentar arquitectura y operación.
- Preparar evidencias.
- Mantener el repositorio ordenado.
- Evitar exposición de credenciales.

### Profesor o evaluador

- Revisar documentación, evidencias y funcionamiento.
- Validar que el proyecto cumpla con los criterios establecidos.
- Evaluar presentación ejecutiva y defensa técnica.

---

## 11. Conclusión

Este SOW define el alcance y entregables del proyecto AWS/TMDb. La solución busca demostrar una arquitectura de datos funcional sobre AWS, integrando ingesta, almacenamiento, transformación, consulta y visualización de información de películas mediante servicios administrados.
