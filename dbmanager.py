#                                            DBMANAGER
# -----------------------------------------------------------------------------------------------------------
# works with database and performs I/O operations and collects statistical data

import sqlite3
import datetime

connection = sqlite3.connect("db.sqlite")
crsr = connection.cursor()


def create_table():
    sql_cmd = """CREATE TABLE new (
                 id INTEGER PRIMARY KEY,
                 name VARCHAR(50),
                 yo INTEGER,
                 profession VARCHAR(50),
                 visits DATE);"""
    crsr.execute(sql_cmd)


def insert_data(dct):
    sql_cmd = """INSERT INTO emp VALUES (35, “Andrey”, “AndreyEx”, “M”, “1979-05-16″);"""
    crsr.execute(sql_cmd)


def export():
    crsr.execute("SELECT * FROM emp")
    ans = crsr.fetchall()
    for i in ans:
        print(i)


def upd():
    connection.execute("UPDATE Student SET name = ‘AndreyEx’ where unix=’B27652′")
    connection.commit()
    print("Общее количество обновленных строк :", connection.total_changes)
    cursor = connection.execute("SELECT * FROM Student")
    for row in cursor:
        print(row, end=',')


create_table()
connection.commit()
connection.close()
'''
x = datetime.datetime.now()
PersonData={'id': 1, 'name': 'Railes', 'y.o.': 16, 'profession': 'CEO', 'visits': []}
insert_data(PersonData)
sql_cmd = """INSERT INTO emp VALUES (11, “Alex”, “Copper”, “M”, “1982-12-34″);"""
crsr.execute(sql_cmd)
connection.commit()
connection.close()
'''
