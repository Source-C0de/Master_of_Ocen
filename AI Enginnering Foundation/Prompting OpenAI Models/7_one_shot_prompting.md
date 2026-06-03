One-shot prompting: will it be enough?
As you saw, there's room for improvement in your initial prompt. Try adding an example Love these! = 5 and including = after each review to see if you can get more consistent formatting and more accurate numbers.

Instructions:
Add the example Love these! = 5 to the start of the prompt, and add = after each review in the prompt to indicate how the result should be formatted.


__code__
client = OpenAI(api_key="<OPENAI_API_TOKEN>")

# Add the example to the prompt
prompt = """Classify sentiment as 1-5 (negative to positive):
1. ____
2. Unbelievably good! ____
3. Shoes fell apart on the second use. ____
4. The shoes look nice, but they aren't very comfortable. ____
5. Can't wait to show them off! ____"""

response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}], max_completion_tokens=100)
print(response.choices[0].message.content

__solution__
client = OpenAI(api_key="<OPENAI_API_TOKEN>")

# Add the example to the prompt
prompt = """Classify sentiment as 1-5 (negative to positive):
1. Love these! = 5 
2. Unbelievably good! = 
3. Shoes fell apart on the second use. = 
4. The shoes look nice, but they aren't very comfortable. = 
5. Can't wait to show them off! = """

response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}], max_completion_tokens=100)


