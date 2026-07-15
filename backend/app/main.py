from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.ingest import router as ingest_router
from app.api.v1.reels import router as reels_router
from app.api.v1.sync import router as sync_router
from app.api.v1.labels import router as labels_router
from app.api.v1.analysis import router as analysis_router

app = FastAPI(title="Laboratorio de Contenido API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # v1 sin auth/cookies; '*' + credentials es combo inválido
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest_router, prefix="/api/v1")
app.include_router(reels_router, prefix="/api/v1")
app.include_router(sync_router, prefix="/api/v1")
app.include_router(labels_router, prefix="/api/v1")
app.include_router(analysis_router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok"}
