
-- =====================================================================
-- Анализ запросов до создания индексов
-- =====================================================================

-- Запрос по дате заказа (до индекса)
EXPLAIN ANALYZE
SELECT * FROM orders WHERE order_date BETWEEN '2023-05-10' AND '2025-05-10';

-- Запрос по email пользователя (до индекса)
EXPLAIN ANALYZE
SELECT * FROM users WHERE email = 'shannonramirez@example.com';

-- Запрос по фамилии пользователя (до индекса)
EXPLAIN ANALYZE
SELECT * FROM users WHERE last_name ILIKE 'smith';

-- Запрос по части текста отзыва (до GIN индекса)
EXPLAIN ANALYZE
SELECT * FROM reviews WHERE comment ILIKE '%quality%';

-- Запрос по id заказа в order_items (до BRIN)
EXPLAIN ANALYZE
SELECT * FROM order_items WHERE order_id BETWEEN 100000 AND 100500;

-- Запрос по дате регистрации пользователей (до BRIN)
EXPLAIN ANALYZE
SELECT * FROM users WHERE registration_date BETWEEN '2023-01-01' AND '2023-12-31';

-- =====================================================================
-- Создание индексов
-- =====================================================================

-- === B-TREE индексы ===
CREATE INDEX idx_orders_order_date ON orders(order_date);
CREATE INDEX idx_users_email ON users(email);

-- === GIN индекс (расширение pg_trgm необходимо) ===
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX idx_reviews_comment_trgm ON reviews USING GIN(comment gin_trgm_ops);
CREATE INDEX idx_users_last_name_trgm ON users USING GIN(last_name gin_trgm_ops);

-- === BRIN индексы ===
CREATE INDEX idx_order_items_order_id_brin ON order_items USING BRIN(order_id);
CREATE INDEX idx_users_registration_brin ON users USING BRIN(registration_date);

-- =====================================================================
-- Анализ тех же запросов после индексации
-- =====================================================================

EXPLAIN ANALYZE
SELECT * FROM orders WHERE order_date BETWEEN '2023-05-10' AND '2025-05-10';

EXPLAIN ANALYZE
SELECT * FROM users WHERE email = 'shannonramirez@example.com';

EXPLAIN ANALYZE
SELECT * FROM users WHERE last_name ILIKE 'smith';

EXPLAIN ANALYZE
SELECT * FROM reviews WHERE comment ILIKE '%quality%';

EXPLAIN ANALYZE
SELECT * FROM order_items WHERE order_id BETWEEN 100000 AND 100500;

EXPLAIN ANALYZE
SELECT * FROM users WHERE registration_date BETWEEN '2023-01-01' AND '2023-12-31';