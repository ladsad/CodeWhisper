from fastapi import FastAPI
from api import analysis

app = FastAPI(title="CodeWhisper API", version="0.1.0")

app.include_router(analysis.router, prefix="/api/v1", tags=["analysis"])

@app.get("/")
def read_root():
    return {"message": "Welcome to CodeWhisper API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
