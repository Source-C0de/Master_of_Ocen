Avoiding inconsistent responses
The team you were working with on the previous project is enthusiastic about the reply generator and asks you if more reviews can be processed. However, some reviews have been mixed up with other documents, and you're being asked not to return responses if the text doesn't contain a review, or relevant information. For example, the review you're considering now doesn't contain a product name, and so there should be no product name being returned.

In this exercise, the get_response() function, and messages and function_definition variables have been preloaded. The messages already contain the user's review, and function_definition contains the two functions: one asking to extract structured data, and one asking to generate a reply.

Instructions
100 XP
Modify the messages to ask the model not to assume any values for the responses.



__CODE__
client = OpenAI(api_key="<OPENAI_API_TOKEN>")

# Modify the messages
____

response = get_response(messages, function_definition)

print(response)


__SOLUTION__
client = OpenAI(api_key="<OPENAI_API_TOKEN>")

# Modify the messages
messages.append(
    {
        "role":"system",
        "content":"Don't assume any values for response"
    }
)

response = get_response(messages, function_definition)

print(response)


