import os
import cv2
import numpy as np
from PIL import Image

class ImageScanner:
    def __init__(self):
        # Directory where labeled food images are stored
        self.labeled_images_dir = "app/static/labeled_images"
        
        # Create the directory if it doesn't exist
        os.makedirs(self.labeled_images_dir, exist_ok=True)
    
    def preprocess_image(self, image_path):
        """Preprocess the image for feature extraction using OpenCV"""
        # Read the image
        img = cv2.imread(image_path)
        
        if img is None:
            raise ValueError(f"Could not read image at {image_path}")
        
        # Resize image to a standard size
        img = cv2.resize(img, (224, 224))
        
        # Convert to RGB (OpenCV loads in BGR)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        return img
    
    def extract_features(self, img):
        """Extract features from the preprocessed image using OpenCV"""
        # Convert to grayscale for feature extraction
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        
        # Extract features using SIFT (Scale-Invariant Feature Transform)
        sift = cv2.SIFT_create()
        keypoints, descriptors = sift.detectAndCompute(gray, None)
        
        return keypoints, descriptors
    
    def compare_images(self, query_image_path, max_results=3, threshold=0.8):
        """Compare query image with labeled images and return the best matches
        that meet the threshold requirement"""
        if not os.path.exists(query_image_path):
            raise ValueError(f"Query image not found at {query_image_path}")
        
        # Get all labeled images
        labeled_images = []
        for filename in os.listdir(self.labeled_images_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                # Extract label from filename (assuming format: label_name.jpg)
                label = os.path.splitext(filename)[0]
                img_path = os.path.join(self.labeled_images_dir, filename)
                labeled_images.append((label, img_path))
        
        if not labeled_images:
            return [("No matches", 0)]
        
        # Process query image
        query_img = self.preprocess_image(query_image_path)
        query_keypoints, query_descriptors = self.extract_features(query_img)
        
        if query_descriptors is None:
            return [("Could not extract features", 0)]
        
        # Compare with each labeled image
        matches = []
        for label, img_path in labeled_images:
            try:
                # Process labeled image
                labeled_img = self.preprocess_image(img_path)
                labeled_keypoints, labeled_descriptors = self.extract_features(labeled_img)
                
                if labeled_descriptors is None:
                    continue
                
                # Match descriptors
                bf = cv2.BFMatcher()
                matches_list = bf.knnMatch(query_descriptors, labeled_descriptors, k=2)
                
                # Apply ratio test to filter good matches
                good_matches = []
                for m, n in matches_list:
                    if m.distance < 0.75 * n.distance:
                        good_matches.append(m)
                
                match_ratio = len(good_matches) / max(len(query_keypoints), 1)
                matches.append((label, match_ratio))
            
            except Exception as e:
                print(f"Error processing {img_path}: {str(e)}")
                continue
        
        # Sort by match ratio (descending)
        matches.sort(key=lambda x: x[1], reverse=True)
        
        # Filter matches by threshold (80%)
        filtered_matches = [match for match in matches if match[1] >= threshold]
        
        # If no matches meet the threshold, return a message
        if not filtered_matches:
            return [("No matches meet the threshold", 0)]
            
        # Return top filtered matches
        return filtered_matches[:max_results]
    
    def save_labeled_image(self, image_path, label):
        """Save a new labeled image to the labeled images directory"""
        try:
            # Create a filename from the label
            filename = f"{label.lower().replace(' ', '_')}.jpg"
            destination_path = os.path.join(self.labeled_images_dir, filename)
            
            # Read the original image
            img = cv2.imread(image_path)
            
            # Resize to a standard size
            img = cv2.resize(img, (224, 224))
            
            # Save the processed image
            cv2.imwrite(destination_path, img)
            
            return True, destination_path
        
        except Exception as e:
            return False, str(e)