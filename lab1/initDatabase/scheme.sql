-- Удаление таблиц, если они уже существуют
DROP TABLE IF EXISTS 
    reviews, order_items, orders, users,
    products, categories, manufacturers CASCADE;

-- Справочники
CREATE TABLE categories (
    category_id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE manufacturers (
    manufacturer_id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

CREATE TABLE products (
    product_id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category_id BIGINT REFERENCES categories(category_id),
    manufacturer_id BIGINT REFERENCES manufacturers(manufacturer_id),
    price NUMERIC(10, 2) NOT NULL
);

-- Пользователи
CREATE TABLE users (
    user_id BIGSERIAL PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    city VARCHAR(100),
    registration_date DATE,
    is_active BOOLEAN
);

-- Заказы
CREATE TABLE orders (
    order_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id),
    order_date DATE,
    payment_method VARCHAR(20),
    total_amount NUMERIC(10, 2)
);

CREATE TABLE order_items (
    item_id BIGSERIAL PRIMARY KEY,
    order_id BIGINT REFERENCES orders(order_id),
    product_id BIGINT REFERENCES products(product_id),
    quantity INT,
    unit_price NUMERIC(10, 2),
    subtotal NUMERIC(12, 2)
);

-- Отзывы
CREATE TABLE reviews (
    review_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id),
    product_id BIGINT REFERENCES products(product_id),
    rating INT CHECK (rating >= 1 AND rating <= 5),
    title VARCHAR(255),
    comment TEXT,
    date DATE
);

