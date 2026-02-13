
from langchain_google_genai import GoogleGenerativeAI

llm = GoogleGenerativeAI(model="gemini-pro")

PROMPT = 'Classify complexity as HIGH MEDIUM or LOW. Return one word.'

def classify(concept):
    return llm(PROMPT + concept)
