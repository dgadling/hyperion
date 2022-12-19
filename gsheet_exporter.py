#!/usr/bin/env python3

import itertools
import os.path
import re
from datetime import date
from typing import List

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from models import Event, Race


class EventRow:
    EVENT_CATEGORY_REPLACEMENTS = {
        "hurricane-heat": "hh_4",
        "spartanhh12hr": "hh_12",
        "spartansprint": "sprint",
        "spartansuper": "super",
        "spartanbeast": "beast",
        "spartanultra": "ultra",
        "spartankids": "kids",
        "trail_10k": "trail_10k",
        "trail_21k": "trail_21k",
        "trail_50k": "trail_50k",
        "trail_100k": "trail_100k",
        "stadion": "stadion",
        "city": "city",
    }

    IGNORED_CATEGORIES = {
        "ultratrifectapass",
        "trifectapass",
        "charitychallenge",
        "spartancombo",
        "teams",
    }

    NAME_FRAGMENTS_TO_DELETE = [
        "Spartan",
        "Super",
        "Sprint",
        "5K",
        "5k",
        "10K",
        "10k",
        "21K",
        "21k",
        "50K",
        "50k",
        "HH",
        "HURRICANE HEAT",
        "Kids",
        "KIDS",
        "Race",
        "Weekend",
        " And",
        " &",
        " and",
        "2023",
        "Half Marathon",
        "Stadion",
        "Charity",
        "Event",
        "/",
        " ,",
    ]

    def __init__(
            self, race: Race, events: List[Event], normalize_race_name=False
    ) -> None:
        self.start_date = race.start_date
        self.name = race.name
        self.event_id = race.spartan_id
        self.event_link = (
            f"https://race.spartan.com/en/race/detail/{race.spartan_id}/overview"
        )
        self.venue_name = race.venue_name
        self.country = race.country
        self.region = race.region
        self.latitude = race.latitude
        self.longitude = race.longitude

        if normalize_race_name:
            self.name = self.normalize_race_name(race.name)
        self.set_categories(events)

    def __repr__(self) -> str:
        attrs = (
            k
            for k in self.__dict__.keys()
            if k.startswith("__") is False
               and k not in ["name", "start_date", "venue_name", "event_id",
                             "event_link"]
        )
        attr_strs = [f"{attr}={getattr(self, attr)}" for attr in sorted(attrs)]
        return (
            f'EventRow(start_date="{self.start_date}", name="{self.name}", '
            f'event_id={self.event_id}, venue_name="{self.venue_name}", '
            f'{", ".join(attr_strs)}, event_link={self.event_link})'
        )

    def normalize_race_name(self, race_name: str) -> str:
        for fragment in self.NAME_FRAGMENTS_TO_DELETE:
            race_name = race_name.replace(fragment, "")

        # Some events have their types mashed/together/like/so
        race_name = re.sub(r" (\w+/)+\w+ ", "", race_name)
        # Some throw the dates in
        race_name = re.sub(r"[a-zA-Z]+ \d+-\d+", "", race_name)
        # Remove duplicated words!
        race_name = re.sub(r"\b(\w+)( +\1\b)+", r"\1", race_name)

        # Collapse spaces
        race_name = re.sub(r"\s+", " ", race_name)

        # trim up any leading/trailing whitespace
        race_name = race_name.strip()
        return race_name

    def set_categories(self, events: List[Event]) -> None:
        event_categories = [
            e.category for e in events if e.category not in self.IGNORED_CATEGORIES
        ]
        unknown_categories = set(event_categories) - set(
            self.EVENT_CATEGORY_REPLACEMENTS.keys()
        )
        if unknown_categories:
            raise Exception(f"idk how to handle {unknown_categories} categories")

        for category in self.EVENT_CATEGORY_REPLACEMENTS.values():
            setattr(self, category, False)

        for category in event_categories:
            setattr(self, self.EVENT_CATEGORY_REPLACEMENTS[category], True)

    RACE_ORDER = [
        "kids",
        "stadion",
        "sprint",
        "super",
        "beast",
        "ultra",
        "city",
        "hh_4",
        "hh_12",
        "trail_10k",
        "trail_21k",
        "trail_50k",
        "trail_100k",
    ]

    def meta_to_sheet_row(self):
        return [
            self.start_date.strftime("%Y-%m-%d"),
            f'=HYPERLINK("{self.event_link}", "{self.name}")',
            self.venue_name,
            self.country,
            self.region,
        ]

    def date_and_location_row(self):
        return [
            self.start_date.strftime("%Y-%m-%d"),
            f'=HYPERLINK("{self.event_link}", "{self.name}")',
        ]

    def country_region_row(self):
        return [
            self.venue_name,
            self.country,
            self.region,
        ]

    @staticmethod
    def _generate_update_cells_request(row_index: int, column_index: int):
        return {
            "updateCells": {
                "rows": [
                    {
                        "values": [
                            {
                                "dataValidation": {"condition": {"type": "BOOLEAN"}},
                            }
                        ],
                    }
                ],
                "fields": "dataValidation",
                "start": {
                    "sheetId": 0,
                    "rowIndex": row_index,
                    "columnIndex": column_index,
                },
            }
        }

    def races_to_sheet_row(self, row_index: int):
        return [
            self._generate_update_cells_request(row_index, 2 + idx)
            for idx, field in enumerate(self.RACE_ORDER)
            if getattr(self, field)
        ]


def create(title, creds):
    """
    Creates a Sheet the user has access to.
    """
    try:
        service = build("sheets", "v4", credentials=creds)
        spreadsheet = {"properties": {"title": title}}
        spreadsheet = (
            service.spreadsheets()
            .create(body=spreadsheet, fields="spreadsheetId")
            .execute()
        )
        print(f"Spreadsheet ID: {(spreadsheet.get('spreadsheetId'))}")
        return spreadsheet.get("spreadsheetId")
    except HttpError as error:
        print(f"An error occurred: {error}")
        raise error


def handle_creds() -> Credentials:
    """
    Figures out Oauth2 credentials either by loading them from a local token.json file,
    or using credentials.json to prompt the user for the details to store in token.json.

    :return: google.oauth2.credentials.Credentials
    """
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", scopes)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", scopes)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return creds


def get_event_rows(starting_on_or_after: date) -> List[EventRow]:
    """
    Queries the local db for `Race` objects, then again for the associated
    `Event` objects.

    These are combined into `EventRow` objects.
    """
    races = (
        Race.select()
        .where(Race.start_date >= starting_on_or_after)
        .order_by(Race.start_date)
    )

    return [
        EventRow(race, Event.select().where(Event.race_id == race.spartan_id))
        for race in races
    ]


def set_location_info(creds, sheet_id, events: List[EventRow]) -> None:
    """
    Sets the event date, name, and location info (venue/country/region)
    """
    try:
        service = build("sheets", "v4", credentials=creds)
        range_name = f"A4:B{len(events) + 3}"
        body = {"values": [event_row.date_and_location_row() for event_row in events]}
        (
            service.spreadsheets()
            .values()
            .update(
                spreadsheetId=sheet_id,
                range=range_name,
                valueInputOption="USER_ENTERED",
                body=body,
            )
            .execute()
        )
        range_name = f"P4:R{len(events) + 3}"
        body = {"values": [event_row.country_region_row() for event_row in events]}
        (
            service.spreadsheets()
            .values()
            .update(
                spreadsheetId=sheet_id,
                range=range_name,
                valueInputOption="USER_ENTERED",
                body=body,
            )
            .execute()
        )
    except HttpError as error:
        print(f"An error occurred: {error}")


def set_race_info(creds, sheet_id, events: List[EventRow]) -> None:
    all_requests = [
        event.races_to_sheet_row(3 + idx) for idx, event in enumerate(events)
    ]
    flat_requests = list(itertools.chain(*all_requests))
    try:
        service = build("sheets", "v4", credentials=creds)
        (
            service.spreadsheets()
            .batchUpdate(
                body={"requests": flat_requests},
                spreadsheetId=sheet_id,
            )
            .execute()
        )
    except HttpError as error:
        print(f"An error occurred: {error}")


def update_sheet(creds, sheet_id, events: List[EventRow]) -> None:
    print("Setting location info")
    set_location_info(creds, sheet_id, events)
    print("Race specific info")
    set_race_info(creds, sheet_id, events)


def main():
    event_rows = get_event_rows(starting_on_or_after=date(2023, 1, 1))
    print(f"Found {len(event_rows)} events")

    update_sheet(
        handle_creds(), "15Tx_2Kqyg2Ir_HIkLPlzibfA9PmA_lkiazRLmPxMRiU", event_rows
    )


if __name__ == "__main__":
    main()
