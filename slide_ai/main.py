"""
Main entry point for Slide AI presentation generator.
"""

from slide_ai.config import get_gemini_api_key, get_unsplash_access_key
from slide_ai.gemini_api import generate_slide_content
from slide_ai.unsplash_api import fetch_unsplash_image, download_image_to_stream
from slide_ai.pptx_builder import create_pptx_with_unsplash


def main():
    print("AI Slide Generator\n====================\n")
    topic = input("Enter presentation topic: ").strip()
    num_slides = int(input("Number of slides: ").strip())

    gemini_key = get_gemini_api_key()
    unsplash_key = get_unsplash_access_key()
    if not gemini_key or not unsplash_key:
        print("ERROR: API keys missing. Please set them in your .env file.")
        return

    print("\nGenerating slide content...")
    
    slides = generate_slide_content(topic, num_slides, gemini_key)
    slide_deck_with_images = []
    print(f"Fetching Unsplash images for {len(slides)} slides...")
    for slide in slides:
        unsplash_query = slide.get("unsplash_query")
        image_url, photographer, photographer_url, error_msg = fetch_unsplash_image(unsplash_query, unsplash_key)
        slide["unsplash_image_url"] = image_url
        slide["unsplash_photographer_name"] = photographer
        slide["unsplash_photographer_url_with_utm"] = photographer_url
        slide["image_fetch_error"] = error_msg
        slide["actual_image_stream"] = None
        if image_url:
            image_stream = download_image_to_stream(image_url)
            if image_stream:
                slide["actual_image_stream"] = image_stream
        slide_deck_with_images.append(slide)

    print("\nCreating PowerPoint file...")
    pptx_file = create_pptx_with_unsplash(slide_deck_with_images, topic)
    print(f"\n🎉 Presentation saved as {pptx_file}")

if __name__ == "__main__":
    main()
