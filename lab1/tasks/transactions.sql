
-- =====================================================================
-- Уровень 1: Транзакция с добавлением заказа и обновлением суммы
-- =====================================================================

BEGIN;

SELECT setval('orders_order_id_seq', (SELECT MAX(order_id) FROM orders));
INSERT INTO orders (user_id, order_date, payment_method, total_amount)
VALUES (1, CURRENT_DATE, 'card', 0)
RETURNING order_id;

SELECT setval('order_items_item_id_seq', (SELECT MAX(item_id) FROM order_items));
INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal)
VALUES (1000, 1, 2, 500.00, 1000.00);

-- Обновление суммы
UPDATE orders
SET total_amount = (
    SELECT SUM(subtotal) FROM order_items WHERE order_id = 1000
)
WHERE order_id = 1000;

COMMIT;


-- =====================================================================
-- Уровень 2: Транзакция с добавлением отзыва (review)
-- =====================================================================

BEGIN;

SELECT setval('reviews_review_id_seq', (SELECT MAX(review_id) FROM reviews));
INSERT INTO reviews (user_id, product_id, rating, title, comment, date)
VALUES (1, 1, 5, 'Отлично', 'Качество превзошло ожидания', CURRENT_DATE);

COMMIT;


-- =====================================================================
-- Уровень 3: Проверка аномалии «грязного чтения» (READ UNCOMMITTED)
-- =====================================================================

-- Session A
BEGIN TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
UPDATE products SET price = price + 100 WHERE product_id = 1;
-- НЕ КОММИТИТЬ

-- Session B
BEGIN TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
SELECT price FROM products WHERE product_id = 1;
COMMIT;

-- Session A
ROLLBACK; -- Цена не изменится


-- =====================================================================
-- Уровень 4: Проверка «неповторяющегося чтения» (REPEATABLE READ)
-- =====================================================================

-- Session A
BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ;
SELECT * FROM products WHERE product_id = 1;

-- Session B (пока A не закоммитила)
BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ;
UPDATE products SET price = price + 200 WHERE product_id = 1;
COMMIT;

-- Session A
SELECT * FROM products WHERE product_id = 1; -- Цена не изменится
COMMIT;


-- =====================================================================
-- Уровень 5: Проверка «фантомного чтения» (SERIALIZABLE)
-- =====================================================================

-- Session A
BEGIN TRANSACTION ISOLATION LEVEL SERIALIZABLE;
SELECT COUNT(*) FROM orders WHERE user_id = 1;

-- Session B
BEGIN TRANSACTION ISOLATION LEVEL SERIALIZABLE;
INSERT INTO orders (user_id, order_date, payment_method, total_amount)
VALUES (1, CURRENT_DATE, 'card', 1000.00);
COMMIT;

-- Session A
SELECT COUNT(*) FROM orders WHERE user_id = 1; -- Не увидит новую строку
COMMIT;
