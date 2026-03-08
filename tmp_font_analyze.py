import sys
try:
    from PIL import Image
    import numpy as np
except ImportError:
    sys.exit(1)

img_path = 'c:/Users/Tanish Singla/Desktop/becse/practica; file/frontend/Picture1.png'
with Image.open(img_path) as img:
    img = img.convert('RGB')
    data = np.array(img)
    # Detect lines of text
    # Background is (0,0,0)
    bg = 0
    # Let's sum across columns for each row
    row_sums = np.sum(data, axis=(1, 2))
    
    # Non-background rows
    text_rows = row_sums > 0
    
    # line heights
    import itertools
    def rle(inarray):
        n = len(inarray)
        if n == 0: 
            return (None, None, None)
        else:
            y = np.array(inarray[1:] != inarray[:-1])
            i = np.append(np.where(y), n - 1)
            z = np.diff(np.append(-1, i))
            p = np.cumsum(np.append(0, z))[:-1]
            return(z, p, inarray[i])
            
    lengths, pos, vals = rle(text_rows)
    print("Heights of text blocks and empty space blocks:")
    for l, v in zip(lengths, vals):
        print(f"Value: {v}, Length: {l}")
        
    # Analyze text thickness
    col_sums = np.sum(data, axis=(0, 2))
    text_cols = col_sums > 0
    clens, cpos, cvals = rle(text_cols)
    print("\nWidths of text characters spaces and strokes:")
    stroke_widths = []
    
    # Calculate simple gradient magnitude heuristic
    diff_h = np.abs(np.diff(data, axis=1)).sum(axis=2)
    stroke_mask = (diff_h > 0)
    strokes = np.sum(stroke_mask, axis=1)
    
    # Just print info
