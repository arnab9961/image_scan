import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import uvicorn

from app.api.endpoints import router as api_router

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Food Nutritional Scanner API",
    description="API for scanning food images and providing nutritional information using Google AI",
    version="1.0.0"
)

# Create uploads folder if it doesn't exist
os.makedirs("app/static/uploads", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include API router
app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)