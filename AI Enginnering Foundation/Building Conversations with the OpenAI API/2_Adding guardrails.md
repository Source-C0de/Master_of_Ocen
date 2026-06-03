Adding guardrails
One of the most popular uses of system messages is to add guardrails, which places restrictions on model outputs.

In this exercise, you'll place a restriction on model outputs preventing learning plans not related to languages, as your system is beginning to find its niche in that space. You'll design a custom message for users requesting these type of learning plans so they understand this change.

Instructions:
Complete the chat request, providing the system message in sys_msg and test a user message containing a non-language-related skill, such as rollerskating.


__code__
client = OpenAI(api_key="<OPENAI_API_TOKEN>")

sys_msg = """You are a study planning assistant that creates plans for learning new skills.

If these skills are non related to languages, return the message:

'Apologies, to focus on languages, we no longer create learning plans on other topics.'
"""

# Create a request to the Chat Completions endpoint
response = client.chat.completions.create(
  model="gpt-4o-mini",
  messages=[
    {"role": "____", "content": ____},
    {"role": "user", "content": "Help me learn to ____."}
  ]
)

print(response.choices[0].message.content)


__code__
client = OpenAI(api_key="<OPENAI_API_TOKEN>")

sys_msg = """You are a study planning assistant that creates plans for learning new skills.

If these skills are non related to languages, return the message:

'Apologies, to focus on languages, we no longer create learning plans on other topics.'
"""

# Create a request to the Chat Completions endpoint
response = client.chat.completions.create(
  model="gpt-4o-mini",
  messages=[
    {"role": "system", "content": sys_msg},
    {"role": "user", "content": "Help me learn to ${sys_msg}."}
  ]
)

print(response.choices[0].message.content)


__output__
Apologies, to focus on languages, we no longer create learning plans on other topics.