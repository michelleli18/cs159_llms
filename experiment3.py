import json
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

from utils import *

from gptutils import ChatGPT_request

from creator import Creator

def main():
    town(1)

def town(n):
    persona_name = "Base1" + str(n)
    base_map = {
                    "name": "Apartments 2",
                    "coordinates": [
                        10,
                        6,
                        22,
                        24
                    ],
                }
    #{"name": "Town", "coordinates": [-50, -25, 50, 25]}
    c = Creator(persona_name, base_map)
    c.create_map()
    c.display_map()

main()