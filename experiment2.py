# EXPERIMENT #2: Adding places for N activities with no boundaries
import json
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

from utils import *

from gptutils import ChatGPT_request

from persona import Persona
from creator import Creator

N_PERSONAS = 1
N_ACTIVITIES_TOTAL = 3

BASE_MAP_JSON_FILEPATH = "data/base/json/base_map.json"

experiment2_dir = "data/experiment2"
os.makedirs(experiment2_dir, exist_ok=True)


def main():
    for i in range(N_PERSONAS):
        persona = Persona()
        creator = Creator(persona.get_name(), load_base_map())

        # Sets bounds for the top level map incredibly large to simulate no bounds
        # Top level map is what ChatGPT sees, so changing only the top json has this effect
        creator.set_no_bounds() 

        # Make info dictionary
        info = dict()
        info["experiment"] = "2"
        info["persona name"] = persona.get_name()
        info["description"] = persona.get_description()
        info["set number of activities"] = N_ACTIVITIES_TOTAL
        info["activities"] = []

        # For each activity, the persona wants to do check if they can do it
        # on the current map, and if not, generate a new place and add it to
        # the map
        activities_list = persona.generate_activities_batch(N_ACTIVITIES_TOTAL)
        for j in range(N_ACTIVITIES_TOTAL):
            activity_info = dict()
            info["activities"].append(activity_info)

            activity_desc = activities_list[j]
            activity_info["description"] = str(activity_desc)
            creator.set_persona_activity(activity_desc)
            print("ACTIVITY DESCRIPTION FOR " + info["persona name"] + "...")
            print(str(activity_desc))
            
            new_place = creator.determine_new_place()
            should_generate_new_place = new_place != None
            activity_info["should generate a new place"] = should_generate_new_place

            if not should_generate_new_place:
                continue

            activity_info["new place"] = new_place

            # Save intermediate files
            filepath = experiment2_dir + "/anywhere_add_" + persona.get_name().lower().replace(" ", "_") + "_" + str(j)

            with open(filepath + "_info.json", 'w') as f:
                json.dump(info, f, indent=4)

            creator.add_place_anywhere(filepath=filepath + "_map.json")
            
            creator.display_map(filepath=filepath + "_map.png")

        # Save final files
        filepath = experiment2_dir + "/anywhere_add_" + persona.get_name().lower().replace(" ", "_") + "_final"

        with open(filepath + "_info.json", 'w') as f:
            json.dump(info, f, indent=4)
            
        map_copy_json = creator.get_json_map_copy()
        with open(filepath + "_map.json", 'w') as f:
            json.dump(map_copy_json, f, indent=4)

        creator.display_map(filepath=filepath + "_map.png")


# Returns the dict object of the base map json
def load_base_map():
    print("LOADING IN BASE MAP...")
    with open(BASE_MAP_JSON_FILEPATH) as f:
        map = json.load(f)
        print("LOADING COMPLETE")
        return map


main()