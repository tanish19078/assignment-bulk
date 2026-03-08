import sys
from collections import Counter

try:
    from PIL import Image
    import numpy as np
except ImportError:
    print("Pillow/Numpy not found.")
    sys.exit(1)

img_path = 'c:/Users/Tanish Singla/Desktop/becse/practica; file/frontend/Picture1.png'
with Image.open(img_path) as img:
    img = img.convert('RGB')
    pixels = list(img.getdata())
    counter = Counter(pixels)
    most_common = counter.most_common(5)
    
    with open('c:/Users/Tanish Singla/Desktop/becse/practica; file/frontend/color_analysis.txt', 'w') as f:
        f.write("Most common colors (RGB):\n")
        for color, count in most_common:
            f.write(f"{color}: {count}\n")
    
    # Try to find text color 
    # Usually text is bright if background is dark
    bg_color = most_common[0][0]
    is_dark_bg = sum(bg_color) < 128 * 3
    
    text_colors = [p for p in pixels if p != bg_color and (sum(p) > 200*3 if is_dark_bg else sum(p) < 50*3)]
    if text_colors:
        text_counter = Counter(text_colors)
        top_text_color = text_counter.most_common(1)[0][0]
        with open('c:/Users/Tanish Singla/Desktop/becse/practica; file/frontend/color_analysis.txt', 'a') as f:
            f.write(f"\nProbable text color: {top_text_color}")
            
    # Print out dimensions
    with open('c:/Users/Tanish Singla/Desktop/becse/practica; file/frontend/color_analysis.txt', 'a') as f:
         f.write(f"\nImage size: {img.size}")
