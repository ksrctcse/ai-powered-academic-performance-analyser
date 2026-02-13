
from langchain_google_genai import GoogleGenerativeAI

llm = GoogleGenerativeAI(model="gemini-2.5-pro")

PROMPT = '''
LOW=1 MEDIUM=2 HIGH=3
Calculate unit progress from concept progress.
Return only percentage.
'''

def calculate(data):
    return llm(PROMPT + str(data))
