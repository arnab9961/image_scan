import os
import cv2
import numpy as np
from PIL import Image
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ImageScanner:
    def __init__(self):
        # Configure OpenAI with the API key from environment variables
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY in .env file.")
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=api_key)
        
        # Directory where uploaded images are stored
        self.uploads_dir = "app/static/uploads"
        
        # Create the directory if it doesn't exist
        os.makedirs(self.uploads_dir, exist_ok=True)
    
    def scan_food_image(self, image_path):
        """
        Scan food image using OpenAI GPT-4o to get nutritional information
        """
        try:
            # Open the image file
            with open(image_path, "rb") as image_file:
                # Generate content using OpenAI's API
                response = self.client.chat.completions.create(
                    model="gpt-4.1",
                    messages=[
                        {
                            "role": "user", 
                            "content": [
                                {
                                    "type": "text", 
                                    "text": """
                                    Analyze this food image and provide detailed nutritional information in the following format:
                                    Food Item: [name of the food item]
                                    Protein: [protein amount in grams]
                                    Details: [brief description of the food item]
                                    Ingredients: [main ingredients]
                                    Calories: [calorie count]
                                    Fat: [fat content in grams]
                                    Carbs: [carbohydrate content in grams]
                                    Recipe: [ALWAYS include detailed recipe steps, even if you have to estimate based on the food's appearance]
                                    If you're uncertain about any values, provide an estimate and indicate it as such.
                                    """
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/jpeg;base64,{self._encode_image(image_path)}"}
                                }
                            ]
                        }
                    ]
                )
            
            # Get the response text
            response_text = response.choices[0].message.content
            
            # Process the response text to extract structured information
            info = self._extract_nutritional_info(response_text)
            
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
                "carbs": "N/A",
                "recipe": "N/A"  # Ensure recipe field is included in error response
            }
    
    def _encode_image(self, image_path):
        """
        Encode image to base64 for API transmission
        """
        import base64
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
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
            "carbs": "N/A",
            "recipe": "N/A",
            "error": None  # Add error field for potential issues
        }
        
        # Parse the response text to extract the information
        lines = text.strip().split('\n')
        current_field = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.lower().startswith('food item:'):
                info["food_item"] = line[10:].strip() or "N/A"
                current_field = None
            elif line.lower().startswith('protein:'):
                info["protein"] = line[8:].strip() or "N/A"
                current_field = None
            elif line.lower().startswith('details:'):
                info["details"] = line[8:].strip() or "N/A"
                current_field = "details"
            elif line.lower().startswith('ingredients:'):
                info["ingredients"] = line[12:].strip() or "N/A"
                current_field = "ingredients"
            elif line.lower().startswith('calories:'):
                info["calories"] = line[9:].strip() or "N/A"
                current_field = None
            elif line.lower().startswith('fat:'):
                info["fat"] = line[4:].strip() or "N/A"
                current_field = None
            elif line.lower().startswith('carbs:'):
                info["carbs"] = line[6:].strip() or "N/A"
                current_field = None
            elif line.lower().startswith('recipe:'):
                info["recipe"] = line[7:].strip() or "N/A"
                current_field = "recipe"
            # Handle multi-line content for details, ingredients or recipe
            elif current_field and line:
                if info[current_field] == "N/A":
                    info[current_field] = line
                else:
                    info[current_field] += "\n" + line
        
        # Ensure error field is included in the response
        if "error" in info and not info["error"]:
            info["error"] = None
            
        return info
