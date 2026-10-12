-- =====================================================================
--  EJERCICIO 1 · Conocer y diseñar
--  Almacenamiento, visualización y procesamiento de datos · Sesión 2
--  Plantilla de trabajo: no se entrega; se corrige en clase.
-- =====================================================================
--  En este ejercicio no se usa IA.
-- =====================================================================

--  No tienes que escribir SQL: selecciona cada sentencia y pulsa F5.
--  Tus respuestas van como comentarios, en las líneas que empiezan por --.

-- ---------------------------------------------------------------------
-- PARTE A · Arrancar y comprobar
-- ---------------------------------------------------------------------
-- A1. Estado de curso-postgres y curso-pgadmin (docker compose ps, en la terminal):

-- A2. Número de pedidos:
SELECT count(*) FROM orders;

--Respuesta: 830

-- A3. Versión de PostgreSQL:
SELECT version();
--Respuesta: PostgreSQL 16.15 (Debian 16.15-1.pgdg13+2) on x86_64-pc-linux-gnu, compiled by gcc (Debian 14.2.0-19) 14.2.0, 64-bit

-- ---------------------------------------------------------------------
-- PARTE B · El mapa de Northwind
-- ---------------------------------------------------------------------
-- B1. Número de tablas del esquema public:
SELECT count(*) FROM information_schema.tables
WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
--Respuesta: 14

-- B2. Clave primaria de order_details y por qué es compuesta: order_id, es compuesto porque un pedido puede tener varios productos
-- B3. Columna de orders que apunta a shippers:ship_via

-- B4. Qué significa reports_to y quién no tiene jefe:
SELECT first_name, last_name FROM employees WHERE reports_to IS NULL; 
--Respuesta: Andrew	Fuller no tiene jefe. Reports to es una clave que relaciona al empleado con su jefe (al que reporta)

-- B5. Tipo de relación entre products y orders y tabla que la resuelve: 
-- Respuesta un order está relacionado con un product a través de order_details, la cual conecta ambas tablas por las claves product_id y order_id.

-- B6. Cómo guardarías varios teléfonos por cliente: Por una tabla adicional llamada customer_phones, con una clave foránea que apunte a la tabla customers y una columna para el teléfono.

-- ---------------------------------------------------------------------
-- PARTE C · Normalizar la tabla de matrícula
-- ---------------------------------------------------------------------

-- C1. Anomalía de actualización (filas): Si se cambia el nombre de una asignatura y no se cambia el profesor.
--     Anomalía de inserción: Si se intenta insertar una nueva nota para un alumno que no existe en la tabla de alumnos pero no tiene asignatura asociada.
--     Anomalía de borrado: Si se elimina un alumno de la tabla de alumnos, todas las notas asociadas a ese alumno también se eliminarán, lo que puede llevar a la pérdida de información importante sobre las calificaciones de ese alumno.
-- C2. Dependencias: dni -> nombre, cod_prov -> provincia, cod_asig -> asignatura, profesor -> asignatura.
-- C3. Tu diseño en 3FN (tablas, claves primarias y foráneas):
-- C4. Diferencias entre tu diseño y el script:
--     Filas que devuelve la comprobación:

DROP SCHEMA IF EXISTS practica CASCADE;  
CREATE SCHEMA practica;

CREATE TABLE practica.provincias (
    cod_prov  CHAR(2) PRIMARY KEY,
    provincia TEXT NOT NULL
);
CREATE TABLE practica.alumnos (
    dni      CHAR(9) PRIMARY KEY,
    nombre   TEXT NOT NULL,
    cod_prov CHAR(2) NOT NULL REFERENCES practica.provincias (cod_prov)
);
CREATE TABLE practica.asignaturas (
    cod_asig   TEXT PRIMARY KEY,
    asignatura TEXT NOT NULL,
    profesor   TEXT NOT NULL
);
CREATE TABLE practica.notas (
    dni      CHAR(9) REFERENCES practica.alumnos (dni),
    cod_asig TEXT    REFERENCES practica.asignaturas (cod_asig),
    nota     NUMERIC(4, 2) NOT NULL CHECK (nota BETWEEN 0 AND 10),
    PRIMARY KEY (dni, cod_asig)
);

INSERT INTO practica.provincias VALUES ('41', 'Sevilla'), ('14', 'Córdoba');
INSERT INTO practica.alumnos VALUES
    ('12345678A', 'Pablo Ruiz', '41'), ('87654321B', 'Lucía Gómez', '14'),
    ('11223344C', 'Marta León', '41');
INSERT INTO practica.asignaturas VALUES
    ('BD', 'Bases de datos', 'Ana Gil'), ('VIS', 'Visualización', 'Luis Mora'),
    ('IA', 'Inteligencia artificial', 'Ana Gil');
INSERT INTO practica.notas VALUES
    ('12345678A', 'BD', 8.5), ('12345678A', 'VIS', 6.0),
    ('87654321B', 'BD', 7.0), ('87654321B', 'VIS', 9.0),
    ('11223344C', 'IA', 6.5), ('11223344C', 'BD', 5.0);

-- Comprobación: tiene que devolver 6 filas
SELECT a.dni, a.nombre, p.cod_prov, p.provincia,
       s.cod_asig, s.asignatura, s.profesor, n.nota
FROM practica.notas n
JOIN practica.alumnos a     ON a.dni = n.dni
JOIN practica.provincias p  ON p.cod_prov = a.cod_prov
JOIN practica.asignaturas s ON s.cod_asig = n.cod_asig
ORDER BY a.dni, s.cod_asig;

-- ---------------------------------------------------------------------
-- PARTE D · Romper las reglas a propósito (una sentencia cada vez)
-- ---------------------------------------------------------------------
-- D1 · Nota de un alumno que no existe
INSERT INTO practica.notas VALUES ('99999999Z', 'BD', 5);
-- Mensaje de error: ERROR:  insert or update on table "notas" violates foreign key constraint "notas_dni_fkey"
--Key (dni)=(99999999Z) is not present in table "alumnos". 
--SQL state: 23503
--Detail: Key (dni)=(99999999Z) is not present in table "alumnos".

-- Regla que lo impide: insertar una nota para un alumno que no existe en la tabla de alumnos.

-- D2 · La misma nota dos veces
INSERT INTO practica.notas VALUES ('12345678A', 'BD', 6);
-- Mensaje de error: ERROR:  duplicate key value violates unique constraint "notas_pkey"
--Key (dni, cod_asig)=(12345678A, BD) already exists. 
--SQL state: 23505
--Detail: Key (dni, cod_asig)=(12345678A, BD) already exists.
-- Regla que lo impide: no se puede insertar la misma nota dos veces para el mismo alumno y asignatura, ya que la clave primaria de la tabla notas es compuesta por dni y cod_asig.

-- D3 · Una nota de 11
INSERT INTO practica.notas VALUES ('12345678A', 'IA', 11);
-- Mensaje de error:ERROR:  new row for relation "notas" violates check constraint "notas_nota_check"
--Failing row contains (12345678A, IA, 11.00). 
--SQL state: 23514
--Detail: Failing row contains (12345678A, IA, 11.00).
-- Regla que lo impide: check constraint "NOT NULL CHECK (nota BETWEEN 0 AND 10)"

-- D4 · Borrar una asignatura que tiene notas
DELETE FROM practica.asignaturas WHERE cod_asig = 'BD';
-- Mensaje de error:ERROR:  update or delete on table "asignaturas" violates foreign key constraint "notas_cod_asig_fkey" on table "notas"
--Key (cod_asig)=(BD) is still referenced from table "notas". 
--SQL state: 23503
--Detail: Key (cod_asig)=(BD) is still referenced from table "notas".
-- Regla que lo impide: No puede borrarse una clave que está siendo referenciada por otra tabla, en este caso, la tabla notas.

-- ---------------------------------------------------------------------
-- PARTE E · Transacciones paso a paso (sentencia a sentencia)
-- ---------------------------------------------------------------------
-- Consulta de control (ejecútala antes de empezar y anota el stock de partida):
SELECT product_name, units_in_stock FROM products WHERE product_id <= 2;
-- Stock de partida de Chai y Chang: "Chai"	39 "Chang"	17

-- E1 · Me arrepiento: ROLLBACK
BEGIN;
UPDATE products SET units_in_stock = units_in_stock - 10 WHERE product_id = 1;
SELECT product_name, units_in_stock FROM products WHERE product_id <= 2;
ROLLBACK;
SELECT product_name, units_in_stock FROM products WHERE product_id <= 2;
-- E1.1. Chai antes y después del ROLLBACK, y qué ha hecho el ROLLBACK: 
--Antes "Chai"	29 "Chang"	27
--Después "Chai" 39 "Chang"	17

-- E2 · Todo va bien: COMMIT
BEGIN;
UPDATE products SET units_in_stock = units_in_stock - 10 WHERE product_id = 1;
UPDATE products SET units_in_stock = units_in_stock + 10 WHERE product_id = 2;
SELECT product_name, units_in_stock FROM products WHERE product_id <= 2;
COMMIT;
ROLLBACK;     -- ¿se puede deshacer ya?
SELECT product_name, units_in_stock FROM products WHERE product_id <= 2;

-- Deja el stock como estaba, con otra transacción con el movimiento contrario:
BEGIN;
UPDATE products SET units_in_stock = units_in_stock + 10 WHERE product_id = 1;
UPDATE products SET units_in_stock = units_in_stock - 10 WHERE product_id = 2;
COMMIT;
SELECT product_name, units_in_stock FROM products WHERE product_id <= 2;
-- E2.1. Stock de Chai y Chang después del COMMIT: "Chai"	29 "Chang"	27
-- E2.2. Mensaje del ROLLBACK posterior y por qué no deshace nada: WARNING:  there is no transaction in progress ROLLBACK, no deshace nada
-- ya que tras un commit ya se ha cerrado la transacción incumpliría el principiio de consistencia.

-- E2.3. Por qué hace falta otra transacción para volver al stock de partida: Porque el commit cierra la transacción y hace permanentes los cambios.

-- E3 · Algo falla: la transacción se bloquea
BEGIN;
UPDATE products SET units_in_stock = units_in_stock - 10 WHERE product_id = 1;
-- Errata a propósito: la columna se llama units_in_stock, no unidades
UPDATE products SET unidades = unidades + 10 WHERE product_id = 2;
SELECT product_name, units_in_stock FROM products WHERE product_id <= 2;
ROLLBACK;
SELECT product_name, units_in_stock FROM products WHERE product_id <= 2;
-- E3.1. Mensaje del SELECT que va después del error y qué significa: ERROR:  column "unidades" does not exist
-- E3.2. Unidades de Chai y Chang al final, y por qué (letra de ACID): No se han guardado los cambios porque la transacción se ha revertido. Letra I de ACID, la integridad de la base de datos se mantiene y no se han aplicado cambios parciales.
-- E3.3. Sin BEGIN, unidades de Chai al final y dónde estarían las 10 que faltan: 
