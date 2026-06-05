Project Instructions
You'll create a chatbot using the OpenAI API to generate responses to the following Parisian tourist questions:

How far away is the Louvre from the Eiffel Tower (in miles) if you are driving?
Where is the Arc de Triomphe?
What are the must-see artworks at the Louvre Museum?
Create a list of dictionaries called conversation that lists the 'role' and 'content' for each question and response. You should start the conversation with a 'system' message to set the model's behavior, and use a temperature of 0.0 and maximum number of tokens of 100:
[ {"role": "system", "content": ...}, {"role": "user", "content": ...}, ... ]


