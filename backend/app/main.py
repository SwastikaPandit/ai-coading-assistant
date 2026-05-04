from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router

app = FastAPI(
    title="AI Coding Assistant",
    description="Multi-agent code generation pipeline",
    version="1.0.0",
)

# Allow React frontend to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # We'll restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def health_check():
    return {"status": "ok", "message": "AI Coding Assistant API is running"}