#!/usr/bin/env python3


from peewee import *

db = SqliteDatabase("races.db")


class Race(Model):
    spartan_id = IntegerField()
    name = CharField()
    start_date = DateField()

    class Meta:
        database = db


class Event(Model):
    spartan_id = IntegerField()
    # parent_race = ForeignKeyField(Race, backref='events')
    category = CharField()
    name = CharField()
    race_id = IntegerField()
    start_date = DateField()
    venue_name = CharField()

    class Meta:
        database = db


if __name__ == "__main__":
    db.connect()
    db.create_tables([Event, Race])
    db.close()
