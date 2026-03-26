
import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAI

load_dotenv()

# Lazy initialization - only create LLM when calculate() is called
_llm = None

def get_llm():
    """Get or create LLM instance (lazy loading)"""
    global _llm
    if _llm is None:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key or api_key == "your-google-api-key":
            raise ValueError(
                "GOOGLE_API_KEY not configured. "
                "Please set the GOOGLE_API_KEY environment variable in .env file."
            )
        _llm = GoogleGenerativeAI(model="gemini-2.5-pro", temperature=0.3)
    return _llm

PROMPT = '''
LOW=1 MEDIUM=2 HIGH=3
Calculate unit progress from concept progress.
Return only percentage.
'''

def calculate(data):
    llm = get_llm()
    return llm(PROMPT + str(data))
