from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.db.connection import engine
from src.models.base import Base
from src.api.routes import router
from src.config import config

# Initialize database
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"Warning: Could not create tables: {e}")
    
# Create app
app = FastAPI(
    title="Engineering Risk Intelligence Platform",
    description="Risk intelligence for engineering decisions",
    version="0.1.0",
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=config.API_PORT,
        reload=config.DEBUG,
    )