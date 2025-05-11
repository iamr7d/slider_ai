"""
FastAPI API endpoints for AI Slide Generator (for React+Tailwind frontend).
"""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from slide_ai.config import get_gemini_api_key, get_unsplash_access_key
from slide_ai.gemini_api import generate_slide_content
from slide_ai.unsplash_api import fetch_unsplash_image, download_image_to_stream
from slide_ai.pptx_builder import create_pptx_with_unsplash
from PIL import Image
from slide_ai.image_editor import add_rounded_corners, pil_image_to_stream
import os
import base64

router = APIRouter()

class GenerateRequest(BaseModel):
    topic: str
    num_slides: int

class UpdateSlideRequest(BaseModel):
    slide_index: int
    title: str
    content_points: list
    speaker_notes: str
    image_url: str | None

class GeneratePPTXRequest(BaseModel):
    slides: list
    topic: str
    colors: dict
    fonts: dict

class EnhancePromptRequest(BaseModel):
    prompt: str

import logging

@router.post("/api/generate")
async def generate_slides(req: GenerateRequest):
    try:
        gemini_key = get_gemini_api_key()
        unsplash_key = get_unsplash_access_key()
        data = generate_slide_content(req.topic, req.num_slides, gemini_key)
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
        return JSONResponse({"colors": data["colors"], "fonts": data["fonts"], "slides": slides})
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(tb)
        logging.exception("Error in /api/generate")
        return JSONResponse({"error": str(e), "traceback": tb}, status_code=500)

@router.post("/api/enhance-prompt")
async def enhance_prompt(req: EnhancePromptRequest):
    try:
        # Get API key
        gemini_key = get_gemini_api_key()
        if not gemini_key:
            logging.error("API key not configured for Gemini")
            return JSONResponse(
                status_code=500,
                content={"error": "API key not configured"}
            )
        
        # Create a more creative and detailed enhanced version of the prompt
        original_prompt = req.prompt
        logging.info(f"Received prompt for enhancement: {original_prompt}")
        
        # Define different enhancement styles based on the prompt content
        art_keywords = ['art', 'painting', 'drawing', 'artist', 'portrait', 'illustration', 'sketch', 'canvas']
        nature_keywords = ['nature', 'landscape', 'mountain', 'ocean', 'forest', 'sky', 'sunset', 'beach', 'river', 'waterfall', 'garden']
        tech_keywords = ['tech', 'technology', 'futuristic', 'robot', 'digital', 'cyber', 'computer', 'AI', 'machine', 'device']
        fantasy_keywords = ['fantasy', 'magical', 'dragon', 'fairy', 'wizard', 'elf', 'mythical', 'enchanted', 'medieval']
        food_keywords = ['food', 'cuisine', 'dish', 'meal', 'restaurant', 'cooking', 'dessert', 'chef', 'gourmet']
        architecture_keywords = ['building', 'architecture', 'structure', 'skyscraper', 'house', 'interior', 'design', 'construction']
        space_keywords = ['space', 'galaxy', 'planet', 'star', 'universe', 'cosmic', 'astronaut', 'nebula', 'astronomy']
        animal_keywords = ['animal', 'wildlife', 'pet', 'dog', 'cat', 'bird', 'fish', 'lion', 'tiger', 'elephant']
        
        # Check if the prompt contains any of the keywords
        prompt_lower = original_prompt.lower()
        
        if any(keyword in prompt_lower for keyword in art_keywords):
            # Art-focused enhancement
            styles = [
                f"{original_prompt}, masterpiece, intricate details, professional lighting, vibrant colors, artistic composition, trending on ArtStation, award-winning, museum quality, hyperrealistic, 8K resolution",
                f"{original_prompt}, oil painting, masterpiece, vivid colors, detailed brushwork, professional lighting, gallery quality, artistic composition, trending on ArtStation",
                f"{original_prompt}, watercolor painting, delicate brushstrokes, vibrant palette, artistic composition, detailed, professional lighting, museum quality"
            ]
            enhanced_prompt = styles[hash(original_prompt) % len(styles)]
            
        elif any(keyword in prompt_lower for keyword in nature_keywords):
            # Nature-focused enhancement
            styles = [
                f"{original_prompt}, breathtaking view, golden hour lighting, atmospheric, cinematic, detailed, National Geographic, professional photography, ultra-realistic, 8K resolution, perfect composition",
                f"{original_prompt}, stunning landscape photography, dramatic lighting, atmospheric, panoramic view, detailed, professional photography, ultra HD",
                f"{original_prompt}, aerial view, drone photography, beautiful scenery, perfect weather conditions, high detail, professional photography"
            ]
            enhanced_prompt = styles[hash(original_prompt) % len(styles)]
            
        elif any(keyword in prompt_lower for keyword in tech_keywords):
            # Tech-focused enhancement
            styles = [
                f"{original_prompt}, highly detailed, sci-fi, concept art, ultra-realistic, octane render, 8K resolution, intricate details, futuristic lighting, sleek design, hyper-detailed",
                f"{original_prompt}, cyberpunk aesthetic, neon lighting, futuristic design, highly detailed, concept art, ultra HD, ray tracing, glossy surfaces",
                f"{original_prompt}, technical illustration, blueprint style, detailed schematics, futuristic design, clean lines, professional rendering"
            ]
            enhanced_prompt = styles[hash(original_prompt) % len(styles)]
            
        elif any(keyword in prompt_lower for keyword in fantasy_keywords):
            # Fantasy-focused enhancement
            styles = [
                f"{original_prompt}, fantasy art, magical atmosphere, detailed character design, mystical lighting, epic scene, professional illustration, trending on ArtStation",
                f"{original_prompt}, mythical scene, magical realism, detailed fantasy world, professional concept art, epic lighting, cinematic composition",
                f"{original_prompt}, enchanted realm, fantasy illustration, detailed character design, magical atmosphere, professional artwork, epic scale"
            ]
            enhanced_prompt = styles[hash(original_prompt) % len(styles)]
            
        elif any(keyword in prompt_lower for keyword in food_keywords):
            # Food-focused enhancement
            styles = [
                f"{original_prompt}, professional food photography, studio lighting, shallow depth of field, mouth-watering, high-end restaurant presentation, gourmet, 8K resolution",
                f"{original_prompt}, culinary masterpiece, professional food styling, perfect lighting, fresh ingredients, gourmet presentation, magazine quality photography",
                f"{original_prompt}, appetizing food photography, perfect composition, studio lighting, professional styling, cookbook quality, detailed textures"
            ]
            enhanced_prompt = styles[hash(original_prompt) % len(styles)]
            
        elif any(keyword in prompt_lower for keyword in architecture_keywords):
            # Architecture-focused enhancement
            styles = [
                f"{original_prompt}, architectural photography, perfect symmetry, golden hour lighting, detailed structure, professional photography, ultra HD, wide angle lens",
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
        
        return {"enhanced_prompt": enhanced_prompt}
    except Exception as e:
        logging.error(f"Error enhancing prompt: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to enhance prompt: {str(e)}"}
        )

@router.post("/api/generate_pptx")
async def generate_pptx(req: GeneratePPTXRequest):
    try:
        # Accepts edited slides, colors, fonts, and topic
        # Ensure the topic is valid for filename creation
        safe_topic = req.topic.replace(' ', '_').lower()
        if not safe_topic:
            safe_topic = "slide_presentation"
            
        # Generate a unique filename with timestamp to avoid conflicts
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")
        filename = f"{safe_topic}_{timestamp}.pptx"
        
        # Create the PowerPoint file
        create_pptx_with_unsplash(req.slides, req.topic, filename=filename)  # Pass the filename explicitly
        
        # Return the filename for download
        return JSONResponse({"pptx_file": filename})
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(tb)
        logging.exception("Error in /api/generate_pptx")
        return JSONResponse({"error": str(e), "traceback": tb}, status_code=500)
