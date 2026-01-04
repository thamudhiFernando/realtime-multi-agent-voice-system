# app/utils/tracing.py
import os
from langsmith import Client

# Initialize LangSmith client
# You can store your API key in a .env file as LANGSMITH_API_KEY
client = Client(api_key=os.getenv("LANGSMITH_API_KEY"))

# Optional: quick test
print("LangSmith client initialized:", client is not None)
