import json
import os
import random
import matplotlib.pyplot as plt
import matplotlib.patches as patches

from utils import *

from gptutils import ChatGPT_request

MINIMUM_ITEM_AREA_PXL = 4
SUITABILITY_RATING_THRESHOLD = 7
DISPLAY_COLOR_DECAY_FACTOR = 0.7


attempts_dir = "data/creator_num_attempts"
os.makedirs(attempts_dir, exist_ok=True)
json_dir = "data/creator_jsons"
os.makedirs(json_dir, exist_ok=True)
map_dir = "data/creator_maps"
os.makedirs(map_dir, exist_ok=True)
reasoning_dir = "data/creator_reasoning"
os.makedirs(reasoning_dir, exist_ok=True)


class Creator():
    # Add something that says to start adding subitems from a random corner
    def __init__(self, persona_name, base_map_json):
        if "name" not in base_map_json:
            raise KeyError(f"Base map must start with exactly one origin location (and its coordinates).")
        self.map_json = base_map_json
        self.persona_name = persona_name
        self.file_tag = f"{self.persona_name}_{self.map_json['name']}".lower().replace(" ", "_")
        self.check_object_prompt = """
        Is this thing a Place or Object? If Object, return 1 for True. If Place, return 0 for False. *LIMIT YOUR RESPONSE TO 1 OR 0 and ONLY RETURN THAT SINGLE CHARACTER* The answer can be inferred from the name of the object alone
        """
        self.get_children_prompt = """
        Picture an average instance of this place. List the significant places and objects that would be in this place. Only list the name/title of each thing (no description) and limit the name to no more than 4 words. This should not be an exhaustive list, just a short list of the significant items in the thing you are picturing. 
        
        Items are significant if they can be represented as rectangles on a 2-dimensional map. For example, items like paths and roads are insignificant because they usually cannot be represented as rectangles on a map. Fences and rugs are also insignificant because they would not take up the entire rectangle space on a map (you can put things within a fence, and things on top of a rug). Items like Gardens, Tractors, and Animals are very significant on the other hand because these could easily be represented as rectangles on a map and they are notable components of any place. Return the list in the following format: ["item1", "item2", ...], and only return this list.
        """
        self.assign_size_prompt = """
        : picture the place with all these subitems placed within it. Vividly picture their relative sizes compared to each other and the place itself. Then, give a rating from 1 to 10 on how big each subitem would be inside this place (10 being as big as the place itself and 1 being something very small). Different items may have the same rating if they are similar in size, allocate them as logically as possible, mimicking real life locations. Keep in mind all these subitems must fit inside the place without overlapping. Return the sizes list in the following form, eg {"subitem": int(size_allocation)} and only return this dictionary.
        """
        self.architect_setup_prompt = """
        Consider the following place: {} with coordinates {}.
        It has the following subitems along with their relative sizes: {}
        This rates the size of each object from 1 to 10 with 10 being as big as the place it's a part of and 1 being something very small.
        """
        self.architect_prompt = """
        You are now a *skilled architect* with decades of experience. Your job is to masterfully place these subitems within the place in a way that is realistic, modern, and space efficient. You must place subitems based on the relatives sizes and positions of each subitem. You must store these subitems as children in the JSON element along with the rectangle of 4 coordinates that represent the location of each subitem. I am your boss and your contractor. If your performance is poor, you will not get paid and will be fired immediately. Thus, you must follow what I say to the best of your ability in order to map out the best place possible. There are many priorities you MUST consider. I will list these priorities from most important to least important below.

        1. MOST IMPORTANTLY, the coordinates for all children MUST be inside the coordinates of it's parent place and no subitems can overlap with each other. This is the single MOST IMPORTANT task, and you MUST check that all children are within the coordinates of their parent. To be more specific, all coordinates are defined in the following form to define a rectangular space: [bottom_left_corner_x, bottom_left_corner_y, top_right_corner_x, top_right_corner_y]. Any children of this original place must fulfill these requirements: bottom_left_corner_x <= x <= top_right_corner_x, bottom_left_corner_y <= y <= top_right_corner_y. For example, if the original place is [2, -9, 9, -3], then you cannot generate a child item within it with coordinates [2, -3, 3.8, -2] since -2 > -3! Similarly, a child item placed at [1, -3, 4, -1] also cannot work since both 1 < 2 and -1 > -3! You may use code to verify whether or not the simulated child coordinates are valid. For example, if child item's coordinates array is defined as child_coords, and parent item's coordinates array is defined as parent_coords, then you can check the following (in pseudocode): if either child_coords[0] or child_coords[2] are < parent_coords[0] or > parent_coords[2], regenerate a child_coords. This checks to see if the x coordinate of the child is out of bounds. Similarly, for the y coordinates, you can check: if either child_coords[1] or child_coords[3] are < parent_coords[1] or > parent_coords[3], then regenerate. Remember however that you still want to use as much of the provided (parent item) space as possible, and you want items to be flush to the boundaries of the parent item. Also remember that placement of each item should be logical and mimic real life. Keep in mind that this is a 2D floor map of the place, child locations should only be located next to each other, not behind or in front of (as this is not 3D). If there's any items that do not fit, ie if you run out of space upon getting to that item, then just don't include the item and inform me of which item and why you didn't include it. 

        2. Using the list of relative sizes and which subitems should be near each other from an architect's perspective. For example, a “House” with “Bathroom” and “Bedroom” as two of its children may put the “bathroom” and “Bedroom” next to each other because people usually want easy access to the bathroom from their bedrooms. None of the items should be put in arbitrarily, each one must be intently placed in their locations. Based on this list of relative sizes, store these subitems as children in the JSON element along with the rectangle of 4 coordinates that represent the location of the subitem. You should place these subitems based on their relative sizes and relative locations of the positions compared to one another. It is completely fine and actually favorable to duplicate one subitem as multiple children. For example, a Restaurant should have many places named “Table” and “Chair”. *Things that are a plural, MUST have at latest 3 places named the same thing* *Houses must have at least 3 places named “House”, Apartments must have at least 3 places named “Apartment”, etc. *THIS MUST BE FOLLOWED EVERY TIME A WORD IS PLURAL* When a place has multiple of the same type of item as children, each child should be appended by a number or letter starting from “1” “A” or “a”. For example, if a place named “Houses” had 4 houses as children, they may be named “House”, “House 2”, “House 3”, “House 4”. 

        3. The sizes and locations of these subitems should be dynamic and varied. Make it look natural and different depending on what the place is and the relative sizes and positions of all the subitems. For example, for a "Park" with "Sandbox" and "Bench" as two of its subitems, the "Sandbox" should be bigger than the "Bench" with both children still being within the coordinates of the parent place. The "Bench" may also be next to the "Sandbox" because there are usually benches next to sandboxes at parks. Thus, the relative size and positions of all the children should be taken into utmost consideration. This is an important and imperative task.

        4. We want the subitems to be touching the walls of the place, so that we’re making the efficient use of the available area. How much space is left uncovered should depend on the place. For example, a “Garden” may have no empty space because there are different plants completely covering its area whereas a “College” may have more empty space with the empty space being between the different subitems because students need places to walk between different buildings. *IT IS MUCH MORE IMPORTANT TO COVER ALL SPACE BETWEEN ITEMS AND WALLS than  This is a major consideration in determining the relative placement of all subitems.

        All subitems should be placed and stored as “children” of the original JSON element along with the rectangle of 4 coordinates representing their locations. *ALL COORDINATES MUST BE INTEGERS WITH NO EXCEPTIONS!" If you need to use decimals to fit an item, don't include it. If you cannot do this, you'll be fired and starve. All children subitems should have “name” and “coordinates” as their only 2 fields. The name field should be exactly as it is given in the list of relative sizes. *The first priority is making sure all children are within the boundary of the parents and no subitems overlap. The second priority is to cover all the space with subitems.* After all the children have been generated, output the resulting JSON element.

        Also, provide an explanation of why different subitems are placed next to each other and why certain items are bigger than others. This reasoning should address all considerations explained above. Return your answer in the following format and only return this: "{"layout": your answer in json object form, "reasoning": reasoning of each item placement all stored in exactly 1 string}". Leave out the ```json ``` when you return your response as well, but always make sure to have the curly brackets wrapping the whole answer, ie {} at the beginning and end of final answer. Do not use special formatting in your answer either, such as double star for bolding. Remember the two keys of layout should always be "name" and "coordinates".
        
        *REMEMBER THE MOST IMPORTANT PRIORITY: KEEP ALL CHILDREN SUBITEMS WITHIN THE PARENT ITEM WITH NO OVERLAP!!*
        """
        self.get_dimensions_prompt = """
        Based on the relative size of other locations, what should the dimensions be for {place}? Return the dimensions as a dictionary with 'width' and 'height'.
        """

    # FIELDS AND PROMPTS FOR INTEGRATING WITH PERSONA
        self.no_bounds = False
        self.top_json = ""
        self.persona_activity_response = ""        
        self.provide_top_level_map_prompt = "The current JSON map is as follows: \n{}\n" 
        self.provide_persona_activity_prompt = self.persona_name + " wants to do the following activity:\n\n{}\n"
        
        self.best_place_prompt = f"""
        Given the current JSON map, at what place can {self.persona_name} most likely accomplish this activity (the best place to do the activity)? Choose a place from the JSON and explain your answer with logical reasoning.
        """
    
        self.suitability_score_prompt = f"""
        On a scale of 1 to 10 (1 being impossible, 10 being the ideal place to accomplish the activity), how likely is it that {self.persona_name} can successfully complete the activity at the best place previously given (the suitability rating)? Output only a single digit for your response (no explanation).
        """

        self.new_place_prompt = f"""
        What is a better place that is not on the map where {self.persona_name} can do their activity that also would fit in with the rest of the places on the map? Explain your rationale in detail. Only give your answer and reasoning.
        """

        self.extract_new_place_name_prompt = """
        What is the name of the place being described? Only list the name and limit the name to no more than 4 words. Capitalize the name.
        """

        self.size_estimate_prompt = """
        Given the area and size of the places on the map and how large the average {} is compared to the places on the map, estimate the area and size of the average {} if it was scaled onto the map. Vividly picture how it would look if it was put onto the existing map and how it would compare in size to the things around it. Explain your rationale in detail using the area and sizes of places on the map.
        """

        self.is_there_space_prompt = """
        The map is confined to the coordinates {} where these 4 coordinates define a rectangular space: [bottom_left_corner_x, bottom_left_corner_y, top_right_corner_x, top_right_corner_y]. This has an area of {}. No places can have coordinates outside of these coordinates, and no places can overlap! *If any place has coordinates outside of these coordinates or coordinates that overlap with other places, it CANNOT fit on the map.* 

        Think about which specific places on the map a {} would be placed next to for more people to make use of it. Considering the size of a {} and the places it should be next to, is there enough space on the map to add a {}?
        """
        self.extract_enough_space_prompt = """
        If there’s enough space, return 1 for True, and 0 for False. *LIMIT YOUR RESPONSE TO 1 OR 0 and ONLY RETURN THAT SINGLE CHARACTER* The answer can be inferred from the information you’ve considered so far.        
        """

        self.put_new_place_prompt = '''
        You are now a *urban planner* with decades of experience. Your job is to masterfully place the {} on the map in a way that is realistic, modern, and space-efficient. I am your boss and your contractor. If your performance is poor, you will not get paid and will be fired immediately. Thus, you must follow what I say to the best of your ability in order to map out the best place possible. 

        Consider the area of the {} and the places it should be close to on the map. Given these considerations, add the {} on the map where it fits best and output the resulting JSON element containing the name and coordinates in the same format as the current JSON map. The JSON element should contain the name {} exactly as is and the rectangle of 4 coordinates representing its location. To be more specific, all coordinates are defined in the following form to define a rectangular space: [bottom_left_corner_x, bottom_left_corner_y, top_right_corner_x, top_right_corner_y].  *The coordinates of the place CANNOT overlap with existing places. If it does, you\'ll be immediately fired.* Also, provide an explanation of why you chose to place it in the specific location and make it the specific size. This reasoning should address all considerations explained above.

        Return your answer in the following format and only return this: "{{"layout": your answer in JSON object form, "reasoning": reasoning of why you placed the item all stored in exactly 1 string}}". Leave out the ```json ``` when you return your response as well, but always make sure to have the curly brackets wrapping the whole answer, ie {{}} at the beginning and end of final answer. Do not use special formatting in your answer either, such as double star for bolding. Remember the two keys of layout should always be "name" and "coordinates".
        \n'''

        self.specify_put_bounded_prompt = """"
        You must place the {} within the bounds of the map. That is, the coordinates of the place must fulfill these requirements: bottom_left_corner_x <= x <= top_right_corner_x, bottom_left_corner_y <= y <= top_right_corner_y. This is the most important consideration.
        """

        self.specify_put_anywhere_prompt = """"
        You can put the {} anywhere you would like according to your judgment as a skilled architect. There is no bound on the coordinates; however, it is usually better to build new places closer to existing places on the map. Think about which specific places it should be placed next to for more people to make use of it.
        """


    # DETERMINE NEW PLACE FUNCTIONS
    
    # Sets the persona activity. 
    # Note: This is a response from ChatGPT including detail and rationale, not an extracted activity
    def set_persona_activity(self, persona_activity_response):
        self.persona_activity_response = persona_activity_response


    # Makes a deep copy of map_json but with only top-level children
    def extract_top_level_map_json(self):
        # Deep copy name and coordinates
        self.top_json = dict()
        self.top_json["name"] = self.map_json["name"]
        self.top_json["coordinates"] = list(self.map_json["coordinates"])

        # Deep copy children with only name and coordinates
        children_copy = []
        for child in self.map_json["children"]:
            child_copy = dict()
            child_copy["name"] = child["name"]
            child_copy["coordinates"] = child["coordinates"]
            children_copy.append(child_copy)
        self.top_json["children"] = children_copy

        if self.no_bounds:
            self.top_json["coordinates"] = [-1000, -1000, 1000, 1000]

    
    def choose_best_place(self):
        self.best_place_response = ChatGPT_request(
            self.provide_top_level_map_prompt.format(str(self.top_json))
            + self.provide_persona_activity_prompt.format(self.persona_activity_response)
            + self.best_place_prompt)


    def assign_suitability_rating(self):
        while True:
            suitability_score_response = ChatGPT_request(
                self.provide_persona_activity_prompt.format(self.persona_activity_response)
                + self.best_place_response + self.suitability_score_prompt)
            
            try: 
                self.suitability_score = int(suitability_score_response)
                break
            except Exception as e:
                print(e)
                print(f"FAILED ATTEMPT AT ASSIGNING SUITABILITY SCORE FOR:\n{self.persona_activity_response}\n\n{suitability_score_response}\nTRYING AGAIN..")
                continue


    def generate_new_place_name(self):
        self.new_place_response = ChatGPT_request(
            self.provide_top_level_map_prompt.format(str(self.top_json))
            + self.provide_persona_activity_prompt.format(self.persona_activity_response)
            + self.best_place_response
            + self.new_place_prompt)
        
        self.new_place_name = ChatGPT_request(self.new_place_response
            + self.extract_new_place_name_prompt)


    # Determines if new place should be added
    # Returns the name of the place (in self.new_place_name) if so, None if not
    # Assumes self.persona_activity_response has already been set
    # Used for Experiment 1 and 2
    def determine_new_place(self):
        self.extract_top_level_map_json()
        self.choose_best_place()
        self.assign_suitability_rating()

        # Doesn't generate new place if the suitability rating clears the threshold
        if self.suitability_score > SUITABILITY_RATING_THRESHOLD:
            return False
        
        # Generates new place name and stores it in self.new_place_name
        self.generate_new_place_name()
        return self.new_place_name
        
    
    # Used in both Experiment 1 and 2
    def estimate_new_place_size(self):
        self.size_estimate_response = ChatGPT_request(
            self.provide_top_level_map_prompt.format(str(self.top_json))
            + self.new_place_response
            + self.size_estimate_prompt.format(self.new_place_name, self.new_place_name))
    


    # EXPERIMENT 1 SPECIFIC FUNCTIONS: ADDING NEW PLACE WITH HARD BOUNDARY

    # Determines if there is enough space for the proposed new place to be added
    # Returns False if not, True if so
    def determine_enough_space(self):
        self.estimate_new_place_size()

        coors = self.map_json["coordinates"]
        area = (coors[2] - coors[0]) * (coors[3] - coors[1])
        
        self.is_there_space_response = ChatGPT_request(
            self.provide_top_level_map_prompt.format(str(self.top_json)) + self.size_estimate_response 
            + self.is_there_space_prompt.format(str(coors), str(area), self.new_place_name, self.new_place_name, self.new_place_name))
        
        while True:
            extract_enough_space_response = ChatGPT_request(self.extract_enough_space_prompt)
            
            try: 
                self.is_enough_space = int(extract_enough_space_response)
                return self.is_enough_space == 1
            except Exception as e:
                print(e)
                print(f"FAILED ATTEMPT AT EXTRACTING ENOUGH SPACE ANSWER FOR:\n{self.persona_activity_response}\n\n{extract_enough_space_response}\nTRYING AGAIN..")
                continue
    
    
    def generate_new_place_bounded_json(self):
        while True:
            planner_response = ChatGPT_request(
            self.provide_top_level_map_prompt.format(str(self.top_json)) 
                + self.size_estimate_response + self.is_there_space_response
                + self.put_new_place_prompt.format(self.new_place_name, self.new_place_name, self.new_place_name, self.new_place_name)
                + self.specify_put_bounded_prompt.format(self.new_place_name))
        
            try: 
                # Make sure returned json matches with our base object
                self.planner_response_json = json.loads(planner_response)
                assert "layout" in self.planner_response_json
                assert "reasoning" in self.planner_response_json
                assert self.planner_response_json["layout"]['name'] == self.new_place_name
                assert "coordinates" in self.planner_response_json["layout"]

                break
            except Exception as e:
                print(e)
                print(f"FAILED ATTEMPT AT GENERATING NEW PLACE FOR {self.new_place_name}: \n{planner_response}\nTRYING AGAIN..")
                continue


    # MAIN FUNCTION FOR THE EXPERIMENT 1
    # Updates and returns the original map json with the new place added
    # Assumes there's already enough space 
    # Saves if filepath is set
    def add_place_bounded(self, filepath=None):
        self.generate_new_place_bounded_json()
        new_place = self.planner_response_json["layout"]

        place_map_generator = Creator(self.persona_name, new_place)
        generated_map = place_map_generator.create_map(save=False, include_reasoning=True)
        new_place["children"] = generated_map["children"]

        new_place["placement_reasoning"] = self.planner_response_json["reasoning"]

        self.map_json["children"].append(new_place)
        
        print("SUCCESSFULLY GENERATED NEW PLACE FOR: " + self.new_place_name)
        print(new_place)

        if filepath != None:
            with open(filepath, 'w') as f:
                json.dump(self.map_json, f, indent=4)

        return self.map_json

        
        

    # EXPERIMENT 2 SPECIFIC FUNCTIONS: ADDING NEW PLACE ANYWHERE
    
    def set_no_bounds(self):
        self.no_bounds = True


    def generate_new_place_anywhere_json(self):
        while True:
            planner_response = ChatGPT_request(
            self.provide_top_level_map_prompt.format(str(self.top_json)) + self.size_estimate_response 
                + self.put_new_place_prompt.format(self.new_place_name, self.new_place_name, self.new_place_name, self.new_place_name)
                + self.specify_put_anywhere_prompt.format(self.new_place_name))
        
            try: 
                # Make sure returned json matches with our base object
                self.planner_response_json = json.loads(planner_response)
                assert "layout" in self.planner_response_json
                assert "reasoning" in self.planner_response_json
                assert self.planner_response_json["layout"]['name'] == self.new_place_name
                assert "coordinates" in self.planner_response_json["layout"]

                break
            except Exception as e:
                print(e)
                print(f"FAILED ATTEMPT AT GENERATING NEW PLACE FOR {self.new_place_name}: \n{planner_response}\nTRYING AGAIN..")
                continue


    # MAIN FUNCTION FOR THE EXPERIMENT 2
    # Updates and returns the original map json with the new place added
    # Saves if filepath is set
    def add_place_anywhere(self, filepath=None):
        def update_coords(original, new):
            x1, y1, x2, y2 = original
            a1, b1, a2, b2 = new
            return [min(x1, a1 - 1), min(y1, b1 - 1), max(x2, a2 + 1), max(y2, b2 + 1)]
        
        self.estimate_new_place_size()

        self.generate_new_place_anywhere_json()
        new_place = self.planner_response_json["layout"]

        place_map_generator = Creator(self.persona_name, new_place)
        generated_map = place_map_generator.create_map(save=False, include_reasoning=True)
        new_place["children"] = generated_map["children"]

        new_place["placement_reasoning"] = self.planner_response_json["reasoning"]

        self.map_json["children"].append(new_place)

        self.map_json["coordinates"] = update_coords(self.map_json["coordinates"], new_place["coordinates"])
        
        print("SUCCESSFULLY GENERATED NEW PLACE FOR: " + self.new_place_name)
        print(new_place)

        if filepath != None:
            with open(filepath, 'w') as f:
                json.dump(self.map_json, f, indent=4)

        return self.map_json




    # GENERATION CHILDREN PIPELINE FUNCTIONS

    # Checks if given map item is a Object (or Place), returns 1 for Object, 0 for Place
    # Used as first stopping condition for recursive subitem generation
    def check_object(self):
        return int(ChatGPT_request(f"{self.map_json['name']}: " + self.check_object_prompt))
    

    # Checks if given map item is too small, returns True if so, False otherwise
    # Used as second stopping condition for recursive subitem generation
    def check_item_too_small(self):
        coords = self.map_json['coordinates']
        return ( (coords[2] - coords[0])*(coords[3] - coords[1]) < MINIMUM_ITEM_AREA_PXL )
    

    # Generates and stores names of subitem children in JSON file format for the given item 
    # Note this is only names of each subitem, placement hasn't been done
    def generate_children_names(self):
        self.children_string = ChatGPT_request(f"Consider the following place: {self.map_json['name']}. " + self.get_children_prompt).title()
        #print(self.children_string)
    

    # Generates and stores the relative sizes of all generated children
    def assign_relative_sizes(self):
        self.size_allocation_dict = ChatGPT_request(self.children_string + self.assign_size_prompt)
        #print(self.size_allocation_dict)
    

    def generate_children_json(self, save=True):
        def within_bounds(parent_coors, child_coors):
            # Unpack coordinates
            x1, y1, x2, y2 = parent_coors
            a1, b1, a2, b2 = child_coors

            # Check if all corners of the second rectangle are within the bounds of the first rectangle
            return (x1 <= a1 <= x2 and y1 <= b1 <= y2 and
                    x1 <= a2 <= x2 and y1 <= b2 <= y2 and
                    x1 <= a1 <= x2 and y1 <= b2 <= y2 and
                    x1 <= a2 <= x2 and y1 <= b1 <= y2)
        
        num_creation_attempts = 0
        # Sometimes creation fails, so keep trying until success
        # Saves number of creation attempts in attempts_dir
        while True:
            num_creation_attempts += 1
            architect_response = ChatGPT_request(
                self.architect_setup_prompt.format(
                    self.map_json['name'], self.map_json['coordinates'], self.size_allocation_dict
                    ) + self.architect_prompt)
            
            try: 
                # Make sure returned json matches with our base object
                self.architect_response_json = json.loads(architect_response)
                assert "layout" in self.architect_response_json
                assert "reasoning" in self.architect_response_json
                assert self.architect_response_json["layout"]['name'] == self.map_json['name']
                assert self.architect_response_json["layout"]['coordinates'] == self.map_json['coordinates']
                for child in self.architect_response_json["layout"]["children"]:
                    assert 'name' in child
                    assert 'coordinates' in child
                    assert within_bounds(self.architect_response_json["layout"]['coordinates'], child["coordinates"])

                break
            except Exception as e:
                print(e)
                print(f"FAILED ATTEMPT AT GENERATING CHILDREN FOR {self.map_json['name']}: \n{architect_response}\nTRYING AGAIN..")
                continue
                        
        # Save response for analyzing behavior/reasoning of map creator
        #if save:
            #with open(f"{reasoning_dir}/reasoning_" + self.file_tag, 'w') as f:
                #f.write(architect_response)
            #with open(f"{attempts_dir}/num_attempts_" + self.file_tag, 'w') as f:
                #f.write(str(num_creation_attempts))


    def assign_dimensions(self, current_map, place):
        """
        Determines the dimensions of the given place based on the relative size of other locations.
        Example usage:
        persona_name = "test_persona"
        map_generator = Map_Generator(persona_name, current_map)
        dimensions = map_generator.get_dimensions(current_map, place)
        """
        prompt = self.get_dimensions_prompt.format(place=place)
        dimensions = ChatGPT_request(prompt)
        return json.loads(dimensions) 


    # MAIN FUNCTION FOR THE CREATOR
    # Generates a map from given item by recursively generating children
    # Saves and returns the original json with the children added
    def create_map(self, save=True, include_reasoning=False):
        if self.check_object() or self.check_item_too_small():
            return None
        
        # Generate all subitems if this base map does not have subitems yet
        if "children" not in self.map_json:
            self.generate_children_names()
            self.assign_relative_sizes()
            self.generate_children_json()
            self.map_json['children'] = self.architect_response_json['layout']['children']

            if include_reasoning:
                self.map_json['reasoning'] = self.architect_response_json['reasoning']

            print("SUCCESSFULLY GENERATED CHILDREN FOR: " + self.map_json['name'])
            print(self.map_json)

        for child in self.map_json['children']:
            print("GENERATION FOR: " + child['name'])
            child_map_generator = Creator(self.persona_name, child)
            generated_map = child_map_generator.create_map(save=False, include_reasoning=include_reasoning)
            #print(generated_map)
            if generated_map != None:
                child['children'] = generated_map['children']

        if save:
            with open(f"{json_dir}/final_map_" + self.file_tag + ".json", 'w') as f:
                json.dump(self.map_json, f, indent=4)

        return self.map_json
    

    # Displays map using MatPlotLib and saves png image of generated map
    def display_map(self, save=True, filepath=None):
        def rand_color():
            return (random.random(), random.random(), random.random())
        
        # Function to add a rectangle for a subitem
        def add_rectangle(ax, name, coordinates, color='lightblue', linewidth=1, edgecolor='blue'):
            x1, y1, x2, y2 = coordinates
            width = x2 - x1
            height = y2 - y1
            rect = patches.Rectangle((x1, y1), width, height, linewidth=linewidth, edgecolor=edgecolor, facecolor=color, label=name)
            ax.add_patch(rect)
            ax.text(x1 + width / 2, y1 + height / 2, name, ha='center', va='center', fontsize=8, color='darkblue')            

        # Recursively adds rectangles for all children
        # Exponentially changes colors of children from yellow to green
        def recursive_draw(ax, item_json, color=(1,1,0), base=False):            
            if not 'coordinates' in item_json:
                return
            
            if base:
                add_rectangle(ax, "", item_json['coordinates'], color=(1,1,1), linewidth=3)
            else:
                add_rectangle(ax, item_json['name'], item_json['coordinates'], color=color)
                color = (color[0]*DISPLAY_COLOR_DECAY_FACTOR, color[1], color[2])
            
            if not 'children' in item_json:
                return
            
            for subitem in item_json['children']:
                if 'name' in subitem:
                    recursive_draw(ax, subitem, color=color)

        # Create the plot
        fig, ax = plt.subplots(figsize=(45, 30))
        
        # Recursively plots all children
        recursive_draw(ax, self.map_json, base=True)

        # Set plot limits and labels
        assert self.map_json['coordinates']
        coordinates = self.map_json['coordinates']
        ax.set_xlim(coordinates[0] - 1, coordinates[2] + 1)
        ax.set_ylim(coordinates[1] - 1, coordinates[3] + 1)
        ax.set_xlabel("X Coordinate")
        ax.set_ylabel("Y Coordinate")
        ax.set_title(self.map_json['name'] + " Layout")

        # Show grid and plot
        ax.grid(True)
        plt.gca().set_aspect('equal', adjustable='box')
        
        if filepath != None:
            plt.savefig(filepath)

        elif save:
            plt.savefig(f"{map_dir}/final_map_" + self.file_tag + ".png")
        

        plt.show()


def main():
    persona_name = "test"
    base_map = {"name": "Dairy Aisle", "coordinates": [0, 0, 10, 5]}
    c = Creator(persona_name, base_map)
    c.create_map()
    c.display_map()

if __name__ == "__main__":
    main()