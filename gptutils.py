import openai

openai.api_key = api key
DISPLAY_OUT = False

# ChatGPT_request function taken directly from Generative Agents paper github (Park et al, 2023) without modification
# Prints prompt and response to out if displayOut
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

    if DISPLAY_OUT:
        print("Prompt:")
        print(prompt)

    try:
        completion = openai.chat.completions.create(
            model="gpt-4o", messages=[{"role": "user", "content": prompt}]
        )
        response = completion.choices[0].message.content

        if DISPLAY_OUT:
            print("Response:")
            print(response)

        return response

    except Exception as e:
        print(f"ChatGPT ERROR: {e}")
        return "ChatGPT ERROR"