import requests
import base64
import os
from urls import font_urls

def create_svg(font_url, output_path, text="Sample", font_size=100, width=200, height=100):
    # Download font
    response = requests.get(font_url)
    response.raise_for_status()
    font_data = response.content

    # Base64-encode font for embedding in SVG
    b64 = base64.b64encode(font_data).decode('ascii')
    font_name = os.path.basename(font_url).replace('.woff2', '')

    # Check if the font provides glyphs for the sample text using Pillow (fallback if not)
    from PIL import Image, ImageDraw, ImageFont
    import tempfile

    embed_font = True
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.woff2') as tf:
            tf.write(font_data)
            temp_font_path = tf.name
        try:
            test_font = ImageFont.truetype(temp_font_path, size=100)
            test_img = Image.new('RGBA', (1, 1), (255, 255, 255, 0))
            test_draw = ImageDraw.Draw(test_img)
            bbox = test_draw.textbbox((0, 0), text, font=test_font)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            if w == 0 or h == 0:
                embed_font = False
        except Exception:
            embed_font = False
    finally:
        try:
            os.unlink(temp_font_path)
        except Exception:
            pass

    # Compute a dynamic font size so the text fits inside the SVG
    padding = 8
    max_w = max(10, width - 2 * padding)
    max_h = max(10, height - 2 * padding)

    # Start with a font size based on height and then scale down to fit width if needed
    fs = int(max_h * 0.8)
    if text:
        # approximate glyph width factor (empirical)
        char_factor = 0.6
        approx_w = fs * char_factor * len(text)
        if approx_w > max_w:
            fs = max(10, int((max_w) / (char_factor * len(text))))
    fs = min(fs, max_h)

    # Build SVG; if font has no glyphs, use a generic fallback (sans-serif)
    if embed_font:
        font_face = f"@font-face {{\n      font-family: '{font_name}';\n      src: url('data:font/woff2;base64,{b64}') format('woff2');\n    }}\n"
        family_css = f"'{font_name}', sans-serif"
    else:
        font_face = ""
        family_css = "sans-serif"

    svg = f'''<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" overflow="hidden">
  <style type="text/css">
    {font_face}    .sample {{ font-family: {family_css}; font-size: {fs}px; fill: #000; }}
  </style>
  <rect width="100%" height="100%" fill="none" />
  <text x="50%" y="50%" class="sample" dominant-baseline="middle" text-anchor="middle">{text}</text>
</svg>
'''

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(svg)

    # Log whether we embedded the font or used fallback
    if embed_font:
        print(f"Created SVG for {font_name} (embedded font)")
    else:
        print(f"Created SVG for {font_name} (fallback to sans-serif - no glyphs for '{text}')")


def main():
    os.makedirs('svgs', exist_ok=True)
    for url in font_urls:
        font_name = url.split('/')[-1].replace('.woff2', '')
        output_path = f"svgs/{font_name}_thumbnail.svg"
        create_svg(url, output_path)


if __name__ == "__main__":
    main()
