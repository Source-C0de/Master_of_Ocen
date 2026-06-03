Adding assistant messages
Chat models are great for creating conversational applications, but they can be further improved by providing part of a conversation for the model to build on.

Improve this geography tutor application by including this example student prompt and ideal model response in the messages:

Example Question: Give me a quick summary of Portugal.
Example Answer: Portugal is a country in Europe that borders Spain. The capital city is Lisboa.


Instructions:
Add the example question and answer provided as a user-assistant pair in the messages sent to the model.
Example Question: Give me a quick summary of Portugal.
Example Answer: Portugal is a country in Europe that borders Spain. The capital city is Lisboa.


__code__
client = OpenAI(api_key="<OPENAI_API_TOKEN>")

response = client.chat.completions.create(
    model="gpt-4o-mini",
    # Add a user and assistant message for in-context learning
    messages=[
        {"role": "system", "content": "You are a helpful Geography tutor that generates concise summaries for different countries."},
        ____,
        ____,
        {"role": "user", "content": "Give me a quick summary of Greece."}
    ]
)

print(response.choices[0].message.content)


__solution__
client = OpenAI(api_key="<OPENAI_API_TOKEN>")

response = client.chat.completions.create(
    model="gpt-4o-mini",
    # Add a user and assistant message for in-context learning
    messages=[
        {"role": "system", 
        "content": "You are a helpful Geography tutor that generates concise summaries for different countries."},
        {"role": "user",
        "content": " Give me a quick summary of Portugal."},
        {
            "role": "assistant",
            "content": "Portugal is a country in Europe that borders Spain. The capital city is Lisboa."
        },
        {"role": "user", "content": "Give me a quick summary of Greece."}
    ]
)

print(response.choices[0].message.content)

__output__
Greece is a southeastern European country known for its rich history and contributions to Western culture. It consists of a mainland peninsula and numerous islands, with Athens as the capital. Greece is famous for its ancient ruins, such as the Acropolis, and is also recognized for its beautiful landscapes, Mediterranean cuisine, and vibrant traditions. The country has a strong tourism industry and is a member of the European Union.