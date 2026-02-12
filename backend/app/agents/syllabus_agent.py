
from langchain.llms import GoogleGenerativeAI

llm = GoogleGenerativeAI(model="gemini-pro")

PROMPT = '''
Extract syllabus into units and concepts.
Return JSON only.
'''

def analyze(text):
    return llm(PROMPT + text)
