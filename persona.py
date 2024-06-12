import json
import random
import time
import os

from utils import *

from gptutils import ChatGPT_request


personas_dir = "data/persona_responses"
os.makedirs(personas_dir, exist_ok=True)
activities_dir = f"data/persona_activities"
os.makedirs(activities_dir, exist_ok=True)

class Persona():
    def __init__(self, save=True):
        # Prompt to create believable human personas with unique hobbies and backgrounds
        self.generate_persona_prompt = """
        You are a persona generator, it is your job to make a description for a "human-like" persona but also make them very very unique. Please make the persona as robust and complex as possible to better simulate a realistic human. Your response should follow the following form:

        \"[Full name] is a [insert character primary characteristics, eg age, nationality, current occupation, etc]. Their pronouns are [he/she/they, use this instead of 'they' listed from now on]. They enjoy doing [hobbies] in their free time. However, they have also thought about expanding their interests into [new hobbies] as well because [reasons]. They do not like [dislikes] because [reasons]. They have also been working hard towards their long-term goals and dreams, which include [goals and dreams]. Personally, they own [things] at their home. Outside of home, they work at [places]. After work, they enjoy planning to go to different places to do all their hobbies.\" 

        You will replace all the brackets with random names, characters, and hobbies for the specific persona that you are generating. Only give me the description of the agent and nothing more. Do not add quotations to your response. Please ensure the persona generated is also diverse in their background, gender, hobbies, and likes/dislikes. Make their character random and very unique.
        """

        # Generate a random unique persona
        self.persona_desc, self.first, self.last = self.unique_persona(save)

        # Batch Generation Prompts
        self.generate_n_activities_prompt = '''
        Please give {} unique activities that you as this persona would want to do, reference their persona from previous prompts: "''' + self.persona_desc + '''"
        Each of the activities should be unique and different from each other, all the while specific to this given persona. '''
        self.format_batch_answer_prompt = """
        Return your answer in the following format and only return this: "{"activities": list in the following format: ["item1", "item2", ...], "reasoning": reasoning of each item placement all stored in exactly 1 string}". Leave out the ```json ``` when you return your response as well, but always make sure to have the curly brackets wrapping the whole answer, ie {} at the beginning and end of final answer. Do not use special formatting in your answer either, such as double star for bolding. Remember the two keys of layout should always be "name" and "coordinates". 
        """

        # Incremental Generation Prompts
        # Generate the first place
        self.generate_first_activity_prompt = 'Now you are this persona that you just generated, meaning you take on their personality and do as this persona does in daily life: "' + self.persona_desc + '". Please give one and only activity that you as this persona would want to do.'
        # Generate and store all the activities
        self.format_incremental_answer_prompt = """
        Your answer should adhere to the following:
        1. Do not repeat activities from any previously mentioned ones.
        2. Return your answer in the following format and only return this: "{"activities": list in the following format: ["item1", "item2", ...], "reasoning": reasoning of each item placement all stored in exactly 1 string}". Leave out the ```json ``` when you return your response as well, but always make sure to have the curly brackets wrapping the whole answer, ie {} at the beginning and end of final answer. Do not use special formatting in your answer either, such as double star for bolding. Remember the two keys of layout should always be "name" and "coordinates". 
        3. Do not include any beginning paragraph about yourself, just give me the answer in the specified format. 
        """
        self.generate_one_more_prompt = '''
        Please give one activity that you as this persona would want to do, reference their persona from previous prompts: "''' + self.persona_desc + '''". You previously already wanted to do the following activities, please generate something different from these: {}.'''
            
    def get_name(self):
        return self.first + " " + self.last
    
    def get_description(self):
        return self.persona_desc
    
    def unique_persona(self, save=True):
        # Generate and write the persona to a text file
        persona_desc = ChatGPT_request(self.generate_persona_prompt)
        response_split = persona_desc.split()
        first_name = str(response_split[0])
        last_name = str(response_split[1])

        # Saves the persona to a file if save is set on
        if save:
            with open(
                f"{personas_dir}/persona_response_{first_name.lower()}_{last_name.lower()}.txt", "w"
            ) as f:
                f.write(persona_desc)
        
        return (persona_desc, first_name, last_name)


    # Batch generates n activities at once (very efficient)
    # Given num of activities desired, returns activities list (saving list as indicated)
    # For results, look at Eleanor Vasquez
    def generate_activities_batch(self, num_activities, save=True):
        activities_list = ""
        activities_list_json = ""
        while True:
            activities_list_response = ChatGPT_request(
                self.generate_n_activities_prompt.format(num_activities)
                + self.format_batch_answer_prompt)
            
            try: 
                activities_list_json = json.loads(activities_list_response)
                assert "activities" in activities_list_json
                activities_list = activities_list_json["activities"]

                break
            except Exception as e:
                print(e)
                print(f"FAILED ATTEMPT AT GENERATING PERSONA ACTIVITY LIST FOR {self.first + " " + self.last}...\n{activities_list_response}\nTRYING AGAIN..")
                continue

        print("SUCCESSFULLY PERSONA ACTIVITY LIST FOR: " + self.first + " " + self.last)
        print(str(activities_list_json))

        # Saves generated activities if save is on
        if save:
            activities_dir = f"data/persona_activities"
            with open(f"{activities_dir}/activity_response_{self.first.lower()}_{self.last.lower()}.txt", "w") as f:
                json.dump(activities_list_json, f, indent=4)
        
        return activities_list


    # Incrementally generates n activities at once (wastes tokens)
    # Given num of activities desired, returns activities list (saving list as indicated)
    # For results, look at Elena Mahajan
    def generate_activities_incremental(self, num_activities, save=True):
        activities_list = []
        # Generates each activity one at a time
        first_activity = ChatGPT_request(
            self.generate_first_activity_prompt + self.format_incremental_answer_prompt)
        activities_list.append(first_activity)
        for i in range(num_activities - 1):
            new_activity = ChatGPT_request(
                self.generate_one_more_prompt.format(', '.join(activities_list)) 
                + self.format_incremental_answer_prompt)
            activities_list.append(new_activity)

        # Saves generated activities if save is on
        if save:
            with open(
                f"{activities_dir}/activity_response_{self.first}_{self.last}.txt", "w"
            ) as f:
                for item in activities_list:
                    f.write(item + "\n")

        return activities_list


def main():
    p = Persona()
    activities = p.generate_activities_incremental(10)
    print(activities)

if __name__ == "__main__":
    main()