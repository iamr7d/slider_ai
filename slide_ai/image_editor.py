"""
Image editing utilities for Slide AI, e.g., rounded corners, resizing, etc.
"""
from PIL import Image, ImageDraw
import numpy as np

def add_rounded_corners(img: Image.Image, radius: int = 40) -> Image.Image:
    """
    Returns a copy of the image with rounded corners.
    """
    # Ensure RGBA
    img = img.convert("RGBA")
    w, h = img.size
    # Create rounded mask
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), (w, h)], radius=radius, fill=255)
    # Apply mask
    img.putalpha(mask)
    return img

def pil_image_to_stream(img: Image.Image) -> bytes:
    """
    Converts a PIL image to a BytesIO stream for pptx insertion.
    """
    from io import BytesIO
    output = BytesIO()
    img.save(output, format="PNG")
    output.seek(0)
    return output
