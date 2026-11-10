 
from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db

# Create FastAPI application first
app = FastAPI(
    title="EcoSage AI",
    description="Environmental Intelligence Platform",
    version="1.0.0"
)

# Home endpoint
@app.get("/")
def home():
    return {
        "message": "Welcome to EcoSage AI",
        "status": "running"
    }

# Application health check
@app.get("/health")
def health():
    return {
        "status": "healthy"
    }

# Database health check
@app.get("/health/db")
def database_health(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT version()")).scalar_one()

    return {
        "status": "connected",
        "database": "ecosage_db",
        "version": result
    }
