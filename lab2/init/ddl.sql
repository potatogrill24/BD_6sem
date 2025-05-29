CREATE TABLE Клиент (
    id BIGSERIAL PRIMARY KEY,
    ФИО CHAR(100),
    Совершеннолетие BOOLEAN,
    Логин VARCHAR(50) UNIQUE NOT NULL,
    Пароль VARCHAR(255) NOT NULL,
    Хешированный_пароль VARCHAR(255) NOT NULL
);

CREATE TABLE Роль (
    id BIGSERIAL PRIMARY KEY,
    Название VARCHAR(50) NOT NULL
);

CREATE TABLE Компьютер (
    id BIGSERIAL PRIMARY KEY,
    Сборка CHAR(50),
    Видеокарта CHAR(50),
    Процессор CHAR(50),
    Материнская_плата CHAR(50),
    Блок_питания CHAR(50)
);

CREATE TABLE Бронь (
    id BIGSERIAL PRIMARY KEY,
    id_клиента BIGINT REFERENCES Клиент(id) ON DELETE CASCADE,
    id_компьютера BIGINT REFERENCES Компьютер(id) ON DELETE CASCADE,
    Дата DATE NOT NULL,
    Время_начала TIME NOT NULL,
    Время_окончания TIME NOT NULL,
    Продление BOOLEAN
);

CREATE TABLE Буткемп (
    id BIGSERIAL PRIMARY KEY,
    Название CHAR(50),
    Количество_человек INT,
    Дата DATE NOT NULL,
    Время_начала TIME NOT NULL,
    Время_окончания  TIME NOT NULL,
    Продление BOOLEAN
);

CREATE TABLE Клиент_Роль (
    id BIGSERIAL PRIMARY KEY,
    id_клиента BIGINT REFERENCES Клиент(id) ON DELETE CASCADE,
    id_роли BIGINT REFERENCES Роль(id) ON DELETE CASCADE
);

CREATE TABLE Клиент_Буткемп (
    id BIGSERIAL PRIMARY KEY,
    id_клиента BIGINT REFERENCES Клиент(id) ON DELETE CASCADE,
    id_буткемпа BIGINT REFERENCES Буткемп(id) ON DELETE CASCADE
);

CREATE TABLE Компьютер_Буткемп (
    id BIGSERIAL PRIMARY KEY,
    id_компьютера BIGINT REFERENCES Компьютер(id) ON DELETE CASCADE,
    id_буткемпа BIGINT REFERENCES Буткемп(id) ON DELETE CASCADE
);
