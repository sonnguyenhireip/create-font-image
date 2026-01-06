#!/usr/bin/env python3
"""
Standalone Font SVG Generator
- No project dependencies
- Can be placed in any project and run independently
- Usage: python generate_font_svg.py
"""

import requests
import base64
import os
import tempfile
import re
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.misc.transform import Transform
from PIL import Image, ImageDraw, ImageFont

# ============================================================================
# CONFIGURATION - Modify these to change behavior
# ============================================================================

# Base URL where fonts are served
BASE_FONT_URL = os.environ.get('BASE_FONT_URL', 'https://fonts.hiresdot.com/')

# Fonts API URL
FONTS_API_URL_BASE = os.environ.get('FONTS_API_URL', 'http://primary.hiresdot.com:8955/sample/fonts')

# Default number of fonts to request from API
DEFAULT_LIMIT = int(os.environ.get('FONTS_API_LIMIT', '1'))

# Request timeout (seconds)
REQUEST_TIMEOUT = int(os.environ.get('FONTS_REQUEST_TIMEOUT', '10'))

# Which styles to include when parsing API results
INCLUDE_STYLES = ('regular',)

# SVG generation defaults
DEFAULT_TEXT = "Sample"
DEFAULT_FONT_SIZE = 100
DEFAULT_WIDTH = 200
DEFAULT_HEIGHT = 100
PADDING = 8

# Output directory
OUTPUT_DIR = 'svgs'

# ============================================================================
# API FUNCTIONS
# ============================================================================

def fetch_font_urls(limit=None, api_url=None, base_url=BASE_FONT_URL):
    """Fetch fonts from the samples API and return a list of absolute font URLs."""
    if api_url is None:
        env_api = os.environ.get('FONTS_API_URL')
        limit = limit or DEFAULT_LIMIT
        if env_api:
            api_url = env_api
        else:
            api_url = f"{FONTS_API_URL_BASE}?limit={limit}"
    
    try:
        resp = requests.get(api_url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        items = data.get('items', []) if isinstance(data, dict) else []
        urls = []
        
        for item in items:
            for f in item.get('fonts', []):
                style = (f.get('style') or '').lower()
                urls_in_font = f.get('urls', []) or []

                if style and style not in INCLUDE_STYLES:
                    has_match = any(any(s.capitalize() in os.path.basename(u) for s in INCLUDE_STYLES) for u in urls_in_font)
                    if not has_match:
                        continue

                for u in urls_in_font:
                    if (not style or style not in INCLUDE_STYLES) and not any(s.capitalize() in os.path.basename(u) for s in INCLUDE_STYLES):
                        continue

                    if u.startswith('http://') or u.startswith('https://'):
                        urls.append(u)
                    else:
                        path = u.lstrip('/')
                        if path.startswith('fonts/'):
                            path = path[len('fonts/'):]
                        urls.append(base_url.rstrip('/') + '/' + path)
        
        # Dedupe while preserving order
        seen = set()
        uniq = []
        for u in urls:
            if u not in seen:
                seen.add(u)
                uniq.append(u)
        return uniq
    except Exception as e:
        print(f"Warning: Failed to fetch fonts from API: {e}")
        return None


# ============================================================================
# SVG GENERATION FUNCTIONS
# ============================================================================

def create_svg(font_url, output_path, text=DEFAULT_TEXT, font_size=DEFAULT_FONT_SIZE, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT):
    """Create an SVG from a font URL."""
    # Download font
    response = requests.get(font_url)
    response.raise_for_status()
    font_data = response.content

    font_name = os.path.basename(font_url).replace('.woff2', '')

    embed_font = True
    temp_font_path = None
    font = None
    
    try:
        # Write font to a temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.woff2') as tf:
            tf.write(font_data)
            temp_font_path = tf.name

        font = TTFont(temp_font_path)

        # Quick check whether we can load the font
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

        # Compute dynamic font size
        padding = PADDING
        max_w = max(10, width - 2 * padding)
        max_h = max(10, height - 2 * padding)

        fs = int(max_h * 0.8)
        fs = min(fs, max_h)

        if text:
            # Measure actual rendered text width
            try:
                if embed_font:
                    meas_font = ImageFont.truetype(temp_font_path, size=fs)
                else:
                    try:
                        meas_font = ImageFont.truetype("DejaVuSans.ttf", size=fs)
                    except Exception:
                        try:
                            meas_font = ImageFont.truetype("/Library/Fonts/Arial.ttf", size=fs)
                        except Exception:
                            meas_font = ImageFont.load_default()

                measure_img = Image.new('RGBA', (max(2000, int(max_w * 3)), max(500, int(max_h * 3))), (255, 255, 255, 0))
                measure_draw = ImageDraw.Draw(measure_img)
                bbox = measure_draw.textbbox((0, 0), text, font=meas_font)
                text_w = bbox[2] - bbox[0]
                text_h = bbox[3] - bbox[1]
            except Exception:
                char_factor = 0.6
                text_w = int(fs * char_factor * len(text))
                text_h = fs

            required_w = int(text_w + 2 * padding)
            width = required_w

            if text_h > max_h:
                scale_factor = max_h / float(text_h)
                fs = max(10, int(fs * scale_factor))

    finally:
        try:
            if temp_font_path:
                os.unlink(temp_font_path)
        except Exception:
            pass

    fs = min(fs, max_h)

    # Build SVG
    if embed_font and font:
        cmap = font.getBestCmap()
        units_per_em = font['head'].unitsPerEm
        scale = fs / units_per_em
        
        from fontTools.pens.boundsPen import BoundsPen
        glyf = font['glyf']
        min_y = None
        max_y = None
        
        for char in text:
            code = ord(char)
            if code in cmap:
                glyph_name = cmap[code]
                glyph = glyf[glyph_name]
                pen = BoundsPen(glyf)
                try:
                    glyph.draw(pen, glyf)
                    bounds = pen.bounds
                    if bounds:
                        _, yMin, _, yMax = bounds
                        if min_y is None or yMin < min_y:
                            min_y = yMin
                        if max_y is None or yMax > max_y:
                            max_y = yMax
                except Exception:
                    pass
        
        if min_y is None or max_y is None:
            ascent = font['hhea'].ascent
            descent = font['hhea'].descent
            min_y = descent
            max_y = ascent
        
        baseline_y = height / 2 + ((max_y + min_y) * scale) / 2
        
        # Calculate total width for centering
        total_width = 0
        saw_suspect_metric = False
        
        for char in text:
            code = ord(char)
            if code in cmap:
                glyph_name = cmap[code]
                raw_advance = font['hmtx'][glyph_name][0]
                
                if raw_advance >= 0xFF00 or raw_advance < -units_per_em * 10 or raw_advance > units_per_em * 100:
                    if not saw_suspect_metric:
                        print(f"Warning: font {font_name} contains suspicious advance width ({raw_advance}) for glyph {glyph_name}")
                        saw_suspect_metric = True
                    advance = 0
                else:
                    advance = raw_advance * scale
                total_width += advance
        
        x_pos = (width - total_width) / 2
        paths = []
        
        for char in text:
            code = ord(char)
            if code in cmap:
                glyph_name = cmap[code]
                glyph = font['glyf'][glyph_name]
                
                if glyph.numberOfContours > 0:
                    transform = Transform(scale, 0, 0, -scale, x_pos, baseline_y)
                    svg_pen = SVGPathPen(font['glyf'])
                    pen = TransformPen(svg_pen, transform)
                    glyph.draw(pen, font['glyf'])
                    path_d = svg_pen.getCommands()
                    paths.append(f'<path d="{path_d}" fill="#000" />')
                
                raw_advance = font['hmtx'][glyph_name][0]
                if raw_advance >= 0xFF00 or raw_advance < -units_per_em * 10 or raw_advance > units_per_em * 100:
                    advance = 0
                else:
                    advance = raw_advance * scale
                x_pos += advance

        svg = f'''<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" overflow="visible">
  <rect width="100%" height="100%" fill="none" />
  <g>
    {''.join(paths)}
  </g>
</svg>
'''
        print(f"✓ Created SVG for {font_name} (vector paths)")
    else:
        svg = f'''<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" overflow="visible">
  <style type="text/css">
    .sample {{ font-family: sans-serif; font-size: {fs}px; fill: #000; }}
  </style>
  <rect width="100%" height="100%" fill="none" />
  <text x="50%" y="50%" class="sample" dominant-baseline="middle" text-anchor="middle">{text}</text>
</svg>
'''
        print(f"✓ Created SVG for {font_name} (fallback to sans-serif)")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(svg)


def main():
    """Main entry point."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Try to fetch fonts from API
    print("Fetching fonts from API...")
    font_urls = fetch_font_urls()
    
    if not font_urls:
        print("⚠ No fonts fetched from API. Check your API configuration.")
        return
    
    print(f"Found {len(font_urls)} fonts. Generating SVGs...\n")
    
    for url in font_urls:
        try:
            font_name = url.split('/')[-1].replace('.woff2', '')
            display_name = re.sub(r"\b(regular|italic|bold|semibold|thin|light|medium|black)\b$", "", 
                                 font_name.replace('-', ' ').replace('_', ' '), flags=re.I).strip()
            if not display_name:
                display_name = font_name
            
            output_path = f"{OUTPUT_DIR}/{font_name}_thumbnail.svg"
            create_svg(url, output_path, text=display_name)
        except Exception as e:
            print(f"✗ Error processing {url}: {e}")
    
    print(f"\n✓ Done! SVGs saved to '{OUTPUT_DIR}/' directory")


if __name__ == "__main__":
    main()
