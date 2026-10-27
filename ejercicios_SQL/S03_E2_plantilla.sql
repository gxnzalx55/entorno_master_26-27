-- =====================================================================
--  EJERCICIO 2 · Consultas en pasos y con ventanas
--  Almacenamiento, visualización y procesamiento de datos · Sesión 3
--  Plantilla de trabajo: no se entrega; se corrige en clase.
-- =====================================================================
--  Sin IA, salvo en los retos marcados «Con IA». En esos retos, anota:
--    Herramienta y versión:
--    Prompt principal (menos de 20 palabras):
-- =====================================================================

-- ---------------------------------------------------------------------
-- BLOQUE 1 · JOIN y subconsultas
-- ---------------------------------------------------------------------

-- Pregunta 1
SELECT p.product_name
FROM products p
WHERE NOT EXISTS (
	SELECT *
	FROM order_details od 
	JOIN orders o ON o.order_id = od.order_id
	JOIN customers c ON c.customer_id = o.customer_id
	WHERE p.product_id = od.product_id AND c.country='Spain'
)

-- Resultado (filas y primera fila): 40 Aniseed Syrup

-- Pregunta 2
SELECT c.category_name,
       count(*) FILTER (WHERE p.discontinued = 0) AS activos,
       count(*) FILTER (WHERE p.discontinued = 1) AS descatalogados
FROM categories c
JOIN products p ON p.category_id = c.category_id
GROUP BY c.category_name
ORDER BY c.category_name;

-- Resultado (filas y primera fila): "Beverages"	9	3 ; 8 filas

-- Pregunta 3
SELECT a.city,
       a.company_name AS cliente_1,
       b.company_name AS cliente_2
FROM customers a
JOIN customers b
  ON a.city = b.city
 AND a.customer_id < b.customer_id
WHERE a.country = 'Spain'
  AND b.country = 'Spain'
ORDER BY a.city, cliente_1, cliente_2;

-- Resultado (filas y primera fila): "Madrid"	"Bólido Comidas preparadas"	"FISSA Fabrica Inter. Salchichas S.A." ; 3 filas

-- ---------------------------------------------------------------------
-- BLOQUE 2 · CTE
-- ---------------------------------------------------------------------

-- Pregunta 4
WITH importe_pedido AS (
    SELECT o.order_id,
           EXTRACT(YEAR FROM o.order_date)::int AS anio,
           SUM(od.unit_price * od.quantity * (1 - od.discount))::numeric AS importe
    FROM orders o
    JOIN order_details od ON od.order_id = o.order_id
    GROUP BY o.order_id, EXTRACT(YEAR FROM o.order_date)
)
SELECT anio,
       count(*)                    AS pedidos,
       round(SUM(importe), 2)      AS facturacion,
       round(AVG(importe), 2)      AS pedido_medio
FROM importe_pedido
GROUP BY anio
ORDER BY anio;


-- Resultado (filas y primera fila): 1996	152	208083.97	1368.97 ; 3 rows

-- Pregunta 5
WITH por_cliente AS (
    SELECT c.customer_id,
           c.company_name,
           SUM(od.unit_price * od.quantity * (1 - od.discount))::numeric AS facturacion
    FROM customers c
    JOIN orders o         ON o.customer_id = c.customer_id
    JOIN order_details od ON od.order_id   = o.order_id
    GROUP BY c.customer_id, c.company_name
)
SELECT company_name,
       round(facturacion, 2) AS facturacion
FROM por_cliente
WHERE facturacion > 3 * (SELECT AVG(facturacion) FROM por_cliente)
ORDER BY facturacion DESC;

-- Resultado (filas y primera fila): "QUICK-Stop"	110277.31 ; 5 filas

-- Pregunta 6
WITH por_pais AS (
    SELECT c.country,
           SUM(od.unit_price * od.quantity * (1 - od.discount))::numeric AS facturacion
    FROM customers c
    JOIN orders o         ON o.customer_id = c.customer_id
    JOIN order_details od ON od.order_id   = o.order_id
    GROUP BY c.country
),
total AS (
    SELECT SUM(facturacion) AS total
    FROM por_pais
)
SELECT p.country,
       round(p.facturacion, 2)                    AS facturacion,
       round(100 * p.facturacion / t.total, 1)    AS pct
FROM por_pais p
CROSS JOIN total t
ORDER BY p.facturacion DESC
LIMIT 5;

-- Resultado (filas y primera fila): "USA"	245584.61	19.4 ; 5 filas

-- ---------------------------------------------------------------------
-- BLOQUE 3 · Funciones de ventana
-- ---------------------------------------------------------------------

-- Pregunta 7
WITH por_cliente AS (
    SELECT c.country,
           c.company_name,
           SUM(od.unit_price * od.quantity * (1 - od.discount))::numeric AS facturacion
    FROM customers c
    JOIN orders o         ON o.customer_id = c.customer_id
    JOIN order_details od ON od.order_id   = o.order_id
    GROUP BY c.customer_id, c.country, c.company_name
),
ranking AS (
    SELECT country,
           company_name,
           facturacion,
           RANK() OVER (PARTITION BY country ORDER BY facturacion DESC) AS pos
    FROM por_cliente
)
SELECT country,
       company_name,
       round(facturacion, 2) AS facturacion
FROM ranking
WHERE pos = 1
ORDER BY country;

-- Resultado (filas y primera fila):  "Argentina"	"Océano Atlántico Ltda."	3460.20 ; 21 filas

-- Pregunta 8
WITH por_mes AS (
    SELECT DATE_TRUNC('month', o.order_date)::date AS mes,
           SUM(od.unit_price * od.quantity * (1 - od.discount))::numeric AS facturacion
    FROM orders o
    JOIN order_details od ON od.order_id = o.order_id
    WHERE EXTRACT(YEAR FROM o.order_date) = 1998
    GROUP BY DATE_TRUNC('month', o.order_date)
)
SELECT mes,
       round(facturacion, 2)                           AS facturacion,
       round(SUM(facturacion) OVER (ORDER BY mes), 2)  AS acumulado
FROM por_mes
ORDER BY mes;

-- Resultado (filas y primera fila): "1998-01-01"	94222.11	94222.11 ; 5 filas

-- Pregunta 9
WITH por_empleado_anio AS (
    SELECT e.employee_id,
           e.first_name || ' ' || e.last_name AS empleado,
           EXTRACT(YEAR FROM o.order_date)::int AS anio,
           SUM(od.unit_price * od.quantity * (1 - od.discount))::numeric AS facturacion
    FROM employees e
    JOIN orders o         ON o.employee_id = e.employee_id
    JOIN order_details od ON od.order_id   = o.order_id
    GROUP BY e.employee_id, e.first_name, e.last_name, EXTRACT(YEAR FROM o.order_date)
)
SELECT empleado,
       anio,
       round(facturacion, 2) AS facturacion,
       round(LAG(facturacion) OVER (PARTITION BY employee_id ORDER BY anio), 2) AS anio_anterior
FROM por_empleado_anio
ORDER BY empleado, anio;

-- Resultado (filas y primera fila): "Andrew Fuller"	1996	21757.06	; 27 filas
