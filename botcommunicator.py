#                                            BOTCOMMUNICATOR
# -----------------------------------------------------------------------------------------------------------
# is responsible for controlling the dialogue between user and bot and to ask for new messages from user

import telebot
import config

import pika
import db_table
import datetime
from main.database.launch_db_session import Session, engine, Base


bot = telebot.TeleBot(config.TOKEN)


@bot.message_handler(commands=['start'])
def welcome(message):
    bot.send_message(message.chat.id, "Hello, {0.first_name}!".format(message.from_user, bot.get_me()))


@bot.message_handler(commands=['help'])
def welcome(message):
    bot.send_message(message.chat.id, "Let's look at sth I can do:\n/welcome - allow newcomer to enter\n/keep_out - otherwise, the door won't be opened\n/edit_info ID KEY VALUE = type missing info about employee or change it")
    bot.send_message(message.chat.id, "Attention: /edit_info thisis Vladislav_Railes - the words of thisis should be divided by _, not whitespace")
    bot.send_message(message.chat.id, "KEYs are: thisis (name+surname), yo (years old), profession, visits")
    bot.send_message(message.chat.id, "In order to delete incorrect visit mark,\ntype /del_visit YYYY-mm-dd")


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
    channel.basic_publish(exchange='', routing_key='apply_info', body=message.text[8:].encode('utf-8'))
    connection.close()


@bot.message_handler(commands=['get'])
def get_person_info(message):
    ID = int(message.text.split()[1])
    bot.send_message(message.chat.id, db_table.convert_to_pd(db_table.get(ID)))


@bot.message_handler(commands=['get_all'])
def get_all(message):
    emps = db_table.get_all()
    for emp in emps:
        bot.send_message(message.chat.id, f'{emp.thisis}, {emp.yo}, who is {emp.profession}, has visited building during {", ".join(map(str, emp.visits))}')


@bot.message_handler(commands=['edit_info'])
def edit_person_info(message):
    msg = message.text.split()
    if len(msg) > 3:
        ID = int(msg[1])
        person = db_table.get(ID)
        i = 2
        while i < len(msg):
            if msg[i] == 'thisis':
                person.thisis = msg[i+1]
                i += 2
            elif msg[i] == 'yo':
                person.yo = msg[i+1]
                i += 2
            elif msg[i] == 'profession':
                person.profession = msg[i+1]
                i += 2
            else:
                i = len(msg)
        Session.flush()  # /edit ID thisis Vladislav_Ralles yo 17
    else:
        bot.send_message(message.chat.id, "Incorrect parameters. Try again)")


@bot.message_handler(commands=['del_visit'])
def del_visit(message):
    ID = int(message.text.split()[1])
    visit = datetime.datetime.strptime(message.text.split()[2], '%Y-%m-%d').date()
    person = db_table.get(ID)
    vz = list(map(str, person.visits))
    del(vz[vz.index(str(visit))])
    nvz = []
    for d in vz:
        nvz.append(datetime.datetime.strptime(d, '%Y-%m-%d').date())
    person.visits = nvz
    Session.flush()


# TODO: add searching by visit and deleting it (del(visits.index(visit)), session.flush())
bot.polling(none_stop=True)
