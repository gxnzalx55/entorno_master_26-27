-- =====================================================================
--  ventas_grandes: 2 millones de ventas inventadas para medir rendimiento
--  Almacenamiento, visualización y procesamiento de datos · Sesión 4
--
--  Los valores salen de una función hash de PostgreSQL: todos tenemos
--  exactamente la misma tabla y los mismos resultados.
--  Se ejecuta en pgAdmin (Query Tool, F5). Tarda entre 10 y 30 segundos.
--  Si la vuelves a ejecutar, borra también las vistas creadas sobre ella.
-- =====================================================================
DROP TABLE IF EXISTS ventas_grandes CASCADE;

CREATE TABLE ventas_grandes AS
SELECT g AS venta_id,
       (abs(hashint4(g)::bigint) % 91) + 1                             AS cliente_id,
       (abs(hashint4(g + 5000000)::bigint) % 77) + 1                   AS product_id,
       DATE '2020-01-01' + (abs(hashint4(g * 7)::bigint) % 1827)::int  AS fecha,
       round((abs(hashint4(g * 13)::bigint) % 50000) / 100.0, 2)       AS importe
FROM generate_series(1, 2000000) AS g;

ALTER TABLE ventas_grandes ADD PRIMARY KEY (venta_id);
ANALYZE ventas_grandes;

-- Comprobación: 2000000 filas
SELECT count(*) AS filas, pg_size_pretty(pg_relation_size('ventas_grandes')) AS tamano
FROM ventas_grandes;
