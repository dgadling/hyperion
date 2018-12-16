#!/usr/bin/env python3


class Event:
    id: int
    category: str
    name: str
    status: str
    is_active: str
    race_id: str
    racedate_desc: str
    reg_url: str
    start_date: str

    def __init__(self, *args, **kwargs):
        self.id = kwargs["id"]
        self.category = kwargs["category"]
        self.name = kwargs["event_name"]
        self.status = kwargs["event_status"]
        self.is_active = kwargs["is_active"]
        self.race_id = kwargs["race_id"]
        self.racedate_desc = kwargs["racedate_desc"]
        self.reg_url = kwargs["reg_url"]
        self.start_date = kwargs["start_date"]

    def __str__(self):
        return f"Event({self.id}, {self.name}, {self.status})"


class Race:
    id: int
    name: str
    venue: str
    start_date: str

    def __init__(self, *args, **kwargs):
        self.id = int(kwargs["id"])
        self.name = kwargs["event_name"]
        self.start_date = kwargs["start_date"]
        self.subevents = [Event(**e) for e in kwargs["subevents"]]

    def __str__(self):
        return f"Race({self.id}, {self.name}, {self.start_date})"
