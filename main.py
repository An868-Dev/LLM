import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

from LLM.settings import settings
from LLM.supervisor import Supervisor
from LLM.knowledge import HR_KNOWLEDGE_BASE

# ─── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger(__name__)

# ─── Global Supervisor ────────────────────────────────────────────────────────
supervisor: Optional[Supervisor] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global supervisor

    logger.info("🚀 Starting CHRO AI System...")
    settings.validate()

    supervisor = Supervisor()

    stats = supervisor.vector_store.get_stats()
    if stats["total_documents"] == 0:
        logger.info("📥 Ingesting HR knowledge base...")
        supervisor.vector_store.ingest_documents(HR_KNOWLEDGE_BASE)
        logger.info(f"✅ Ingested {len(HR_KNOWLEDGE_BASE)} documents")

    logger.info("✅ CHRO AI System ready!")
    yield

    logger.info("👋 Shutting down CHRO AI System...")


# ─── FastAPI App ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="Gucci Group CHRO AI",
    description="AI-powered Chief HR Officer cho Gucci Group",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Schemas ──────────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"


class ChatResponse(BaseModel):
    response: str
    intent: str
    rag_documents_used: int
    session_id: str


class IngestRequest(BaseModel):
    documents: List[dict]


# ─── Routes ───────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "system": "Gucci Group CHRO AI",
        "status": "operational",
        "model": settings.gemini_model,
        "docs": "/docs"
    }


@app.get("/health")
def health():
    if supervisor is None:
        raise HTTPException(503, "System not initialized")
    return supervisor.get_system_status()


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    if supervisor is None:
        raise HTTPException(503, "System not initialized")

    if not request.message.strip():
        raise HTTPException(400, "Message cannot be empty")

    state = supervisor.run(request.message)

    return ChatResponse(
        response=state.final_response,
        intent=state.router_output.intent if state.router_output else "unknown",
        rag_documents_used=len(state.rag_results),
        session_id=request.session_id or "default"
    )


@app.post("/reset")
def reset_conversation():
    """Reset hội thoại."""
    if supervisor:
        supervisor.reset_conversation()
    return {"status": "conversation reset"}


@app.post("/ingest")
def ingest_documents(request: IngestRequest):
    if supervisor is None:
        raise HTTPException(503, "System not initialized")

    count = supervisor.vector_store.ingest_documents(request.documents)
    return {"ingested": count, "total": supervisor.vector_store.get_stats()["total_documents"]}


@app.get("/knowledge/stats")
def knowledge_stats():
    """Thống kê VectorDB."""
    if supervisor is None:
        raise HTTPException(503, "System not initialized")
    return supervisor.vector_store.get_stats()


# ─── Run ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)