#!/usr/bin/env python3

import json
import logging
import os
from datetime import date, datetime
from typing import List

import requests

from models import Race, Event


def _load(file_name: str):
    if not os.path.exists(file_name):
        logging.info(f"Asked to use persisted info but didn't find it")
        raise FileNotFoundError()

    logging.info(f"Asked to use persisted stuff and found {file_name}!")
    with open(file_name) as in_f:
        return json.load(in_f)


def _save(file_name: str, info):
    try:
        with open(file_name, "w") as out_f:
            json.dump(info, out_f)
        logging.info(f"Persisted to {file_name}")
    except OSError:
        logging.exception(f"Couldn't persist to {file_name} but continuing")


def fetch_raw_race_info(persist: bool = False, file_name: str = None) -> List:
    """
    Will fetch race info from spartan.com, unless file_name already exists, in which
    case that will be used. Any issues with that file will cause us to simply
    re-fetch from the internet.
    :param: persist: Should we try to load/save from some path?
    :param: file_name: If we should try to load/save, from where?
    :return: A list of dicts of races
    """
    if persist:
        try:
            return _load(file_name)
        except Exception:
            logging.exception(f"Well that didn't work, fetching!")

    headers = {
        "referrer": "https://www.spartan.com/en/race/find-race",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        " (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36",
    }

    r = requests.get(
        "https://api2.spartan.com/api/races/upcoming_past_planned",
        params={
            "new_api": "yes",
            "plimit": 0,
            "ulimit": 500,
            "prlimit": 0,
            "units": "miles",
            "radius": 1000,
        },
        headers=headers,
    )

    info = json.loads(r.text)["upcoming"]

    if persist:
        _save(file_name, info)
    return info


def main():
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(module)s: %(message)s",
        level=logging.INFO,
    )

    logging.getLogger("chardet").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("peewee").setLevel(logging.WARNING)

    logging.debug("Fetching data from Spartan")
    info = fetch_raw_race_info(persist=False, file_name="race_info.json")
    logging.debug("Time to compare what we found!")

    for overall_event in info:
        venue_info = overall_event["venue"]
        curr_race = Race(
            spartan_id=overall_event["id"],
            name=overall_event["name"],
            start_date=datetime.strptime(
                overall_event["start_date"], "%Y-%m-%d"
            ).date(),
            venue_name=venue_info["name"],
            country=venue_info.get("country", "TBD"),
            region=venue_info.get("region", "TBD"),
            latitude=float(venue_info.get("latitude", "0.0")),
            longitude=float(venue_info.get("longitude", "0.0")),
        )
        try:
            old_race = Race.get(spartan_id=overall_event["id"])
            diff = old_race.diff(curr_race)
            if diff:
                logging.info(diff)
                curr_race.id = old_race.id
                curr_race.save()
        except Race.DoesNotExist:
            curr_race.save()
            logging.info(
                f"Saved {curr_race.name} ({curr_race.spartan_id}), "
                "adding specific events"
            )

        for e in overall_event["events"]:
            if "start_date" in e:
                start_date = datetime.strptime(e["start_date"], "%Y-%m-%d")
            else:
                start_date = date.today()

            # Fix up some poor quality data from Spartan
            try:
                category_key = (
                    "category_identifier"
                    if "category_identifier" in e["category"]
                    else "category_name"
                )
                curr_event = Event(
                    spartan_id=e["id"],
                    # race=race,
                    category=e["category"][category_key],
                    name=e["name"],
                    race_id=e["race_id"],
                    start_date=start_date,
                    venue_name=venue_info["name"],
                )
            except KeyError as ke:
                # Item #1 overall_event["venue"]["name"] is missing - id 20 = Red deer
                # Item #2 category_identifier missing for HH24HR
                logging.exception(
                    f"{ke}: event = {e} ; overall_event = {overall_event}"
                )
                continue

            try:
                old_event = Event.get(spartan_id=e["id"])
                diff = old_event.diff(curr_event)
                if diff:
                    logging.info(diff)
                    curr_event.id = old_event.id
                    curr_event.save()
            except Event.DoesNotExist:
                curr_event.save()
                logging.info(f"Saved {curr_event.name}!")
    logging.debug("Done!")


if __name__ == "__main__":
    main()
