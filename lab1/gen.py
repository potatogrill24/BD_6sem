import csv
import random
from faker import Faker
from datetime import datetime, timedelta
from pathlib import Path

fake = Faker()
OUTPUT_DIR = Path("data")
OUTPUT_DIR.mkdir(exist_ok=True)

NUM_USERS = 5000000
NUM_ORDERS = 10000000
NUM_ORDER_ITEMS = 5000000
NUM_REVIEWS = 5000000

NUM_CATEGORIES = 8
NUM_MANUFACTURERS = 50
NUM_PRODUCTS = 5000

CATEGORY_NAMES = ["Notebooks", "Monitors", "Keyboards", "Mouses", "Printers", "Processors", "Motherboards", "Videocards"]
PAYMENT_METHODS = ["card", "cash", "online"]


def save_csv(filename, header, rows):
    with open(OUTPUT_DIR / filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


def generate_categories():
    rows = [[i + 1, name] for i, name in enumerate(CATEGORY_NAMES)]
    save_csv("categories.csv", ["category_id", "name"], rows)
    return rows


def generate_manufacturers(n):
    prefixes = [
        "Cyber", "Neo", "Techno", "Quantum", "Alpha", "Omega", "Core", "Nexus", "Hyper", "Vertex",
        "Nova", "Pixel", "Fusion", "Vortex", "Titan", "Nano", "Iron", "Turbo", "Astro", "Xeno"
    ]
    suffixes = [
        "Tech", "Systems", "Labs", "Works", "Solutions", "Devices", "Electronics", "Industries", "Informatics", "Dynamics"
    ]

    generated_names = set()
    rows = []

    while len(rows) < n:
        name = f"{random.choice(prefixes)} {random.choice(suffixes)}"
        if name not in generated_names:
            generated_names.add(name)
            rows.append([len(rows) + 1, name])

    save_csv("manufacturers.csv", ["manufacturer_id", "name"], rows)
    return rows


def generate_products(n, categories, manufacturers):
    product_types = {
        "Notebooks": ["Lenovo ThinkPad", "HP Pavilion", "Dell XPS", "MacBook Air", "Asus ROG"],
        "Monitors": ["Samsung 27\"", "LG UltraGear", "BenQ DesignVue", "ASUS ProArt", "Acer Predator"],
        "Keyboards": ["Logitech MX Keys", "Razer BlackWidow", "Corsair K95", "SteelSeries Apex", "HyperX Alloy"],
        "Mouses": ["Logitech G502", "Razer DeathAdder", "SteelSeries Rival", "Corsair Harpoon", "HP X3000"],
        "Printers": ["HP LaserJet", "Canon PIXMA", "Epson EcoTank", "Brother HL", "Xerox Phaser"],
        "Processors": ["Intel Core i9", "AMD Ryzen 7", "Intel Core i5", "AMD Ryzen 9", "Intel Pentium"],
        "Motherboards": ["ASUS TUF", "MSI MAG", "Gigabyte Aorus", "ASRock Phantom", "Biostar Racing"],
        "Videocards": ["NVIDIA RTX 4080", "AMD Radeon RX 7900", "NVIDIA GTX 1660", "AMD RX 6700", "Intel Arc A770"]
    }

    rows = []
    for i in range(1, n + 1):
        category = random.choice(categories)
        category_name = category[1]
        name = random.choice(product_types.get(category_name, ["Generic Component"]))
        category_id = category[0]
        manufacturer_id = random.choice(manufacturers)[0]
        price = round(random.uniform(100, 100000), 2)
        rows.append([i, name, category_id, manufacturer_id, price])

    save_csv("products.csv", ["product_id", "name", "category_id", "manufacturer_id", "price"], rows)
    return rows


def generate_users(n):
    rows = []
    for i in range(1, n + 1):
        registration_date = fake.date_between(start_date="-5y", end_date="today")
        is_active = random.choice([True, True, True, False])
        rows.append([i, fake.first_name(), fake.last_name(), fake.email(), fake.city(), registration_date, is_active])
    save_csv("users.csv", ["user_id", "first_name", "last_name", "email", "city", "registration_date", "is_active"], rows)
    return rows


def generate_orders(n, users):
    rows = []
    for i in range(1, n + 1):
        user_id = random.choice(users)[0]
        order_date = fake.date_between(start_date="-2y", end_date="today")
        payment = random.choice(PAYMENT_METHODS)
        total_amount = round(random.uniform(100, 5000), 2)
        rows.append([i, user_id, order_date, payment, total_amount])
    save_csv("orders.csv", ["order_id", "user_id", "order_date", "payment_method", "total_amount"], rows)
    return rows


def generate_order_items(n, orders, products):
    rows = []
    for i in range(1, n + 1):
        order_id = random.choice(orders)[0]
        product_id = random.choice(products)[0]
        quantity = random.randint(1, 5)
        unit_price = round(random.uniform(100, 3000), 2)
        subtotal = round(quantity * unit_price, 2)
        rows.append([i, order_id, product_id, quantity, unit_price, subtotal])
    save_csv("order_items.csv", ["item_id", "order_id", "product_id", "quantity", "unit_price", "subtotal"], rows)
    return rows


def generate_reviews(n, users, products):
    rows = []
    for i in range(1, n + 1):
        user_id = random.choice(users)[0]
        product_id = random.choice(products)[0]
        rating = random.randint(1, 5)
        title = fake.sentence(nb_words=4)
        comment = fake.paragraph(nb_sentences=2)
        date = fake.date_between(start_date="-2y", end_date="today")
        rows.append([i, user_id, product_id, rating, title, comment, date])
    save_csv("reviews.csv", ["review_id", "user_id", "product_id", "rating", "title", "comment", "date"], rows)
    return rows


if __name__ == "__main__":
    print("Генерация справочников...")
    categories = generate_categories()
    manufacturers = generate_manufacturers(NUM_MANUFACTURERS)
    products = generate_products(NUM_PRODUCTS, categories, manufacturers)

    print("Генерация пользователей и транзакций...")
    users = generate_users(NUM_USERS)
    orders = generate_orders(NUM_ORDERS, users)
    order_items = generate_order_items(NUM_ORDER_ITEMS, orders, products)
    reviews = generate_reviews(NUM_REVIEWS, users, products)

    print("Генерация завершена. Файлы сохранены в папке 'data'.")
