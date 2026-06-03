Generating a product description
Imagine you're writing marketing copy for SonicPro headphones. Your goal is to generate a persuasive product description using the OpenAI API.

Test how different prompting techniques, response lengths, and temperature settings influence the output!

Instructions:
Create a detailed prompt to generate a product description for SonicPro headphones, including:
Active noise cancellation (ANC)
40-hour battery life
Foldable design
Experiment with max_completion_tokens and temperature settings to see how they affect the output


__code__
client = OpenAI(api_key="<OPENAI_API_TOKEN>")

# Create a detailed prompt
prompt = """
____
"""

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": prompt}],
    # Experiment with max_completion_tokens and temperature settings
    max_completion_tokens=____,
    temperature=____
)

print(response.choices[0].message.content)


__solution__
client = OpenAI(api_key="<OPENAI_API_TOKEN>")

# Create a detailed prompt
prompt = f"""
Create a detailed prompt to generate a product description for SonicPro headphones,, including: 
1. Active noise cancellation (ANC)
2. 40-hour battery life
3. Foldable design
"""

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": prompt}],
    # Experiment with max_completion_tokens and temperature settings
    max_completion_tokens=400,
    temperature=1
)

print(response.choices[0].message.content)


__output__
based on changes output becomes changed