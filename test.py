# from google import genai
# from google.genai import types

# # client = genai.Client()
# client = genai.Client(api_key="AIzaSyAhjN2PNNQwAQN6GSav-VdkdR_ujVjmOpE")
# texts = "This is a review, check if it seems AI generated or human written and Respond with 'AI' or 'Human'.\n\nReview : This product exceeded my expectations in every conceivable way. From the moment I started using it, I noticed a significant improvement in overall performance and usability. The design is intuitive, and the functionality is both robust and user-friendly. Based on my analysis, this solution represents an optimal choice for individuals seeking high efficiency and reliability. I would highly recommend it to anyone looking for a top-tier experience" 
# response = client.models.generate_content(
#     model="gemini-2.5-flash",
#     contents=texts,
#     config=types.GenerateContentConfig(
#         thinking_config=types.ThinkingConfig(thinking_budget=1024)
#         # Turn off thinking:
#         # thinking_config=types.ThinkingConfig(thinking_budget=0)
#         # Turn on dynamic thinking:
#         # thinking_config=types.ThinkingConfig(thinking_budget=-1)
#     ),
# )

# print(response.text)
import google.generativeai as genai

# Configure the API - use environment variables for API keys in production!
genai.configure(api_key="AIzaSyAhjN2PNNQwAQN6GSav-VdkdR_ujVjmOpE")

# Initialize the model
model = genai.GenerativeModel('gemini-1.5-flash')

# Create the prompt
prompt = """Analyze this review and respond with exactly one word - either 'AI' or 'Human':
Review: This product exceeded my expectations in every conceivable way. From the moment I started using it, I noticed a significant improvement in overall performance and usability. The design is intuitive, and the functionality is both robust and user-friendly. Based on my analysis, this solution represents an optimal choice for individuals seeking high efficiency and reliability. I would highly recommend it to anyone looking for a top-tier experience"""

# Generate the response
response = model.generate_content(
    prompt,
    generation_config=genai.types.GenerationConfig(
        temperature=0.3,
        top_p=0.9,
        top_k=40,
        max_output_tokens=2048  # More tokens for complex reasoning
    )
)

print(response.text)