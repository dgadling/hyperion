import json
import logging
import os


def main():
    interesting_events = []

    raw_dir = "raw_event_results"
    for f in os.listdir(raw_dir):
        if not f.endswith(".json"):
            continue

        with open(os.path.join(raw_dir, f), "r", newline="") as in_f:
            info = json.load(in_f)
            if not info["races"]:
                continue

            logging.info(f"Found {info['name']} with {len(info['races'])} races!")
            interesting_events.append(info)
    logging.info(f"Found {len(interesting_events)} interesting events, persisting.")
    with open("interesting_events.json", "w+", newline="") as out_f:
        json.dump(interesting_events, out_f)


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s: %(message)s", level=logging.INFO
    )
    main()
