import json
import random
import openai
import time
import os

from utils import *

openai.api_key = openai_key
personas_dir = "data/persona_responses"
os.makedirs(personas_dir, exist_ok=True)
activities_dir = f"data/persona_activities"
os.makedirs(activities_dir, exist_ok=True)

# Prompt to create believable human personas with unique hobbies and backgrounds
generate_persona_prompt = """
You are a persona generator, it is your job to make a description for a "human-like" persona but also make them very very unique. Please make the persona as robust and complex as possible to better simulate a realistic human. Your response should follow the following form:

\"[Full name] is a [insert character primary characteristics, eg age, nationality, current occupation, etc]. Their pronouns are [he/she/they, use this instead of 'they' listed from now on]. They enjoy doing [hobbies] in their free time. However, they have also thought about expanding their interests into [new hobbies] as well because [reasons]. They do not like [dislikes] because [reasons]. They have also been working hard towards their long-term goals and dreams, which include [goals and dreams]. Personally, they own [things] at their home. Outside of home, they work at [places]. After work, they enjoy planning to go to different places to do all their hobbies.\" 

You will replace all the brackets with random names, characters, and hobbies for the specific persona that you are generating. Only give me the description of the agent and nothing more. Do not add quotations to your response. Please ensure the persona generated is also diverse in their background, gender, hobbies, and likes/dislikes. Make their character random and very unique.
"""


# ChatGPT_request function taken directly from Generative Agents paper github (Park et al, 2023) without modification
def ChatGPT_request(prompt):
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

    except:
        print("ChatGPT ERROR")
        return "ChatGPT ERROR"


def unique_persona(generate_persona_prompt=generate_persona_prompt, num_activities=10):
    # Generate and write the persona to a text file
    generated_persona = ChatGPT_request(generate_persona_prompt)
    response_split = generated_persona.split()
    first_name = response_split[0].lower()
    last_name = response_split[1].lower()
    with open(
        f"{personas_dir}/persona_response_{first_name}_{last_name}.txt", "w"
    ) as f:
        f.write(generated_persona)

    # Generate and store all the activities
    format_prompt_answer = """
    Your answer should adhere to the following:
    1. Do not repeat activities from any previously mentioned ones.
    2. Return your answer in the following format and only return this: "{"activities": list in the following format: ["item1", "item2", ...], "reasoning": reasoning of each item placement all stored in exactly 1 string}". Leave out the ```json ``` when you return your response as well, but always make sure to have the curly brackets wrapping the whole answer, ie {} at the beginning and end of final answer. Do not use special formatting in your answer either, such as double star for bolding. Remember the two keys of layout should always be "name" and "coordinates". 
    3. Do not include any beginning paragraph about yourself, just give me the answer in the specified format. 
    """

    # Generate the first place
    generate_first_place_prompt = f'Now you are this persona that you just generated, meaning you take on their personality and do as this persona does in daily life: "{generated_persona}" Please give one and only activity that you as this persona would want to do.'
    first_place = ChatGPT_request(generate_first_place_prompt + format_prompt_answer)

    # GENERATE N ACTIVITIES WITH REASONINGS (results look like Elena Mahajan)
    activities_generated = []
    activities_generated.append(first_place)
    for i in range(num_activities - 1):
        generate_one_more_prompt = f"""
        Please give one activity that you as this persona would want to do, reference their persona from previous prompts: "{generated_persona}". You previously already wanted to do the following activites, please generate something different from these: {', '.join(activities_generated)}. """
        new_activity = ChatGPT_request(generate_one_more_prompt + format_prompt_answer)
        activities_generated.append(new_activity)
    print(first_name)
    with open(
        f"{activities_dir}/activity_response_{first_name}_{last_name}.txt", "w"
    ) as f:
        for item in activities_generated:
            f.write(item + "\n")


    ## CODE TO GENERATE N ACTIVITIES AT A TIME (results look like Eleanor Vasquez)
    # generate_n_activities = f"""
    # Please give {num_activities} unique activities that you as this persona would want to do, reference their persona from previous prompts: "{generated_persona}". Each of the activiites should be unique and different from each other, all the while specific to this given persona. 
    # """
    # format_prompt_answer = """
    # Return your answer in the following format and only return this: "{"activities": list in the following format: ["item1", "item2", ...], "reasoning": reasoning of each item placement all stored in exactly 1 string}". Leave out the ```json ``` when you return your response as well, but always make sure to have the curly brackets wrapping the whole answer, ie {} at the beginning and end of final answer. Do not use special formatting in your answer either, such as double star for bolding. Remember the two keys of layout should always be "name" and "coordinates". 
    # """
    # activities_dir = f"data/persona_activities"
    # activities_list = ChatGPT_request(generate_n_activities + format_prompt_answer)
    # with open(f"{activities_dir}/activity_response_{first_name}_{last_name}.txt", "w") as f:
    #     f.write(activities_list)

unique_persona()