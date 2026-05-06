from fastapi import FastAPI

from app.db.init_db import init_db
from app.routers.chat import router as chat_router
from app.routers.documents import router as documents_router


app = FastAPI(title="intra-Q Document API")


@app.on_event("startup")
def on_startup() -> None:
    # Create SQLite tables when the application starts.
    init_db()


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(documents_router, prefix="/api/documents", tags=["documents"])
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])

