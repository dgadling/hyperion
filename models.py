#!/usr/bin/env python3


from datetime import date

import playhouse.migrate as migrate
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
                    f"{self.__class__.__name__}(name={self.name})"
                    f".{k}: {getattr(self, k)} -> {getattr(other, k)}"
                )
        return ", ".join(diffs)


class Race(BaseModel):
    spartan_id = IntegerField()
    name = CharField()
    start_date = DateField()
    venue_name = CharField()
    country = CharField()
    region = CharField()
    latitude = DoubleField()
    longitude = DoubleField()


class Event(BaseModel):
    spartan_id = IntegerField()
    # parent_race = ForeignKeyField(Race, backref='events')
    category = CharField()
    name = CharField()
    race_id = IntegerField()
    start_date = DateField(default=date.today())
    venue_name = CharField()


def init_db():
    db.connect()
    db.create_tables([Event, Race])
    db.close()


def extended_location_migration():
    migrator = migrate.SqliteMigrator(db)
    venue_name = CharField(default='TBD')
    country = CharField(default='TBD')
    region = CharField(default='TBD')
    latitude = DoubleField(default=0.0)
    longitude = DoubleField(default=0.0)
    with db.atomic():
        migrate.migrate(
            migrator.add_column('race', 'venue_name', venue_name),
            migrator.add_column('race', 'country', country),
            migrator.add_column('race', 'region', region),
            migrator.add_column('race', 'latitude', latitude),
            migrator.add_column('race', 'longitude', longitude),
        )


if __name__ == "__main__":
    print("Update me with what you want to do!")
