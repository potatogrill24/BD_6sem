
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS pg_bigm;

-- =====================================================================
-- Шаг 1: Поиск с использованием trigram-сходства (pg_trgm)
-- =====================================================================
-- Создание индекса GIN на комментарии отзывов для ускорения поиска
CREATE INDEX IF NOT EXISTS idx_reviews_comment_trgm ON reviews USING GIN(comment gin_trgm_ops);

-- Пример запроса: найти отзывы, содержащие слова, похожие на "quality"
SELECT *
FROM reviews
WHERE comment % 'quality'
ORDER BY similarity(comment, 'quality') DESC
LIMIT 10;

-- =====================================================================
-- Шаг 2: Использование расширения pg_bigm для быстрого LIKE-поиска
-- =====================================================================
-- Индекс с использованием pg_bigm (BIGRAM индекс)
CREATE INDEX IF NOT EXISTS idx_reviews_comment_bigram ON reviews USING gin (comment gin_bigm_ops);

-- Пример запроса с LIKE (ускоряется pg_bigm)
SELECT * FROM reviews WHERE comment LIKE '%performance%' LIMIT 10;

-- =====================================================================
-- Шаг 3: Шифрование данных (pgcrypto)
-- =====================================================================
-- Пример: зашифровать email пользователей при вставке
-- Для демонстрации создадим копию users:
CREATE TABLE IF NOT EXISTS secure_users AS
SELECT *, NULL::BYTEA AS email_encrypted FROM users LIMIT 1000;

-- Обновим email в зашифрованном виде
UPDATE secure_users
SET email_encrypted = pgp_sym_encrypt(email, 'secret_key');

-- Расшифровка email (пример)
SELECT user_id,
       pgp_sym_decrypt(email_encrypted, 'secret_key') AS decrypted_email
FROM secure_users
LIMIT 10;