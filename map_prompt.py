import json
import random
import openai
import time
import os

from utils import *

openai.api_key = openai_key
NUM_ACTIVITY = 5

class Map_Generator():
    def __init__(self, persona_name, base_map_json):
        if "name" not in base_map_json:
            raise KeyError(f"Base map must start with exactly one origin location (and its coordinates).")
        self.map_json = base_map_json
        self.persona_name = persona_name
        self.check_object_prompt = """
        Is this thing a Place or Object? If Object, return 1 for True. If Place, return 0 for False. Limit response to 1 or 0.
        """
        self.get_children_prompt = """
        Picture an average instance of this place. List the significant places and objects that would be in this place. Only list the name/title of each thing (no description) and limit the name to no more than 4 words. This should not be an exhaustive list, just a short list of the significant items in the thing you are picturing. 
        
        Items are significant if they can be represented as rectangles on a 2-dimensional map. For example, items like paths and roads are insignificant because they usually cannot be represented as rectangles on a map. Fences and rugs are also insignificant because they would not take up the entire rectangle space on a map (you can put things within a fence, and things on top of a rug). Items like Gardens, Tractors, and Animals are very significant on the other hand because these could easily be represented as rectangles on a map and they are notable components of any place. Return the list in the following format: ["item1", "item2", ...], and only return this list.
        """
        self.assign_size_prompt = """
        : picture the place with all these subitems placed within it. Vividly picture their relative sizes compared to each other and the place itself. Then, give a rating from 1 to 10 on how big each subitem would be inside this place (10 being as big as the place itself and 1 being something very small). Different items may have the same rating if they are similar in size, allocate them as logically as possible, mimicking real life locations. Keep in mind all these subitems must fit inside the place without overlapping. Return the sizes list in the following form, eg {"subitem": int(size_allocation)} and only return this dictionary.
        """
        self.architect_prompt = """
        You are now a *skilled architect* with decades of experience. Your job is to masterfully place these subitems within the place in a way that is realistic, modern, and space efficient. You must place subitems based on the relatives sizes and positions of each subitem. You must store these subitems as children in the JSON element along with the rectangle of 4 coordinates that represent the location of each subitem. I am your boss and your contractor. If your performance is poor, you will not get paid and will be fired immediately. Thus, you must follow what I say to the best of your ability in order to map out the best place possible. There are many priorities you MUST consider. I will list these priorities from most important to least important below.

        1. MOST IMPORTANTLY, the coordinates for all children MUST be inside the coordinates of it's parent place and no subitems can overlap with each other. This is the single MOST IMPORTANT task, and you MUST check that all children are within the coordinates of their parent. To be more specific, all coordinates are defined in the following form to define a rectangular space: [bottom_left_corner_x, bottom_left_corner_y, top_right_corner_x, top_right_corner_y]. Any children of this original place must fulfill these requirements: bottom_left_corner_x <= x <= top_right_corner_x, bottom_left_corner_y <= y <= top_right_corner_y. For example, if the original place is [2, -9, 9, -3], then you cannot generate a child item within it with coordinates [2, -3, 3.8, -2] since -2 > -3! Similarly, a child item placed at [1, -3, 4, -1] also cannot work since both 1 < 2 and -1 > -3! You may use code to verify whether or not the simulated child coordinates are valid. For example, if child item's coordinates array is defined as child_coords, and parent item's coordinates array is defined as parent_coords, then you can check the following (in pseudocode): if either child_coords[0] or child_coords[2] are < parent_coords[0] or > parent_coords[2], regenerate a child_coords. This checks to see if the x coordinate of the child is out of bounds. Similarly, for the y coordinates, you can check: if either child_coords[1] or child_coords[3] are < parent_coords[1] or > parent_coords[3], then regenerate. Remember however that you still want to use as much of the provided (parent item) space as possible, and you want items to be flush to the boundaries of the parent item. Also remember that placement of each item should be logical and mimic real life. Keep in mind that this is a 2D floor map of the place, child locations should only be located next to each other, not behind or in front of (as this is not 3D). If there's any items that do not fit, ie if you run out of space upon getting to that item, then just don't include the item and inform me of which item and why you didn't include it. 

        2. Using the list of relative sizes and which subitems should be near each other from an architect's perspective. For example, a “House” with “Bathroom” and “Bedroom” as two of its children may put the “bathroom” and “Bedroom” next to each other because people usually want easy access to the bathroom from their bedrooms. None of the items should be put in arbitrarily, each one must be intently placed in their locations. Based on this list of relative sizes, store these subitems as children in the JSON element along with the rectangle of 4 coordinates that represent the location of the subitem. You should place these subitems based on their relative sizes and relative locations of the positions compared to one another. It is completely fine and actually favorable to duplicate one subitem as multiple children. For example, a place named “Houses” may have multiple children named “House” because there should be many Houses in an area named “Houses”. When a place has multiple of the same type of item as children, each child should be appended by a number or letter starting from “1” “A” or “a”. For example, if a place named “Houses” had 4 houses as children, they may be named “House”, “House 2”, “House 3”, “House 4”.

        3. The sizes and locations of these subitems should be dynamic and varied. Make it look natural and different depending on what the place is and the relative sizes and positions of all the subitems. For example, for a "Park" with "Sandbox" and "Bench" as two of its subitems, the "Sandbox" should be bigger than the "Bench" with both children still being within the coordinates of the parent place. The "Bench" may also be next to the "Sandbox" because there are usually benches next to sandboxes at parks. Thus, the relative size and positions of all the children should be taken into utmost consideration. This is a important and imperative task.

        4. The subitems should cover all or most of the area of the place. In other words, the area of each place should be almost completely covered by subitems. *If there is some area left uncovered, the empty area MUST be put between subitems.* Try not to leave empty space between any subitems and the walls of the place. We want the subitems to be touching the walls of the place, so that we're making the efficient use of the available area. How much space is left uncovered should depend on the place. For example, a “Garden” may have no empty space because there are different plants completely covering its area whereas a “College” may have more empty space with the empty space being between the different subitems because students need places to walk between different buildings. This is a major consideration in determining the relative placement of all subitems.

        All subitems should be placed and stored as “children” of the original JSON element along with the rectangle of 4 coordinates representing their locations. All children subitems should have “name” and “coordinates” as their only 2 fields. After all the children have been generated, output the resulting JSON element.

        Also, provide an explanation of why different subitems are placed next to each other and why certain items are bigger than others. This reasoning should address all considerations explained above. Return your answer in the following format and only return this: "{"layout": your answer in json object form, "reasoning": reasoning of each item placement all stored in exactly 1 string}". Leave out the ```json ``` when you return your response as well, but always make sure to have the curly brackets wrapping the whole answer, ie {} at the beginning and end of final answer. Do not use special formatting in your answer either, such as double star for bolding. Remember the two keys of layout should always be "name" and "coordinates". 
        """
        self.fill_base_map_prompt = f"""
        Fill in the base map with a set number of locations ({NUM_ACTIVITY} activities), with no constraint on boundaries. The map should simulate an infinite (endless) map for {NUM_ACTIVITY} time steps. If an activity doesn’t need another place, it still counts as a number. There are no coordinates of the location inputted. 
        Return the resulting JSON layout with all locations and activities included.
        """

    # ChatGPT_request function taken directly from Generative Agents paper github (Park et al, 2023) without modification
    def ChatGPT_request(self, prompt):
        """
        Given a prompt and a dictionary of GPT parameters, make a request to OpenAI
        server and returns the response.
        ARGS:
        prompt: a str prompt
        gpt_parameter: a python dictionary with the keys indicating the names of
                        the parameter and the values indicating the parameter
                        values.
        RETURNS:
        a str of GPT-4o's response.
        """
        # temp_sleep()
        try:
            completion = openai.chat.completions.create(
                model="gpt-4o", messages=[{"role": "user", "content": prompt}]
            )
            return completion.choices[0].message.content

        except Exception as e:
            print(f"ChatGPT ERROR: {e}")
            return "ChatGPT ERROR"
        
    def check_object(self):
        return int(self.ChatGPT_request(f"{self.map_json['name']}: " + self.check_object_prompt))
    
    def check_item_too_small(self):
        coords = self.map_json['coordinates']
        if (coords[2] - coords[0])*(coords[3] - coords[1]) < 4:
            return True
        return False
    
    def generate_children(self):
        self.children_string = self.ChatGPT_request(f"Consider the following place: {self.map_json['name']}. " + self.get_children_prompt)
        print(self.children_string)
    
    def get_relative_sizes(self):
        self.size_allocation_dict = self.ChatGPT_request(self.children_string + self.assign_size_prompt)
        print(self.size_allocation_dict)
    
    def get_children_json(self):
        parent_children_description = f"""
        Consider the following place: {self.map_json['name']} with coordinates {self.map_json['coordinates']}.
        It has the following subitems: {self.size_allocation_dict}
        """
        architect_response = self.ChatGPT_request(parent_children_description + self.architect_prompt)
        print(architect_response)
        # Save response for analyzing behavior/reasoning of map creator
        with open(f"{self.persona_name}/{self.map_json['name']}_layout", 'w') as f:
            f.write(architect_response)
        
        # Make sure returned json matches with our base object
        self.architect_response_json = json.loads(architect_response)
        assert self.architect_response_json['layout']['name'] == self.map_json['name']
        assert self.architect_response_json['layout']['coordinates'] == self.map_json['coordinates']    

    def get_dimensions(self, current_map, place):
        """
        Determines the dimensions of the given place based on the relative size of other locations.
        Example usage:
        persona_name = "test_persona"
        map_generator = Map_Generator(persona_name, current_map)
        dimensions = map_generator.get_dimensions(current_map, place)
        """
        prompt = f"""
        Based on the relative size of other locations in the current map, what should the dimensions be for {place}? 
        Current map: {json.dumps(current_map, indent=2)}
        Return the dimensions as a dictionary with 'width' and 'height'.
        """
        dimensions = self.ChatGPT_request(prompt)
        return json.loads(dimensions)
    
    def create_map(self):
        if self.check_object() or self.check_item_too_small():
            return None
        
        # Generate all subitems if this base map does not have subitems yet
        if "children" not in self.map_json:
            self.generate_children()
            self.get_relative_sizes()
            self.get_children_json()
            self.map_json['children'] = self.architect_response_json['layout']['children']
            print(self.map_json['children'])

        for child in self.map_json['children']:
            print(child)
            child_map_generator = Map_Generator(self.persona_name, child)
            generated_map = child_map_generator.create_map()
            print(generated_map)
            if generated_map != None:
                child['children'] = generated_map

        print(self.map_json)
        return self.map_json["children"]

    def fill_base_map(self):
        response = self.ChatGPT_request(self.fill_base_map_prompt)
        return json.loads(response)


def experiment_2(persona_name, base_map_json, n_steps):
    # Initialize base map
    os.makedirs(persona_name, exist_ok=True)
    base_map = base_map_json
    
    for step in range(n_steps):
        # Create a map generator instance
        map_generator = Map_Generator(persona_name, base_map)
        
        # Fill in the base map for each time step
        filled_map = map_generator.create_map()
        
        # Print the filled map for this step
        print(f"Step {step + 1}:\n", json.dumps(filled_map, indent=4))
        
        # Save the filled map to a file
        with open(f"{persona_name}/final_layout_step_{step + 1}.json", 'w') as f:
            json.dump(base_map, f, indent=4)

        # Update the base map with the filled map for the next step
        base_map['children'] = filled_map


# persona_name = "test3"
# base_map = {"name": "Dairy Aisle", "coordinates": [2, -3, 8, 0]}
# # os.makedirs(persona_name)
# base_map["children"] = Map_Generator(persona_name, base_map).create_map()
# with open(f"{persona_name}/final_layout", 'w') as f:
#     f.write(str(base_map))
persona_name = "bluh"
base_map = {"name": "Dairy Aisle", "coordinates": [2, -3, 8, 0]}
experiment_2(persona_name, base_map, NUM_ACTIVITY)
