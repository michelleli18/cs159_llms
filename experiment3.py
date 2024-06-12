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
                    "name": "Houses",
                    "coordinates": [
                        -42,
                        7,
                        -21,
                        17
                    ],
                }
    #{"name": "Town", "coordinates": [-50, -25, 50, 25]}
    c = Creator(persona_name, base_map)
    c.create_map()
    c.display_map()

main()