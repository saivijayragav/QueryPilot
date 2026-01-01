from dotenv import load_dotenv
import os
from langchain.chat_models import init_chat_model

load_dotenv()

key = os.getenv("GOOGLE_API_KEY")
print(f"Key loaded: {key[:5]}...{key[-5:] if key else 'None'}")

try:
    llm = init_chat_model("google_genai:gemini-2.0-flash")
    print("Invoking LLM...")
    response = llm.invoke("Hi")
    print(f"Success: {response.content}")
except Exception as e:
    print(f"Key Error: {e}")
