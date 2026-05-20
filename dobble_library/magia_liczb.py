import json
import random

with open("models_55.json", "r") as file:
    models_json = json.load(file)
    for model in models_json["models"]:
        for symbol in model["rects"]:
            ang_deg = symbol["ang_deg"]
            if ang_deg >= 180:
                continue
            if random.randint(0, 1) == 0:
                symbol["ang_deg"] += 180

    with open("models_55_v2.json", "w") as file:
        file.write(json.dumps(models_json))
