"""
Handles Unsplash image search and download.
"""

import requests
from io import BytesIO

def fetch_unsplash_image(query, access_key, orientation="landscape", app_name_for_utm="SlideAI"):
    """
    Fetches an image URL and attribution from Unsplash based on a query.
    Returns (image_url, photographer_name, photographer_url_with_utm, error_msg)
    """
    if not access_key:
        return None, None, None, "Unsplash Access Key not available."
    if not query:
        return None, None, None, "No query provided for Unsplash."
    api_url = "https://api.unsplash.com/search/photos"
    headers = {"Authorization": f"Client-ID {access_key}", "Accept-Version": "v1"}
    params = {"query": query, "per_page": 1, "orientation": orientation}
    try:
        http_response = requests.get(api_url, headers=headers, params=params, timeout=10)
        http_response.raise_for_status()
        data = http_response.json()
        if data.get("results") and len(data["results"]) > 0:
            image_info = data["results"][0]
            image_url = image_info["urls"]["regular"]
            photographer_name = image_info["user"]["name"]
            base_photographer_url = image_info["user"]["links"]["html"]
            if "?" in base_photographer_url:
                photographer_url_with_utm = f"{base_photographer_url}&utm_source={app_name_for_utm}&utm_medium=referral"
            else:
                photographer_url_with_utm = f"{base_photographer_url}?utm_source={app_name_for_utm}&utm_medium=referral"
            return image_url, photographer_name, photographer_url_with_utm, None
        else:
            return None, None, None, f"No image found for '{query}'."
    except Exception as e:
        return None, None, None, str(e)

def download_image_to_stream(image_url):
    if not image_url:
        return None
    try:
        response = requests.get(image_url, stream=True, timeout=15)
        response.raise_for_status()
        image_stream = BytesIO(response.content)
        return image_stream
    except Exception:
        return None
