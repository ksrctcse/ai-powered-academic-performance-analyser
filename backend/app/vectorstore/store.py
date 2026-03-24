
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
                # Try newer embedding model first, fallback to older one
                embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
                logger.info("Using text-embedding-004 model for embeddings")
            except Exception as e:
                logger.warning(f"Could not initialize with text-embedding-004, trying embedding-001: {str(e)}")
                try:
                    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
                    logger.info("Using embedding-001 model for embeddings")
                except Exception as e2:
                    logger.error(f"Could not initialize embeddings with any model: {str(e2)}")
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
        if not text or not text.strip():
            logger.warning("Empty text provided to vector store")
            return None
            
        if db is None:
            # Initialize FAISS with the first text
            logger.info(f"Initializing FAISS vector store with text of length {len(text)}")
            db = FAISS.from_texts([text], embed_model)
            logger.info("FAISS vector store initialized successfully")
        else:
            logger.info(f"Adding text of length {len(text)} to vector store")
            db.add_texts([text])
            logger.info("Text added to vector store successfully")
        return True
    except Exception as e:
        logger.error(f"Error adding to vector store: {str(e)}", exc_info=True)
        # Reset db on error to allow retry
        db = None
        return None
