import telebot
import requests
from bs4 import BeautifulSoup
from flask import Flask
import os
import threading

# Загрузка токена
token = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(token)

# Flask-приложение
app = Flask(__name__)

# Маршрут для проверки работоспособности
@app.route('/')
def index():
    return 'Бот работает!'

# Функция получения результатов экзамена
form_url = "https://profiuniversity.uz/ru/result/form"
submit_url = "https://profiuniversity.uz/ru/result/get"

def get_exam_result(key):
    session = requests.Session()

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "text/html,application/xhtml+xml",
        "Referer": form_url,
    }

    response = session.get(form_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    token_input = soup.find("input", {"name": "_token"})
    if not token_input:
        return "Ошибка: не удалось найти CSRF токен."

    csrf_token = token_input.get("value")

    data = {
        "_token": csrf_token,
        "key": key
    }

    submit_response = session.post(submit_url, headers=headers, data=data)
    result_soup = BeautifulSoup(submit_response.text, "html.parser")

    # Извлекаем таблицу
    rows = result_soup.select("table tr")
    if not rows:
        return "Результаты не найдены. Возможно, ID неверный."

    data = {}
    for row in rows:
        th = row.find("th")
        td = row.find("td")
        if th and td:
            data[th.text.strip()] = td.text.strip()

    return f"""📄 *Результат экзамена:*
👤 ФИО: {data.get("ФИО", "–")}
🆔 ID: {data.get("ID", "–")}
🏫 Факультет: {data.get("Факультет", "–")}
🎓 Тип образования: {data.get("Тип образования", "–")}
🗣 Язык обучения: {data.get("Язык обучения", "–")}
📅 Дата экзамена: {data.get("Дата и место проведения экзамена", "–")}
📍 Адрес: {data.get("Место проведения экзамена", "–")}
⏰ Время: {data.get("Время экзамена", "–")}
📘 1 - Предмет: {data.get("1 - Предмет (Тест)", "–")}
📙 2 - Предмет: {data.get("2 - Предмет (Тест)", "–")}
📊 Общий балл: {data.get("Общий балл", "–")}
🔎 Статус: {data.get("Статус", "–")}
""".strip()


# Команды Telegram-бота
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привет! Отправь мне свой ID для проверки результата экзамена.")

@bot.message_handler(func=lambda message: message.text.isdigit())
def handle_id(message):
    user_key = message.text.strip()
    bot.send_message(message.chat.id, "🔎 Проверяю результат...")
    result_text = get_exam_result(user_key)
    bot.send_message(message.chat.id, result_text, parse_mode="Markdown")

# Функция запуска бота в отдельном потоке
def run_bot():
    bot.infinity_polling()

# Запуск Flask и бота
if __name__ == '__main__':
    threading.Thread(target=run_bot).start()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
