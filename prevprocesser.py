#                                            PROCESSER
# -----------------------------------------------------------------------------------------------------------
# responsible for processing all the information given by facefinder and dbmanager
# notifies about new face detected via bot and adds it to a database

import time
import sys

import pika
import telebot

from main import config
from main import queues_purge

import datetime


def main():
    print("Processer console\n________________________________")
    bot = telebot.TeleBot(config.TOKEN)
    chat_id = 737474036
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel(1)
    channel.queue_declare(queue='hello')
    channel.queue_declare(queue='newcomers')
    channel1 = connection.channel(2)
    channel1.queue_declare(queue='allowance')
    channel1.queue_declare(queue='apply_info')

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

                    channel1.queue_purge('allowance')
                    allowed = False

                    def callback_allowance(chA, methodA, propertiesA, bodyA):
                        bd = int.from_bytes(bodyA, sys.byteorder)
                        print('[x] Acceptance from telegram received: %r' % bd)
                        print("[x] Closing connection with the queue...")
                        channel1.queue_purge('allowance')
                        if bd == 1:
                            raise ValueError  # exiting
                        if bd == -1:
                            raise IndentationError

                    channel1.basic_consume(queue='allowance', on_message_callback=callback_allowance, auto_ack=True)
                    print('[x] Waiting for acceptance from telegram...')
                    try:
                        channel1.start_consuming()
                    except IndentationError:
                        allowed = False
                        channel1.queue_purge('allowance')
                        # channel1.close()
                        channel1.stop_consuming()
                    except ValueError:
                        allowed = True
                        channel1.queue_purge('allowance')
                        # channel1.close()
                        channel1.stop_consuming()

                    if allowed:
                        bot.send_message(chat_id, "Okay, now please type all the info about him: ")
                        bot.send_message(chat_id, "/apply <name> <y.o> <profession>")
                        # VULNERABILITY: if there are mistakes, there's no chance to change anything
                        bot.send_message(chat_id, "Always check correct info!")

                        # channel1 = connection.channel(1)

                        channel1.queue_purge('apply_info')
                        PersonData = {}

                        def callback_application(chAP, methodAP, propertiesAP, bbytes):
                            if bbytes:
                                pd = bbytes.decode("utf-8")
                                PersonData.setdefault('name', pd[0])
                                PersonData.setdefault('y.o', pd[1])
                                PersonData.setdefault('profession', pd[2])
                                x = datetime.datetime.now()
                                visits = [str(x.day)+str(x.month)+str(x.year)]
                                PersonData.setdefault('visits', visits)
                                bd = int.from_bytes(body, sys.byteorder)
                                channel1.queue_purge('apply_info')
                                raise ValueError  # exiting

                        channel1.basic_consume(queue='apply_info', on_message_callback=callback_application, auto_ack=True)
                        try:
                            channel1.start_consuming()
                        except ValueError:
                            channel1.queue_purge('allowance')
                            # channel1.close()
                            channel1.stop_consuming()
                        # FOR ADMIN: id = -1 means an impostor!
                        '''
                        def generate_name():
                            name = chr(random.randint(97, 122)).upper()
                            n = random.randint(4, 10)
                            for i in range(n):
                                name += chr(random.randint(97, 122))
                            return name
                     
                        PersonData = {
                            'name': 'Railes',
                            'years old': 16,
                            'profession': 'newcomer',
                            'visits': [1, 5, 31],
                        }
                        '''
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

                        # TODO: writing to a database (parameters are personID from names.txt and PersonData from telegram)

                        # now we just need to send the id to facefinder
                        channel.queue_purge('newcomers')
                        channel.basic_publish(exchange='', routing_key='newcomers', body=bytes([personID]))
                        bot.send_message(chat_id, str(PersonData))
                        print("[x] Sent new person ID (%r) to facefinder" % personID)
                    else:
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
                        'visits': [1, 5, 31],
                    }
                    # TODO: adding day to visitsMonth

                    channel.queue_purge('newcomers')
                    channel.basic_publish(exchange='', routing_key='newcomers', body=bytes([0]))
                    print("[x] Sent known person ID (%s) to facefinder" % personID)
                    bot.send_message(chat_id, "Newcomer status: "+str(PersonDataRead))
                    print(" [-] Person is "+PersonDataRead['name']+" and id is "+personID)
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
