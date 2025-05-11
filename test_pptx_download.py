"""
Test script for PowerPoint download functionality in Slide.AI
"""
import os
import sys
import json
import requests
from pathlib import Path

# Add the project root directory to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Create a test presentation
test_slides = [
    {
        "title": "Test Slide 1",
        "content_points": [
            "This is a test slide",
            "Created for download testing",
            "Testing PowerPoint export functionality"
        ],
        "speaker_notes": "Speaker notes for slide 1"
    },
    {
        "title": "Test Slide 2",
        "content_points": [
            "Second test slide",
            "With more bullet points",
            "To ensure proper formatting"
        ],
        "speaker_notes": "Speaker notes for slide 2"
    }
]

test_data = {
    "slides": test_slides,
    "topic": "Test Presentation",
    "colors": {},
    "fonts": {}
}

def test_generate_pptx():
    """Test the generate_pptx endpoint"""
    print("Testing generate_pptx endpoint...")
    
    response = requests.post(
        "http://localhost:8000/api/generate_pptx",
        json=test_data
    )
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None
    
    data = response.json()
    print(f"Response: {data}")
    
    if "pptx_file" not in data:
        print("Error: No pptx_file in response")
        return None
    
    return data["pptx_file"]

def test_download_pptx(pptx_file):
    """Test downloading the PPTX file"""
    print(f"Testing download endpoint for file: {pptx_file}")
    
    response = requests.get(f"http://localhost:8000/download/{pptx_file}")
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return False
    
    # Check content type
    content_type = response.headers.get("Content-Type", "")
    print(f"Content-Type: {content_type}")
    
    if "application/vnd.openxmlformats-officedocument.presentationml.presentation" not in content_type:
        print(f"Warning: Unexpected content type: {content_type}")
    
    # Check content disposition
    content_disposition = response.headers.get("Content-Disposition", "")
    print(f"Content-Disposition: {content_disposition}")
    
    # Save the file
    download_path = Path(os.path.join(project_root, "test_download.pptx"))
    with open(download_path, "wb") as f:
        f.write(response.content)
    
    print(f"File saved to: {download_path}")
    print(f"File size: {os.path.getsize(download_path)} bytes")
    
    return True

def test_direct_download():
    """Test the direct_download endpoint"""
    print("Testing direct_download endpoint...")
    
    # Create form data
    form_data = {
        "data": json.dumps(test_data)
    }
    
    response = requests.post(
        "http://localhost:8000/api/direct_download",
        data=form_data
    )
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return False
    
    # Check content type
    content_type = response.headers.get("Content-Type", "")
    print(f"Content-Type: {content_type}")
    
    if "application/vnd.openxmlformats-officedocument.presentationml.presentation" not in content_type:
        print(f"Warning: Unexpected content type: {content_type}")
    
    # Check content disposition
    content_disposition = response.headers.get("Content-Disposition", "")
    print(f"Content-Disposition: {content_disposition}")
    
    # Save the file
    download_path = Path(os.path.join(project_root, "test_direct_download.pptx"))
    with open(download_path, "wb") as f:
        f.write(response.content)
    
    print(f"File saved to: {download_path}")
    print(f"File size: {os.path.getsize(download_path)} bytes")
    
    return True

if __name__ == "__main__":
    print("=== Testing PowerPoint Download Functionality ===")
    
    # Test generate_pptx endpoint
    pptx_file = test_generate_pptx()
    
    if pptx_file:
        # Test download endpoint
        test_download_pptx(pptx_file)
    
    # Test direct download endpoint
    test_direct_download()
    
    print("=== Testing Complete ===")
