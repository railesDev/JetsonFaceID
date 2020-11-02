import cv2
import os
import numpy as np
from PIL import Image
import pika, sys
from main import queues_purge

recognizer = cv2.face.LBPHFaceRecognizer_create()
detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')


# TODO: OPTIMIZATION
# TODO: we can create a dataset for every face in turn, and in recognition part we can go in cycle and try to load every dataset
# TODO: cases:
# TODO: if no datasets are found, we leave a notification for processer (id=unknown) in order to make him send photo and ask for data about a newcomer
# TODO: if dataset is found, we find out the id of a person and send data to processer in order to make him send information and make statistics
# TODO: facefinder calls recognise


def recognise():
    print("Facefinder console\n________________________________")
    cam = cv2.VideoCapture(0)
    cam.set(3, 640)  # set video width
    cam.set(4, 480)  # set video height
    recognizer.read('trainer/trainer.yml')
    font = cv2.FONT_HERSHEY_SIMPLEX
    # initiate id counter
    id = 0
    prev_id = -1
    idsprev = []  # IN STR
    idsnew = []
    # names related to ids
    # Define min window size to be recognized as a face
    minW = 0.1 * cam.get(3)
    minH = 0.1 * cam.get(4)
    while True:
        ret, img = cam.read()
        file = open("names.txt", "r")
        names = file.read().split(' ')
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
                    if round(100-confidence) < 22:
                        idS = "Unknown"
                        id = -1
                    else:
                        idS = names[id]
                    confidence = "  {0}%".format(round(100 - confidence))
                except IndexError:
                    # if taught already, but not added to names.txt!!!
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
            '''
            if prev_id == id:
                # Check if confidence is less than 100 ==> "0" is perfect match
                if confidence < 100:
                    try:
                        """
                        if round(100-confidence) < 22:
                            idS = "Unknown"
                            id = -1
                        else:
                            idS = names[id]
                        """
                        idS = names[id]
                        confidence = "  {0}%".format(round(100 - confidence))
                    except IndexError:
                        # if taught already, but not added to names.txt!!!
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

            if prev_id == -1:
                prev_id = id
        '''
        cv2.imshow('JetsonFaceID Terminal', img)
        eq = np.array_equal([], faces)
        if (not eq) and idsnew != []:  # if any face exists and it is not the previous ones (all)
            cv2.imwrite("faces.png", img)
            # send message that we have found our face to notifier
            connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
            channel = connection.channel()
            channel.queue_declare(queue='hello')
            channel.queue_purge('hello')
            channel.basic_publish(exchange='',
                                  routing_key='hello',
                                  body=bytes(','.join(idsnew), encoding='utf8'))
            print("[INFO] Sent detected faces' data")
            print(" [IDS]: "+', '.join(idsnew))
            connection.close()

            connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
            channel = connection.channel()
            channel.queue_declare(queue='newcomers')
            channel.queue_purge('newcomers')
            newcomers_ids = []

            def callback(ch, method, properties, body):
                bd = int.from_bytes(body, sys.byteorder)
                print('[INFO] Acceptance from telegram received: %r' % bd)
                if bd != 0:
                    newcomers_ids.append(bd)
                if bd == 0:
                    print(" [STATUS] Person is known/shouldn't enter/Finished processing.")
                    print("[INFO] Closing connection with the queue...")
                    channel.queue_purge('newcomers')
                    raise IndentationError  # exiting

            channel.basic_consume(queue='newcomers', on_message_callback=callback, auto_ack=True)
            print('[INFO] Waiting for acceptance from telegram...')
            try:
                channel.start_consuming()
            except IndentationError:
                channel.queue_purge('newcomers')
                connection.close()

            if newcomers_ids:
                print("[INFO] Adding all the new faces")
                cam.release()
                cv2.destroyAllWindows()
                for newcomer in newcomers_ids:
                    add_face_to_dataset(newcomer)
                print("[INFO] Restarting JFID terminal...")
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
    # Do a bit of cleanup
    print("[INFO] Exiting Program and cleanup stuff")
    cam.release()
    cv2.destroyAllWindows()


def add_face_to_dataset(face_id):  # called only if it's a new person
    cam0 = cv2.VideoCapture(0)
    cam0.set(3, 640)  # set video width
    cam0.set(4, 480)  # set video height
    # For each person, enter one numeric face id
    print("[INFO] Initializing face capture ...")
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
                print("[INFO] Tried to add existing face")
                file = open("names.txt", "r")
                names = file.read().split(' ')
                names = names[:face_id]
                file.close()
                file = open("names.txt", "w")
                file.write(' '.join(names))
                file.close()
                cam0.release()
                cv2.destroyAllWindows()
                return

            cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
            count += 1
            # Save the captured image into the datasets folder
            cv2.imwrite("dataset/User." + str(face_id) + '.' + str(count) + ".jpg", gray[y:y + h, x:x + w])
        cv2.imshow('Face Detector', img)
        k = cv2.waitKey(100) & 0xff  # Press 'ESC' for exiting video
        if k == 27:
            break
        elif count >= 30:  # Take 30 face sample and stop video
            break
    # Do a bit of cleanup
    print("[INFO] Exiting Face Detector and cleaning up...")
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
    print("[INFO] Initializing face capture ...")
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
        elif count >= 30:  # Take 30 face sample and stop video
            break
    # Do a bit of cleanup
    print("[INFO] Exiting Face Detector and cleaning up...")
    cam0.release()
    cv2.destroyAllWindows()
    # train with the new face
    perform_training()


def perform_training():  # called if add_to_base was called
    path = 'dataset'

    # function to get the images and label data
    def get_images_and_labels(path):
        imagePaths = [os.path.join(path, f) for f in os.listdir(path)]
        faceSamples = []
        ids = []
        for imagePath in imagePaths:
            PIL_img = Image.open(imagePath).convert('L')  # convert it to grayscale
            img_numpy = np.array(PIL_img, 'uint8')
            id = int(os.path.split(imagePath)[-1].split(".")[1])
            faces = detector.detectMultiScale(img_numpy)
            for (x, y, w, h) in faces:
                faceSamples.append(img_numpy[y:y + h, x:x + w])
                ids.append(id)
        return faceSamples, ids

    print("[INFO] Training faces. It will take a few seconds. Wait ...")
    faces, ids = get_images_and_labels(path)
    recognizer.train(faces, np.array(ids))
    # Save the model into trainer/trainer.yml
    recognizer.write('trainer/trainer.yml')  # recognizer.save() worked on Mac, but not on Pi
    recognizer.save('trainer/trainer.yml')
    print("[INFO] Trainer.yml has been rewritten")
    # Print the number of faces trained and end program
    print("[INFO] {0} faces trained. Exiting Training".format(len(np.unique(ids))))


if __name__ == "__main__":
    queues_purge.qp()
    c = input("Is dataset ready?(Y/N) ")
    if c.lower() == "y":
        recognise()
    if c.lower() == "n":
        create_dataset()
