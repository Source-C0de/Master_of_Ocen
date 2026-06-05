Extracting the response
You work for a company that has just launched a new smartphone. The marketing team has collected customer reviews from various online platforms and wants to analyze the feedback to understand the customer sentiment and the most talked-about features of the smartphone. To accelerate this, you've used the OpenAI API to extract structured data from these reviews, using function calling. You now need to write a function to clean the output and return a dictionary of the response from the function only.

The get_response() function, messages variable (containing the review) and function_definition (containing the function to extract sentiment and product features from reviews) have been preloaded. Notice that both messages and function_definition can be passed as arguments to the get_response() function to get the response from the chat completions endpoint.

Instructions
100 XP
Define a function to return the dictionary containing the output data, as found in the response under arguments.
Print the dictionary.



__code__
client = OpenAI(api_key="<OPENAI_API_TOKEN>")

response = get_response(messages, function_definition)

# Define the function to extract the data dictionary
def extract_dictionary(messages,function_definition):
  
  return {}

# Print the data dictionary
print(extract_dictionary)
