import os
import shutil
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import Optional
from pydantic import BaseModel

from app.models.image_scanner import ImageScanner

router = APIRouter(prefix="/api", tags=["image-scanner"])

# Initialize the ImageScanner
def get_scanner():
    return ImageScanner()

# Response models
class NutritionalInfo(BaseModel):
    food_item: str
    protein: str
    details: str
    ingredients: str
    calories: str
    fat: str
    carbs: str
    error: Optional[str] = None

@router.post("/scan", response_model=NutritionalInfo)
async def scan_food_image(
    file: UploadFile = File(...),
    scanner: ImageScanner = Depends(get_scanner)
):
    """
    Scan a food image using Google API to get nutritional information
    """
    # Create uploads directory if it doesn't exist
    os.makedirs("app/static/uploads", exist_ok=True)
    
    # Generate a unique filename
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = f"app/static/uploads/{unique_filename}"
    
    # Save the uploaded file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Analyze the food image
    try:
        nutritional_info = scanner.scan_food_image(file_path)
        return nutritional_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image analysis failed: {str(e)}")