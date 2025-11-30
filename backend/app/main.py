# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import Base, engine
from app.api import auth

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

app = FastAPI(title="ElectroHub API")

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/status")
def status_endpoint():
    return {"service": "electrohub-api", "status": "ok"}
