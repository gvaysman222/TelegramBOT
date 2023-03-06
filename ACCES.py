import telebot
import sqlite3

bot = telebot.TeleBot('TELEGRAM_BOT_TOKEN')

conn = sqlite3.connect('user_messages.db')

cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS acces_users (
        chat_id INTEGER PRIMARY KEY
    )
""")
conn.commit()
cursor.close()

@bot.message_handler(commands=['add'])
def add_user(message):
    chat_id = message.text.split('/add ')[-1]  
    conn = sqlite3.connect('user_messages.db')
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id FROM acces_users WHERE chat_id=?", (chat_id,))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO acces_users (chat_id) VALUES (?)", (chat_id,))
        conn.commit()
        bot.reply_to(message, "Chat ID добавлен в базу данных.")
    else:
        bot.reply_to(message, "Chat ID уже находится в базе данных.")
    cursor.close()
    conn.close()


@bot.message_handler(commands=['remove'])
def remove_user(message):
    chat_id = message.text.split('/remove ')[-1]
    conn = sqlite3.connect('user_messages.db')
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id FROM acces_users WHERE chat_id=?", (chat_id,))
    if cursor.fetchone() is not None:
        cursor.execute("DELETE FROM acces_users WHERE chat_id=?", (chat_id,))
        conn.commit()
        bot.reply_to(message, "Chat ID удален из базы данных.")
    else:
        bot.reply_to(message, "Chat ID не найден в базе данных.")
    cursor.close()
    conn.close()


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "Я понимаю только команды /add и /remove, попробуйте снова.")

bot.polling()
