-- ==============================================================================
-- Query: Which genres currently dominate in popularity and quality?
-- Description: Retrieves the overall performance of genres based on a combined 
--              performance metric (score_desempeno).
-- Use Case: Ideal for identifying which movie categories are globally 
--           most attractive for future acquisitions or promotions.
-- ==============================================================================

SELECT *
FROM gold_performance_genero
ORDER BY score_desempeno DESC;
