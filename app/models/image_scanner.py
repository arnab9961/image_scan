import os
import cv2
import numpy as np
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ImageScanner:
    def __init__(self):
        # Configure Google API with the API key from environment variables
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("Google API key not found. Please set GOOGLE_API_KEY in .env file.")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Directory where uploaded images are stored
        self.uploads_dir = "app/static/uploads"
        
        # Create the directory if it doesn't exist
        os.makedirs(self.uploads_dir, exist_ok=True)
    
    def scan_food_image(self, image_path):
        """
        Scan food image using Google Gemini API to get nutritional information
        """
        try:
            # Open the image with PIL
            img = Image.open(image_path)
            
            # Create a prompt that asks for specific nutritional information
            prompt = """
            Analyze this food image and provide detailed nutritional information in the following format:
            Food Item: [name of the food item]
            Protein: [protein amount in grams]
            Details: [brief description of the food item]
            Ingredients: [main ingredients]
            Calories: [calorie count]
            Fat: [fat content in grams]
            Carbs: [carbohydrate content in grams]

            If you're uncertain about any values, provide an estimate and indicate it as such.
            """
            
            # Generate content using the Google model
            response = self.model.generate_content([prompt, img])
            
            # Process the response text to extract structured information
            info = self._extract_nutritional_info(response.text)
            
            return info
            
        except Exception as e:
            return {
                "error": f"Error analyzing image: {str(e)}",
                "food_item": "N/A",
                "protein": "N/A",
                "details": "Unable to process image",
                "ingredients": "N/A",
                "calories": "N/A", 
                "fat": "N/A",
                "carbs": "N/A"
            }
    
    def _extract_nutritional_info(self, text):
        """
        Extract structured nutritional information from the API response text
        """
        info = {
            "food_item": "N/A",
            "protein": "N/A",
            "details": "N/A",
            "ingredients": "N/A", 
            "calories": "N/A",
            "fat": "N/A",
            "carbs": "N/A"
        }
        
        # Parse the response text to extract the information
        lines = text.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line.lower().startswith('food item:'):
                info["food_item"] = line[10:].strip()
            elif line.lower().startswith('protein:'):
                info["protein"] = line[8:].strip()
            elif line.lower().startswith('details:'):
                info["details"] = line[8:].strip()
            elif line.lower().startswith('ingredients:'):
                info["ingredients"] = line[12:].strip()
            elif line.lower().startswith('calories:'):
                info["calories"] = line[9:].strip()
            elif line.lower().startswith('fat:'):
                info["fat"] = line[4:].strip()
            elif line.lower().startswith('carbs:'):
                info["carbs"] = line[6:].strip()
        
        return info