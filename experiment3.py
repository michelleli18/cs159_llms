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
    persona_name = "Bar" + str(n)
    base_map = {
                    "name": "Supply Store",
                    "coordinates": [
                        -13,
                        -10,
                        0,
                        0
                    ],
                }
    #{"name": "Town", "coordinates": [-50, -25, 50, 25]}
    c = Creator(persona_name, base_map)
    c.create_map()
    c.display_map()

main()