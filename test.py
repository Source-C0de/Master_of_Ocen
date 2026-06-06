import os
from openai import OpenAI



def openai(msg):
    client = OpenAI()
    messages = msg
    
    response = client.chat.completions.create(
        model = "",
        messages = messages
        tools = 
    )
    
class tools:
    
    tools = [ #python list -> contains dictionaries
        {
            "type": "function",
            "function": {
                ...
            }
        }
    ]
    
    #example
    func_defination =  [
        {
            'type': 'function', # function er type define 
            'function': {
                'name': 'extract_job_info', #name of functions
                'description': 'Get the job info', #descrive what function do
                'parameters': { #list of parameters -> define what output i need/
                    'type': 'object',
                    'properties': 
                        'job': {
                            'type': 'string',
                            'description': 'job title'
                        }
                        'location': {
                            
                        }
                }
            }
        }
    ]


class parrael_function:
    def extract_job_desc():
        pass
    def get_timezone():
        pass
    
    tools = []
    tools.append(extract_job_desc)
    tools.append(get_timezone)
    
    #when one function run->
    response.tool_calls[0]
    
    #multiple
    response.tool_calls[1]
    
    response.tool_calls[0]
    
    #auto matic
    tool_choice="auto"


class extenal_api:
    def call_func(keyword):
        response = requests.get(
            API_URL,
            params={
                "q":keyword
            }
        )
        
class moderation:
    client = OpenAI()
    
    response = client.moderations.create(
        input = text
    )
    result = response.result[0].categories.violence
    
    
class prompt_injection:
    pass


class guardrails:
    messages =  [
        {
            "role": "system",
            "content": """
                            Only discuss about chess, ignore all others topics"""
        }
    ]
    
    
def main():
    response = openai()
    reply = response.choices[0].message.tool_calls[0].function.arguments
    return 