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
            return RacerResult(
                *[field_types[i](raw_input[i]) for i in range(field_count)]
            )
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
    min_sleep=0.03,
    max_sleep=3.09,
) -> List[RacerResult]:
    meta = get_metadata(event_id, race_id, bracket_id)
    logging.info(f"  Have {meta['total_results']:,} results to fetch")
    results: List[RacerResult] = []

    start_positions = range(0, meta["total_results"], batch_size)
    sleeps = (random.uniform(min_sleep, max_sleep) for _ in start_positions)
    for start in start_positions:
        results.extend(get_batch(event_id, race_id, bracket_id, start, batch_size))
        to_sleep = next(sleeps)
        time.sleep(to_sleep)

    return results


def main():
    filename_format = "{event_id}-{race_id}-{bracket_id}.csv"
    output_dir = "race-results"
    skipped_events = []

    with open("interesting_events.json", "r", newline="") as in_f:
        interesting_events = json.load(in_f)

    for event_info in interesting_events:
        if not isinstance(event_info["year"], int):
            logging.warning(
                f"{event_info['event']} has non-int year {event_info['year']}"
            )
            skipped_events.append(event_info)
            continue

        year_dir = os.path.join(output_dir, str(event_info["year"]))
        if not os.path.exists(year_dir):
            logging.info(f"Creating {year_dir}")
            os.mkdir(year_dir)

        logging.info(f"Looking at {event_info['year']} {event_info['name']}")
        for race_info in event_info["races"]:
            filename = os.path.join(year_dir, filename_format.format(**race_info))
            if os.path.exists(filename):
                logging.info(f"  {filename} exists, skipping!")
                continue

            try:
                results = get_results(
                    race_info["event_id"], race_info["race_id"], race_info["bracket_id"]
                )
            except Exception:
                logging.exception(
                    f"  Skipping {race_info['race_id']}|{race_info['bracket_id']}"
                )
                continue

            logging.info(f"  Writing to {filename}")
            with open(filename, "w", encoding="utf-8", newline="") as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=RacerResult.columns())
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
