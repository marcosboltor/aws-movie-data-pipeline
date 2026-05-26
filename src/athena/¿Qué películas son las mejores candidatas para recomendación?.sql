-- ==============================================================================
-- Query: Which movies are the best candidates for recommendation?
-- Description: Ranks individual movies based on a recommendation score that 
--              balances popularity, average rating, and vote volume.
-- Use Case: Can be used directly to feed user interface carousels, 
--           highlighting the best high-quality titles (Top 20).
-- ==============================================================================

SELECT *
FROM gold_ranking_peliculas
ORDER BY score_recomendacion DESC
LIMIT 20;
