Text summarization
One really common use case for using OpenAI models is summarizing text. This has a ton of applications in business settings, including summarizing reports into concise one-pagers or a handful of bullet points, or extracting the next steps and timelines for different stakeholders.

In this exercise, you'll summarize a passage of text on financial investment (finance_text) into two concise bullet points using a chat completion model.

Instructions:
Use an f-string to insert finance_text into prompt.
Create a request, sending the prompt provided; use a maximum of 400 tokens.

_source_
client = OpenAI(api_key="<OPENAI_API_TOKEN>")

# Use an f-string to format the prompt
prompt = f"""Summarize the following text into two concise bullet points:
{____}"""

# Create a request to the Chat Completions endpoint
response = client.chat.completions.create(
  model="gpt-4o-mini",
  messages=[{"role": "user", "content": prompt}],
  ____
)

print(response.choices[0].message.content)


__solutions__
client = OpenAI(api_key="<OPENAI_API_TOKEN>")

# Use an f-string to format the prompt
prompt = f"""Summarize the following text into two concise bullet points:
{finance_text}"""

# Create a request to the Chat Completions endpoint
response = client.chat.completions.create(
  model="gpt-4o-mini",
  messages=[{"role": "user", "content": prompt}],
  max_completion_tokens=400
)

print(response.choices[0].message.content)

__output__
<script.py> output:
    - Investment involves committing money to various options (like stocks, bonds, and real estate) with the goal of generating profit while assessing risk and potential rewards.  
    - Effective investing requires diversification to minimize risk and can significantly contribute to wealth building and financial security.