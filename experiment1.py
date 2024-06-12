# EXPERIMENT #1: Adding with Hard Boundary Until Map is Full
import json
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

from utils import *

from gptutils import ChatGPT_request

from persona import Persona
from creator import Creator

N_PERSONAS = 1
N_ACTIVITIES_AT_A_TIME = 20

BASE_MAP_JSON_FILEPATH = "data/base/json/base_map.json"

experiment1_dir = "data/experiment1"
os.makedirs(experiment1_dir, exist_ok=True)


def main():
    base_map = load_base_map()
    base_map["coordinates"] = [-100, -50, 100, 50]

    for i in range(N_PERSONAS):
        persona = Persona()
        creator = Creator(persona.get_name(), base_map)

        # Make info dictionary
        info = dict()
        info["experiment"] = "1"
        info["persona name"] = persona.get_name()
        info["description"] = persona.get_description()
        info["activities"] = []
        
        # For each activity, the persona wants to do check if they can do it
        # on the current map, and if not, generate a new place and add it to
        # the map
        activity_count = 0
        activities_list = persona.generate_activities_batch(N_ACTIVITIES_AT_A_TIME)
        j = 0
        while True:
            activity_info = dict()

            activity_desc = activities_list[j]
            activity_info["description"] = activity_desc
            creator.set_persona_activity(activity_desc)
            
            # Increment and Cycle Counters
            j += 1
            if (j >= N_ACTIVITIES_AT_A_TIME):
                activities_list = persona.generate_activities_batch(N_ACTIVITIES_AT_A_TIME)
                j = 0
            activity_count += 1
            
            
            new_place = creator.determine_new_place()
            should_generate_new_place = new_place != None
            activity_info["should generate a new place"] = should_generate_new_place

            if not should_generate_new_place:
                continue

            activity_info["new place"] = new_place

            is_enough_space = creator.determine_enough_space()
            activity_info["is there enough space"] = is_enough_space

            if not is_enough_space:
                print(f"Ran out of space after {activity_count} activities")
                break

            info["activities"].append(activity_info)

            # Save files
            filepath = experiment1_dir + "/bounded_add_" + persona.get_name().lower().replace(" ", "_") + "_" + str(j)
            
            with open(filepath + "_info.json", 'w') as f:
                json.dump(info, f, indent=4)

            # Also updates the map
            creator.add_place_bounded(filepath=filepath + "_map.json")

            creator.display_map(filepath=filepath + "_map.png")


# Returns the dict object of the base map json
def load_base_map():
    print("LOADING IN BASE MAP...")
    with open(BASE_MAP_JSON_FILEPATH) as f:
        map = json.load(f)
        print("LOADING COMPLETE")
        return map

main()