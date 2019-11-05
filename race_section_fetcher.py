import requests
import json


SESSION = requests.Session()
LOAD_MODEL = "https://results.chronotrack.com/embed/results/load-model"


event_id = 46713
raw = SESSION.get(
    url=LOAD_MODEL,
    params={
        'modelID': 'event',
        'eventID': event_id
    }
)

info = json.loads(raw.text[1:-2])
print(f"{info['model']['name']} - started {info['model']['start_time']}")
for race_id, race_info in info['model']['races'].items():
    race_name = race_info['name']
    bracket_id = race_info['default_bracket_id']
    print(f"event {event_id} race {race_name} ({race_id}), bracket {bracket_id}")
