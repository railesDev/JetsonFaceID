# notifies about new face detected via bot and adds it to a dataset
from main import config
import telebot
import pika, sys, time
from main import queues_purge
import random


def main():
    print("Processer console\n________________________________")
    bot = telebot.TeleBot(config.TOKEN)
    chat_id = 737474036
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='hello')
    channel.queue_declare(queue='newcomers')

    def callback(ch, method, properties, body_bytes):
        if body_bytes:
            body = body_bytes.decode("utf-8")
            print("[x] Received %r" % body)
            ids = body.split(',')
            photo = open('faces.png', 'rb')
            data = photo.read()
            bot.send_photo(chat_id, data, "New person detected!")
            for person in ids:
                if person == '-1':
                    bot.send_message(chat_id, "Newcomer! Is he allowed to enter?")
                    # TODO: collecting info
                    allowed = True
                    if allowed:
                        # TODO: typing info, waiting for answer
                        # TODO: receiving info - find "collecting new messages only once"
                        # TODO: next we will parse them
                        # thinking that we theoretically collected data from conversation with admin:
                        # FOR ADMIN: id = -1 means an impostor!
                        names = open("names.txt", "r")
                        strnames = names.read()
                        names.close()
                        new_id = len(strnames.split(' '))

                        def generate_name():
                            name = chr(random.randint(97, 122)).upper()
                            n = random.randint(4, 10)
                            for i in range(n):
                                name += chr(random.randint(97, 122))
                            return name
                        data = {
                            'id': new_id,
                            'name': generate_name(),
                            'years old': 16,
                            'profession': 'newcomer',
                        }
                        names = open("names.txt", "w")
                        if strnames[len(strnames)-1:] == '\n':
                            strnames = strnames[:len(strnames)-1]
                        strnames += " " + data['name']
                        names.write(strnames)
                        names.close()
                        # TODO: adding to a dataset
                        # we only need to send id to facefinder
                        channel.queue_purge('newcomers')
                        channel.basic_publish(exchange='', routing_key='newcomers', body=bytes([data['id']]))
                        bot.send_message(chat_id, str(data))
                        print("[x] Sent new person ID (%r) to facefinder" % data['id'])
                    else:
                        channel.queue_purge('newcomers')
                        channel.basic_publish(exchange='', routing_key='newcomers', body=bytes([0]))
                        print("[x] Sent ignoring request to facefinder")
                        bot.send_message(chat_id, "Ok, the door won't be opened for him!")
                else:
                    # TODO: reading dataset - search by int(person) (it is id)
                    data = {
                        'id': 1,
                        'name': 'Vlad',
                        'years old': 16,
                        'profession': 'CEO',
                    }
                    channel.queue_purge('newcomers')
                    channel.basic_publish(exchange='', routing_key='newcomers', body=bytes([0]))
                    print("[x] Sent known person ID (%s) to facefinder" % person)
                    bot.send_message(chat_id, str(data))  # for now treating output as dictionary
                    print(" [x] Person is "+data['name']+" and id is "+person)
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
