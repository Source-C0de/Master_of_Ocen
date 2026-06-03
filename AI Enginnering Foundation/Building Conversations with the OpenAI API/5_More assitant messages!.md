More assistant messages!
Expand on your previous messages to provide additional examples, stored as example1, response1, example2, response2, example3, and response3.

Let's see if we can get this model outputting information in the desired format!

Instructions:
Expand your previous messages to include additional examples of other countries, which are stored as example1, response1, example2, response2, example3, and response3.


__code__
client = OpenAI(api_key="<OPENAI_API_TOKEN>")

response = client.chat.completions.create(
   model="gpt-4o-mini",
   # Add in the extra examples and responses
   messages=[
       {"role": "system", "content": "You are a helpful Geography tutor that generates concise summaries for different countries."},
       {"role": "user", "content": "Give me a quick summary of Portugal."},
       {"role": "assistant", "content": "Portugal is a country in Europe that borders Spain. The capital city is Lisboa."},
       {"role": "user", "content": ____},
       {"role": "assistant", "content": ____},
       {"role": "user", "content": ____},
       {"role": "assistant", "content": ____},
       {"role": "user", "content": ____},
       {"role": "assistant", "content": ____},
       {"role": "user", "content": "Give me a quick summary of Greece."}
   ]
)

print(response.choices[0].message.content)


__solution__
client = OpenAI(api_key="<OPENAI_API_TOKEN>")

response = client.chat.completions.create(
   model="gpt-4o-mini",
   # Add in the extra examples and responses
   messages=[
       {"role": "system", "content": "You are a helpful Geography tutor that generates concise summaries for different countries."},
       {"role": "user", "content": "Give me a quick summary of Portugal."},
       {"role": "assistant", "content": "Portugal is a country in Europe that borders Spain. The capital city is Lisboa."},
       {"role": "user", "content": ____},
       {"role": "assistant", "content": ____},
       {"role": "user", "content": ____},
       {"role": "assistant", "content": ____},
       {"role": "user", "content": ____},
       {"role": "assistant", "content": ____},
       {"role": "user", "content": "Give me a quick summary of Greece."}
   ]
)

print(response.choices[0].message.content)


__output__