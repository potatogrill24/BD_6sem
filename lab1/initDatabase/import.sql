-- Отключаем триггеры (ускорение импорта)
ALTER TABLE products DISABLE TRIGGER ALL;
ALTER TABLE categories DISABLE TRIGGER ALL;
ALTER TABLE manufacturers DISABLE TRIGGER ALL;
ALTER TABLE users DISABLE TRIGGER ALL;
ALTER TABLE orders DISABLE TRIGGER ALL;
ALTER TABLE order_items DISABLE TRIGGER ALL;
ALTER TABLE reviews DISABLE TRIGGER ALL;

-- Загрузка из CSV (пути предполагаются в Docker-контейнере или локально)
COPY categories(category_id, name) FROM '/data/categories.csv' CSV HEADER;
COPY manufacturers(manufacturer_id, name) FROM '/data/manufacturers.csv' CSV HEADER;
COPY products(product_id, name, category_id, manufacturer_id, price) FROM '/data/products.csv' CSV HEADER;
COPY users(user_id, first_name, last_name, email, city, registration_date, is_active) FROM '/data/users.csv' CSV HEADER;
COPY orders(order_id, user_id, order_date, payment_method, total_amount) FROM '/data/orders.csv' CSV HEADER;
COPY order_items(item_id, order_id, product_id, quantity, unit_price, subtotal) FROM '/data/order_items.csv' CSV HEADER;
COPY reviews(review_id, user_id, product_id, rating, title, comment, date) FROM '/data/reviews.csv' CSV HEADER;

-- Включаем триггеры обратно
ALTER TABLE products ENABLE TRIGGER ALL;
ALTER TABLE categories ENABLE TRIGGER ALL;
ALTER TABLE manufacturers ENABLE TRIGGER ALL;
ALTER TABLE users ENABLE TRIGGER ALL;
ALTER TABLE orders ENABLE TRIGGER ALL;
ALTER TABLE order_items ENABLE TRIGGER ALL;
ALTER TABLE reviews ENABLE TRIGGER ALL;

