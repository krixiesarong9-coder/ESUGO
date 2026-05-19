from pathlib import Path
from PIL import Image
p = Path('static/logo.png')
with Image.open(p) as im:
    print(im.format, im.mode, im.size)
    print(im.info)
    print(im.getpixel((0,0)))
    print(im.getpixel((im.width//2, im.height//2)))
