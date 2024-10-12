import os
from dotenv import load_dotenv
import openai

# Load the .env file
load_dotenv()

# Set the OpenAI API key from the environment
api_key = os.getenv('OPENAI_API_KEY')

if not api_key:
    raise ValueError("OpenAI API key is not set in the environment variables.")

# Set the OpenAI API key in the OpenAI library
openai.api_key = api_key

# Optionally, if you want to use openai.Client explicitly
openai_client = openai