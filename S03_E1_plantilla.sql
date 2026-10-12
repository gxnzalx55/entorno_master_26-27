-- =====================================================================
--  EJERCICIO 1 · Preguntas a Northwind
--  Almacenamiento, visualización y procesamiento de datos · Sesión 3
--  Plantilla de trabajo: no se entrega; se corrige en clase.
-- =====================================================================
--  En este ejercicio no se usa IA.
--  Las preguntas son independientes: hazlas en el orden que quieras.
--  Debajo de cada consulta, anota lo que te ha salido y si cuadra con
--  el dato de control del enunciado.
-- =====================================================================

-- ---------------------------------------------------------------------
-- PARTE A · UNIONES
-- ---------------------------------------------------------------------

-- A1. Mecanismo: JOIN de tres tablas: products con categories y con suppliers, cada una con su ON.
SELECT p.product_name, s.company_name
FROM categories c
JOIN products p ON c.category_id = p.category_id AND c.category_name = 'Seafood'
JOIN suppliers s ON p.supplier_id = s.supplier_id
GROUP BY p.product_name, s.company_name

-- Resultado (¿cuadra con el control?): Si (Total rows: 12) "Rogede sild"	"Lyngbysild" "Röd Kaviar"	"Svensk Sjöföda AB" "Gravad lax"	"Svensk Sjöföda AB" "Nord-Ost Matjeshering"	
-- "Nord-Ost-Fisch Handelsgesellschaft mbH" "Konbu"	"Mayumi's" "Escargots de Bourgogne"	"Escargots Nouveaux" "Jack's New England Clam Chowder"	"New England Seafood Cannery"
-- "Carnarvon Tigers"	"Pavlova, Ltd." "Spegesild"	"Lyngbysild" "Boston Crab Meat"	"New England Seafood Cannery" "Inlagd Sill"	"Svensk Sjöföda AB" "Ikura"	"Tokyo Traders"

-- A2. Mecanismo: LEFT JOIN de customers con orders y count(o.order_id), no count(*).
SELECT c.company_name, c.country, count(o.order_id) AS cant
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.customer_id 
WHERE c.country = 'France'
GROUP BY c.company_name, c.country
ORDER BY cant

-- Resultado (¿cuadra con el control?):Si (Total rows: 11) "Paris spécialités"	0

-- A3. Mecanismo: LEFT JOIN … IS NULL (anti-join), con la condición de la fecha en el ON: AND o.order_date >= '1997-01-01' AND o.order_date < '1998-01-01'.
SELECT c.customer_id, c.company_name, count(o.order_id) AS total
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id AND o.order_date >= '1997-01-01' AND o.order_date < '1998-01-01'
WHERE o.customer_id IS NULL
GROUP BY c.company_name, c.customer_id
ORDER BY total

-- Resultado (¿cuadra con el control?): Sí (Total rows: 5)

-- A4. Mecanismo: Autounión: employees e JOIN employees j ON j.employee_id = e.reports_to.
SELECT e.first_name || ' ' || e.last_name AS empleado, e.city AS ciudad_empleado, j.first_name || ' ' || j.last_name AS jefe, j.city AS ciudad_jefe
FROM employees e
LEFT JOIN employees j ON j.employee_id = e.reports_to WHERE e.city != j.city
ORDER BY e.employee_id

-- Resultado (¿cuadra con el control?): Sí (Total rows: 5), "Andrew Fuller" "Andrew Fuller" "Andrew Fuller" "Andrew Fuller" "Andrew Fuller".

-- A5. Mecanismo: Un camino de cinco tablas: customers → orders → order_details → products → categories. El filtro está en un extremo (país) y la agrupación en el otro (categoría).
SELECT cat.category_name, sum(od.quantity) total
FROM customers c 
JOIN orders o ON c.customer_id = o.customer_id AND c.country = 'Germany' 
JOIN order_details od ON od.order_id = o.order_id AND o.order_date >= '1997-01-01' AND o.order_date < '1998-01-01'
JOIN products p ON od.product_id = p.product_id
JOIN categories cat on cat.category_id = p.category_id
GROUP BY cat.category_name
ORDER BY total DESC

-- Resultado (¿cuadra con el control?):Sí (Total rows: 8) "Confections"	989

-- A6. Mecanismo: Filas multiplicadas (fan-out). Antes de sumar, pregúntate qué es una fila: ¿un pedido o una línea de pedido?
--FORMA 1:
SELECT sum(o.freight)
FROM orders o
JOIN order_details od ON o.order_id = od.order_id
JOIN products p ON od.product_id = p.product_id
JOIN categories c ON c.category_id=p.category_id
WHERE c.category_name = 'Beverages'

--FORMA 2:
SELECT sum(o.freight)
FROM orders o
WHERE o.order_id IN (
SELECT od.order_id
FROM order_details od
JOIN products p ON p.product_id = od.product_id
WHERE p.category_id = 1)


-- Resultado (¿cuadra con el control?): 1) 39886.746 2) 34964.59, El segundo resultado es el correcto, ya que al poder haber varias bebidas en un mismo pedido se produce fan-out.

-- ---------------------------------------------------------------------
-- PARTE B · SUBCONSULTAS
-- ---------------------------------------------------------------------

-- B1. Mecanismo: Subconsulta escalar en el WHERE: freight > (SELECT avg(freight) FROM orders).


-- Resultado (¿cuadra con el control?):

-- B2. Mecanismo: IN con una subconsulta que devuelve los customer_id de los pedidos con productos de ese proveedor (orders, order_details, products y suppliers).


-- Resultado (¿cuadra con el control?):

-- B3. Mecanismo: NOT EXISTS con una subconsulta correlacionada: dentro, WHERE o.customer_id = c.customer_id AND p.category_id = 1.


-- Resultado (¿cuadra con el control?):

-- B4. Mecanismo: Subconsulta en el FROM: primero cuenta las líneas de cada pedido en order_details; después calcula avg, max y min sobre esos recuentos. avg(count(*)) da error.


-- Resultado (¿cuadra con el control?):

-- B5. Mecanismo: Agregación condicional: count(*) FILTER (WHERE …), o sum(CASE WHEN … THEN 1 ELSE 0 END).


-- Resultado (¿cuadra con el control?):

-- ---------------------------------------------------------------------
-- PARTE C · CONJUNTOS Y COMPROBACIÓN
-- ---------------------------------------------------------------------

-- C1. Mecanismo: EXCEPT entre SELECT country FROM customers y SELECT country FROM suppliers.


-- Resultado (¿cuadra con el control?):

-- C2. Mecanismo: Total de control. Primero customers, orders y order_details con GROUP BY country; después suma ese resultado (subconsulta en el FROM) y compáralo con SELECT sum(…) FROM order_details.


-- Resultado (¿cuadra con el control?):
