
from langchain.vectorstores import FAISS
from langchain.embeddings import GoogleGenerativeAIEmbeddings

embeddings = GoogleGenerativeAIEmbeddings()
db = FAISS.from_texts([], embeddings)

def add(text):
    db.add_texts([text])
