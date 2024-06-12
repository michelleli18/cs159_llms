# EXPERIMENT #2: Adding places for N activities with no boundaries
import json
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

from utils import *

from gptutils import ChatGPT_request

from persona import Persona
from creator import Creator

N_TRIALS = 1
N_ACTIVITIES_TOTAL = 10

BASE_MAP_JSON_FILEPATH = "data/base/json/base_map.json"

experiment2_dir = "data/experiment2"
os.makedirs(experiment2_dir, exist_ok=True)


def main():
    for i in range(N_TRIALS):
        persona = Persona()
        creator = Creator(persona.get_name(), load_base_map())

        # Sets bounds for the top level map incredibly large to simulate no bounds
        # Top level map is what ChatGPT sees, so changing only the top json has this effect
        creator.set_no_bounds() 

        # For each activity, the persona wants to do check if they can do it
        # on the current map, and if not, generate a new place and add it to
        # the map
        activities_list = persona.generate_activities_batch(N_ACTIVITIES_TOTAL)
        for j in range(N_ACTIVITIES_TOTAL):
            activity_description = activities_list[j]
            creator.set_persona_activity(activity_description)
            
            should_generate_new_place = creator.determine_new_place()

            if not should_generate_new_place:
                continue

            filepath = experiment2_dir + "/anywhere_add" + persona.get_name().lower().replace(" ", "_") + str(j)

            creator.add_place_anywhere(filepath=filepath + ".json")
            
            creator.display_map(filepath=filepath + ".png")


# Returns the dict object of the base map json
def load_base_map():
    print("LOADING IN BASE MAP...")
    with open(BASE_MAP_JSON_FILEPATH) as f:
        map = json.load(f)
        print("LOADING COMPLETE")
        return map


main()