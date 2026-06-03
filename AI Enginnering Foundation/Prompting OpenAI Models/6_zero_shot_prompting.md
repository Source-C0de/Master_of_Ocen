Zero-shot prompting with reviews
As well as answering questions, transforming text, and generating new text, OpenAI's models can also be used for classification tasks, such as categorization and sentiment analysis.

In this exercise, you'll explore using OpenAI's chat models for sentiment classification using reviews from an online shoe store called Toe-Tally Comfortable.

Instructions:
Define a prompt to classify the sentiment of the statements provided using the numbers 1 to 5 (positive to negative).
Create a request to the Chat Completions endpoint to send this prompt to gpt-4o-mini.


__code__
client = OpenAI(api_key="<OPENAI_API_TOKEN>")

# Define a multi-line prompt to classify sentiment
prompt = """____:
1. Unbelievably good!
2. Shoes fell apart on the second use.
3. The shoes look nice, but they aren't very comfortable.
4. Can't wait to show them off!"""

# Create a request to the Chat Completions endpoint
response = client.chat.completions.create(
  model="gpt-4o-mini",
  messages=[{"role": "user", "content": ____}],
  max_completion_tokens=100
)

print(response.choices[0].message.content)


__solution__
client = OpenAI(api_key="<OPENAI_API_TOKEN>")

# Define a multi-line prompt to classify sentiment
prompt = """classify the review 1 to 5 (postive to negative):
1. Unbelievably good!
2. Shoes fell apart on the second use.
3. The shoes look nice, but they aren't very comfortable.
4. Can't wait to show them off!"""

# Create a request to the Chat Completions endpoint
response = client.chat.completions.create(
  model="gpt-4o-mini",
  messages=[{"role": "user", "content": prompt}],
  max_completion_tokens=100
)

print(response.choices[0].message.content)


