
import json
import random
import openai
import time 

from utils import *
openai.api_key = openai_api_key

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
    completion = openai.ChatCompletion.create(
    model="gpt-4o", 
    messages=[{"role": "user", "content": prompt}]
    )
    return completion["choices"][0]["message"]["content"]
  
  except: 
    print ("ChatGPT ERROR")
    return "ChatGPT ERROR"

initial_prompt = """
 I am trying to create a description of a persona for one particular agent given the following structure: 
 "[Name] is a [insert character bio, eg age, student status]. They enjoy [hobbies] in their free time. 
 Currently, they are making a plan to go to different places to do all their hobbies. Their long term goals are [goals].
 They hate [hate].  They own [things]. They work at [places]. " You will replace all the brackets with random names, 
 characters, and hobbies for the specific agent that you are generating. Only give me the description of the agent and nothing more. 
"""


persona_response = ChatGPT_request(initial_prompt)

follow_up_prompt = """
Now you are this persona: 
"""

follow_up_prompt += persona_response

follow_up_prompt += """
 Now assume the personality and what this persona does in a daily life. 
Give one activity that this persona will do in a daily life. 
"""

activity_response = ChatGPT_request(follow_up_prompt)











