#                                            BOTCOMMUNICATOR
# -----------------------------------------------------------------------------------------------------------
# is responsible for controlling the dialogue between user and bot and to ask for new messages from user

# TODO: admin|user|guest authentication

import telebot
from main import config

import pika


bot = telebot.TeleBot(config.TOKEN)


@bot.message_handler(commands=['start'])
def welcome(message):
    bot.send_message(message.chat.id, "Привет, {0.first_name}!".format(message.from_user, bot.get_me()))


@bot.message_handler(commands=['enter'])
def check_newcomer(message):
    allowed = 1 if message.text.split(' ')[1].lower() == 'y' else 0
    bot.send_message(message.chat.id, "OK")
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel(2)
    channel.queue_declare(queue='allowance')
    channel.queue_purge('allowance')
    channel.basic_publish(exchange='', routing_key='allowance', body=bytes([allowed]))
    connection.close()


@bot.message_handler(commands=['apply'])
def newcomer_info(message):
    bot.send_message(message.chat.id, "OK   ")
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel(2)
    channel.queue_declare(queue='apply_info')
    channel.queue_purge('apply_info')
    # channel.basic_publish(exchange='', routing_key='apply_info', body=bytes(' '.join(message.text.split(' ')[1:]), encoding='utf8'))
    channel.basic_publish(exchange='', routing_key='apply_info', body=' '.join(message.text.split(' ')[1:]).encode('utf-8'))

    connection.close()


@bot.message_handler(commands=['help'])
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
