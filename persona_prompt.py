import json
import random
import openai
import time
import os

from utils import *

openai.api_key = openai_api_key

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
    # store generated persona in a text file
    personas_dir = "data/persona_responses"
    os.makedirs(personas_dir, exist_ok=True)
    with open(
        f"{personas_dir}/persona_response_{first_name}_{last_name}.txt", "w"
    ) as f:
        f.write(generated_persona)

    # Generate the first place
    generate_first_place_prompt = f'Now you are this persona that you just generated, meaning you take on their personality and do as this persona does in daily life: "{generated_persona}" Please give one and only activity that you as this persona would want to do.'
    first_place = ChatGPT_request(generate_first_place_prompt)

    activities_generated = []
    activities_generated.append(first_place)

    # Generate and store all the activities
    generate_one_more_prompt = f"Please give one activity that you as this persona would want to do, reference their persona from previous prompts: \"{generated_persona}\". You previously already wanted to do the following activites, please generate something different from these: {', '.join(activities_generated)}."
    for i in range(num_activities - 1):
        new_activity = ChatGPT_request(generate_one_more_prompt)
        activities_generated.append(new_activity)
    # Store activity response in a text file
    activities_dir = f"data/persona_activities"
    os.makedirs(activities_dir, exist_ok=True)
    with open(
        f"{activities_dir}/activity_response_{first_name}_{last_name}.txt", "w"
    ) as f:
        for item in activities_generated:
            f.write(item + "\n")
