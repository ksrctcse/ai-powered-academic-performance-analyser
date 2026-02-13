
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings

embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
db = None

def add(text):
    global db
    if db is None:
        # Initialize FAISS with the first text
        db = FAISS.from_texts([text], embeddings)
    else:
        db.add_texts([text])
