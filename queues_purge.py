#                                            QUEUES PURGER
# -----------------------------------------------------------------------------------------------------------
# needed for deleting data in pika queues from other, sometimes halted, sessions

import pika


def qp():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='hello')
    channel.queue_declare(queue='newcomers')
    channel.queue_purge('hello')
    channel.queue_purge('newcomers')
