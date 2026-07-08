import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load env variables
load_dotenv()

from db.session import engine, Base
from db.seed import seed_db
from api import hcps, interactions, followups, agent

# Auto create tables and seed database
try:
    print("Initializing database...")
    Base.metadata.create_all(bind=engine)
    print("Tables verified/created. Running seeder...")
    seed_db()
    print("Database seeding completed/verified.")
except Exception as e:
    print(f"Database initialization warning: {e}")

app = FastAPI(
    title="AI-First CRM - HCP Log Interaction API",
    description="Backend API for logging and managing interactions with HCPs",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for dev
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(hcps.router, prefix="/api")
app.include_router(interactions.router, prefix="/api")
app.include_router(followups.router, prefix="/api")
app.include_router(agent.router, prefix="/api")

@app.get("/")
def read_root():
    return {
        "status": "healthy",
        "service": "AI-First CRM HCP API",
        "database": os.getenv("DATABASE_URL", "sqlite:///./aicrm.db").split("://")[0]
    }
