import random
import time
import logging
import requests
import json


SESSION = requests.Session()
LOAD_MODEL = "https://results.chronotrack.com/embed/results/load-model"
INTERESTING_FIELDS = ["start_time", "location", "time_zone"]


def get_info(event_id: int):
    raw = SESSION.get(url=LOAD_MODEL, params={"modelID": "event", "eventID": event_id})
    info = json.loads(raw.text[1:-2])

    return {f: info["model"][f] for f in INTERESTING_FIELDS}


def main():
    with open("interesting_events.json", "r", newline="") as in_f:
        interesting_events = json.load(in_f)

    for event in interesting_events:
        try:
            logging.info(f"Looking at {event['name']}")
            event.update(get_info(event["event"]))
        except Exception:
            logging.exception(f"Skipping {event['name']}")

        to_sleep = random.uniform(0.03, 3.09)
        logging.debug(f"Snoozing for {to_sleep}s")
        time.sleep(to_sleep)

    logging.info("Writing output")
    with open("event_addendum.json", "w+", newline="") as out_f:
        json.dump(interesting_events, out_f)
    logging.info("Done!")


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s: %(message)s", level=logging.INFO
    )
    main()
