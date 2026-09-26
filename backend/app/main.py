from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.agents.orchestrator import run_query

app = FastAPI(title="ORCA", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"name": "ORCA", "problem_statement": "SIH-26176", "status": "running"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/api/query")
async def query(q: str, location: str = "Kakinada"):
    return await run_query(q, location)
