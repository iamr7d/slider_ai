"""
Handles Gemini (Google Generative AI) text generation for slides.
"""
import google.generativeai as genai
import json

def generate_slide_content(topic, num_slides, api_key, model_name="gemini-1.5-flash-latest"):
    """
    Generate slide content and design (colors, fonts, layouts) for a topic.
    Returns a dict with keys: colors, fonts, slides.
    """
    genai.configure(api_key=api_key)
    text_model = genai.GenerativeModel(model_name)
    prompt = f"""
    You are an expert presentation designer and content strategist.
    For a presentation on the topic: \"{topic}\", generate:
    1. A color palette (background, accent, text colors as hex codes)
    2. Font families for headings and body (Google Fonts or web-safe)
    3. For each slide: title, 3-5 content_points, speaker_notes, unsplash_query, and a layout_type (e.g. 'image-left', 'image-bg', 'quote', etc.)
    Return a single JSON object:
    {{
      "colors": {{"background": "#hex", "accent": "#hex", "text": "#hex"}},
      "fonts": {{"heading": "...", "body": "..."}},
      "slides": [{{"title":..., "content_points":..., "speaker_notes":..., "unsplash_query":..., "layout_type":...}}, ...]
    }}
    Only return valid JSON, no explanation.
    """
    response = text_model.generate_content(prompt)
    cleaned = response.text.strip()
    if cleaned.startswith("```json"): cleaned = cleaned[7:]
    if cleaned.endswith("```"): cleaned = cleaned[:-3]
    cleaned = cleaned.strip()
    print("[Gemini API] Cleaned response for JSON parsing:", repr(cleaned))
    try:
        slide_data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        print("[Gemini API] JSONDecodeError:", str(e))
        raise ValueError(f"Gemini API returned invalid JSON: {e}\nRaw response: {repr(cleaned)}")
    return slide_data
