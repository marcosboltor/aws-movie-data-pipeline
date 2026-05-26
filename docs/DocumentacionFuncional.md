# Documentación Funcional  
# Sistema de Analítica de Catálogo para Plataforma de Streaming

**Cliente:** Plataforma de Streaming  
**Proyecto:** Analítica de catálogo audiovisual con TMDb y AWS  
**Fecha:** Mayo 2026  
**Versión:** 2.0

---

## 1. Objetivo del documento

Este documento describe el funcionamiento del sistema desde una perspectiva de negocio. Su propósito es explicar qué hace la solución, qué usuarios la utilizan, qué decisiones apoya y qué valor entrega a una plataforma de streaming.

El sistema permite analizar información reciente de películas populares obtenida desde TMDb para apoyar la gestión informada del catálogo: adquisición de contenido, priorización de títulos, promoción de películas y detección de tendencias por género.

---

## 2. Descripción funcional del sistema

La plataforma de streaming necesita evaluar el mercado reciente de películas populares para fortalecer su catálogo con mejores criterios de decisión. Para ello, el sistema toma datos de TMDb, los procesa en AWS y entrega tablas analíticas listas para consulta y visualización.

La solución no busca reemplazar la estrategia editorial o comercial de la plataforma. Su función es aportar evidencia cuantitativa para apoyar decisiones sobre qué géneros y películas podrían tener mayor atractivo para los usuarios.

---

## 3. Preguntas de negocio que responde

La capa Gold está diseñada para responder cuatro preguntas principales:

| Pregunta de negocio | Tabla Gold | Uso de negocio |
|---|---|---|
| ¿Qué géneros tienen mejor desempeño reciente? | `gold_performance_genero` | Identificar géneros atractivos para fortalecer el catálogo. |
| ¿Qué películas conviene recomendar o promocionar? | `gold_ranking_peliculas` | Priorizar títulos con buena mezcla de popularidad, calificación y votos. |
| ¿Qué películas son populares pero tienen baja calificación? | `gold_peliculas_sobreexpuestas` | Detectar contenido sobreexpuesto que podría no cumplir expectativas. |
| ¿Qué géneros están creciendo en popularidad? | `gold_tendencia_generos` | Detectar tendencias recientes para adquisición y promoción. |

---

## 4. Usuarios del sistema

| Rol | Responsabilidades |
|---|---|
| Analista de catálogo | Interpreta las tablas Gold para apoyar decisiones de adquisición, promoción y priorización. |
| Equipo de contenido | Usa los resultados para identificar géneros o películas con potencial para el catálogo. |
| Equipo de marketing | Consulta rankings y tendencias para definir campañas de promoción. |
| Data Engineer | Mantiene el pipeline de ingesta, transformación y publicación de datos. |
| Dirección / Stakeholder | Revisa el dashboard ejecutivo en Power BI para tomar decisiones de alto nivel. |

---

## 5. Procesos de negocio soportados

### 5.1 Evaluación de desempeño por género

El sistema calcula métricas agregadas por género para identificar categorías con mejor desempeño reciente. Esto ayuda a decidir qué tipos de películas podrían fortalecerse dentro del catálogo.

**Salida principal:** `gold_performance_genero`.

### 5.2 Priorización de películas recomendables

El sistema genera un ranking de películas con base en una combinación de popularidad, calificación y volumen de votos. Esto permite detectar títulos con señales positivas para promoción o incorporación al catálogo.

**Salida principal:** `gold_ranking_peliculas`.

### 5.3 Detección de contenido sobreexpuesto

El sistema identifica películas con alta popularidad pero baja calificación. Esta información ayuda a evitar promocionar contenido que podría generar expectativas altas pero baja satisfacción.

**Salida principal:** `gold_peliculas_sobreexpuestas`.

### 5.4 Identificación de tendencias por género

El sistema analiza géneros con crecimiento reciente en popularidad. Esto apoya decisiones de adquisición, curaduría y campañas alrededor de tendencias emergentes.

**Salida principal:** `gold_tendencia_generos`.

### 5.5 Visualización ejecutiva

Power BI consume las tablas Gold desde Athena para presentar KPIs, rankings y tendencias en un dashboard ejecutivo. Esto facilita que usuarios no técnicos interpreten los resultados.

---

## 6. Casos de uso

### Caso de uso 1: Identificar géneros atractivos para el catálogo

**Actor principal:** Analista de catálogo.  
**Entrada:** Tabla `gold_performance_genero`.  
**Flujo:**

1. El analista revisa el desempeño reciente por género.
2. Compara popularidad, calificación y volumen de votos.
3. Identifica géneros con señales positivas.
4. Propone fortalecer el catálogo en esos géneros.

**Resultado esperado:** Lista de géneros prioritarios para análisis comercial.

---

### Caso de uso 2: Priorizar películas para promoción

**Actor principal:** Equipo de marketing.  
**Entrada:** Tabla `gold_ranking_peliculas`.  
**Flujo:**

1. El equipo consulta el ranking de películas recomendables.
2. Selecciona títulos con buen balance entre popularidad y calificación.
3. Define títulos candidatos para campañas o recomendaciones destacadas.

**Resultado esperado:** Selección de películas con mayor potencial de promoción.

---

### Caso de uso 3: Evitar promoción de contenido con baja satisfacción potencial

**Actor principal:** Equipo de contenido o marketing.  
**Entrada:** Tabla `gold_peliculas_sobreexpuestas`.  
**Flujo:**

1. El usuario revisa películas con alta popularidad y baja calificación.
2. Evalúa si conviene limitar su promoción.
3. Ajusta la estrategia de visibilidad del catálogo.

**Resultado esperado:** Identificación de títulos que podrían requerir cautela en promoción.

---

### Caso de uso 4: Detectar tendencias recientes

**Actor principal:** Dirección o equipo de estrategia.  
**Entrada:** Tabla `gold_tendencia_generos`.  
**Flujo:**

1. El usuario revisa géneros con crecimiento reciente.
2. Compara tendencias con la estrategia de catálogo.
3. Define oportunidades para adquisición o campañas temáticas.

**Resultado esperado:** Insumos para decisiones estratégicas de catálogo.

---

## 7. Reglas de negocio

- Solo se consideran películas con `vote_count >= 100`.
- La capa Gold analiza una ventana móvil de 30 días.
- Si una película aparece varias veces en el histórico, Gold utiliza el registro más reciente según `ingestion_timestamp`.
- Una película puede pertenecer a varios géneros.
- El análisis por género separa géneros múltiples con `UNNEST(split(...))`.
- El score de desempeño combina popularidad, calificación y volumen de votos.
- Bronze conserva snapshots crudos.
- Silver conserva histórico limpio.
- Gold representa una vista analítica reciente orientada al negocio.
- Power BI no modifica los datos del Data Lake; únicamente consume resultados procesados.

---

## 8. Entradas y salidas

### 8.1 Entradas

- Datos de películas populares desde TMDb API.
- Géneros, popularidad, calificación promedio, volumen de votos, fecha de estreno e idioma.
- Metadatos de ingesta como `source_page`, `ingestion_timestamp` e `ingestion_date`.

### 8.2 Salidas

- Datos crudos en Bronze.
- Datos limpios en Silver.
- Tablas analíticas Gold.
- Consultas disponibles en Athena.
- Dashboard ejecutivo en Power BI.

---

## 9. Indicadores de negocio

| Indicador | Uso |
|---|---|
| Popularidad promedio por género | Detectar géneros con mayor atracción de mercado. |
| Calificación promedio por género | Evaluar percepción de calidad. |
| Volumen de votos por género | Medir representatividad de las calificaciones. |
| Score de desempeño | Priorizar géneros o títulos combinando popularidad, votos y calificación. |
| Ranking de películas | Identificar títulos recomendables o promocionables. |
| Películas sobreexpuestas | Detectar películas populares con baja calificación. |
| Tendencia de géneros | Identificar crecimiento reciente en categorías de contenido. |

---

## 10. Disponibilidad funcional

El pipeline se ejecuta lunes y viernes a las 8:00 a.m. mediante EventBridge. Después de cada ejecución:

1. Se actualiza Bronze con datos nuevos.
2. Se dispara automáticamente Silver.
3. Silver invoca Gold.
4. Gold recrea las tablas analíticas.
5. Power BI puede actualizarse manualmente desde Desktop.

En un escenario productivo, el dashboard puede publicarse en Power BI Service y programar su actualización mediante Power BI Gateway después de cada corrida del pipeline.

---

## 11. Limitaciones funcionales

- TMDb es una fuente externa y sus métricas no representan directamente el comportamiento interno de los usuarios de la plataforma.
- La solución analiza popularidad de mercado, no consumo interno real.
- Las decisiones de catálogo deben complementar estos resultados con costos de licenciamiento, disponibilidad de derechos y estrategia editorial.
- Power BI Desktop requiere actualización manual.
- La actualización automática productiva requiere Power BI Service y Gateway.
- La solución no implementa recomendaciones personalizadas por usuario.

---

## 12. Glosario

| Término | Definición |
|---|---|
| Catálogo | Conjunto de películas disponibles o candidatas para una plataforma de streaming. |
| TMDb | Fuente externa de datos sobre películas. |
| Popularidad | Métrica de TMDb que aproxima visibilidad o interés en una película. |
| Calificación promedio | Promedio de votos otorgados por usuarios en TMDb. |
| Volumen de votos | Cantidad de votos registrados para una película. |
| Bronze | Capa de datos crudos. |
| Silver | Capa de datos limpios y estructurados. |
| Gold | Capa de datos analíticos para negocio. |
| Athena | Servicio para consultar datos de S3 con SQL. |
| Power BI | Herramienta para construir dashboard ejecutivo. |
| Dashboard | Vista visual con indicadores clave para toma de decisiones. |

---

## 13. Conclusión

El sistema permite convertir datos externos de TMDb en información útil para la gestión de catálogo de una plataforma de streaming. La capa Gold y el dashboard ejecutivo ayudan a identificar géneros atractivos, películas recomendables, contenido sobreexpuesto y tendencias recientes que pueden apoyar decisiones comerciales y editoriales.
