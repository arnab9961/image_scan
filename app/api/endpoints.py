import os
import shutil
import uuid
import json  # Add this import
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import Optional, Dict, Any
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
from app.models.image_scanner import ImageScanner

load_dotenv()

router = APIRouter(prefix="/api", tags=["image-scanner"])

# Initialize the ImageScanner
def get_scanner():
    return ImageScanner()

def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY in .env file.")
    return OpenAI(api_key=api_key)


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

class HealthData(BaseModel):
    oxygen_saturation: float
    pulse_rate: float
    blood_pressure: str
    body_temperature: float
    blood_sugar: float
    rest_urine: float
    water_intake: float

class AnalysisResponse(BaseModel):
    abnormal_readings: Dict[str, Any]
    recommendation: str    

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
    
@router.post("/health/analyze", response_model=AnalysisResponse)
async def analyze_health_data(
    health_data: HealthData,
    openai_client: OpenAI = Depends(get_openai_client)
):
    """
    Analyze health metrics and provide recommendations
    """
    # Normal ranges for health metrics
    normal_ranges = {
        "oxygen_saturation": (80, 100),
        "pulse_rate": (50, 100),
        "blood_pressure": "80-120",  # This is simplified and will need custom parsing
        "body_temperature": (95, 105),
        "blood_sugar": (70, 140),
        "rest_urine": (800, 2000),
        "water_intake": (2.7, 3.7)
    }
    
    
    # Check for abnormal readings
    abnormal_readings = {}
    
    # Check oxygen saturation
    if health_data.pulse_rate < normal_ranges["pulse_rate"][0] or health_data.pulse_rate > normal_ranges["pulse_rate"][1]:
        abnormal_readings["pulse_rate"] = {
            "value": health_data.pulse_rate,
            "normal_range": normal_ranges["pulse_rate"]
        }
    
    # Check blood pressure (simplified)
    bp_parts = health_data.blood_pressure.split("/")
    if len(bp_parts) == 2:
        try:
            systolic = int(bp_parts[0])
            diastolic = int(bp_parts[1])
            bp_normal_parts = normal_ranges["blood_pressure"].split("-")
            systolic_normal = int(bp_normal_parts[0])
            diastolic_normal = int(bp_normal_parts[1])
            
            if systolic < systolic_normal or systolic > diastolic_normal or diastolic < systolic_normal or diastolic > diastolic_normal:
                abnormal_readings["blood_pressure"] = {
                    "value": health_data.blood_pressure,
                    "normal_range": normal_ranges["blood_pressure"]
                }
        except:
            abnormal_readings["blood_pressure"] = {
                "value": health_data.blood_pressure,
                "normal_range": normal_ranges["blood_pressure"],
                "note": "Invalid format. Should be systolic/diastolic (e.g., 120/80)"
            }
    
    # Check body temperature
    if health_data.body_temperature < normal_ranges["body_temperature"][0] or health_data.body_temperature > normal_ranges["body_temperature"][1]:
        abnormal_readings["body_temperature"] = {
            "value": health_data.body_temperature,
            "normal_range": normal_ranges["body_temperature"]
        }
    
    # Check blood sugar
    if health_data.blood_sugar < normal_ranges["blood_sugar"][0] or health_data.blood_sugar > normal_ranges["blood_sugar"][1]:
        abnormal_readings["blood_sugar"] = {
            "value": health_data.blood_sugar,
            "normal_range": normal_ranges["blood_sugar"]
        }
    
    # Check rest urine
    if health_data.rest_urine < normal_ranges["rest_urine"][0] or health_data.rest_urine > normal_ranges["rest_urine"][1]:
        abnormal_readings["rest_urine"] = {
            "value": health_data.rest_urine,
            "normal_range": normal_ranges["rest_urine"]
        }
    
    # Check water intake
    if health_data.water_intake < normal_ranges["water_intake"][0] or health_data.water_intake > normal_ranges["water_intake"][1]:
        abnormal_readings["water_intake"] = {
            "value": health_data.water_intake,
            "normal_range": normal_ranges["water_intake"]
        }
    
    # Determine alert level
    alert_level = "Normal"
    if len(abnormal_readings) > 0:
        alert_level = "Warning"
    if "oxygen_saturation" in abnormal_readings or "pulse_rate" in abnormal_readings or "blood_pressure" in abnormal_readings:
        alert_level = "Critical"
    
    try:
        prompt = f"""
            Please analyze the following health data and provide detailed medical insights and recommendations. 
            Be professional but easy to understand. Focus especially on any abnormal readings.
            
            Health Data:
            - Oxygen Saturation: {health_data.oxygen_saturation}% (Normal range: 80-100%)
            - Pulse Rate: {health_data.pulse_rate} bpm (Normal range: 50-100 bpm)
            - Blood Pressure: {health_data.blood_pressure} mm Hg (Normal range: 80-120)
            - Body Temperature: {health_data.body_temperature}°F (Normal range: 95-105°F)
            - Blood Sugar: {health_data.blood_sugar} mg/dL (Normal range: 70-140 mg/dL)
            - Rest Urine: {health_data.rest_urine} ml (Normal range: 800-2000 ml)
            - Water Intake: {health_data.water_intake} liters (Normal range: 2.7-3.7 liters)
            
            Abnormal Readings: {json.dumps(abnormal_readings, indent=2)}
            Alert Level: {alert_level}
            
            Provide a comprehensive analysis of this data and clear recommendations for the patient.
            Always format your response with an Analysis section followed by a Recommendations section.
        """
        
        # Call OpenAI API
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a healthcare assistant providing medical analysis and recommendations."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500
        )
        
        recommendation = response.choices[0].message.content.strip()

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Full error details: {error_details}")
        raise HTTPException(status_code=500, detail=f"API Error: {str(e)}")

    # Return the analysis results
    return {
        "abnormal_readings": abnormal_readings,
        "recommendation": recommendation
    }