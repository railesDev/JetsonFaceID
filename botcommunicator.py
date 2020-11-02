# is responsible for controlling the dialogue between user and bot
# and to search for new messages from user
import telebot
from main import config

bot = telebot.TeleBot(config.TOKEN)


@bot.message_handler(commands=['start'])
def welcome(message):
    bot.send_message(message.chat.id, "Привет, {0.first_name}!".format(message.from_user, bot.get_me()))


@bot.message_handler(content_types=["text"])
def echo(message):
    bot.send_message(message.chat.id, message.text)


# Обработчик для документов и аудиофайлов
@bot.message_handler(content_types=['document', 'audio'])
def handle_docs_audio(message):
    pass


# Обработчик сообщений, подходящих под указанное регулярное выражение
@bot.message_handler(regexp="SOME_REGEXP")
def handle_message(message):
    pass


# Обработчик сообщений, содержащих документ с mime_type 'text/plain' (обычный текст)
@bot.message_handler(func=lambda message: message.document.mime_type == 'text/plain', content_types=['document'])
def handle_text_doc(message):
    pass


@bot.message_handler(content_types=['text'])
def send_text(message):
    if message.text.lower() == 'привет':
        bot.send_message(message.chat.id, 'Привет, мой создатель')
    elif message.text.lower() == 'пока':
        bot.send_message(message.chat.id, 'Прощай, создатель')


bot.polling()
