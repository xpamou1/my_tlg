from peewee import *
from datetime import datetime

db = SqliteDatabase('people.db')


class MyModel(Model):
    class Meta:
        database = db


class Day(MyModel):
    chat_id = IntegerField()
    in_time = DateTimeField()
    out_time = DateTimeField()
    delta = BigIntegerField()


'''
class Person(MyModel):
    name = CharField()
    birthday = DateField(null=True)
    is_relative = BooleanField(default=True)

class Pet(MyModel):
    owner = ForeignKeyField(Person)
    name = CharField()
    animal_rype = CharField()
'''


def get_all_days_by_chat_id(chat_id):
    return Day.select().where(chat_id == Day.chat_id)


def dell_all(chat_id):
    query = Day.delete().where(Day.chat_id == chat_id)
    return query.execute()


def create_day(chat_id, in_time, out_time):
    delta = out_time - in_time
    new_day = Day.create(chat_id=chat_id, in_time=in_time, out_time=out_time, delta=(delta.total_seconds()))
    return new_day


def get_delta(day):
    assert type(day) == Day
    return day.delta


if __name__ == "__main__":
    try:
        Day.create_table()
    except Exception as e:
        print(e)
        print("hi")
