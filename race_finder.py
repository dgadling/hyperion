import random
import time
import pickle
import os
import requests
import logging


SESSION = requests.Session()
REQ_TMP = "https://results.chronotrack.com/event/results/event/event-{event_id}"
STATE_FILE = "race_finder_state.pckl"
random.seed()


def get_ids(low=2900, high=46713):
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "rb") as state_f:
            return pickle.load(state_f)

    logging.info(f"Generating candidates from scratch between {low} and {high}")
    from_scratch = list(range(low, high + 1))
    put_ids(from_scratch)
    return from_scratch


def put_ids(ids):
    with open(STATE_FILE, "wb+") as state_f:
        logging.info(f"Save {len(ids)} ids to check in the future")
        pickle.dump(ids, state_f)


def save_winner(event_id):
    with open("winners.txt", "a+", newline='') as out_f:
        out_f.write(f"{event_id}\n")


def main():
    ids = get_ids()
    random.shuffle(ids)
    logging.info(f"Loaded up {len(ids)} candidates")

    processed = 0
    while ids:
        try:
            try:
                event_id = ids.pop()
                url = REQ_TMP.format(event_id=event_id)
                response = SESSION.get(url)
                processed += 1

                if response.status_code != 200:
                    logging.debug(f"Got a {response.status_code}, not 200 for {event_id}")
                    continue

                if "spartan" not in response.text.lower():
                    logging.debug(f"Didn't see 'spartan' in the response for {event_id}")
                    continue

                logging.info(f"Candidate: {url}")
                save_winner(event_id)
            except Exception:
                logging.exception(f"Putting {event_id} at the end of the list")
                ids.append(event_id)
            finally:
                event_id = None
                to_sleep = random.uniform(0.03, 3.09)
                logging.debug(f"Snoozing for {to_sleep}s")
                time.sleep(to_sleep)
        except KeyboardInterrupt:
            if event_id:
                logging.info(f"Saving {event_id} as unknown and exiting")
                ids.append(event_id)
            put_ids(ids)
            break
    if not ids:
        logging.info("RAN OUT OF IDS! WOOO!")


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s: %(message)s", level=logging.INFO
    )
    main()
