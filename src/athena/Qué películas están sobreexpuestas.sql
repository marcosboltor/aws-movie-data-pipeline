-- ==============================================================================
-- Query: Which movies are overexposed?
-- Description: Identifies movies that have exceptionally high popularity but 
--              average or low user ratings.
-- Use Case: Helps avoid promoting content that might disappoint viewers 
--           despite being well-known (e.g., massive marketing campaigns 
--           but poor audience reception).
-- ==============================================================================

SELECT *
FROM gold_peliculas_sobreexpuestas
ORDER BY popularity DESC;
