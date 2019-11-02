"""
Fetches results from chronotrack directly.
This seems to work pretty well, but it's a PITA.
I haven't found a way to discover the event, race, and bracket from athlinks or Spartan.
There doesn't seem to be any direct link from a spartan.com race to chronotrack results.

So I can only get data for races I've been to and show up in my Chronotrack results.
After that I have to inspect the chronotrack results page for those values.

Hopefully the next version will be able to do this via more direct linkage from a
spartan.com race to athlinks to chronotrack, or just directly to athlinks.
"""
from typing import Any, Dict, List, NamedTuple, Iterable

import csv
import json
import logging
import os
import random
import requests
import time


SESSION = requests.Session()


class RacerResult(NamedTuple):
    id: int
    rank: int
    name: str
    bib: str
    duration: int
    pace: str
    hometown: str
    age: int
    gender: str
    division: str
    division_rank: int

    @classmethod
    def build(cls, raw_input: List[Any]) -> "RacerResult":
        field_types = list(RacerResult.__annotations__.values())
        field_count = len(field_types)
        assert len(raw_input) == field_count, "lol what is this even?"

        raw_input[4] = sum(
            a * b for a, b in zip([3600, 60, 1], map(int, raw_input[4].split(":")))
        )
        try:
            return RacerResult(*[field_types[i](raw_input[i]) for i in range(field_count)])
        except ValueError:
            logging.exception(f"With input ->{raw_input}<-")
            raise

    @classmethod
    def columns(cls) -> List[str]:
        return list(cls.__annotations__.keys())

    def as_dict(self):
        return self._asdict()


def get_info(event_id: int, race_id: int, bracket_id: int, start: int, length: int):
    raw = SESSION.get(
        "https://results.chronotrack.com/embed/results/results-grid",
        params={
            "iDisplayStart": start,
            "iDisplayLength": length,
            "raceID": race_id,
            "bracketID": bracket_id,
            "eventID": event_id,
        },
    )
    return json.loads(raw.text[1:-2])


def get_batch(
    event_id: int, race_id: int, bracket_id: int, start: int, length: int
) -> Iterable[RacerResult]:
    return (
        RacerResult.build(record)
        for record in get_info(event_id, race_id, bracket_id, start, length)["aaData"]
    )


def get_metadata(event_id: int, race_id: int, bracket_id: int) -> Dict[str, int]:
    # NOTE: Have to fetch _at least_ one record
    info = get_info(event_id, race_id, bracket_id, 0, 1)
    return {"total_results": int(info["iTotalRecords"])}


def get_results(
    event_id: int,
    race_id: int,
    bracket_id: int,
    batch_size=500,
    min_sleep=0.0,
    max_sleep=1.0,
) -> List[RacerResult]:
    meta = get_metadata(event_id, race_id, bracket_id)
    results: List[RacerResult] = []

    start_positions = range(0, meta["total_results"], batch_size)
    sleeps = (random.uniform(min_sleep, max_sleep) for _ in start_positions)
    for start in start_positions:
        results.extend(get_batch(event_id, race_id, bracket_id, start, batch_size))
        to_sleep = next(sleeps)
        time.sleep(to_sleep)

    return results


races = [
    {
        "year": 2019,
        "venue": "lebec",
        "day": "saturday",
        "time": "morning",
        "kind": "beast",
        "heat": "elite",
        "event": 46713,
        "race": 118132,
        "bracket": 1285188,
    },
    {
        "year": 2019,
        "venue": "lebec",
        "day": "saturday",
        "time": "morning",
        "kind": "beast",
        "heat": "ag",
        "event": 46713,
        "race": 118133,
        "bracket": 1285191,
    },
    {
        "year": 2019,
        "venue": "lebec",
        "day": "saturday",
        "time": "morning",
        "kind": "beast",
        "heat": "open",
        "event": 46713,
        "race": 118134,
        "bracket": 1285206,
    },
    {
        "year": 2019,
        "venue": "seattle",
        "day": "saturday",
        "time": "morning",
        "kind": "beast",
        "heat": "elite",
        "event": 43572,
        "race": 109482,
        "bracket": 1188538,
    },
    {
        "year": 2019,
        "venue": "seattle",
        "day": "saturday",
        "time": "morning",
        "kind": "beast",
        "heat": "ag",
        "event": 43572,
        "race": 109483,
        "bracket": 1188541,
    },
    {
        "year": 2019,
        "venue": "seattle",
        "day": "saturday",
        "time": "morning",
        "kind": "beast",
        "heat": "open",
        "event": 43572,
        "race": 109484,
        "bracket": 1188556,
    },
    {
        "year": 2019,
        "venue": "hawaii",
        "day": "saturday",
        "time": "morning",
        "kind": "beast",
        "heat": "elite",
        "event": 45512,
        "race": 114773,
        "bracket": 1250136,
    },
    {
        "year": 2019,
        "venue": "hawaii",
        "day": "saturday",
        "time": "morning",
        "kind": "beast",
        "heat": "ag",
        "event": 45512,
        "race": 114774,
        "bracket": 1250139,
    },
    {
        "year": 2019,
        "venue": "hawaii",
        "day": "saturday",
        "time": "morning",
        "kind": "beast",
        "heat": "open",
        "event": 45512,
        "race": 114775,
        "bracket": 1250154,
    },
    {
        "year": 2019,
        "venue": "monterey",
        "day": "saturday",
        "time": "morning",
        "kind": "super",
        "event": 41665,
        "heat": "elite",
        "race": 104416,
        "bracket": 1132032,
    },
    {
        "year": 2019,
        "venue": "monterey",
        "day": "saturday",
        "time": "morning",
        "kind": "super",
        "event": 41665,
        "heat": "ag",
        "race": 104417,
        "bracket": 1132035,
    },
    {
        "year": 2019,
        "venue": "monterey",
        "day": "saturday",
        "time": "morning",
        "kind": "super",
        "event": 41665,
        "heat": "open",
        "race": 104418,
        "bracket": 1132038,
    },
    {
        "year": 2019,
        "venue": "big-bear",
        "day": "sunday",
        "time": "morning",
        "kind": "sprint",
        "event": 43269,
        "heat": "elite",
        "race": 108532,
        "bracket": 1178600,
    },
    {
        "year": 2019,
        "venue": "big-bear",
        "day": "sunday",
        "time": "morning",
        "kind": "sprint",
        "event": 43269,
        "heat": "ag",
        "race": 108533,
        "bracket": 1178603,
    },
    {
        "year": 2019,
        "venue": "big-bear",
        "day": "sunday",
        "time": "morning",
        "kind": "sprint",
        "event": 43269,
        "heat": "open",
        "race": 108534,
        "bracket": 1178618,
    },
    {
        "year": 2019,
        "venue": "san-jose",
        "day": "saturday",
        "time": "morning",
        "kind": "super",
        "event": 38970,
        "heat": "elite",
        "race": 97603,
        "bracket": 1054059,
    },
    {
        "year": 2019,
        "venue": "san-jose",
        "day": "saturday",
        "time": "morning",
        "kind": "super",
        "event": 38970,
        "heat": "ag",
        "race": 97604,
        "bracket": 1054062,
    },
    {
        "year": 2019,
        "venue": "san-jose",
        "day": "saturday",
        "time": "morning",
        "kind": "super",
        "event": 38970,
        "heat": "open",
        "race": 97605,
        "bracket": 1054065,
    },
    {
        "year": 2018,
        "venue": "att-park",
        "day": "saturday",
        "time": "morning",
        "kind": "stadium-sprint",
        "event": 36583,
        "heat": "elite",
        "race": 91892,
        "bracket": 997205,
    },
    {
        "year": 2018,
        "venue": "att-park",
        "day": "saturday",
        "time": "morning",
        "kind": "stadium-sprint",
        "event": 36583,
        "heat": "ag",
        "race": 91893,
        "bracket": 997212,
    },
    {
        "year": 2018,
        "venue": "att-park",
        "day": "saturday",
        "time": "morning",
        "kind": "stadium-sprint",
        "event": 36583,
        "heat": "open",
        "race": 91894,
        "bracket": 997243,
    },
    {
        "year": 2018,
        "venue": "lebec",
        "day": "saturday",
        "time": "morning",
        "kind": "beast",
        "event": 36347,
        "heat": "elite",
        "race": 91272,
        "bracket": 991307,
    },
    {
        "year": 2018,
        "venue": "lebec",
        "day": "saturday",
        "time": "morning",
        "kind": "beast",
        "event": 36347,
        "heat": "ag",
        "race": 91273,
        "bracket": 991312,
    },
    {
        "year": 2018,
        "venue": "lebec",
        "day": "saturday",
        "time": "morning",
        "kind": "beast",
        "event": 36347,
        "heat": "open",
        "race": 91274,
        "bracket": 991343,
    },
    {
        "year": 2018,
        "venue": "monterey",
        "day": "saturday",
        "time": "morning",
        "kind": "super",
        "event": 30838,
        "heat": "elite",
        "race": 76842,
        "bracket": 821687,
    },
    {
        "year": 2018,
        "venue": "monterey",
        "day": "saturday",
        "time": "morning",
        "kind": "super",
        "event": 30838,
        "heat": "ag",
        "race": 76843,
        "bracket": 821690,
    },
    {
        "year": 2018,
        "venue": "monterey",
        "day": "saturday",
        "time": "morning",
        "kind": "super",
        "event": 30838,
        "heat": "open",
        "race": 76844,
        "bracket": 821693,
    },
    {
        "year": 2018,
        "venue": "san-jose",
        "day": "sunday",
        "time": "morning",
        "kind": "sprint",
        "event": 29145,
        "heat": "elite",
        "race": 72646,
        "bracket": 769369,
    },
    {
        "year": 2018,
        "venue": "san-jose",
        "day": "sunday",
        "time": "morning",
        "kind": "sprint",
        "event": 29145,
        "heat": "ag",
        "race": 72647,
        "bracket": 769372,
    },
    {
        "year": 2018,
        "venue": "san-jose",
        "day": "sunday",
        "time": "morning",
        "kind": "sprint",
        "event": 29145,
        "heat": "open",
        "race": 72648,
        "bracket": 769375,
    },
    # {"year": , "venue": "", "day": "", "time": "", "kind": "", "event": , "heat": "elite", "race": , "bracket": },
    # {"year": , "venue": "", "day": "", "time": "", "kind": "", "event": , "heat": "ag",    "race": , "bracket": },
    # {"year": , "venue": "", "day": "", "time": "", "kind": "", "event": , "heat": "open",  "race": , "bracket": },
]


def main():
    filename_format = "{year}-{venue}-{day}-{time}-{heat}.csv"

    for race_info in races:
        filename = filename_format.format(**race_info)
        if os.path.exists(filename):
            logging.info(f"{filename} exists, skipping!")
            continue

        results = get_results(
            race_info["event"], race_info["race"], race_info["bracket"]
        )

        logging.info(f"Working on {filename}")
        with open(filename, "w", encoding="utf-8", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=RacerResult.columns())
            writer.writeheader()
            for row in results:
                try:
                    writer.writerow(row.as_dict())
                except Exception:
                    logging.exception(f"Issue with {row}")
                    raise
        logging.info("Done!")
    logging.info("Done with all races!")


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s: %(message)s", level=logging.INFO
    )
    main()
