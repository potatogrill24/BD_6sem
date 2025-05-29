import streamlit as st
import psycopg2
import hashlib
from datetime import datetime
from datetime import date, time
import re
import pandas as pd
import os
import redis
import uuid
import json


DB_CONFIG = {
    "host": "localhost",
    "database": "postgre",
    "user": "postgre",
    "password": "postgre",
    "port": "5432",
}


redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True
)

TOKEN_TTL = int(os.getenv("TOKEN_TTL", 3600))

def generate_token(user_id):
    token = str(uuid.uuid4())
    redis_client.setex(f"user_token:{token}", TOKEN_TTL, user_id)
    return token


def get_user_id_by_token(token):
    return redis_client.get(f"user_token:{token}")

def save_session_data(session_id, data, ttl=3600):
    redis_client.hset(f"session:{session_id}", mapping=data)
    redis_client.expire(f"session:{session_id}", ttl)

def get_session_data(session_id):
    return redis_client.hgetall(f"session:{session_id}")

def cache_bootcamps(data, ttl=600):
    def convert(obj):
        if isinstance(obj, (date, time)):
            return obj.isoformat()
        return obj

    safe_data = [[convert(item) for item in row] for row in data]
    redis_client.setex("bootcamp_list", ttl, json.dumps(safe_data))


def get_cached_bootcamps():
    value = redis_client.get("bootcamp_list")
    return json.loads(value) if value else None

def cache_available_computers(key, data, ttl=300):
    redis_client.setex(key, ttl, json.dumps(data))

def get_cached_available_computers(key):
    val = redis_client.get(key)
    return json.loads(val) if val else None

def update_order_status(order_id, status):
    redis_client.hset("order_statuses", order_id, status)

def get_order_status(order_id):
    return redis_client.hget("order_statuses", order_id)

def publish_event(channel, message):
    redis_client.publish(channel, message)
    redis_client.rpush("notifications_history", message)    
    redis_client.ltrim("notifications_history", -50, -1)


# Подключение к БД
def get_connection():
    try:

        return psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB", "postgre"),
            user=os.getenv("POSTGRES_USER", "postgre"),
            password=os.getenv("POSTGRES_PASSWORD", "postgre"),
            host=os.getenv("POSTGRES_HOST", "db"),
            port=os.getenv("POSTGRES_PORT", "5432")
        )
    except Exception as e:
        st.error(f"Ошибка подключения к базе данных: {e}")
        return None


# Функция для хеширования пароля
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

#Валидация пароля
def validate_password(password):
    if len(password) < 5:
        return "Пароль должен быть не менее 5 символов."
    if not re.search(r"\d", password):
        return "Пароль должен содержать хотя бы одну цифру."
    if not re.search(r"[A-z]", password):
        return "Пароль должен содержать хотя бы одну латинскую букву."
    if re.search(r"[!@#$%^&*_(),.?\":{}|<>]", password):
        return "Пароль не должен содержать специальные символы."
    return None

def validate_age(birth_date):
    birth_date = datetime.strptime(birth_date, "%Y-%m-%d")
    today = datetime.today()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    if (age < 14):
        return "Пользователь должен достичь 14-летнего возраста."
    return None

# Проверка существования логина
def is_login_unique(login):
    conn = get_connection()
    if conn is None:
        return False
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM Клиент WHERE Логин = %s", (login,))
        count = cursor.fetchone()[0]
        return count == 0
    except Exception as e:
        st.error(f"Ошибка при проверке логина: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

# Функция для регистрации пользователя
def register_user(fio, login, password, birth_date, role):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Хеширование пароля
        hashed_password = hash_password(password)

        # Вычисление совершеннолетия и наличия скидок
        birth_date = datetime.strptime(birth_date, "%Y-%m-%d")
        today = datetime.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        is_adult = age >= 18

        # Вставка данных в таблицу Клиент
        cursor.execute(
            "INSERT INTO Клиент (ФИО, Совершеннолетие, Логин, Пароль, Хешированный_пароль) VALUES (%s, %s, %s, %s, %s)",
            (fio, is_adult, login, password, hashed_password)
        )
        conn.commit()

        # Получение id пользователя
        cursor.execute("SELECT id FROM Клиент WHERE Логин = %s", (login,))
        user_id = cursor.fetchone()[0]

        # Получение id роли
        cursor.execute("SELECT id FROM Роль WHERE Название = %s", (role,))
        role_id = cursor.fetchone()[0]

        # Вставка данных в таблицу Клиент_Роль
        cursor.execute(
            "INSERT INTO Клиент_Роль (id_клиента, id_роли) VALUES (%s, %s)",
            (user_id, role_id)
        )
        conn.commit()
    except Exception as e:
        st.error(f"Ошибка при регистрации пользователя: {e}")
    finally:
        cursor.close()
        conn.close()

# Функция для авторизации пользователя
def login_user(login, password):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Хеширование пароля
        hashed_password = hash_password(password)

        cursor.execute(
            "SELECT * FROM Клиент WHERE Логин = %s AND Хешированный_пароль = %s",
            (login, hashed_password)
        )
        user = cursor.fetchone()
        if user:
            user_id = user[0]
            cursor.execute(
                "SELECT Название FROM Роль WHERE id = (SELECT id_роли FROM Клиент_Роль WHERE id_клиента = %s)",
                (user_id,)
            )
            role = cursor.fetchone()[0]

            # Генерация токена
            token = generate_token(user_id)
            session_data = {"login": login, "role": role}
            save_session_data(token, session_data)

            st.session_state["page"] = "dashboard"
            st.session_state["login"] = login
            st.session_state["role"] = role
            st.session_state["token"] = token  # можно использовать в будущем
            st.session_state["user_id"] = user_id

            session_info = get_session_data(st.session_state["token"])
            st.write(f"Вы вошли как {session_info['login']} с ролью {session_info['role']}")

            st.rerun()
        else:
            st.error("Неверный логин или пароль или такой учетной записи не существует.")
    except Exception as e:
        st.error(f"Ошибка при авторизации пользователя: {e}")
    finally:
        cursor.close()
        conn.close()


# Функция для проверки админки
def check_admin(login, password):
    if login == "admin" and password == "admin":
        st.session_state["page"] = "dashboard"
        st.session_state['login'] = login
        st.session_state['role'] = "Администратор"
        st.rerun()

# Функция для выхода из учетной записи
def logout_user():
    st.session_state["page"] = "login"
    st.session_state["login"] = None
    st.session_state["role"] = None
    st.rerun()

def window_register():
    st.title("Регистрация пользователей")

    fio = st.text_input("ФИО")
    login = st.text_input("Логин")
    password = st.text_input("Пароль", type="password")
    birth_date = st.date_input("Дата рождения")
    role = st.selectbox("Выберите роль", ("Игрок", "Менеджер"))

    password_not_valid = validate_password(password)

    password_staff = None
    if role == "Менеджер":
        password_staff = st.text_input("Пароль для персонала", type="password")

    if st.button("Зарегистрироваться"):
        # Проверка заполненности всех полей
        if not fio or not login or not password or not birth_date or not role:
            st.error("Все поля должны быть заполнены.")

        # Проверка уникальности логина
        elif (not is_login_unique(login)):
            st.error("Пользователь с таким логином уже существует.")

        elif login == "admin":
            st.error("Извините, но регистрация с таким логином невозможна!")

        elif password_not_valid:
            st.error(password_not_valid)
            return

        elif role == "Менеджер" and password_staff != "staff":
            st.error("Неправильный пароль для персонала.")

        else:
            register_user(fio, login, password, birth_date.strftime("%Y-%m-%d"), role)
            st.success("Пользователь успешно зарегистрирован!")
            st.session_state["page"] = "dashboard"
            st.session_state['login'] = login
            st.session_state['role'] = role
            st.rerun()

def window_authorization():
    st.title("Авторизация пользователей")

    login = st.text_input("Логин")
    password = st.text_input("Пароль", type="password")

    if st.button("Войти"):
        if (login == "admin" and password == "admin"):
            check_admin(login, password)
        else:
            login_user(login, password)

# Функция для отображения доступных компьютеров и выбора одного
def book_computer():
    """Функция для бронирования компьютера."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Получаем логин текущего пользователя
        client_login = st.session_state["login"]

        # Получаем ID клиента
        cursor.execute("SELECT id FROM Клиент WHERE Логин = %s", (client_login,))
        client_id = cursor.fetchone()

        if not client_id:
            st.error("Ошибка: Пользователь не найден.")
            return

        client_id = client_id[0]  # Извлекаем ID из результата запроса

        # Пользователь выбирает дату и интервал времени
        st.subheader("Выберите дату и время для бронирования")
        selected_date = st.date_input("Дата бронирования")
        start_time = st.time_input("Время начала брони")
        end_time = st.time_input("Время окончания брони")

        if st.button("Назад", key="back_booking"):
            reset_booking_session()
            st.rerun()

        if start_time >= end_time:
            st.warning("Время окончания должно быть позже времени начала.")
            return

       
        # Генерация ключа для кэша
        cache_key = f"available_computers:{selected_date}:{start_time}-{end_time}"
        available_computers = get_cached_available_computers(cache_key)

        if not available_computers:
            # Запрос только при отсутствии кэша
            cursor.execute(
                """
                SELECT id, Сборка
                FROM Компьютер
                WHERE id NOT IN (
                    SELECT id_компьютера
                    FROM Бронь
                    WHERE Дата = %s AND (
                        (Время_начала < %s AND Время_окончания > %s) OR
                        (Время_начала < %s AND Время_окончания >= %s) OR
                        (Время_начала >= %s AND Время_окончания <= %s)
                    )
                ) AND id NOT IN (
                    SELECT id_компьютера
                    FROM Компьютер_Буткемп
                    WHERE id_буткемпа IN (
                        SELECT id
                        FROM Буткемп
                        WHERE Дата = %s AND (
                            (Время_начала < %s AND Время_окончания > %s) OR
                            (Время_начала < %s AND Время_окончания >= %s) OR
                            (Время_начала >= %s AND Время_окончания <= %s)
                        )
                    )
                )
                """,
                (selected_date, start_time, start_time, end_time, end_time,
                 start_time, end_time, selected_date, start_time, start_time,
                 end_time, end_time, start_time, end_time)
            )
            available_computers = cursor.fetchall()
            cache_available_computers(cache_key, available_computers)  # Сохраняем в Redis

        if not available_computers:
            st.write("Нет доступных компьютеров для выбранного времени.")
            return

        # Преобразуем данные для выпадающего списка
        computer_options = {f"Компьютер №{comp[0]}, Сборка: {comp[1]}": comp[0] for comp in available_computers}

        selected_computer = st.selectbox(
            "Выберите доступный компьютер:", options=list(computer_options.keys())
        )

        if st.button("Подтвердить бронь"):
            computer_id = computer_options[selected_computer]

            # Записываем бронь в базу данных
            cursor.execute(
                """
                INSERT INTO Бронь (id_клиента, id_компьютера, Дата, Время_начала, Время_окончания, Продление)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (client_id, computer_id, selected_date, start_time, end_time, False)
            )
            conn.commit()

            cursor.execute("SELECT id FROM Бронь WHERE id_клиента = %s ORDER BY id DESC LIMIT 1", (client_id,))
            booking_id = cursor.fetchone()[0]
            update_order_status(booking_id, "создана")

            st.success(
                f"Компьютер №{selected_computer} успешно забронирован на {selected_date} с {start_time} до {end_time}.")
            publish_event("events", f"{client_login} забронировал компьютер №{computer_id} на {selected_date}")
            reset_booking_session()

    except Exception as e:
        st.error(f"Ошибка при бронировании компьютера: {e}")
    finally:
        cursor.close()
        conn.close()

def register_in_bootcamp():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Получаем логин текущего пользователя из сессии
        client_login = st.session_state["login"]

        # Получаем ID клиента по логину
        cursor.execute("SELECT id FROM Клиент WHERE Логин = %s", (client_login,))
        client_id = cursor.fetchone()

        if not client_id:
            st.error("Ошибка: Пользователь не найден.")
            return

        client_id = client_id[0]  # Извлекаем ID из результата запроса

        # Получаем список доступных буткемпов
        bootcamps = get_cached_bootcamps()
        if not bootcamps:
            cursor.execute("SELECT * FROM Буткемп WHERE Количество_человек < 5")
            bootcamps = cursor.fetchall()
            cache_bootcamps(bootcamps)

        if not bootcamps:
            st.write("На данный момент нет доступных буткемпов.")
            return

        # Преобразуем данные для выпадающего списка
        bootcamp_options = {
            f"Название: {bootcamp[1]}, Дата проведения: {bootcamp[3]}, Время начала: {bootcamp[4]}, Время окончания: {bootcamp[5]}": bootcamp[0]
            for bootcamp in bootcamps
        }

        # Устанавливаем значение по умолчанию для выбранного буткемпа в session_state
        if "selected_bootcamp" not in st.session_state:
            st.session_state["selected_bootcamp"] = "-"

        # Выбор буткемпа без обновления сессии
        selected_bootcamp = st.selectbox(
            "Выберите буткемп для регистрации:",
            options=list(bootcamp_options.keys()),
            key="selectbox_bootcamp"
        )

        # Обновляем состояние выбранного буткемпа
        st.session_state["selected_bootcamp"] = selected_bootcamp

        if st.session_state["selected_bootcamp"] == "-":
            st.write("Выберите буткемп для регистрации.")
            return

        # Кнопка для выхода из режима просмотра
        if st.button("Назад", key="back_bootcamp"):
            reset_bootcamp_registration()
            st.rerun()

        # Кнопка для подтверждения регистрации
        if st.button("Подтвердить регистрацию в буткемпе"):
            bootcamp_id = bootcamp_options[st.session_state["selected_bootcamp"]]

            # Проверяем, не зарегистрирован ли клиент уже в одном буткемпе
            cursor.execute(
                "SELECT * FROM Клиент_Буткемп WHERE id_клиента = %s and id_буткемпа = %s",
                (client_id, bootcamp_id)
            )
            existing_registration = cursor.fetchone()

            if existing_registration:
                st.warning("Вы уже зарегистрированы в этом буткемпе.")
                reset_bootcamp_registration()
                return

            # Добавляем запись о регистрации клиента в буткемпе
            cursor.execute(
                """
                INSERT INTO Клиент_Буткемп (id_клиента, id_буткемпа)
                VALUES (%s, %s)
                """,
                (client_id, bootcamp_id)
            )

            conn.commit()

            cursor.execute("SELECT id FROM Клиент_Буткемп WHERE id_клиента = %s AND id_буткемпа = %s ORDER BY id DESC LIMIT 1", (client_id, bootcamp_id))
            result = cursor.fetchone()
            if result:
                bootcamp_client_id = result[0]
                update_order_status(bootcamp_client_id, "зарегистрирован в буткемпе")

            st.success("Вы успешно зарегистрировались в выбранном буткемпе!")
            publish_event("events", f"{client_login} зарегистрировался в буткемпе ID {bootcamp_id}")

            # Очистка состояния после успешной регистрации
            reset_bootcamp_registration()

    except Exception as e:
        st.error(f"Ошибка при регистрации в буткемпе: {e}")
    finally:
        cursor.close()
        conn.close()


def watch_books_bootcamps():
    """Просмотр броней и буткемпов для текущего пользователя."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Получаем логин текущего пользователя из сессии
        client_login = st.session_state["login"]

        # Получаем ID клиента
        cursor.execute("SELECT id FROM Клиент WHERE Логин = %s", (client_login,))
        client_id = cursor.fetchone()

        client_id = client_id[0]  # Извлекаем ID из результата запроса

        # Получаем информацию о бронях клиента
        cursor.execute(
            """
            SELECT Компьютер.id, Компьютер.Сборка, Бронь.Дата, Бронь.Время_начала, Бронь.Время_окончания 
            FROM Бронь
            JOIN Компьютер ON Бронь.id_компьютера = Компьютер.id
            WHERE Бронь.id_клиента = %s
            """,
            (client_id,)
        )
        bookings = cursor.fetchall()

        # Получаем информацию о буткемпах клиента
        cursor.execute(
            """
            SELECT Буткемп.Название, Буткемп.Дата, Буткемп.Время_начала, Буткемп.Время_окончания
            FROM Клиент_Буткемп
            JOIN Буткемп ON Клиент_Буткемп.id_буткемпа = Буткемп.id
            WHERE Клиент_Буткемп.id_клиента = %s
            """,
            (client_id,)
        )
        bootcamps = cursor.fetchall()

        # Отображение информации
        st.subheader("Ваши брони")
        if bookings:
            for booking in bookings:
                st.write(f"Компьютер №{booking[0]}, Сборка: {booking[1]}, Дата брони: {booking[2]}, Время начала: {booking[3]}, Время окончания: {booking[4]}")
        else:
            st.write("У вас нет активных броней.")

        st.subheader("Ваши буткемпы")
        if bootcamps:
            for bootcamp in bootcamps:
                st.write(f"Буткемп: {bootcamp[0]}, Дата проведения: {bootcamp[1]}, Время начала: {bootcamp[2]}, Время окончания: {bootcamp[3]}")
        else:
            st.write("Вы не зарегистрированы в буткемпах.")
        
        # Кнопка для выхода из режима просмотра
        if st.button("Назад", key="back_watch"):
            reset_watch_books_bootcamps()
            st.rerun()

    except Exception as e:
        st.error(f"Ошибка при просмотре данных: {e}")
    finally:
        cursor.close()
        conn.close()



def reset_booking_session():
    st.session_state["booking_active"] = False

def reset_bootcamp_registration():
    st.session_state["bootcamp_registration_active"] = False
    st.session_state.pop("selected_bootcamp", None)

def reset_watch_books_bootcamps():
    st.session_state["watch_books_bootcamps_active"] = False

# Основной интерфейс игрока
def player_dashboard():
    st.sidebar.title(f"Ваш логин: {st.session_state['login']}")
    st.sidebar.title(f"Ваша роль: {st.session_state['role']}")
    if st.sidebar.button("Выйти из аккаунта"):
        logout_user()

    st.title("Ваши действия")

    # Проверяем, активен ли режим бронирования
    if "booking_active" not in st.session_state:
        st.session_state["booking_active"] = False

    if "bootcamp_registration_active" not in st.session_state:
        st.session_state["bootcamp_registration_active"] = False

    if "watch_books_bootcamps_active" not in st.session_state:
        st.session_state["watch_books_bootcamps_active"] = False

    if st.button("Забронировать компьютер", key="activate_booking"):
        st.session_state["booking_active"] = True

    # Если активен режим бронирования — рендерим бронирование
    if st.session_state["booking_active"]:
        book_computer()

    if st.button("Зарегистрироваться в буткемпе", key="activate_bootcamp"):
        st.session_state["bootcamp_registration_active"] = True

        # Если активен режим регистрации в буткемпе — рендерим регистрацию
    if st.session_state["bootcamp_registration_active"]:
        register_in_bootcamp()

    #Если активен режим просмотра брони и буткемпов - рендерим просмотр
    if st.button("Мои брони и буткемпы", key="activate_watch_books_bootcamps"):
        st.session_state["watch_books_bootcamps_active"] = True

    if st.session_state["watch_books_bootcamps_active"]:
        watch_books_bootcamps()




def create_bootcamp():
    """Функция для создания буткемпа и бронирования компьютеров."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Ввод данных о буткемпе
        st.subheader("Создание нового буткемпа")
        bootcamp_name = st.text_input("Название буткемпа")
        date = st.date_input("Дата начала буткемпа")
        start_time = st.time_input("Время начала буткемпа")
        end_time = st.time_input("Время окончания буткемпа")

        if st.button("Назад", key="back_bootcamp_create"):
            reset_bootcamp_creating()
            st.rerun()

        if not bootcamp_name or start_time >= end_time:
            st.warning("Пожалуйста, введите корректные данные для буткемпа.")
            return

        # Поиск доступных компьютеров
        cursor.execute(
            """
            SELECT id, Сборка
            FROM Компьютер
            WHERE id NOT IN (
                SELECT id_компьютера
                FROM Бронь
                WHERE Дата = %s AND (
                    (Время_начала < %s AND Время_окончания > %s) OR
                    (Время_начала < %s AND Время_окончания >= %s) OR
                    (Время_начала >= %s AND Время_окончания <= %s)
                )
            ) AND id NOT IN (
                SELECT id_компьютера
                FROM Компьютер_Буткемп
                WHERE id_буткемпа IN (
                    SELECT id
                    FROM Буткемп
                    WHERE (
                        (Время_начала < %s AND Время_окончания > %s) OR
                        (Время_начала < %s AND Время_окончания >= %s) OR
                        (Время_начала >= %s AND Время_окончания <= %s)
                    )
                )
            )
            """,
            (date, start_time, start_time, end_time, end_time, start_time, end_time, start_time, start_time, end_time, end_time, start_time, end_time)
        )
        available_computers = cursor.fetchall()

        if len(available_computers) < 5:
            st.error("Недостаточно доступных компьютеров для создания буткемпа.")
            reset_bootcamp_creating()
            return

        # Выбираем первые 5 доступных компьютеров
        selected_computers = available_computers[:5]

        if st.button("Подтвердить создание буткемпа"):
            # Создаем буткемп в таблице
            cursor.execute(
                """
                INSERT INTO Буткемп (Название, Количество_человек, Дата, Время_начала, Время_окончания, Продление)
                VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
                """,
                (bootcamp_name, 0, date, start_time, end_time, False)
            )
            bootcamp = cursor.fetchall()
            bootcamp_id = bootcamp[0]

            # Бронируем компьютеры для буткемпа
            for computer in selected_computers:
                cursor.execute(
                    """
                    INSERT INTO Компьютер_Буткемп (id_компьютера, id_буткемпа)
                    VALUES (%s, %s)
                    """,
                    (computer[0], bootcamp_id)
                )

            conn.commit()
            st.success(f"Буткемп '{bootcamp_name}' успешно создан! Забронированные компьютеры с номерами: {[comp[0] for comp in selected_computers]}")
            reset_bootcamp_creating()

    except Exception as e:
        st.error(f"Ошибка при создании буткемпа: {e}")
    finally:
        cursor.close()
        conn.close()


def edit_booking_or_bootcamp():
    """Редактирование времени окончания и даты брони или буткемпа."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        st.subheader("Редактирование брони или буткемпа")

        # Получаем список броней
        cursor.execute(
            """
            SELECT * FROM Бронь
            """
        )
        bookings = cursor.fetchall()

        # Получаем список буткемпов
        cursor.execute(
            """
            SELECT * from Буткемп
            """
        )
        bootcamps = cursor.fetchall()

        # Выбор объекта для редактирования
        options = ["-"] + [
            f"Бронь: Компьютер №{b[2]}, Дата: {b[3]}, Начало: {b[4]}, Окончание: {b[5]}" for b in bookings
        ] + [
            f"Буткемп: {bc[1]}, Дата: {bc[3]}, Начало: {bc[4]}, Конец: {bc[5]}" for bc in bootcamps
        ]
        selected_option = st.selectbox("Выберите бронь или буткемп для редактирования:", options)

        if selected_option == "-":
            st.write("Выберите объект для редактирования.")
            return

        # Обработка выбора
        is_booking = "Бронь" in selected_option
        obj_id = (
            bookings[options.index(selected_option) - 1][0]
            if is_booking
            else bootcamps[options.index(selected_option) - len(bookings) - 1][0]
        )

        # Получение новых данных
        new_date = st.date_input("Новая дата")
        new_start_time = st.time_input("Новое время начала")
        new_end_time = st.time_input("Новое время окончания")

        if st.button("Назад", key="back_bootcamps_books_editing"):
            reset_books_bootcamps_editing()
            st.rerun()

        # Проверка на корректность ввода
        if not new_date or new_start_time > new_end_time:
            st.warning("Введите корректные данные для изменения.")
            return

        if is_booking:
            # Проверка доступности для брони
            if st.button("Подтвердить изменения", key="change_booking"):
                cursor.execute(
                    """
                    WITH available_computers AS 
                    (SELECT id, Сборка
                    FROM Компьютер
                    WHERE id NOT IN (
                        SELECT id_компьютера
                        FROM Бронь
                        WHERE Дата = %s AND (
                            (Время_начала < %s AND Время_окончания > %s) OR
                            (Время_начала < %s AND Время_окончания >= %s) OR
                            (Время_начала >= %s AND Время_окончания <= %s)
                        )
                    ) AND id NOT IN (
                        SELECT id_компьютера
                        FROM Компьютер_Буткемп
                        WHERE id_буткемпа IN (
                            SELECT id
                            FROM Буткемп
                            WHERE Дата = %s AND (
                                (Время_начала < %s AND Время_окончания > %s) OR
                                (Время_начала < %s AND Время_окончания >= %s) OR
                                (Время_начала >= %s AND Время_окончания <= %s)
                            )
                        )
                    ))
                    
                    SELECT id FROM available_computers WHERE id in (SELECT id_компьютера from Бронь WHERE id = %s)
                    """,
                    (new_date, new_start_time, new_start_time, new_end_time, new_end_time, new_start_time, new_end_time, new_date, new_start_time, new_start_time, new_end_time, new_end_time, new_start_time, new_end_time, obj_id)
                )
                available_time = cursor.fetchall()

                if not available_time:
                    st.error("На выбранном временном промежутке и дате уже существует бронь для этого компьютера")
                    reset_books_bootcamps_editing()
                    return

                # Обновление данных брони
                cursor.execute(
                    """
                    UPDATE Бронь
                    SET Дата = %s, Время_начала = %s, Время_окончания = %s, Продление = True
                    WHERE id = %s
                    """,
                    (new_date, new_start_time, new_end_time, obj_id)
                )
                conn.commit()
                st.success("Бронь успешно обновлена.")
                reset_books_bootcamps_editing()
        else:
            if st.button("Подтвердить изменения", key="change_bootcamp"):
                # Проверка доступности для буткемпа
                cursor.execute(
                    """
                    WITH available_computers AS 
                    (SELECT id, Сборка
                    FROM Компьютер
                    WHERE id NOT IN (
                        SELECT id_компьютера
                        FROM Бронь
                        WHERE Дата = %s AND (
                            (Время_начала < %s AND Время_окончания > %s) OR
                            (Время_начала < %s AND Время_окончания >= %s) OR
                            (Время_начала >= %s AND Время_окончания <= %s)
                        )
                    ) AND id NOT IN (
                        SELECT id_компьютера
                        FROM Компьютер_Буткемп
                        WHERE id_буткемпа IN (
                            SELECT id
                            FROM Буткемп
                            WHERE Дата = %s AND (
                                (Время_начала < %s AND Время_окончания > %s) OR
                                (Время_начала < %s AND Время_окончания >= %s) OR
                                (Время_начала >= %s AND Время_окончания <= %s)
                            )
                        )
                    ))

                    SELECT id FROM available_computers WHERE id in (SELECT id_компьютера from Компьютер_Буткемп WHERE id_буткемпа = %s)
                    """,
                    (new_date, new_start_time, new_start_time, new_end_time, new_end_time, new_start_time, new_end_time, new_date,
                     new_start_time, new_start_time, new_end_time, new_end_time, new_start_time, new_end_time, obj_id)
                )

                available_time = cursor.fetchall()
                if (len(available_time) < 5):
                    st.error("На выбранное время и дату уже существует бронирование.")
                    reset_books_bootcamps_editing()
                    return

                # Обновление данных буткемпа
                cursor.execute(
                    """
                    UPDATE Буткемп
                    SET Дата = %s, Время_начала = %s, Время_окончания = %s, Продление = True
                    WHERE id = %s
                    """,
                    (new_date, new_start_time, new_end_time, obj_id)
                )
                conn.commit()
                st.success("Буткемп успешно обновлен.")
                reset_books_bootcamps_editing()
    except Exception as e:
        st.error(f"Ошибка при редактировании: {e}")
    finally:
        cursor.close()
        conn.close()

def reset_bootcamp_creating():
    st.session_state["bootcamp_creating_active"] = False

def reset_books_bootcamps_editing():
    st.session_state["bootcamp_books_editing_active"] = False

# Навигация для менеджера
def manager_dashboard():
    st.sidebar.title(f"Ваш логин: {st.session_state['login']}")
    st.sidebar.title(f"Ваша роль: {st.session_state['role']}")
    if st.sidebar.button("Выйти из аккаунта"):
        logout_user()

    st.title("Ваши действия")

    # Проверяем, активен ли режим создания буткемпа
    if "bootcamp_creating_active" not in st.session_state:
        st.session_state["bootcamp_creating_active"] = False

    if "bootcamp_books_editing_active" not in st.session_state:
        st.session_state["bootcamp_books_editing_active"] = False

    if (st.button("Создать буткемп", key="create_bootcamp")):
        st.session_state["bootcamp_creating_active"] = True

    if (st.button("Редактировать бронь/буткемп", key="edit_books_bootcamps")):
        st.session_state["bootcamp_books_editing_active"] = True

    if st.session_state["bootcamp_creating_active"]:
        create_bootcamp()

    if st.session_state["bootcamp_books_editing_active"]:
        edit_booking_or_bootcamp()




# Функция для удаления записи из таблицы
def delete_record(table_name, record_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        delete_query = f"DELETE FROM {table_name} WHERE id = %s"
        check_query = f"SELECT id FROM {table_name} WHERE id = %s"

        cursor.execute(check_query, (record_id,))
        checked_id = cursor.fetchall()

        if not checked_id:
            st.error("Записи с таким айди не существует.")
            return

        cursor.execute(delete_query, (record_id,))
        conn.commit()
        st.success(f"Запись с ID {record_id} удалена из таблицы {table_name}")
    except Exception as e:
        st.error(f"Ошибка при удалении записи: {e}")
    finally:
        cursor.close()
        conn.close()

# Функция для редактирования таблицы
def edit_table(table_name):
    tables_with_delete_permission = ["Компьютер", "Бронь", "Клиент", "Буткемп"]

    st.subheader(f"Таблица: {table_name}")

    # Отображение данных
    conn = get_connection()
    cursor = conn.cursor()
    try:
        data_query = f"SELECT * FROM {table_name}"
        cursor.execute(data_query)
        data = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]

        if data:
            df = pd.DataFrame(data, columns=columns)
            st.dataframe(df, use_container_width=True)

            # Удаление записи
            if table_name in tables_with_delete_permission:
                with st.expander("Удалить запись"):
                    record_id = st.number_input("Введите ID записи для удаления", min_value=1, step=1)
                    if st.button("Удалить запись"):
                        delete_record(table_name, record_id)
        else:
            st.warning(f"Таблица {table_name} пуста или не существует.")
    except Exception as e:
        st.error(f"Ошибка при загрузке данных: {e}")
    finally:
        cursor.close()
        conn.close()

# Страница администратора
def admin_dashboard():
    st.title("Панель администратора")
    st.write("Управляйте всеми данными из одной панели.")

    # Выбор таблицы
    tables = [
        "Клиент", "Роль", "Компьютер", "Бронь", "Буткемп", "Клиент_Роль", "Клиент_Буткемп", "Компьютер_Буткемп"
    ]
    selected_table = st.selectbox("Выберите таблицу для управления", tables)

    if selected_table:
        edit_table(selected_table)

    if st.button("Выйти из аккаунта"):
        logout_user()


# Основное приложение
def main():
    if "page" not in st.session_state:
        st.session_state["page"] = "login"  # По умолчанию авторизация

    if st.session_state["page"] == "dashboard":
        if "role" in st.session_state:
            if st.session_state["role"] == "Администратор":
                admin_dashboard()
            elif st.session_state["role"] == "Игрок":
                player_dashboard()
            elif st.session_state["role"] == "Менеджер":
                manager_dashboard()
        else:
            st.error("Ошибка: роль пользователя не определена.")
    else:
        st.title("Навигация")
        page = st.selectbox("Перейти к странице", ["Авторизация", "Регистрация"])
        if page == "Регистрация":
            window_register()
        elif page == "Авторизация":
            window_authorization()

if __name__ == "__main__":
    main()