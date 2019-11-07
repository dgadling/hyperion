from datetime import datetime
import random
import time
import logging
import requests
import json
import os


SESSION = requests.Session()
LOAD_MODEL = "https://results.chronotrack.com/embed/results/load-model"


def get_info(event_id: int):
    raw = SESSION.get(
        url=LOAD_MODEL,
        params={
            'modelID': 'event',
            'eventID': event_id
        }
    )
    info = json.loads(raw.text[1:-2])

    results = {
        "event": event_id,
        "name": info['model']['name'].split("-")[0].strip(),
        "races": [],
    }

    try:
        event_time = datetime.strptime(info['model']['start_time'], "%b %d, %Y %I:%M%p")
        results["year"] = event_time.year
        results["date"] = event_time.strftime("%Y-%m-%d")
    except ValueError:
        try:
            event_time = datetime.strptime(info['model']['start_time'], "%d %b, %Y %I:%M%p")
            results["year"] = event_time.year
            results["date"] = event_time.strftime("%Y-%m-%d")
        except ValueError:
            logging.exception(f"Bad date format ({info['model']['start_time']}), fall back")
            results["year"] = info['model']['start_time']
            results["date"] = info['model']['start_time']

    if 'races' not in info['model'].keys():
        return results

    if not info['model']['races']:
        return results

    for race_id, race_info in info['model']['races'].items():
        if " - " in race_info['name']:
            heat = race_info['name'].split(' - ')[1].lower()
        else:
            heat = race_info['name']

        results['races'].append({
            "event_id": event_id,
            "race_id": int(race_id),
            "bracket_id": int(race_info['default_bracket_id']),
            "heat": heat,
        })

    return results


def main():
    output_dir = "raw_event_results"
    if not os.path.exists(output_dir):
        logging.error(f"Couldn't find output_dir ({output_dir}), giving up!")
        return

    with open("winners.txt", "r", newline="") as in_f:
        for event_id_str in in_f:
            event_id_str = event_id_str.strip()
            info_f_path = os.path.join(output_dir, f"{event_id_str}.json")
            if os.path.exists(info_f_path):
                logging.debug(f"Skipping {event_id_str}, {info_f_path} exists")
                continue

            logging.info(f"Getting info for {event_id_str}")
            try:
                info = get_info(int(event_id_str))
            except Exception:
                logging.exception(f"Skipping {event_id_str}")
                continue

            with open(info_f_path, "w", newline="") as out_f:
                logging.info("Writing out results")
                json.dump(info, out_f)

            to_sleep = random.uniform(0.03, 3.09)
            logging.debug(f"Snoozing for {to_sleep}s")
            time.sleep(to_sleep)


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s: %(message)s", level=logging.INFO
    )
    main()
