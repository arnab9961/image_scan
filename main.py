import os
import shutil
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from typing import Optional
import uvicorn

from app.models.image_scanner import ImageScanner
from app.api.endpoints import router as api_router

# Create FastAPI app
app = FastAPI(
    title="Food Image Scanner API",
    description="API for scanning food images using OpenCV",
    version="1.0.0"
)

# Create folders if they don't exist
os.makedirs("app/static/uploads", exist_ok=True)
os.makedirs("app/static/labeled_images", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include API router
app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)