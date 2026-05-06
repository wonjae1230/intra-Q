from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.settings import ALLOWED_ORIGINS
from app.database.init_db import init_db
from app.routers.chat import router as chat_router
from app.routers.documents import router as documents_router
from app.schemas.common import HealthResponse
from app.utils.logging import configure_logging


configure_logging()

app = FastAPI(
    title="intra-Q Document API",
    description="FastAPI-based RAG chatbot backend for PDF upload, chunking, document retrieval, and mock chat responses.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    # Create SQLite tables when the application starts.
    init_db()


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Return the operational status of the backend service.",
)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok")


app.include_router(documents_router, prefix="/api/documents", tags=["documents"])
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])

