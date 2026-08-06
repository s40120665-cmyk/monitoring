import csv
import os
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# Пути к файлам базы данных
TARGETS_FILE = "targets.csv"
PRICES_FILE = "prices.csv"


def parse_citilink(url):
    """Парсер для магазина Ситилинк"""
    headers = {
        # Маскируемся под обычный браузер Chrome на Windows
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"Ошибка загрузки Ситилинк: {response.status_code}")
            return None, None

        soup = BeautifulSoup(response.text, "html.parser")

        # 1. Ищем название товара (в теге h1)
        title_tag = soup.find("h1")
        title = (
            title_tag.text.strip() if title_tag else "Название не найдено"
        )

        # 2. Ищем цену. В Ситилинке цена часто лежит в теге с мета-данными или специальным классом
        # Пробуем найти через JSON-LD или класс цены
        price_meta = soup.find("meta", itemprop="price")
        if price_meta:
            price_text = price_meta.get("content", "0")
        else:
            # Запасной вариант, если meta изменится
            price_tag = soup.find(
                lambda tag: tag.name == "span"
                and "price" in "".join(tag.get("class", [])).lower()
            )
            price_text = price_tag.text if price_tag else "0"

        # Очищаем цену от мусора, оставляем только цифры
        price = int(re.sub(r"\D", "", price_text))
        return title, price

    except Exception as e:
        print(f"Ошибка при парсинге Ситилинка: {e}")
        return None, None


def main():
    # Проверяем, есть ли файл со ссылками
    if not os.path.exists(TARGETS_FILE):
        print(f"Файл {TARGETS_FILE} не найден! Создайте его.")
        return

    # Получаем текущую дату в формате ГГГГ-ММ-ДД
    current_date = datetime.now().strftime("%Y-%m-%d")
    new_rows = []

    # Читаем цели для парсинга
    with open(TARGETS_FILE, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            category = row["Category"]
            store = row["Store"].lower()
            link = row["Link"]

            print(f"Парсим [{row['Store']}] из категории {category}...")

            title, price = None, None
            if "citilink" in store:
                title, price = parse_citilink(link)
            elif "dns" in store:
                # Сюда мы добавим сложный обход DNS на следующем шаге
                print("Парсер DNS в разработке, пропускаем...")
                continue

            if price and title:
                print(f"Успешно: {title} -> {price} руб.")
                new_rows.append([current_date, row["Store"], category, title, price, link])
            else:
                print(f"Не удалось получить данные по ссылке: {link}")

    # Если что-то распарсили, записываем в огромный файл prices.csv
    if new_rows:
        file_exists = os.path.exists(PRICES_FILE)
        with open(PRICES_FILE, mode="a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            # Если файл создается впервые, пишем заголовки колонок
            if not file_exists:
                writer.writerow(["Date", "Store", "Category", "Product", "Price", "Link"])
            writer.writerows(new_rows)
        print(f"Данные успешно сохранены в {PRICES_FILE}!")


if __name__ == "__main__":
    main()
