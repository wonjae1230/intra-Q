from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.init_db import init_db
from app.routers.auth import router as auth_router
from app.routers.chat import router as chat_router
from app.routers.chat_history import router as chat_history_router
from app.routers.curriculum import router as curriculum_router
from app.routers.documents import router as documents_router
from app.schemas.common import HealthResponse
from app.utils.logging import configure_logging


configure_logging()

app = FastAPI(
    title="intra-Q Document API",
    description="FastAPI-based RAG chatbot backend for PDF upload, chunking, document retrieval, and chat responses.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
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


app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(documents_router, prefix="/api/documents", tags=["documents"])
app.include_router(curriculum_router, prefix="/api/curriculum", tags=["curriculum"])
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
app.include_router(chat_history_router, prefix="/api/chat/history", tags=["chat-history"])
