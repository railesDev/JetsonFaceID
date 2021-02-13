#                                            PROCESSER
# -----------------------------------------------------------------------------------------------------------
# responsible for processing all the information given by facefinder and dbmanager
# notifies about new face detected via bot and adds it to a database

import random
import time
import sys

import pika
import telebot

from main import config
from main.utilitary import queues_purge

import datetime


def main():
    print("Processer console\n________________________________")
    bot = telebot.TeleBot(config.TOKEN)
    chat_id = 737474036
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel(1)
    channel.queue_declare(queue='hello')
    channel.queue_declare(queue='newcomers')
    channel.queue_declare(queue='allowance')
    channel.queue_declare(queue='apply_info')

    def callback(ch, method, properties, body_bytes):
        if body_bytes:
            body = body_bytes.decode("utf-8")
            print("[x] Received %r" % body)
            ids = body.split(',')
            photo = open('faces.png', 'rb')
            data = photo.read()
            bot.send_photo(chat_id, data, "New people detected!")
            for personID in ids:
                if personID == '-1':
                    bot.send_message(chat_id, "Newcomer! Is he allowed to enter?")
                    bot.send_message(chat_id, "/enter Y|N")

                    channel.queue_purge('allowance')
                    allowed = False
                    print('[x] Waiting for acceptance from telegram...')
                    while True:
                        method_frame, header_frame, body = channel.basic_get(queue="allowance", auto_ack=False)
                        if method_frame:
                            bd = int.from_bytes(body, sys.byteorder)
                            print('[x] Acceptance from telegram received: %r' % bd)
                            channel.basic_ack(method_frame.delivery_tag)
                            break
                    print("[x] Disconnecting from the queue...")
                    channel.queue_purge('allowance')
                    allowed = (bd == 1)

                    if allowed:
                        bot.send_message(chat_id, "Okay, now please type all the info about him: ")
                        bot.send_message(chat_id, "You should do it like this: /apply <name> <y.o> <profession>")
                        # VULNERABILITY: if there are mistakes, there's no chance to change anything
                        # IDEA: /edit - edit incorrect data in database
                        bot.send_message(chat_id, "Always check correct info!")

                        # channel1 = connection.channel(1)

                        channel.queue_purge('apply_info')
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
                        print("[x] Disconnecting from the queue...")
                        channel.queue_purge('apply_info')

                        names = open("names.txt", "r")
                        strnames = names.read()
                        names.close()
                        personID = len(strnames.split(' '))
                        names = open("names.txt", "w")
                        if strnames[len(strnames)-1:] == '\n':
                            strnames = strnames[:len(strnames)-1]
                        strnames += " " + PersonData['name']
                        names.write(strnames)
                        names.close()
                        print("[x] Updated the names list - now all new ones are available for facefinder")
                        # TODO: writing PersonData to a database (parameters are personID from names.txt and PersonData from telegram)
                        # FOR ADMIN: id = -1 means an impostor
                        # now we just need to send the id to facefinder
                        channel.queue_purge('newcomers')
                        channel.basic_publish(exchange='', routing_key='newcomers', body=bytes([personID]))
                        bot.send_message(chat_id, str(PersonData))
                        print("[x] Sent new person ID (%r) to facefinder" % personID)
                    else:  # if not allowed
                        channel.queue_purge('newcomers')
                        channel.basic_publish(exchange='', routing_key='newcomers', body=bytes([0]))
                        print("[x] Sent ignoring request to facefinder")
                        bot.send_message(chat_id, "Ok, the door won't be opened for him!")

                else:
                    # TODO: reading database - search by int(person) (it is id)
                    # search result goes as PersonData
                    PersonDataRead = {
                        'name': 'Vlad',
                        'years old': 16,
                        'profession': 'CEO',
                        'visits': ["1 01 2020", "05 05 2020", "31 12 2019"],
                    }
                    x = datetime.datetime.now()
                    PersonDataRead['visits'].append(str(x.day)+' '+str(x.month)+' '+str(x.year))

                    # TODO: adding day to visitsMonth

                    channel.queue_purge('newcomers')
                    # channel.basic_publish(exchange='', routing_key='newcomers', body=bytes([0]))
                    # print("[x] Sent known person ID (%s) to facefinder" % personID)
                    bot.send_message(chat_id, "Newcomer is known as: "+str(PersonDataRead))
                    print(" [-] Person is "+PersonDataRead['name']+" and his id is "+personID)
            channel.basic_publish(exchange='', routing_key='newcomers', body=bytes([0]))
        else:
            channel.queue_purge('newcomers')
            channel.basic_publish(exchange='', routing_key='newcomers', body=bytes([0]))

    channel.basic_consume(queue='hello', on_message_callback=callback, auto_ack=True)
    print('[x] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()
    print('[x] Suddenly ended work. Restarting...')
    channel.queue_purge("hello")
    channel.queue_purge("newcomers")


while True:
    if __name__ == '__main__':
        try:
            queues_purge.qp()
            main()
        except telebot.apihelper.ApiTelegramException:
            time.sleep(3)

# except KeyboardInterrupt:
# print('Interrupted')
# sys.exit(0)
"""
def generate_name():
    name = chr(random.randint(97, 122)).upper()
    n = random.randint(4, 10)
    for i in range(n):
        name += chr(random.randint(97, 122))
    return name
                     
    PersonData = { 'name': 'Railes', 'years old': 16, 'profession': 'newcomer', 'visits': [1, 5, 31],}
"""
