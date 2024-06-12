# EXPERIMENT #1: Adding with Hard Boundary Until Map is Full
import json
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

from utils import *

from gptutils import ChatGPT_request

from persona import Persona
from creator import Creator

N_TRIALS = 1
N_ACTIVITIES_AT_A_TIME = 20

BASE_MAP_JSON_FILEPATH = "data/base/json/base_map.json"

experiment1_dir = "data/experiment1"
os.makedirs(experiment1_dir, exist_ok=True)


def main():
    base_map = load_base_map()
    base_map["coordinates"] = [-100, -50, 100, 50]

    for i in range(N_TRIALS):
        persona = Persona()
        creator = Creator(persona.get_name(), base_map)

        # For each activity, the persona wants to do check if they can do it
        # on the current map, and if not, generate a new place and add it to
        # the map
        activity_count = 0
        activities_list = persona.generate_activities_batch(N_ACTIVITIES_AT_A_TIME)
        j = 0
        while True:
            activity_description = activities_list[j]
            
            # Increment and Cycle Counters
            j += 1
            if (j >= N_ACTIVITIES_AT_A_TIME):
                activities_list = persona.generate_activities_batch(N_ACTIVITIES_AT_A_TIME)
                j = 0
            activity_count += 1
            
            creator.set_persona_activity(activity_description)
            should_generate_new_place = creator.determine_new_place()

            if not should_generate_new_place:
                continue

            is_enough_space = creator.determine_enough_space()
            if not is_enough_space:
                print(f"Ran out of space after {activity_count} activities")
                break

            filepath = experiment1_dir + "/bounded_add_" + persona.get_name().lower().replace(" ", "_") + str(j)
            creator.add_place_bounded(filepath=filepath + ".json")

            creator.display_map(filepath=filepath + ".png")


# Returns the dict object of the base map json
def load_base_map():
    print("LOADING IN BASE MAP...")
    with open(BASE_MAP_JSON_FILEPATH) as f:
        map = json.load(f)
        print("LOADING COMPLETE")
        return map

main()