Utilizing systems messages
The Chat Completions endpoint supports three different roles to shape the messages sent to the model:

System: controls assistant's behavior
User: instruct the assistant
Assistant: response to user instruction
In this exercise, you'll begin to design an AI system for helping people learn new skills, using a system message to set an appropriate model behavior.

Instructions:
Create a request using both system and user messages to create a study plan to learn to speak Dutch.
Extract and print the assistant's text response.


__code__
client = OpenAI(api_key="<OPENAI_API_TOKEN>")

# Create a request to the Chat Completions endpoint
response = client.chat.completions.create(
  model="gpt-4o-mini",
  max_completion_tokens=150,
  messages=[
    {"role": ____,
     "content": "You are a study planning assistant that creates plans for learning new skills."},
    {"____": "____",
     "____": "I want to learn to speak Dutch."}
  ]
)

# Extract the assistant's text response
print(response.choices[0].____.____)

__solution__
client = OpenAI(api_key="<OPENAI_API_TOKEN>")

# Create a request to the Chat Completions endpoint
response = client.chat.completions.create(
  model="gpt-4o-mini",
  max_completion_tokens=150,
  messages=[
    {"role": "system",
     "content": "You are a study planning assistant that creates plans for learning new skills."},
    {"role": "user",
     "content": "I want to learn to speak Dutch."}
  ]
)

# Extract the assistant's text response
print(response.choices[0].message.content)


__output__
That's a great choice! Learning Dutch can be enjoyable and rewarding, and having a structured plan can help you progress efficiently. Below is a 12-week study plan to help you get started with speaking Dutch. You can adjust the intensity and duration according to your schedule:

### Week 1-2: Basics of Dutch
- **Daily Goals**: 30 minutes to 1 hour of study
  - **Vocabulary**: Learn basic greetings, numbers, colors, and essential phrases.
  - **Pronunciation**: Familiarize yourself with Dutch phonetics and common pronunciation rules.
  - **Resources**: Use language apps like Duolingo or Babbel for vocabulary and pronunciation practice.
  
### Week 3-4: Building Vocabulary and

