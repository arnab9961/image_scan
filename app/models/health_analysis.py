from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

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

@app.post("/analyze/", response_model=AnalysisResponse)
async def analyze_health_data(health_data: HealthData):
    # Get API key from environment variables
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY in .env file.")
            
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    
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
    # Add your health analysis logic here
    
    # Return analysis results
    return {
        "abnormal_readings": abnormal_readings,
        "recommendation": "Sample recommendation"
    }