#!/usr/bin/env python3


from datetime import date
from peewee import *

db = SqliteDatabase("races.db")


class BaseModel(Model):
    class Meta:
        database = db

    def diff(self, other):
        assert self.__class__ == other.__class__, "Not even the same class?!"
        diffs = []
        for k, v in self._meta.fields.items():
            if k == "id":
                continue

            us = getattr(self, k)
            them = self._meta.fields[k].python_value(getattr(other, k))
            if us != them:
                diffs.append(
                    f"{self.__class__.__name__}(spartan_id={self.spartan_id})"
                    f".{k}: {getattr(self, k)} -> {getattr(other, k)}"
                )
        return ", ".join(diffs)


class Race(BaseModel):
    spartan_id = IntegerField()
    name = CharField()
    start_date = DateField()


class Event(BaseModel):
    spartan_id = IntegerField()
    # parent_race = ForeignKeyField(Race, backref='events')
    category = CharField()
    name = CharField()
    race_id = IntegerField()
    start_date = DateField(default=date.today())
    venue_name = CharField()


if __name__ == "__main__":
    db.connect()
    db.create_tables([Event, Race])
    db.close()
