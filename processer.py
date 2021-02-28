#                                            PROCESSER
# -----------------------------------------------------------------------------------------------------------
# responsible for processing all the information given by facefinder and dbmanager
# notifies about new face detected via bot and adds it to a database

import time
import sys
import pika
import telebot
import datetime
import config
import queues_purge


def main():
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
            datestamp = str(datetime.datetime.now()).split(' ')[1]
            print("["+datestamp+"] Received %r" % body)
            ids = body.split(',')
            photo = open('faces.png', 'rb')
            data = photo.read()
            bot.send_photo(chat_id, data, "Newcomer detected!")
            for personID in ids:  # let's imagine that ids has only 1 element:)
                # TODO: processing multiple faces or creating a rule = one face per photo
                if personID == '-1':
                    channel.queue_purge('allowance')
                    allowed = False
                    bot.send_message(chat_id, "Hmm, I couldn't find him in database.\n'/welcome' or '/keep_out'?")
                    datestamp = str(datetime.datetime.now()).split(' ')[1]
                    print('['+datestamp+'] Waiting for acceptance from telegram...')
                    while True:
                        method_frame, header_frame, body = channel.basic_get(queue="allowance", auto_ack=False)
                        if method_frame:
                            bd = int.from_bytes(body, sys.byteorder)
                            datestamp = str(datetime.datetime.now()).split(' ')[1]
                            print('['+datestamp+'] Acceptance from telegram received: %r' % bd)
                            channel.basic_ack(method_frame.delivery_tag)
                            break
                    print("[x] Disconnecting from the queue...")
                    channel.queue_purge('allowance')
                    allowed = (bd == 1)
                    
                    if allowed:
                        bot.send_message(chat_id, "Okay, now please type his name:")
                        bot.send_message(chat_id, "You should do it like this: /thisis <name> <surname>")
                        bot.send_message(chat_id, "Always check correct info!")
                        channel.queue_purge('apply_info')
                        datestamp = str(datetime.datetime.now()).split(' ')[1]
                        print("["+datestamp+"] Waiting for info from telegram...")
                        while True:
                            method_frame, header_frame, body = channel.basic_get(queue="apply_info", auto_ack=False)
                            if method_frame and (body is not None):
                                thisis = body.decode('utf-8')
                                datestamp = str(datetime.datetime.now()).split(' ')[1]
                                print('['+datestamp+'] Guest name from telegram received: %r' % thisis)
                                channel.basic_ack(method_frame.delivery_tag)
                                break
                        print("[x] Disconnecting from the queue...")
                        channel.queue_purge('apply_info')
                        names = open("names.txt", "r")
                        strnames = names.read()
                        names.close()
                        personID = len(strnames.split(','))
                        names = open("names.txt", "w")
                        if strnames[len(strnames)-1:] == '\n':
                            strnames = strnames[:len(strnames)-1]
                        strnames += "," + thisis
                        names.write(strnames)
                        names.close()
                        bot.send_message(chat_id, "Remember that ID of " + thisis + " is "+str(personID) +\
                                         "\nYou are able to change it and type additional info about an employee via /edit <ID>")
                        print("[x] Updated the names list")
                        # TODO: writing {personID+thisis+[]*other_data} to a database
                        channel.queue_purge('newcomers')
                        channel.basic_publish(exchange='', routing_key='newcomers', body=bytes([personID]))
                        print("[x] Sent new person ID (%r) to facefinder" % personID)
                    else:  # if not allowed
                        channel.queue_purge('newcomers')
                        channel.basic_publish(exchange='', routing_key='newcomers', body=bytes([0]))
                        print("[x] Sent ignoring request to facefinder")

                else:
                    # TODO: reading database - search by int(person) (it is id)
                    #  search result goes as PersonData
                    PersonDataRead = {
                        'name': 'Vlad',
                        'years old': 16,
                        'profession': 'CEO',
                        'visits': ["1 01 2020", "05 05 2020", "31 12 2019"],
                    }
                    x = datetime.datetime.now()
                    PersonDataRead['visits'].append(str(x.day)+' '+str(x.month)+' '+str(x.year))

                    # TODO: adding day to visitsMonth and trying not to use list of ALL visits
                    #  storing array of visits in database

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
    datestamp = str(datetime.datetime.now()).split(' ')[1]
    print('['+datestamp+'] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()
    datestamp = str(datetime.datetime.now()).split(' ')[1]
    print('['+datestamp+'] Suddenly ended work. Restarting...')
    channel.queue_purge("hello")
    channel.queue_purge("newcomers")


print("Processer console\n________________________________")
while True:
    if __name__ == '__main__':
        try:
            queues_purge.qp()
            main()
        except telebot.apihelper.ApiTelegramException:
            time.sleep(3)
