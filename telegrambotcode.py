import time
import requests
from io import BytesIO
from telegram import Bot, Update
from flask import Flask, request
from telegram.ext import Updater, CommandHandler, CallbackContext
import threading
import os
import random
import string

# --- Налаштування ---
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")  # Твій Telegram ID
TRACKING_URL = 'https://www.ups.com/track?loc=en_US&tracknum=1ZA0Y3156822543252'
# Додаємо параметр для уникальності URL
def generate_unique_url():
    random_suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    return f'https://image.thum.io/get/width/1000/{TRACKING_URL}?{random_suffix}'

last_status = ""

# --- Flask ---
app = Flask(__name__)

@app.route('/')
def index():
    return 'Бот працює!'

@app.route('/ping')
def ping():
    return 'OK'

# Отримання статусу трекінгу
def get_tracking_status():
    # У спрощеному варіанті просто повертаємо лінк і текст
    return f"Ось лінк на відстеження:", TRACKING_URL

# Завантаження фото для трекінгу
def get_tracking_photo():
    url = generate_unique_url()
    response = requests.get(url)

    # Перевірка, чи є зображення в відповіді
    if response.status_code == 200 and 'image' in response.headers['Content-Type']:
        return BytesIO(response.content)
    else:
        # Якщо це не зображення, можна обробити як помилку або відправити інший тип даних
        print("Не вдалося отримати зображення.")
        return None

# Надсилання оновлення
def send_tracking_update(bot: Bot):
    global last_status
    # Псевдо-оновлення, тут можна зробити скрапінг або API якщо треба
    status_text, url = get_tracking_status()
    if status_text != last_status:
        last_status = status_text
        bot.send_message(chat_id=CHAT_ID, text=f"🚚 Статус змінився: {status_text}\n{url}")
        photo = get_tracking_photo()
        if photo:
            bot.send_photo(chat_id=CHAT_ID, photo=photo)
        else:
            bot.send_message(chat_id=CHAT_ID, text="Неможливо отримати зображення для цього трекінгу.")

# --- Команди ---
def status_command(update: Update, context: CallbackContext):
    status_text, url = get_tracking_status()
    update.message.reply_text(f"📦 Поточний статус: {status_text}\n{url}")

def photo_command(update: Update, context: CallbackContext):
    photo = get_tracking_photo()
    if photo:
        update.message.reply_photo(photo=photo)
    else:
        update.message.reply_text("Не вдалося отримати фото.")

def info_command(update: Update, context: CallbackContext):
    update.message.reply_text(f"🔍 Трекінг UPS:\n{TRACKING_URL}")

# --- Основна логіка ---
def start_bot():
    # Ініціалізація бота
    updater = Updater(token=TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Додавання команд
    dispatcher.add_handler(CommandHandler("status", status_command))
    dispatcher.add_handler(CommandHandler("photo", photo_command))
    dispatcher.add_handler(CommandHandler("info", info_command))

    updater.start_polling()

# --- Функція для запуску серверу і бота одночасно ---
def run():
    bot = Bot(token=TOKEN)
    threading.Thread(target=start_bot, daemon=True).start()

    # Запуск Flask сервера
    app.run(host='0.0.0.0', port=3000)

    # Цикл автооновлення
    while True:
        try:
            send_tracking_update(bot)
            time.sleep(600)  # Перевірка кожні 10 хвилин
        except Exception as e:
            print(f"Помилка: {e}")
            time.sleep(600)  # Якщо сталася помилка, спробувати через 10 хвилин

if __name__ == '__main__':
    run()
