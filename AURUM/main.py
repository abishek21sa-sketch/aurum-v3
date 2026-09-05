from fastapi import FastAPI
from app.core.logger import logger

app = FastAPI(
    title="AURUM Market Intelligence Engine",
    version="0.1.0",
)


@app.get("/")
def root():
    logger.info("Root endpoint called")
    return {
        "status": "online",
        "message": "AURUM backend running",
        "version": "0.1.0",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "aurum-api",
    }