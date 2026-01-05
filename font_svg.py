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

    # Add small vertical shift for better centering across fonts
    svg = f'''<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" overflow="hidden">
  <style type="text/css">
    @font-face {{
      font-family: '{font_name}';
      src: url('data:font/woff2;base64,{b64}') format('woff2');
    }}
    .sample {{ font-family: '{font_name}'; font-size: {fs}px; fill: #000; }}
  </style>
  <rect width="100%" height="100%" fill="none" />
  <text x="50%" y="50%" class="sample" dominant-baseline="middle" text-anchor="middle">{text}</text>
</svg>
'''

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(svg)


def main():
    os.makedirs('svgs', exist_ok=True)
    for url in font_urls:
        font_name = url.split('/')[-1].replace('.woff2', '')
        output_path = f"svgs/{font_name}_thumbnail.svg"
        create_svg(url, output_path)
        print(f"Created SVG for {font_name}")


if __name__ == "__main__":
    main()
