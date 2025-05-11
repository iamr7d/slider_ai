"""
Handles configuration and API key management for Slide AI.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file in project root
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path=env_path)

def get_gemini_api_key():
    return os.getenv('GOOGLE_API_KEY')

def get_unsplash_access_key():
    return os.getenv('UNSPLASH_ACCESS_KEY')
