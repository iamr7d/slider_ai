"""
Defines slide layout options, alignments, background colors, and more for Slide AI.
"""
from pptx.dml.color import RGBColor

# Example layout options
def get_layout_options():
    """
    Returns a dictionary of layout options (alignment, background color, etc.).
    Extend as needed.
    """
    return {
        "alignments": ["left", "center", "right"],
        "background_colors": [
            (255, 255, 255),  # white
            (245, 245, 245),  # light gray
            (44, 62, 80),     # dark blue
            (39, 174, 96),    # green
            (231, 76, 60),    # red
            (52, 152, 219),   # blue
        ],
        "image_styles": ["rectangle", "rounded"],
    }

def apply_background_color(slide, rgb_tuple):
    """
    Sets the background color of a slide.
    """
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = RGBColor(*rgb_tuple)
