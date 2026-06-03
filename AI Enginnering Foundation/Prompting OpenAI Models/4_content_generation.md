Content generation
AI is playing a much greater role in content generation, from creating marketing content such as blog post titles to creating outreach email templates for sales teams.

In this exercise, you'll harness AI to generate a catchy slogan for a new restaurant. Feel free to test out different prompts, such as varying the type of cuisine (Italian, Chinese, etc.) or the type of restaurant (fine-dining, fast-food, etc.), to see how the response changes.

Instructions:
Create a request to create a slogan for a new restaurant; set the maximum number of tokens to 100.


__code__
client = OpenAI(api_key="<OPENAI_API_TOKEN>")

# Create a request to the Chat Completions endpoint
response = client.chat.completions.create(
  model="gpt-4o-mini",
  messages=[{"role": "user", "content": "____"}],
  ____
)

print(response.choices[0].message.content)

__sol__
client = OpenAI(api_key="<OPENAI_API_TOKEN>")

# Create a request to the Chat Completions endpoint
response = client.chat.completions.create(
  model="gpt-4o-mini",
  messages=[{"role": "user", "content": "Generate a catcy slogan for new restaurent.It's a italian fine-dining & fast-food based."}],
  max_completion_tokens=100
)

print(response.choices[0].message.content)

__output__:
every time new prompt you are able to see new response. 