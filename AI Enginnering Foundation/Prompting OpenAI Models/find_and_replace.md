Find and replace
Find-and-replace tools have been around for decades, but they are often limited to identifying and replacing exact words or phrases. You've been provided with a block of text discussing cars, and you'll use a chat completion model to update the text to discuss planes instead, updating the text appropriately.

Warning: if you send many requests or use lots of tokens in a short period, you may hit your rate limit and see an openai.error.RateLimitError. If you see this error, please wait a minute for your quota to reset and you should be able to begin sending more requests.


Instructions:

Create a request to the Chat Completions endpoint; use a maximum of 100 tokens.
Extract and print the text response from the API.

__code__

client = OpenAI(api_key="<OPENAI_API_TOKEN>")

prompt="""Replace car with plane and adjust phrase:
A car is a vehicle that is typically powered by an internal combustion engine or an electric motor. It has four wheels, and is designed to carry passengers and/or cargo on roads or highways. Cars have become a ubiquitous part of modern society, and are used for a wide variety of purposes, such as commuting, travel, and transportation of goods. Cars are often associated with freedom, independence, and mobility."""

# Create a request to the Chat Completions endpoint
response = client.chat.completions.create(
  model="gpt-4o-mini",
  messages=[{"role": "user", "____": ____}],
  ____
)

# Extract and print the response text
print(response.choices[0].____.____)


__solution__
client = OpenAI(api_key="<OPENAI_API_TOKEN>")

prompt=f"""Replace car with plane and adjust phrase:
A car is a vehicle that is typically powered by an internal combustion engine or an electric motor. It has four wheels, and is designed to carry passengers and/or cargo on roads or highways. Cars have become a ubiquitous part of modern society, and are used for a wide variety of purposes, such as commuting, travel, and transportation of goods. Cars are often associated with freedom, independence, and mobility."""

# Create a request to the Chat Completions endpoint
response = client.chat.completions.create(
  model="gpt-4o-mini",
  messages=[{"role": "user", "content": prompt}],
  max_completion_tokens=100
)

# Extract and print the response text
print(response.choices[0].message.content)