import requests
import logging
from auth import load_tokens

# Настройка логов
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def clean_robots():
    tokens = load_tokens()
    if not tokens:
        print("Нет токенов. Сначала установи приложение.")
        return

    domain = tokens["domain"]
    access_token = tokens["access_token"]

    # 1. Получаем список всех роботов этого приложения
    url_list = f"https://{domain}/rest/bizproc.robot.list.json?auth={access_token}"
    response = requests.get(url_list)

    if response.status_code != 200:
        print(f"Ошибка получения списка: {response.text}")
        return

    # Получаем результат
    result_data = response.json().get("result", [])

    # Если пришел пустой список или null
    if not result_data:
        print("Роботов не найдено (список пуст).")
        return

    # Превращаем результат в список, если это словарь (иногда Битрикс возвращает словарь)
    if isinstance(result_data, dict):
        robots_list = list(result_data.values())  # Пробуем взять значения
        # Если значения - это не словари с кодом, а что-то другое,
        # то возможно ключи являются кодами. Но для надежности соберем всё в список.
        # Для простоты: если это dict, скорее всего ключи нам не важны, важны объекты внутри.
        # НО! Судя по твоей ошибке, там могут быть просто строки.

        # ДАВАЙ СДЕЛАЕМ УНИВЕРСАЛЬНО:
        robots_iterator = result_data if isinstance(result_data, list) else result_data.values()
    else:
        robots_iterator = result_data

    print(f"Найдено объектов: {len(result_data)}")

    # 2. Удаляем каждого найденного робота
    url_delete = f"https://{domain}/rest/bizproc.robot.delete.json?auth={access_token}"

    for item in robots_iterator:
        # ЛОГИКА ИСПРАВЛЕНИЯ ОШИБКИ:
        # Проверяем, является ли элемент строкой или словарем
        if isinstance(item, str):
            code = item  # Если это строка, значит это и есть КОД
            name = "Unknown (Code only)"
        elif isinstance(item, dict):
            code = item.get("CODE")  # Если словарь, берем поле CODE
            name = item.get("NAME", "Без имени")
        else:
            print(f"Непонятный формат данных: {item}")
            continue

        if code:
            print(f"Удаляю робота: {name} (код: {code})...")
            del_resp = requests.post(url_delete, json={"CODE": code})
            # print(del_resp.json()) # раскомментируй, если интересно, что ответил сервер

    print("--- Чистка завершена ---")


if __name__ == "__main__":
    clean_robots()