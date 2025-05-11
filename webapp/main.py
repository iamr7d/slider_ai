"""
FastAPI web app for AI Slide Generator with real-time preview.
"""
# Fix Python module path
import sys
import os

# Add the project root directory to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, StreamingResponse, Response, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Now we can import the slide_ai module
from slide_ai.config import get_gemini_api_key, get_unsplash_access_key
from slide_ai.gemini_api import generate_slide_content
from slide_ai.unsplash_api import fetch_unsplash_image, download_image_to_stream
from slide_ai.pptx_builder import create_pptx_with_unsplash
from PIL import Image
from slide_ai.image_editor import add_rounded_corners, pil_image_to_stream
import os

from webapp.api import router as api_router

app = FastAPI()

# Configure CORS - Allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["Content-Type"],
    max_age=600  # Cache preflight requests for 10 minutes
)

app.include_router(api_router)
import os
import json
from pptx import Presentation
from io import BytesIO

# Use absolute paths for templates and static files
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "webapp", "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "webapp", "static")), name="static")

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate", response_class=HTMLResponse)
async def generate(request: Request, topic: str = Form(...), num_slides: int = Form(...)):
    gemini_key = get_gemini_api_key()
    unsplash_key = get_unsplash_access_key()
    slides = generate_slide_content(topic, num_slides, gemini_key)
    slide_previews = []
    for slide in slides:
        if isinstance(slide, dict):
            unsplash_query = slide.get("unsplash_query")
        else:
            # fallback: treat slide as string, or skip
            unsplash_query = None
            continue
        image_url, photographer, photographer_url, error_msg = fetch_unsplash_image(unsplash_query, unsplash_key)
        slide["unsplash_image_url"] = image_url
        slide["unsplash_photographer_name"] = photographer
        slide["unsplash_photographer_url_with_utm"] = photographer_url
        slide["image_fetch_error"] = error_msg
        slide["actual_image_stream"] = None
        if image_url:
            image_stream = download_image_to_stream(image_url)
            if image_stream:
                pil_img = Image.open(image_stream)
                rounded_img = add_rounded_corners(pil_img, radius=60)
                rounded_stream = pil_image_to_stream(rounded_img)
                slide["actual_image_stream"] = rounded_stream
        # For preview, convert image stream to base64
        img_b64 = None
        if slide["actual_image_stream"]:
            import base64
            img_bytes = slide["actual_image_stream"].getvalue()
            img_b64 = f"data:image/png;base64,{base64.b64encode(img_bytes).decode()}"
        slide_previews.append({
            "title": slide["title"],
            "content_points": slide["content_points"],
            "speaker_notes": slide["speaker_notes"],
            "img_b64": img_b64,
            "photographer": slide["unsplash_photographer_name"],
            "photographer_url": slide["unsplash_photographer_url_with_utm"]
        })
    # Save pptx
    pptx_filename = create_pptx_with_unsplash(slides, topic)
    return templates.TemplateResponse("slide_preview.html", {"request": request, "slides": slide_previews, "pptx_file": pptx_filename})

@app.get("/download/{pptx_file}")
def download_pptx(pptx_file: str):
    # Ensure the file exists
    pptx_path = os.path.join(os.getcwd(), pptx_file)
    if not os.path.exists(pptx_path):
        return JSONResponse({"error": f"File {pptx_file} not found"}, status_code=404)
    
    # Force the file to have a .pptx extension if it doesn't already
    download_filename = pptx_file
    if not download_filename.lower().endswith('.pptx'):
        download_filename += '.pptx'
    
    # Read the file into memory
    with open(pptx_path, "rb") as file:
        file_content = file.read()
    
    # Return the file with explicit headers to force PowerPoint download
    headers = {
        "Content-Disposition": f'attachment; filename="{download_filename}"',
        "Content-Type": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "Access-Control-Expose-Headers": "Content-Disposition"
    }
    
    return Response(
        content=file_content,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers=headers
    )

@app.post("/api/direct_download")
async def direct_download(request: Request):
    try:
        # Get form data
        form_data = await request.form()
        data_json = form_data.get('data')
        
        if not data_json:
            return JSONResponse({"error": "No data provided"}, status_code=400)
        
        # Parse the JSON data
        data = json.loads(data_json)
        slides = data.get('slides', [])
        topic = data.get('topic', 'Untitled')
        colors = data.get('colors', {})
        fonts = data.get('fonts', {})
        
        # Generate a filename if not provided
        filename = data.get('filename')
        if not filename:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            safe_topic = topic.replace(' ', '_').lower()
            filename = f"{safe_topic}_{timestamp}.pptx"
        
        # Ensure the filename has .pptx extension
        if not filename.lower().endswith('.pptx'):
            filename += '.pptx'
        
        # Create a PowerPoint presentation
        from slide_ai.pptx_builder import create_pptx_with_unsplash
        pptx_path = create_pptx_with_unsplash(slides, topic, filename=filename)
        
        # Read the file into memory
        with open(pptx_path, "rb") as file:
            file_content = file.read()
        
        # Return the file with explicit headers for PowerPoint download
        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        }
        
        return Response(
            content=file_content,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers=headers
        )
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(tb)
        return JSONResponse({"error": str(e), "traceback": tb}, status_code=500)
