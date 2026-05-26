-- ==============================================================================
-- Query: Which genres are growing in popularity recently?
-- Description: Analyzes the popularity trend of genres over time, highlighting 
--              those with the highest growth.
-- Use Case: Useful for detecting rapid shifts in audience preferences and 
--           anticipating what type of content will be in high demand soon.
-- ==============================================================================

SELECT *
FROM gold_tendencia_generos
ORDER BY cambio_popularidad DESC;
