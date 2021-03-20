from datetime import date
from sqlalchemy.dialects import postgresql
from main.database.launch_db_session import Session, engine, Base
from sqlalchemy import Column, String, Integer, Date


class Employee(Base):
    __tablename__ = 'employees'

    id = Column(Integer, primary_key=True)
    thisis = Column(String)
    yo = Column(Integer)
    profession = Column(String)
    visits = Column(postgresql.ARRAY(Date))

    def __init__(self, thisis, yo, profession, visits):
        self.thisis = thisis
        self.yo = yo
        self.profession = profession
        self.visits = visits


def add(PD):
    Base.metadata.create_all(engine)
    # railes = Employee("Vladislav Railes", 16, "CEO", [date(2021, 10, 11)])
    Session.add(Employee(PD['thisis'], PD['y.o.'], PD['profession'], PD['visits']))
    Session.commit()
    Session.close()


def get(id):
    query = Session.query(Employee)
    return query.get(id)


def deleteall():
    Session.query(Employee).delete()
    Session.commit()


def get_all():
    emps = Session.query(Employee).all()
    return emps


def gat():
    emps = Session.query(Employee).all()
    print('\n### All employees:')
    for emp in emps:
        print(f'{emp.id} and {emp.thisis}, {emp.yo}, who is {emp.profession}, has visited building during {emp.visits}')


def convert_to_pd(obj):
    return {'thisis': obj.thisis, 'y.o.': obj.yo, 'profession': obj.profession, 'visits': obj.visits}


# deleteall()
# gat()
# print(get(2))
