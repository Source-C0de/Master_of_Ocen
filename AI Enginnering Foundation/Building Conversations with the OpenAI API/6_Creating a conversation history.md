Creating a conversation history
An online math learning platform called Easy as Pi has contracted you to help them develop an AI tutor. You immediately see that you can build this application by utilizing the OpenAI API, and start to design a simple proof-of-concept (POC) for the major stakeholders at the company to review.

To start, you'll demonstrate how responses to student messages can be stored in a message history, which will enable full conversations.

Instructions:
Send messages to the model in a chat request.
Extract the assistant message from response, convert it to a message dictionary, and append it to messages.


__code__
client = OpenAI(api_key="<OPENAI_API_TOKEN>")

messages = [
    {"role": "system", "content": "You are a helpful math tutor that speaks concisely."},
    {"role": "user", "content": "Explain what pi is."}
]

# Send the chat messages to the model
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=____,
    max_completion_tokens=100
)

# Extract the assistant message from the response
assistant_dict = {"role": "____", "content": ____}

# Add assistant_dict to the messages dictionary
messages.____(assistant_dict)
print(messages)

__solution__
client = OpenAI(api_key="<OPENAI_API_TOKEN>")

messages = [
    {"role": "system", "content": "You are a helpful math tutor that speaks concisely."},
    {"role": "user", "content": "Explain what pi is."}
]

# Send the chat messages to the model
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=messages,
    max_completion_tokens=100
)

# Extract the assistant message from the response
assistant_dict = {"role": "assistant", "content": response.choices[0].message.content}

# Add assistant_dict to the messages dictionary
messages.append(assistant_dict)
print(messages)


