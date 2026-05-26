SELECT *
FROM db_movies_tmdb.gold_performance_genero
ORDER BY score_desempeno DESC;

SELECT *
FROM db_movies_tmdb.gold_ranking_peliculas
ORDER BY score_recomendacion DESC;

SELECT *
FROM db_movies_tmdb.gold_peliculas_sobreexpuestas
ORDER BY popularity DESC;

SELECT *
FROM db_movies_tmdb.gold_tendencia_generos
ORDER BY cambio_popularidad DESC;
