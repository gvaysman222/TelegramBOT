import telegram
import openai
import requests
import sqlite3
from io import BytesIO
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import InputMediaPhoto

# Токен API бота Telegram
BOT_TOKEN = 'TELEGRAM_BOT_TOKEN'

# Токен API модели text-davinci-003
OPENAI_API_KEY = 'OPENAI_API_KEY'

# Создаем объекты бота Telegram и модели OpenAI
bot = telegram.Bot(token=BOT_TOKEN)
openai.api_key = OPENAI_API_KEY

import sqlite3

def create_connection():
    return sqlite3.connect('user_messages.db')

def create_table():
    conn = create_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (message_id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id INTEGER, message_type TEXT, text TEXT)''')
    conn.commit()
    conn.close()

def add_message(chat_id, message_type, message_text):
    conn = create_connection()
    c = conn.cursor()
    c.execute("INSERT INTO messages (chat_id, message_type, text) VALUES (?, ?, ?)", (chat_id, message_type, message_text))
    conn.commit()
    conn.close()

def get_last_message(chat_id, message_type):
    conn = create_connection()
    c = conn.cursor()
    c.execute("SELECT text FROM messages WHERE chat_id=? AND message_type=? ORDER BY message_id DESC LIMIT 1", (chat_id, message_type))
    result = c.fetchone()
    conn.close()
    if result is not None:
        return result[0]
    else:
        return None


# Функция для проверки, есть ли пользователь в базе данных access_user
def is_user_in_access_list(chat_id):
    conn = create_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM acces_users WHERE chat_id=?", (chat_id,))
    result = c.fetchone()
    conn.close()
    if result is not None:
        return True
    else:
        return False


# Функция для обработки сообщений пользователя
def handle_message(update, context):
    # Получаем chat_id пользователя
    chat_id = update.message.chat_id
    # Проверяем, есть ли пользователь в базе данных access_user
    if not is_user_in_access_list(chat_id):
        bot.send_message(chat_id=chat_id, text="Вы не имеете доступа к этому боту")
        return
    # Получаем текст сообщения от пользователя
    message_text = update.message.text
    # Создаем таблицу, если ее еще нет
    create_table()
    # Добавляем сообщение пользователя в базу данных
    add_message(chat_id, 'user', message_text)
    # Получаем последнее сообщение пользователя из базы данных
    last_user_message = get_last_message(chat_id, 'user')
    # Формируем запрос к модели OpenAI с учетом контекста сообщения пользователя
    if last_user_message is not None:
        prompt = f"{last_user_message}\n{message_text}"
    else:
        prompt = message_text
    # Отправляем запрос к модели OpenAI с текстом сообщения от пользователя
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=message_text,
        max_tokens=4000,
        n=1,
        stop=None,
        temperature=0.0,
        presence_penalty=0,
        frequency_penalty=0
    )

    # Получаем ответ от модели OpenAI
    response_text = response.choices[0].text.strip()

    # Отправляем ответ от модели OpenAI пользователю
    bot.send_message(chat_id=update.message.chat_id, text=response_text)

    # Добавляем ответ бота в базу данных
    add_message(update.message.chat_id, 'bot', response_text)

# Функция для обработки команды /pict от пользователей
def handle_pict_command(update, context):
    # Получаем chat_id пользователя
    chat_id = update.message.chat_id
    # Проверяем, есть ли пользователь в базе данных access_user
    if not is_user_in_access_list(chat_id):
        bot.send_message(chat_id=chat_id, text="Вы не имеете доступа к этому боту")
        return
    # Получаем запрос пользователя из команды /pict
    query = " ".join(context.args)

    # Создаем URL-адрес запроса для API генерации изображений OpenAI
    url = "https://api.openai.com/v1/images/generations"

    # Определяем параметры запроса к API генерации изображений OpenAI
    data = {
        "model": "image-alpha-001",
        "prompt": query,
        "num_images": 10,
        "size": "512x512",
        "response_format": "url"
    }

    # Отправляем POST-запрос к API генерации изображений OpenAI и получаем URL сгенерированных изображений
    response = requests.post(url, headers={'Authorization': f'Bearer {OPENAI_API_KEY}'}, json=data)
    response.raise_for_status()
    response_text_list = [r['url'] for r in response.json()['data']]

    # Создаем список InputMediaPhoto объектов
    media_list = [InputMediaPhoto(requests.get(response_text).content) for response_text in response_text_list]

    # Отправляем все сгенерированные изображения как одно сообщение пользователю
    bot.send_message(chat_id=update.message.chat_id, text=f"Вот несколько изображений на тему '{query}':")
    bot.send_media_group(chat_id=update.message.chat_id, media=media_list)

def start_command(update, context):
    # Отправляем пользователю приветственное сообщение
    update.message.reply_text('Привет! Я бот, который может общаться с вами и генерировать изображения на заданную тему.')


# Создаем объект Updater для обработки сообщений
updater = Updater(token=BOT_TOKEN, use_context=True)

# Регистрируем обработчики команд и сообщений от пользователей
updater.dispatcher.add_handler(CommandHandler('start', start_command))
updater.dispatcher.add_handler(CommandHandler('pict', handle_pict_command))
updater.dispatcher.add_handler(MessageHandler(Filters.text, handle_message))

# Запускаем бота
updater.start_polling()
print("Бот успешно запущен!")
updater.idle()
