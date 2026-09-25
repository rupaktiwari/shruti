# app/services/rag_service.py
from pathlib import Path

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from app.core.logging_config import get_logger

logger = get_logger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHROMA_DIRECTORY = PROJECT_ROOT / "chroma_db"
COLLECTION_NAME = "shruti_knowledge"

class RAGService:
    def __init__(self, persist_directory: str | Path = CHROMA_DIRECTORY):
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        self.vector_db = Chroma(
            persist_directory=str(persist_directory),
            collection_name=COLLECTION_NAME,
            embedding_function=self.embeddings,
        )
        logger.info("RAG vector store loaded from %s", persist_directory)

    def retrieve(self, query: str, k: int = 2):
        results = self.vector_db.similarity_search(query, k=k)
        if not results:
            return None
        return "\n".join(doc.page_content for doc in results)

rag_service = RAGService()