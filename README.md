# JetsonFaceID
Product for businesses and schools with easy-to-use face recognition, collecting statistical data about pupils'/employees' visits (in development now because I haven't managed with pandas yet). Works with telegram bot which provides admins with notifications.
This documentation is created in order to explain parts of code, especially its blocks and process division

Main: 
Facefinder, Processer, BotCommunicator are parallel processes that should be launched at the same time. Repository contains a bash launch.sh script that tries to do it, but it is not an ideal decision - programs are likely to be launched in separate windows, because they have their own consoles with output and some features as timestamps


Facefinder


This subprocess works with OpenCV and uses Haar Cascades. 

The structure of code is divided into four main functions: recognise(), add_face_to_dataset(), create_dataset() and perform_training()

create_dataset() takes 30 photos of face and adds it to /dataset/ directory and is used if there're no faces

add_face_to_dataset(face_id) does the same but checks if neural network has made an error and recognised a known person as unknown.

perform_training() overwrites the contents of trainer.yml that is used by predictor and uses /dataset/ directory

recognise() performs recognition and sends via rabbitmq server all ids of detected people (if unknown, id is -1)
when it receives answer (whether newcomer should enter or not), it saves new info and calls add_face_to_dataset() for all accepted guests

Issues:

Problems with recognising many people - when turning to training mode, only one face should be in the camera sight. So, there should be some limitations provided by companies that use this software.

Processer

This subprocess is responsible for notifications via telegram and communicates with botcommunicator and facefinder, making them all work as one whole system
TODO: adding new info to database

Botcommunicator

Performs replying to user's messages and handles commands

Purge_queues deletes all the odd info from queues from older sessions

Requirements can be found in requirements.txt

Db_table works as a library of functions that will be used by processer, botcommunicator and facefinder

UPD: Now takes 60 photos and works with docker postgresql database! The accuracy has been made higher and now there's an option of editing the database and sending the report photo
