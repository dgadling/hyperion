#!/usr/bin/env python3

import json
from datetime import datetime
import logging
import os

import requests


from typing import Dict

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


def fetch_raw_race_info(persist: bool = False, file_name: str = None) -> Dict:
    """
    Will fetch race info from spartan.com, unless file_name already exists, in which
    case that will be used. Any issues with that file will cause us to simply
    re-fetch from the internet.
    :param: persist: Should we try to load/save from some path?
    :param: file_name: If we should try to load/save, from where?
    :return: A dict of races and such
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

    r = requests.get("https://www.spartan.com/en/race/find-race", headers=headers)
    raw_lines = r.text.splitlines()

    for line in raw_lines:
        l = line.strip()
        if not l.startswith("window.races"):
            continue

        race_list = l[14:-1]  # 'window.races = ' to the ; at the end
        info = json.loads(race_list)
        break
    else:
        raise Exception("Couldn't find race list!")

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

    logging.info("Fetching data from Spartan")
    info = fetch_raw_race_info(persist=False, file_name="race_info.json")
    logging.info("Time to compare what we found!")

    for r in info:
        curr_race = Race(
            spartan_id=r["id"],
            name=r["event_name"],
            start_date=datetime.strptime(r["start_date"], "%Y-%m-%d").date(),
        )
        try:
            old_race = Race.get(spartan_id=r["id"])
            diff = old_race.diff(curr_race)
            if diff:
                logging.info(diff)
        except Race.DoesNotExist:
            curr_race.save()
            logging.info(f"Saved {curr_race.name}, adding specific events")

        for e in r["subevents"]:
            curr_event = Event(
                spartan_id=e["id"],
                # race=race,
                category=e["category"]["category_identifier"],
                name=e["event_name"],
                race_id=e["race_id"],
                start_date=datetime.strptime(e["start_date"], "%Y-%m-%d"),
                venue_name=e["venue"]["name"],
            )
            try:
                old_event = Event.get(spartan_id=e["id"])
                diff = old_event.diff(curr_event)
                if diff:
                    logging.info(diff)
            except Event.DoesNotExist:
                curr_event.save()
                logging.info(f"Saved {curr_event.name}!")
    logging.info("Done!")


if __name__ == "__main__":
    main()
