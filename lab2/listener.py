import redis
import os

try:
    r = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        decode_responses=True
    )

    # Проверка соединения с Redis
    r.ping()
    print("Подключение к Redis успешно")

    pubsub = r.pubsub()
    pubsub.subscribe("events")
    print("Подписчик Redis активен. Ждём события...")

    for message in pubsub.listen():
        if message["type"] == "message":
            print(f"[СОБЫТИЕ] {message['data']}")

except Exception as e:
    print(f"❌ Ошибка в слушателе: {e}")


# docker exec -it comp_club_listener /bin/sh
# pip listener.py