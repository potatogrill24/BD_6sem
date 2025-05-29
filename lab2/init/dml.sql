INSERT INTO Роль (Название)
VALUES ('Игрок'),
('Менеджер');

INSERT INTO Компьютер (Сборка, Видеокарта, Процессор, Материнская_плата, Блок_питания)
VALUES ('Standart', 'RTX 4060 super', 'i5-12400f', 'ASUS TUF GAMING B760M-plus', 'Cougar GEX850'),
('Standart', 'RTX 4060 super', 'i5-12400f', 'ASUS TUF GAMING B760M-plus', 'Cougar GEX850'),
('Standart', 'RTX 4060 super', 'i5-12400f', 'ASUS TUF GAMING B760M-plus', 'Cougar GEX850'),
('Standart', 'RTX 4060 super', 'i5-12400f', 'ASUS TUF GAMING B760M-plus', 'Cougar GEX850'),
('Standart', 'RTX 4060 super', 'i5-12400f', 'ASUS TUF GAMING B760M-plus', 'Cougar GEX850'),
('VIP', 'RTX 4080', 'i5-13600fk', 'MSI B760 GAMING PLUS WIFI', 'Chieftec Chieftonic PowerUp 850w'),
('VIP', 'RTX 4080', 'i5-13600fk', 'MSI B760 GAMING PLUS WIFI', 'Chieftec Chieftonic PowerUp 850w'),
('VIP', 'RTX 4080', 'i5-13600fk', 'MSI B760 GAMING PLUS WIFI', 'Chieftec Chieftonic PowerUp 850w'),
('VIP', 'RTX 4080', 'i5-13600fk', 'MSI B760 GAMING PLUS WIFI', 'Chieftec Chieftonic PowerUp 850w'),
('VIP', 'RTX 4080', 'i5-13600fk', 'MSI B760 GAMING PLUS WIFI', 'Chieftec Chieftonic PowerUp 850w'),
('Ultimate', 'RTX 4090', 'i9-13900k', 'MSI PRO Z790-A MAX WIFI', 'Deepcool 1000w PX1000g'),
('Ultimate', 'RTX 4090', 'i9-13900k', 'MSI PRO Z790-A MAX WIFI', 'Deepcool 1000w PX1000g'),
('Ultimate', 'RTX 4090', 'i9-13900k', 'MSI PRO Z790-A MAX WIFI', 'Deepcool 1000w PX1000g'),
('Ultimate', 'RTX 4090', 'i9-13900k', 'MSI PRO Z790-A MAX WIFI', 'Deepcool 1000w PX1000g'),
('Ultimate', 'RTX 4090', 'i9-13900k', 'MSI PRO Z790-A MAX WIFI', 'Deepcool 1000w PX1000g');


-- Создание триггерной функции для обновления количества участников буткемпа
CREATE OR REPLACE FUNCTION update_bootcamp_players()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE Буткемп
    SET Количество_человек = Количество_человек + 1
    WHERE id = NEW.id_буткемпа;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Создание триггера, который срабатывает после вставки в таблицу Буткемп_клиент
CREATE TRIGGER set_computer_booked
AFTER INSERT ON Клиент_Буткемп
FOR EACH ROW
EXECUTE FUNCTION update_bootcamp_players();



-- Создание триггерной функции для обновления количества участников буткемпа
CREATE OR REPLACE FUNCTION update_bootcamp_players_delete()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE Буткемп
    SET Количество_человек = Количество_человек - 1
    WHERE id = OLD.id_буткемпа;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

-- Создание триггера, который срабатывает после удаления из таблицы Буткемп_клиент
CREATE TRIGGER set_client_deleted
AFTER DELETE ON Клиент_Буткемп
FOR EACH ROW
EXECUTE FUNCTION update_bootcamp_players_delete()
