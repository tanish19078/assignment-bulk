import sys
from collections import Counter

try:
    from PIL import Image, ImageFont, ImageDraw
except ImportError:
    print("Pillow not found.")
    sys.exit(1)

img_path = 'c:/Users/Tanish Singla/Desktop/becse/practica; file/frontend/Picture1.png'
img = Image.open(img_path).convert('RGB')
pixels = list(img.getdata())
counter = Counter(pixels)
print("Most common colors (BG):", counter.most_common(5))

# Try to find text color
# The user asked for background, font weight and size.
# For size, let's just approximate by looking at the image dimensions and number of lines, or I can just use OCR.
# Actually I'd better just output the most common color.
