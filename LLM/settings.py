import os
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()
class settings(BaseModel):
    # Gemini
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    gemini_embedding_model: str = os.getenv("GEMINI_EMBEDDING_MODEL", "models/text-embedding-004")

    # VectorDB
    chroma_persist_dir: str = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma_db")
    chroma_collection_name: str = os.getenv("CHROMA_COLLECTION_NAME", "gucci_hr_knowledge")

    # RAG
    rag_top_k: int = int(os.getenv("RAG_TOP_K", "5"))
    rag_similarity_threshold: float = float(os.getenv("RAG_SIMILARITY_THRESHOLD", "0.75"))
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "512"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "64"))

    # Agent
    max_iterations: int = int(os.getenv("MAX_ITERATIONS", "10"))
    temperature: float = float(os.getenv("TEMPERATURE", "0.3"))
    max_output_tokens: int = int(os.getenv("MAX_OUTPUT_TOKENS", "2048"))

    # System
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    environment: str = os.getenv("ENVIRONMENT", "development")

    def validate(self):
        if not self.gemini_api_key or self.gemini_api_key == "your_gemini_api_key_here":
            raise ValueError("❌ GEMINI_API_KEY chưa được cấu hình trong file .env")
        return self


settings = settings()