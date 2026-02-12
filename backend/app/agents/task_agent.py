
from langchain.llms import GoogleGenerativeAI

llm = GoogleGenerativeAI(model="gemini-pro")

PROMPT = '''
Generate academic tasks based on concept complexity.
Return JSON tasks.
'''

def generate(concept, complexity):
    return llm(PROMPT + concept + complexity)
