#                                            FACEFINDER
# -----------------------------------------------------------------------------------------------------------
# reads camera, finds faces, recognises them, sends response to processer
# performs training and creates && updates /dataset/ and trainer.yml

import cv2
import os
import numpy as np
from PIL import Image
import pika
import sys
import datetime
import queues_purge
import db_table
from main.docker_shell.launch_db_session import Session, engine, Base


recognizer = cv2.face.LBPHFaceRecognizer_create()
detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')


def recognise():
    cam = cv2.VideoCapture(0)
    cam.set(3, 640)  # set video width
    cam.set(4, 480)  # set video height
    recognizer.read('trainer/trainer.yml')
    font = cv2.FONT_HERSHEY_SIMPLEX
    id = 0
    prev_id = -1
    idsprev = []  # IN STR
    idsnew = []
    minW = 0.1 * cam.get(3)
    minH = 0.1 * cam.get(4)
    while True:
        ret, img = cam.read()
        file = open("names.txt", "r")
        names = file.read().split(',')
        last = names[len(names)-1]
        if last[len(last)-1] == '\n':
            names[len(names)-1] = last[:len(last)-1]
        file.close()
        # img = cv2.flip(img, -1)  # Flip vertically
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(
            gray,
            scaleFactor=1.2,
            minNeighbors=5,
            minSize=(int(minW), int(minH)),
        )
        for (x, y, w, h) in faces:
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            id, confidence = recognizer.predict(gray[y:y + h, x:x + w])
            if confidence < 100:
                try:
                    if round(100-confidence) < 25:
                        idS = "Unknown"
                        id = -1
                    else:
                        idS = names[id]
                    confidence = "  {0}%".format(round(100 - confidence))
                except IndexError:
                    # if taught already, but not added to names.txt:
                    print('[WARNING] In trainer.yml there is a wrong face and id: ' + str(id))
                    continue
            else:
                idS = "Unknown"
                id = -1
                confidence = "  {0}%".format(round(100 - confidence))
            cv2.putText(img, str(idS), (x + 5, y - 5), font, 1, (255, 255, 255), 2)
            cv2.putText(img, str(confidence), (x + 5, y + h - 5), font, 1, (255, 255, 0), 1)
            if (not str(id) in idsprev) or id == -1:
                idsnew.append(str(id))
        cv2.imshow('JetsonFaceID Terminal', img)
        eq = np.array_equal([], faces)
        if (not eq) and idsnew != []:  # if any face exists and it is not the previous ones (all)
            cv2.imwrite("faces.png", img)
            # send message to notifier that we have found our face
            connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
            channel = connection.channel(1)
            channel.queue_declare(queue='hello')
            channel.queue_purge('hello')
            channel.basic_publish(exchange='',
                                  routing_key='hello',
                                  body=bytes(','.join(idsnew), encoding='utf8'))
            datestamp = str(datetime.datetime.now()).split(' ')[1]
            print("["+datestamp+"] Sent detected faces' data")
            print(" [IDS]: "+', '.join(idsnew))
            connection.close()

            connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
            channel = connection.channel(1)
            channel.queue_declare(queue='newcomers')
            channel.queue_purge('newcomers')
            newcomers_ids = []

            def callback(ch, method, properties, body):
                bd = int.from_bytes(body, sys.byteorder)
                datestamp = str(datetime.datetime.now()).split(' ')[1]
                print('['+datestamp+'] Acceptance from telegram received: %r' % bd)
                if bd != 0:
                    newcomers_ids.append(bd)
                if bd == 0:
                    print(" [STATUS] All unknown people have been processed.")
                    print("[x] Closing connection with the queue...")
                    channel.queue_purge('newcomers')
                    raise IndentationError  # exiting
            channel.basic_consume(queue='newcomers', on_message_callback=callback, auto_ack=True)
            datestamp = str(datetime.datetime.now()).split(' ')[1]
            print('['+datestamp+'] Waiting for acceptance from telegram...')
            try:
                channel.start_consuming()
            except IndentationError:
                channel.queue_purge('newcomers')
                connection.close()
            if newcomers_ids:
                print("[x] Adding all the new faces")
                cam.release()
                cv2.destroyAllWindows()
                for newcomer in newcomers_ids:
                    add_face_to_dataset(newcomer)
                print("[x] Restarting JFID terminal...")
                cam = cv2.VideoCapture(0)
                cam.set(3, 640)  # set video width
                cam.set(4, 480)  # set video height
                recognizer.read('trainer/trainer.yml')
        if idsnew:
            idsprev = idsnew
        idsnew = []
        k = cv2.waitKey(10) & 0xff  # Press 'ESC' for exiting video
        if k == 27:
            break
    print("[x] Exiting Program and cleanup stuff")
    cam.release()
    cv2.destroyAllWindows()


def add_face_to_dataset(face_id):  # called only if it's a new person
    cam0 = cv2.VideoCapture(0)
    cam0.set(3, 640)  # set video width
    cam0.set(4, 480)  # set video height
    # For each person, enter one numeric face id
    print("[x] Initializing face capture ...")
    # Initialize individual sampling face count
    count = 0
    recognizer.read('trainer/trainer.yml')
    while True:
        ret, img = cam0.read()
        # img = cv2.flip(img, -1)  # flip video image vertically
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(gray, 1.3, 5)
        for (x, y, w, h) in faces:

            id, confidence = recognizer.predict(gray[y:y + h, x:x + w])
            if round(100-confidence) >= 60:
                print("[x] Tried to add existing face")
                file = open("names.txt", "r")
                names = file.read().split(',')
                names = names[:face_id]
                file.close()
                file = open("names.txt", "w")
                file.write(','.join(names))
                file.close()
                cam0.release()
                cv2.destroyAllWindows()
                return

            cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
            count += 1
            # Save the captured image into the datasets folder
            cv2.imwrite("dataset/User." + str(face_id) + '.' + str(count) + ".jpg", gray[y:y + h, x:x + w])
        cv2.imshow('LOOK AT THE CAMERA', img)
        k = cv2.waitKey(100) & 0xff  # Press 'ESC' for exiting video
        if k == 27:
            break
        elif count >= 60:  # Take 60 face sample and stop video
            break
    # Do a bit of cleanup
    print("[x] Exiting Face Detector and cleaning up...")
    cam0.release()
    cv2.destroyAllWindows()
    # train with the new face
    perform_training()


def create_dataset():  # called only if it's a new person
    face_id = 1
    cam0 = cv2.VideoCapture(0)
    cam0.set(3, 640)  # set video width
    cam0.set(4, 480)  # set video height
    # For each person, enter one numeric face id
    print("[x] Initializing face capture...")
    # Initialize individual sampling face count
    count = 0
    while True:
        ret, img = cam0.read()
        # img = cv2.flip(img, -1)  # flip video image vertically
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(gray, 1.3, 5)
        for (x, y, w, h) in faces:
            cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
            count += 1
            # Save the captured image into the datasets folder
            cv2.imwrite("dataset/User." + str(face_id) + '.' + str(count) + ".jpg", gray[y:y + h, x:x + w])
        cv2.imshow('Face Detector', img)
        k = cv2.waitKey(100) & 0xff  # Press 'ESC' for exiting video
        if k == 27:
            break
        elif count >= 60:  # Take 60 face sample and stop video
            break
    # Do a bit of cleanup
    print("[x] Exiting Face Detector and cleaning up...")
    cam0.release()
    cv2.destroyAllWindows()
    # train with the new face
    perform_training()


def perform_training():  # called if add_to_base was called
    path = 'dataset'

    # function to get the images and label data
    def get_images_and_labels(path_):
        imagePaths = [os.path.join(path_, f) for f in os.listdir(path_)]
        faceSamples = []
        id_s = []
        for imagePath in imagePaths:
            PIL_img = Image.open(imagePath).convert('L')  # convert it to grayscale
            img_numpy = np.array(PIL_img, 'uint8')
            id = int(os.path.split(imagePath)[-1].split(".")[1])
            facesF = detector.detectMultiScale(img_numpy)
            for (x, y, w, h) in facesF:
                faceSamples.append(img_numpy[y:y + h, x:x + w])
                id_s.append(id)
        return faceSamples, id_s

    print("[x] Training faces. It will take a few seconds. Please wait...")
    faces, ids = get_images_and_labels(path)
    recognizer.train(faces, np.array(ids))
    # Save the model into trainer/trainer.yml
    recognizer.write('trainer/trainer.yml')  # recognizer.save() worked on Mac, but not on Pi
    recognizer.save('trainer/trainer.yml')
    print("[x] Trainer.yml has been successfully rewritten")
    # Print the number of faces trained and end program
    print("[x] {0} faces trained. Exiting Training".format(len(np.unique(ids))))


if __name__ == "__main__":
    print("Facefinder console\n________________________________")
    queues_purge.qp()
    print('Welcome. Checking whether dataset is ready...')
    if not any([True for _ in os.scandir('dataset')]):
        datestamp = str(datetime.datetime.now()).split(' ')[1]
        print('['+datestamp+'] Dataset is not ready. Capturing the first face. Look at the camera please')
        create_dataset()
        # PRESET (as well as names.txt with None, Vladislav Railes
        NCData = {
            'thisis': 'Vladislav Railes',
            'y.o.': -1,
            'profession': '_',
            'visits': [datetime.datetime.today().strftime('%Y-%m-%d')]
        }
        db_table.add(NCData)
        Session.flush()
    datestamp = str(datetime.datetime.now()).split(' ')[1]
    print('['+datestamp+'] Starting main module...')
    recognise()


# TODO'S:______________________________________________________________________________________________________________
# TODO: OPTIMIZATION
#  we can create a dataset for every face in turn, and in recognition part we can go in cycle
#  and try to load every dataset
#  cases:
#  if no datasets are found, we leave a notification for processer (id=unknown)
#  in order to make him send photo and ask for data about a newcomer
#  if dataset is found, we find out the id of a person and send data to processer
#  in order to make him send information and make statistics
#  facefinder calls recognise()
