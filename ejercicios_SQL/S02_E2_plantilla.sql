-- =====================================================================
--  EJERCICIO 2 · Primeras consultas
--  Almacenamiento, visualización y procesamiento de datos · Sesión 2
--  Plantilla de trabajo: no se entrega; se corrige en clase.
-- =====================================================================
--  Sin IA, salvo en los retos marcados «Con IA». En esos retos, anota:
--    Herramienta y versión:
--    Prompt principal (menos de 20 palabras):
-- =====================================================================

-- ---------------------------------------------------------------------
-- NIVEL 1 · Filtrar y ordenar
-- ---------------------------------------------------------------------

-- Pregunta 1
-- Consulta:
SELECT count(*)
FROM products
WHERE discontinued = 1


-- Resultado: 10
-- Explicación (una frase): De todos los productos, 10 de ellos están descontinuados.

-- Pregunta 2
-- Consulta:
SELECT product_name, units_in_stock
FROM products
WHERE units_in_stock > 0
ORDER BY units_in_stock DESC
LIMIT 1

-- Resultado: "Rhönbräu Klosterbier"	125
-- Explicación (una frase): El producto con más existencias en stock es "Rhönbräu Klosterbier" con 125 unidades.

-- Pregunta 3
-- Consulta:
SELECT count(*)
FROM customers
WHERE city = 'London'

-- Resultado: 6
-- Explicación (una frase): Hay 6 clientes en Londres.

-- Pregunta 4
-- Consulta:
SELECT count(*)
FROM orders
WHERE ship_country = 'France' AND EXTRACT(YEAR FROM order_date) = 1997

-- Resultado: 39
-- Explicación (una frase): Hay 38 pedidos enviados a Francia en el año 1997.

-- Pregunta 5
-- Consulta:
SELECT count(*)
FROM orders
WHERE shipped_date is NULL

-- Resultado: 21
-- Explicación (una frase): Hay 21 pedidos que aún no han sido enviados (la fecha de envío es nula).

-- ---------------------------------------------------------------------
-- NIVEL 2 · Calcular por fila
-- ---------------------------------------------------------------------

-- Pregunta 6
-- Consulta:
SELECT order_id, shipped_date - order_date AS days_difference
FROM orders
WHERE shipped_date IS NOT NULL
ORDER BY days_difference DESC
LIMIT 10

-- Resultado: 37
-- Explicación (una frase): El pedido con la mayor diferencia de días entre la fecha de envío y la fecha del pedido es de 37 días.

-- Pregunta 7
-- Consulta:
SELECT count(*)
FROM customers
WHERE LENGTH(company_name) > 30

-- Resultado: 3
-- Explicación (una frase): Hay 3 clientes cuyo nombre de empresa tiene más de 30 caracteres.

-- Pregunta 8
-- Consulta:
SELECT product_name, units_in_stock * unit_price AS almacen
FROM products
ORDER BY almacen DESC
LIMIT 1

-- Resultado: "Côte de Blaye"	4479.5
-- Explicación (una frase): El producto con el mayor valor de inventario (unidades en stock multiplicadas por el precio unitario) es "Côte de Blaye" con un valor de 4479.5.

-- Pregunta 9
-- Consulta:
SELECT count(*)
FROM orders
WHERE required_date - shipped_date < 0

-- Resultado: 37
-- Explicación (una frase): Hay 37 pedidos que fueron enviados después de la fecha requerida.

-- Pregunta 10
-- Consulta:
SELECT product_name, 
CASE
WHEN units_on_order + units_in_stock - reorder_level > 0 THEN 'ok'
ELSE 'reponer'
END AS stocked
FROM products
GROUP BY stocked

-- Resultado: No da
-- Explicación (una frase):

-- ---------------------------------------------------------------------
-- NIVEL 3 · Resumir
-- ---------------------------------------------------------------------

-- Pregunta 11
-- Consulta:
SELECT count(unit_price * quantity * (1 - discount))
FROM order_details

-- Resultado: 2155
-- Explicación (una frase): No hay mucho más que explicar

-- Pregunta 12
-- Consulta:
SELECT category_id, ROUND(AVG(unit_price)::numeric, 2) AS avg_price
FROM products
GROUP BY category_id
ORDER BY avg_price DESC
LIMIT 1;

-- Resultado: 6 "54.01"
-- Explicación (una frase): La categoría con el precio promedio más alto es la categoría 6 con un precio promedio de 54.01.

-- Pregunta 13
-- Consulta:
SELECT count(DISTINCT customer_id)
FROM orders

-- Resultado: 89
-- Explicación (una frase): Al hacer uso de DISTINCT, solo se cuentan los id de clientes sin repetir.

-- Pregunta 14
-- Consulta:
SELECT ship_country
FROM orders
GROUP BY ship_country
HAVING count(*) > 50

-- Resultado:"USA" "France" "Brazil" "UK" "Germany"
-- Explicación (una frase): Los países con más de 50 pedidos son esos.

-- Pregunta 15
-- Consulta:
SELECT EXTRACT(MONTH FROM DATE_TRUNC('month', order_date)) AS mes, count(*) AS num
FROM orders
GROUP BY mes
ORDER BY num DESC
LIMIT 1

-- Resultado: 4 105
-- Explicación (una frase): Teniendo en cuenta el mes y no el año, el mes con más pedidos es abril con 105 pedidos.

-- ---------------------------------------------------------------------
-- NIVEL 4 · Unir tablas
-- ---------------------------------------------------------------------

-- Pregunta 16
-- Consulta:
SELECT c.category_name, count(p.units_in_stock)
FROM categories c
JOIN products p
ON c.category_id = p.category_id
WHERE c.category_name = 'Beverages'
GROUP BY c.category_id

-- Resultado: Beverages 12
-- Explicación (una frase): Hay 12 tipos distintos de "Beverages" en stock.

-- Pregunta 17
-- Consulta: 
SELECT s.company_name, COUNT(p.product_name) AS num
FROM suppliers s
JOIN products p
ON s.supplier_id = p.supplier_id
GROUP BY company_name
ORDER BY num DESC
limit 3

-- Resultado: "Plutzer Lebensmittelgroßmärkte AG"	5; "Pavlova, Ltd."	5; "Specialty Biscuits, Ltd."	5
-- Explicación (una frase):A ojímetro pongo el limit a 3, viendo antes que hay 3 proveedores con 5 productos.

-- Pregunta 18
-- Consulta:
SELECT e.first_name, e.last_name, count(o.order_id) AS num
FROM employees e
JOIN orders o
ON e.employee_id = o.employee_id
GROUP BY e.first_name, e.last_name
ORDER BY num DESC
LIMIT 1

-- Resultado: "Margaret"	"Peacock"	156
-- Explicación (una frase): La empleada con más pedidos asignados es Margaret Peacock con 156 pedidos.

-- Pregunta 19
-- Consulta:
SELECT c.company_name, sum(od.quantity * od.unit_price) AS ventas
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN order_details od ON o.order_id = od.order_id
WHERE c.country = 'Spain'
GROUP BY c.company_name
ORDER BY ventas DESC
LIMIT 1

-- Resultado: "Godos Cocina Típica"	11830.099954605103
-- Explicación (una frase): El cliente en España con mayores ventas es "Godos Cocina Típica" con un total de 11830.10.

-- Pregunta 20
-- Consulta:
SELECT s.company_name, sum(o.freight) AS total
FROM shippers s
JOIN orders o ON s.shipper_id = o.ship_via       ( AND EXTRACT(YEAR FROM o.order_date) = 1998 ) --Se añade esta condición cuando se quiera filtrar por el año 1998
GROUP BY s.company_name
ORDER BY total DESC
LIMIT 1

-- Resultado: En total: "United Package"	28244.852; En el año 1998: "United Package"	12122.137
-- Explicación (una frase): Po eso