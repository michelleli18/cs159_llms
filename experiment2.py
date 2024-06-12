import json
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

from utils import *

from gptutils import ChatGPT_request

from persona import Persona
from creator import Creator

N_TRIALS = 3
N_ACTIVITIES = 5

BASE_MAP_JSON_FILEPATH = "data/base/json/base_map.json"

def main():
    for i in range(N_TRIALS):
        persona = Persona()
        creator = Creator(persona.get_name(), load_base_map())

        # For each activity, the persona wants to do check if they can do it
        # on the current map, and if not, generate a new place and add it to
        # the map
        activities_list = persona.generate_activities_batch(N_ACTIVITIES)
        for j in range(N_ACTIVITIES):
            activity_description = activities_list[j]
            creator.set_persona_activity(activity_description)
            should_generate_new_place = creator.determine_new_place()
            if should_generate_new_place:
                set filepath to experiments folder
                creator.add_place_anywhere(save=True, filepath='dclksmclksdc sdlkc 
                                           include_reasoning=True)
                # MAKE SURE TO INCLUDE REASSONING -> Set reasoning to true
        
            
            




# Returns the dict object of the base map json
def load_base_map():
    with open(BASE_MAP_JSON_FILEPATH) as f:
        return json.load(f)

def town(n):
    persona_name = "Base1" + str(n)
    base_map = {
                    "name": "Grocery and Pharmacy",
                    "coordinates": [
                        2,
                        -9,
                        18,
                        1
                    ],
                }
    #{"name": "Town", "coordinates": [-50, -25, 50, 25]}
    c = Creator(persona_name, base_map)
    c.create_map()
    c.display_map()

main()