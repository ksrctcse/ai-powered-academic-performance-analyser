
from langchain_google_genai import GoogleGenerativeAI

llm = GoogleGenerativeAI(model="gemini-2.5-pro")

PROMPT = '''
Generate academic tasks based on concept complexity.
Return JSON tasks.
'''

def generate(concept, complexity):
    return llm(PROMPT + concept + complexity)
