#                                            BOTCOMMUNICATOR
# -----------------------------------------------------------------------------------------------------------
# is responsible for controlling the dialogue between user and bot and to ask for new messages from user

import telebot
import config

import pika

bot = telebot.TeleBot(config.TOKEN)


@bot.message_handler(commands=['start'])
def welcome(message):
    bot.send_message(message.chat.id, "Hello, {0.first_name}!".format(message.from_user, bot.get_me()))


@bot.message_handler(commands=['help'])
def welcome(message):
    bot.send_message(message.chat.id, "Let's look at sth I can do:\n/welcome - allow newcomer to enter\n/keep_out - otherwise, the door won't be opened\n/edit - type missing info about employee or change it")


@bot.message_handler(commands=['welcome'])
def check_newcomer(message):
    allowed = 1
    bot.send_message(message.chat.id, "Great, don't forget to greet him)")
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel(2)
    channel.queue_declare(queue='allowance')
    channel.queue_purge('allowance')
    channel.basic_publish(exchange='', routing_key='allowance', body=bytes([allowed]))
    connection.close()


@bot.message_handler(commands=['keep_out'])
def check_newcomer(message):
    allowed = 0
    bot.send_message(message.chat.id, "Ok, the door won't be opened under any circumstances")
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel(2)
    channel.queue_declare(queue='allowance')
    channel.queue_purge('allowance')
    channel.basic_publish(exchange='', routing_key='allowance', body=bytes([allowed]))
    connection.close()


@bot.message_handler(commands=['thisis'])
def newcomer_info(message):
    bot.send_message(message.chat.id, "Name saved")
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel(2)
    channel.queue_declare(queue='apply_info')
    channel.queue_purge('apply_info')
    channel.basic_publish(exchange='', routing_key='apply_info', body=' '.join(message.text[7:]).encode('utf-8'))
    connection.close()


@bot.message_handler(commands=['edit'])
def edit_person_info(message):
    ID = int(message.text.split(' ')[1])
    # TODO: reading database - search by int(person) (it is id)
    #  don't forget about wrong ids
    # search result goes as PersonData
    PersonDataRead = {
        'name': 'Vlad',
        'years old': 16,
        'profession': 'CEO',
        'visits': ["1 01 2020", "05 05 2020", "31 12 2019"],
    }
    '''connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel(2)
    channel.queue_declare(queue='allowance')
    channel.queue_purge('allowance')
    channel.basic_publish(exchange='', routing_key='allowance', body=bytes([allowed]))
    connection.close()'''


bot.polling(none_stop=True)
# commands=['help'], content_types=['document', 'audio', 'text'], regexp="SOME_REGEXP"
'''
PersonData = {}

while True:
    method_frame, header_frame, body = channel.basic_get(queue="apply_info", auto_ack=False)
    if method_frame and (body is not None):
        pd = body.decode('utf-8').split(' ')
        PersonData.setdefault('name', pd[0])
        PersonData.setdefault('y.o', pd[1])
        PersonData.setdefault('profession', pd[2])
        x = datetime.datetime.now()
        visits = [str(x.day)+' '+str(x.month)+' '+str(x.year)]
        PersonData.setdefault('visits', visits)
        bd = int.from_bytes(body, sys.byteorder)
        print('[x] Guest details from telegram received: %r' % bd)
        channel.basic_ack(method_frame.delivery_tag)
        break
'''
