import requests
from PIL import Image, ImageDraw, ImageFont
import tempfile
import os
from urls import font_urls

def create_thumbnail(font_url, output_path):
    # Download font
    response = requests.get(font_url)
    response.raise_for_status()
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.woff2') as temp_file:
        temp_file.write(response.content)
        temp_font_path = temp_file.name
    
    try:
        # Load font
        font = ImageFont.truetype(temp_font_path, size=100)
        
        # Calculate text bbox
        temp_img = Image.new('RGBA', (1, 1), color=(255,255,255,0))
        temp_draw = ImageDraw.Draw(temp_img)
        bbox = temp_draw.textbbox((0, 0), "Sample", font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Create image with small padding
        padding = 10
        img_width = text_width + 2 * padding
        img_height = text_height + 2 * padding
        img = Image.new('RGBA', (img_width, img_height), color=(255,255,255,0))
        draw = ImageDraw.Draw(img)
        
        # Draw text with padding
        draw.text((padding, padding), "Sample", fill=(0,0,0,255), font=font)
        
        # Resize to thumbnail
        img.thumbnail((100, 100))
        
        # Save
        img.save(output_path)
    finally:
        os.unlink(temp_font_path)

def main():
    os.makedirs("thumbnails", exist_ok=True)
    for url in font_urls:
        font_name = url.split('/')[-1].replace('.woff2', '')
        output_path = f"thumbnails/{font_name}_thumbnail.png"
        create_thumbnail(url, output_path)
        print(f"Created thumbnail for {font_name}")

if __name__ == "__main__":
    main()