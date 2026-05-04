from fastapi import FastAPI

from app.api.documents import router as documents_router


app = FastAPI(title="intra-Q Document API")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(documents_router, prefix="/api/documents", tags=["documents"])
