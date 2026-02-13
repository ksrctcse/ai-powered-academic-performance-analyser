
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import logging
import os

logger = logging.getLogger(__name__)

embeddings = None
db = None

def get_embeddings():
    """Get embeddings if API key is available"""
    global embeddings
    if embeddings is None:
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key and api_key != "your-google-api-key":
            try:
                embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
            except Exception as e:
                logger.warning(f"Could not initialize embeddings: {str(e)}")
                return None
    return embeddings

def add(text):
    """
    Add text to vector store.
    Returns None if vector store is unavailable (graceful degradation).
    """
    global db
    
    # Try to get embeddings
    embed_model = get_embeddings()
    if embed_model is None:
        logger.warning("Vector store disabled - embeddings not available")
        return None
    
    try:
        if db is None:
            # Initialize FAISS with the first text
            db = FAISS.from_texts([text], embed_model)
        else:
            db.add_texts([text])
        return True
    except Exception as e:
        logger.error(f"Error adding to vector store: {str(e)}")
        return None
