# openai_config.py
import os
from openai import OpenAI

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))