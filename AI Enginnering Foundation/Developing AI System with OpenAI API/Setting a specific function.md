Setting a specific function
You have been given a few customer reviews to analyze, and have been asked to extract for each one the product name, variant, and customer sentiment. To ensure that the model extracts this specific information, you decide to use function calling and specify the function for the model to use. Use the Chat Completions endpoint with function calling and tool_choice to extract the information.

In this exercise, the messages and function_definition have been preloaded.

Instructions
Add your function definition as tools.
Set the extract_review_info function to be called for the response.
Print the response.


__code__
client = OpenAI(api_key="<OPENAI_API_TOKEN>")

response= client.chat.completions.create(
    model=model,
    messages=messages,
    # Add the function definition
    ____,
    # Specify the function to be called for the response
    tool_choice=____
)

# Print the response
print(____)


__solution__
client = OpenAI(api_key="<OPENAI_API_TOKEN>")

response= client.chat.completions.create(
    model=model,
    messages=messages,
    # Add the function definition
    tools=function_definition,
    # Specify the function to be called for the response
    tool_choice= {
        "type":"function",
        "function":{
            "name":'extract_review_info'
        }
    }
)

# Print the response
print(response.choices[0].message.tool_calls[0].function.arguments)

