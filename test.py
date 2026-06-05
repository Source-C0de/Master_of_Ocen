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
    func_defination =  [
        {
            'type': 'function',
            'function': {
                'name': 'extract_job_info', #name of functions
                'description': 'Get the job info', #descrive what function do
                'parameters': { #list of parameters
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
        
    
    
def main():
    response = openai()
    reply = response.choices[0].message.tool_calls[0].function.arguments
    return 