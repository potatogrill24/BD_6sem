# Лабораторная работа 1: PostgreSQL — индексы, транзакции и расширения

## Навигация

```
├── data/                        # CSV-файлы с данными (до 10 млн строк)
├── docker-compose.yml           # Контейнер PostgreSQL
├── Dockerfile                   # Для настройки контейнера
├── initDatabase/
│   ├── scheme.sql               # Создание таблиц с FK, PK, типами
│   └── import.sql               # Импорт данных из CSV (COPY)
│   
├── gen.py       # Скрипт генерации данных
├── tasks/
│   ├── index_analysis.sql       # Задание 1.1 — Индексы: B-tree, GIN, BRIN
│   ├── transactions.sql         # Задание 1.2 — Транзакции, уровни изоляции
│   ├── extensions.sql           # Задание 1.3 — Расширения: pg_trgm, pg_bigm, pgcrypto
│   └── analysis.md              # Анализ: безопасность и производительность
│   
```

## Команды для запуска проекта и работы с ним

```bash
# 1. Генерация данных
python3 -m venv venv
source venv/bin/activate
python3 gen.py

# 2. Поднятие контейнера с БД
docker-compose down -v && docker-compose build && docker-compose up -d

# 3. Подключение к PostgreSQL внутри контейнера
docker exec -it store_db psql -U postgres -d store

```
**Больше команд в файле tasks/analysis.md**

