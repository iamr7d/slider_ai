import os
import base64
import io
import sys
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from rembg import remove
from PIL import Image
import numpy as np
import requests
import json
from dotenv import load_dotenv
from collections import deque
from datetime import datetime, timedelta
import logging
import google.generativeai as genai

# Add the project root directory to the Python path to import slide_ai modules
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import slide_ai modules
from slide_ai.config import get_gemini_api_key, get_unsplash_access_key
from slide_ai.gemini_api import generate_slide_content
from slide_ai.unsplash_api import fetch_unsplash_image, download_image_to_stream
from slide_ai.image_editor import add_rounded_corners, pil_image_to_stream

# Load environment variables from .env file
load_dotenv(dotenv_path='../.env')

# Rate limiter for Gemini API
class RateLimiter:
    def __init__(self, max_rpm=10, max_rpd=100):
        self.max_rpm = max_rpm  # Max requests per minute
        self.max_rpd = max_rpd  # Max requests per day
        self.minute_requests = deque()
        self.day_requests = deque()
    
    def can_make_request(self):
        current_time = datetime.now()
        
        # Clean up old entries
        self._clean_old_entries(current_time)
        
        # Check if we've exceeded limits
        if len(self.minute_requests) >= self.max_rpm:
            return False, f"Rate limit exceeded: {self.max_rpm} requests per minute"
        
        if len(self.day_requests) >= self.max_rpd:
            return False, f"Rate limit exceeded: {self.max_rpd} requests per day"
        
        # Add this request to our tracking
        self.minute_requests.append(current_time)
        self.day_requests.append(current_time)
        
        return True, None
    
    def _clean_old_entries(self, current_time):
        # Remove entries older than 1 minute
        minute_ago = current_time - timedelta(minutes=1)
        while self.minute_requests and self.minute_requests[0] < minute_ago:
            self.minute_requests.popleft()
        
        # Remove entries older than 1 day
        day_ago = current_time - timedelta(days=1)
        while self.day_requests and self.day_requests[0] < day_ago:
            self.day_requests.popleft()

# Initialize rate limiter
gemini_rate_limiter = RateLimiter()

app = Flask(__name__)
# Enable CORS for all routes and origins
CORS(app)

# CORS decorator for handling preflight requests
def cors_response(f):
    def wrapper(*args, **kwargs):
        if request.method == 'OPTIONS':
            response = make_response()
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
            response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
            return response
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

@app.route('/api/remove-background', methods=['GET', 'POST', 'OPTIONS'])
@cors_response
def remove_background():
    try:
        # Get the image data from the request
        data = request.json
        if not data or 'image' not in data:
            return jsonify({'error': 'No image data provided'}), 400
        
        # Decode the base64 image
        image_data = data['image']
        # Remove the data URL prefix if present
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        # Decode base64 to binary
        image_bytes = base64.b64decode(image_data)
        
        # Open the image with Pillow
        input_image = Image.open(io.BytesIO(image_bytes))
        
        # Process the image with rembg
        output_image = remove(input_image)
        
        # Convert the output image to base64
        buffered = io.BytesIO()
        output_image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        # Return the processed image
        return jsonify({
            'success': True,
            'image': f'data:image/png;base64,{img_str}'
        })
    
    except Exception as e:
        print(f"Error processing image: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-image', methods=['GET', 'POST', 'OPTIONS'])
@cors_response
def generate_image():
    try:
        # Handle OPTIONS request for CORS
        if request.method == 'OPTIONS':
            response = make_response()
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
            response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
            return response
            
        # Get the prompt from the request
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
            
        data = request.get_json()
        if data is None:
            return jsonify({'error': 'Invalid JSON data'}), 400
            
        prompt = data.get('prompt')
        if not prompt:
            return jsonify({'error': 'No prompt provided'}), 400
            
        # Check rate limits before making API call
        can_proceed, rate_limit_message = gemini_rate_limiter.can_make_request()
        if not can_proceed:
            return jsonify({
                'error': 'Rate limit exceeded',
                'message': rate_limit_message,
                'retry_after': '60 seconds'
            }), 429  # 429 Too Many Requests
        
        # Get API key from environment variables
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            return jsonify({'error': 'API key not configured'}), 500
        
        # Call the Gemini API
        print(f"Using API Key: {api_key[:10]}...")
        print(f"Generating image with prompt: {prompt[:100]}...")
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp-image-generation:generateContent?key={api_key}"
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt}
                ]
            }],
            "generationConfig": {"responseModalities": ["Text", "Image"]}
        }
        
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        
        # Check if the request was successful
        if response.status_code != 200:
            error_msg = f'API request failed with status code {response.status_code}'
            print(error_msg)
            print(response.text)
            return jsonify({
                'error': error_msg,
                'details': response.text
            }), 500
        
        print("Response received from Gemini API")
        response_data = response.json()
        
        # Extract the image data
        if not response_data.get('candidates'):
            return jsonify({'error': 'No candidates in response'}), 500
            
        candidate = response_data['candidates'][0]
        if not candidate.get('content') or not candidate['content'].get('parts'):
            return jsonify({'error': 'No content parts in response'}), 500
            
        parts = candidate['content']['parts']
        
        # Find the image part
        image_part = None
        text_response = None
        
        for part in parts:
            if part.get('inlineData') and part['inlineData'].get('mimeType', '').startswith('image/'):
                image_part = part
            elif part.get('text'):
                text_response = part['text']
        
        if not image_part:
            print("No image found in response")
            print(f"Full response: {json.dumps(response_data, indent=2)}")
            return jsonify({'error': 'No image found in the response'}), 500
        
        # Extract the base64 image data
        image_data = image_part['inlineData']['data']
        mime_type = image_part['inlineData']['mimeType']
        
        print(f"Successfully generated image with mime type: {mime_type}")
        
        return jsonify({
            'image': f'data:{mime_type};base64,{image_data}',
            'text': text_response
        })
    
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"Error generating image: {str(e)}")
        print(error_traceback)
        return jsonify({
            'error': str(e),
            'traceback': error_traceback
        }), 500

@app.route('/api/enhance-prompt', methods=['GET', 'POST', 'OPTIONS'])
@cors_response
def enhance_prompt():
    try:
        # Get the prompt from the request
        data = request.json
        original_prompt = data.get('prompt')
        
        if not original_prompt:
            return jsonify({'error': 'No prompt provided'}), 400
        
        # Get API key
        gemini_key = get_gemini_api_key()
        if not gemini_key:
            logging.error("API key not configured for Gemini")
            return jsonify({'error': 'API key not configured'}), 500
        
        # Create a more creative and detailed enhanced version of the prompt
        logging.info(f"Received prompt for enhancement: {original_prompt}")
        
        # Define different enhancement styles based on the prompt content
        prompt_lower = original_prompt.lower()
        art_keywords = ['art', 'painting', 'drawing', 'artist', 'portrait', 'illustration', 'sketch', 'canvas']
        nature_keywords = ['nature', 'landscape', 'mountain', 'ocean', 'forest', 'sky', 'sunset', 'beach', 'river', 'waterfall', 'garden']
        tech_keywords = ['tech', 'technology', 'futuristic', 'robot', 'digital', 'cyber', 'computer', 'AI', 'machine', 'device']
        fantasy_keywords = ['fantasy', 'magical', 'dragon', 'fairy', 'wizard', 'elf', 'mythical', 'enchanted', 'medieval']
        food_keywords = ['food', 'cuisine', 'dish', 'meal', 'restaurant', 'cooking', 'dessert', 'chef', 'gourmet']
        architecture_keywords = ['building', 'architecture', 'structure', 'skyscraper', 'house', 'interior', 'design', 'construction']
        space_keywords = ['space', 'galaxy', 'cosmic', 'universe', 'planet', 'star', 'nebula', 'astronomy', 'astronaut']
        animal_keywords = ['animal', 'wildlife', 'pet', 'dog', 'cat', 'bird', 'fish', 'lion', 'tiger', 'bear', 'elephant']
        
        # Select enhancement style based on keywords
        if any(keyword in prompt_lower for keyword in art_keywords):
            # Art-focused enhancement
            styles = [
                f"{original_prompt}, masterpiece, trending on artstation, award-winning, professional, detailed, vibrant colors, perfect composition",
                f"{original_prompt}, fine art, museum quality, detailed brushwork, professional, trending on artstation, masterpiece",
                f"{original_prompt}, artistic masterpiece, vivid colors, detailed, perfect lighting, trending on artstation, award-winning"
            ]
            enhanced_prompt = styles[hash(original_prompt) % len(styles)]
            
        elif any(keyword in prompt_lower for keyword in nature_keywords):
            # Nature-focused enhancement
            styles = [
                f"{original_prompt}, breathtaking nature photography, golden hour lighting, 8K resolution, perfect composition, National Geographic, ultra-detailed",
                f"{original_prompt}, stunning landscape, professional photography, perfect lighting, ultra HD, photorealistic, detailed textures",
                f"{original_prompt}, beautiful scenery, professional nature photography, perfect lighting, detailed, ultra HD resolution"
            ]
            enhanced_prompt = styles[hash(original_prompt) % len(styles)]
            
        elif any(keyword in prompt_lower for keyword in tech_keywords):
            # Tech-focused enhancement
            styles = [
                f"{original_prompt}, futuristic technology, detailed, high-tech, professional product photography, perfect lighting, ultra HD resolution",
                f"{original_prompt}, cutting-edge technology, detailed, sleek design, professional photography, perfect lighting, ultra-realistic",
                f"{original_prompt}, advanced technology, detailed, modern design, professional product photography, studio lighting, ultra HD"
            ]
            enhanced_prompt = styles[hash(original_prompt) % len(styles)]
            
        elif any(keyword in prompt_lower for keyword in fantasy_keywords):
            # Fantasy-focused enhancement
            styles = [
                f"{original_prompt}, fantasy art, magical atmosphere, detailed, vibrant colors, professional illustration, perfect composition",
                f"{original_prompt}, epic fantasy scene, detailed, magical, professional digital art, perfect lighting, cinematic",
                f"{original_prompt}, mythical scene, detailed, magical atmosphere, professional fantasy art, perfect composition"
            ]
            enhanced_prompt = styles[hash(original_prompt) % len(styles)]
            
        elif any(keyword in prompt_lower for keyword in food_keywords):
            # Food-focused enhancement
            styles = [
                f"{original_prompt}, gourmet food photography, professional, perfect lighting, detailed textures, mouth-watering, ultra HD resolution",
                f"{original_prompt}, culinary masterpiece, professional food photography, perfect composition, detailed, studio lighting",
                f"{original_prompt}, delicious food, professional culinary photography, perfect lighting, detailed textures, ultra-realistic"
            ]
            enhanced_prompt = styles[hash(original_prompt) % len(styles)]
            
        elif any(keyword in prompt_lower for keyword in architecture_keywords):
            # Architecture-focused enhancement
            styles = [
                f"{original_prompt}, architectural visualization, photorealistic rendering, perfect lighting, detailed textures, professional quality, ultra HD resolution",
                f"{original_prompt}, architectural design, detailed structure, professional photography, dramatic lighting, perfect composition, ultra-realistic"
            ]
            enhanced_prompt = styles[hash(original_prompt) % len(styles)]
            
        elif any(keyword in prompt_lower for keyword in space_keywords):
            # Space-focused enhancement
            styles = [
                f"{original_prompt}, cosmic scene, astronomy photography, nebula colors, star details, space exploration, ultra HD, breathtaking view, scientifically accurate",
                f"{original_prompt}, space art, cosmic scenery, stellar details, astronomical phenomenon, scientifically accurate, ultra HD, professional rendering",
                f"{original_prompt}, astrophotography, telescope imagery, detailed cosmic structures, space exploration, NASA quality, ultra HD resolution"
            ]
            enhanced_prompt = styles[hash(original_prompt) % len(styles)]
            
        elif any(keyword in prompt_lower for keyword in animal_keywords):
            # Animal-focused enhancement
            styles = [
                f"{original_prompt}, wildlife photography, National Geographic, perfect timing, natural habitat, detailed fur/feathers, professional photography, ultra HD, telephoto lens",
                f"{original_prompt}, animal portrait, studio lighting, detailed features, professional wildlife photography, perfect composition, ultra-realistic",
                f"{original_prompt}, animal in motion, action shot, perfect timing, natural environment, detailed, professional wildlife photography"
            ]
            enhanced_prompt = styles[hash(original_prompt) % len(styles)]
            
        else:
            # General enhancement for other types of prompts
            styles = [
                f"{original_prompt}, highly detailed, professional photography, cinematic, perfect lighting, 8K resolution, photorealistic, masterpiece quality, perfect composition",
                f"{original_prompt}, ultra-realistic, detailed textures, professional lighting, cinematic composition, 8K resolution, photorealistic rendering",
                f"{original_prompt}, studio photography, perfect lighting, detailed textures, professional quality, ultra HD resolution, photorealistic"
            ]
            enhanced_prompt = styles[hash(original_prompt) % len(styles)]
        
        logging.info(f"Enhanced prompt: {enhanced_prompt}")
        
        return jsonify({"enhanced_prompt": enhanced_prompt})
    except Exception as e:
        logging.error(f"Error enhancing prompt: {str(e)}")
        return jsonify({'error': f"Failed to enhance prompt: {str(e)}"}), 500

@app.route('/api/generate', methods=['GET', 'POST', 'OPTIONS'])
@cors_response
def generate_slides():
    try:
        # Get the prompt and num_slides from the request
        data = request.json
        topic = data.get('topic')
        num_slides = data.get('num_slides', 5)
        
        if not topic:
            return jsonify({'error': 'No topic provided'}), 400
        
        # Get API keys
        gemini_key = get_gemini_api_key()
        unsplash_key = get_unsplash_access_key()
        
        if not gemini_key:
            return jsonify({'error': 'Gemini API key not configured'}), 500
            
        # Generate slide content using the Gemini API
        data = generate_slide_content(topic, num_slides, gemini_key)
        slides = data["slides"]
        
        # Attach images as base64 for preview
        for slide in slides:
            if not isinstance(slide, dict):
                logging.error(f"Slide is not a dict: {slide}")
                continue
                
            image_url, photographer, photographer_url, error_msg = fetch_unsplash_image(slide.get("unsplash_query"), unsplash_key)
            slide["unsplash_image_url"] = image_url
            slide["unsplash_photographer_name"] = photographer
            slide["unsplash_photographer_url_with_utm"] = photographer_url
            slide["image_fetch_error"] = error_msg
            slide["img_b64"] = None
            
            if image_url:
                image_stream = download_image_to_stream(image_url)
                if image_stream:
                    pil_img = Image.open(image_stream)
                    rounded_img = add_rounded_corners(pil_img, radius=60)
                    rounded_stream = pil_image_to_stream(rounded_img)
                    img_bytes = rounded_stream.getvalue()
                    slide["img_b64"] = f"data:image/png;base64,{base64.b64encode(img_bytes).decode()}"
                    
        return jsonify({"colors": data["colors"], "fonts": data["fonts"], "slides": slides})
    
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(tb)
        print(f"Error generating slides: {str(e)}")
        return jsonify({'error': str(e), 'traceback': tb}), 500

@app.route('/api/generate_pptx', methods=['GET', 'POST', 'OPTIONS'])
@cors_response
def generate_pptx():
    try:
        # Get the data from the request
        data = request.json
        slides = data.get('slides', [])
        topic = data.get('topic', 'Untitled')
        colors = data.get('colors', {})
        fonts = data.get('fonts', {})
        
        # Ensure the topic is valid for filename creation
        safe_topic = topic.replace(' ', '_').lower()
        if not safe_topic:
            safe_topic = "slide_presentation"
            
        # Generate a unique filename with timestamp to avoid conflicts
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")
        filename = f"{safe_topic}_{timestamp}.pptx"
        
        # Create the PowerPoint file
        create_pptx_with_unsplash(slides, topic, filename=filename)  # Pass the filename explicitly
        
        # Return the filename for download
        return jsonify({"pptx_file": filename})
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(tb)
        logging.exception("Error in /api/generate_pptx")
        return jsonify({"error": str(e), "traceback": tb}), 500

@app.route('/api/extract-equation', methods=['POST', 'OPTIONS'])
@cors_response
def extract_equation():
    try:
        if request.method == 'OPTIONS':
            return cors_response(jsonify({}))
            
        # Get the API key from environment variable
        api_key = os.environ.get("GOOGLE_API_KEY")
        
        if not api_key:
            return jsonify({"error": "GOOGLE_API_KEY environment variable not set"}), 500
            
        # Configure the Gemini API
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Get the image from the request
        if 'image' not in request.files:
            return jsonify({"error": "No image file provided"}), 400
            
        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({"error": "Empty image file"}), 400
            
        # Read the image file
        img_bytes = image_file.read()
        img = Image.open(io.BytesIO(img_bytes))
        
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
            
        # Save to a BytesIO object
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        # Create a list with the image and prompt
        contents = [
            {"mime_type": "image/png", "data": base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')},
            "Extract the equation from this image. Provide only the equation in LaTeX format."
        ]
        
        # Generate content using Gemini
        response = model.generate_content(contents)
        equation = response.text.strip()
        
        # Clean up the equation - remove markdown code blocks if present
        if '```latex' in equation or '```' in equation:
            equation = equation.replace('```latex', '').replace('```', '').strip()
        
        # Remove any additional markdown formatting
        equation = equation.replace('$', '')
        
        if equation:
            return jsonify({"equation": equation, "latex": f"${equation}$"})
        else:
            return jsonify({"error": "Could not extract the equation"}), 400
            
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(tb)
        logging.exception("Error in /api/extract-equation")
        return jsonify({"error": str(e), "traceback": tb}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
