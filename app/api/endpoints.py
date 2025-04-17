import os
import shutil
import uuid
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional
from pydantic import BaseModel

from app.models.image_scanner import ImageScanner

router = APIRouter(prefix="/api", tags=["image-scanner"])

# Initialize the ImageScanner
def get_scanner():
    return ImageScanner()

# Response models
class FoodScanResponse(BaseModel):
    matches: list

class LabelImageResponse(BaseModel):
    success: bool
    message: str
    file_path: Optional[str] = None

@router.post("/scan", response_model=FoodScanResponse)
async def scan_image(
    file: UploadFile = File(...),
    scanner: ImageScanner = Depends(get_scanner)
):
    """
    Scan a food image and compare it with labeled images.
    Returns only the matches with stored labeled images.
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
    
    # Compare with labeled images
    try:
        matches = scanner.compare_images(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image comparison failed: {str(e)}")
    
    return FoodScanResponse(
        matches=matches
    )

@router.post("/label", response_model=LabelImageResponse)
async def label_image(
    file: UploadFile = File(...),
    label: str = Form(...),
    scanner: ImageScanner = Depends(get_scanner)
):
    """
    Upload a new labeled food image to use as a reference for future scans.
    """
    # Create uploads directory if it doesn't exist
    os.makedirs("app/static/uploads", exist_ok=True)
    
    # Generate a unique filename for the temporary upload
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    temp_file_path = f"app/static/uploads/{unique_filename}"
    
    # Save the uploaded file temporarily
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Save the labeled image
    try:
        success, result = scanner.save_labeled_image(temp_file_path, label)
        
        # Remove the temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        
        if success:
            return LabelImageResponse(
                success=True,
                message=f"Image successfully labeled as '{label}'",
                file_path=result
            )
        else:
            raise HTTPException(status_code=500, detail=f"Failed to label image: {result}")
    
    except Exception as e:
        # Clean up temporary file if an exception occurs
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise HTTPException(status_code=500, detail=f"Error labeling image: {str(e)}")

@router.get("/labeled-images")
async def get_labeled_images(scanner: ImageScanner = Depends(get_scanner)):
    """
    Get a list of all labeled food images.
    """
    labeled_images = []
    
    try:
        # Get all labeled images
        for filename in os.listdir(scanner.labeled_images_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                label = os.path.splitext(filename)[0].replace('_', ' ').title()
                labeled_images.append({
                    "label": label,
                    "filename": filename,
                    "url": f"/static/labeled_images/{filename}"
                })
        
        return {"labeled_images": labeled_images}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving labeled images: {str(e)}")