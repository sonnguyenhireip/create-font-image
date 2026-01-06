import requests
import base64
import os
from urls import font_urls
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.misc.transform import Transform

# Configuration constants (change here to alter default behavior)
DEFAULT_TEXT = "Sample"
DEFAULT_FONT_SIZE = 100
DEFAULT_WIDTH = 200
DEFAULT_HEIGHT = 100
PADDING = 8

def create_svg(font_url, output_path, text=DEFAULT_TEXT, font_size=DEFAULT_FONT_SIZE, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT):
    # Download font
    response = requests.get(font_url)
    response.raise_for_status()
    font_data = response.content

    font_name = os.path.basename(font_url).replace('.woff2', '')

    # Check if the font provides glyphs for the sample text using Pillow (fallback if not)
    from PIL import Image, ImageDraw, ImageFont
    import tempfile

    embed_font = True
    temp_font_path = None
    font = None
    try:
        # write font to a temp file and keep it for measurement
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

        # Compute a dynamic font size and precise width using actual glyph metrics
        padding = PADDING
        max_w = max(10, width - 2 * padding)
        max_h = max(10, height - 2 * padding)

        # Start with a font size based on height
        fs = int(max_h * 0.8)
        fs = min(fs, max_h)

        if text:
            # Measure actual rendered text width at candidate font size
            try:
                if embed_font:
                    meas_font = ImageFont.truetype(temp_font_path, size=fs)
                else:
                    # Try to use a scalable truetype fallback for more accurate measurement.
                    # Prefer DejaVu (common), then macOS Arial, otherwise fall back to load_default().
                    try:
                        meas_font = ImageFont.truetype("DejaVuSans.ttf", size=fs)
                    except Exception:
                        try:
                            meas_font = ImageFont.truetype("/Library/Fonts/Arial.ttf", size=fs)
                        except Exception:
                            meas_font = ImageFont.load_default()

                # use a reasonably large canvas for measurement to avoid clipping
                measure_img = Image.new('RGBA', (max(2000, int(max_w * 3)), max(500, int(max_h * 3))), (255, 255, 255, 0))
                measure_draw = ImageDraw.Draw(measure_img)
                bbox = measure_draw.textbbox((0, 0), text, font=meas_font)
                text_w = bbox[2] - bbox[0]
                text_h = bbox[3] - bbox[1]
            except Exception:
                # fallback to simple approximation if measurement or font loading fails
                char_factor = 0.6
                text_w = int(fs * char_factor * len(text))
                text_h = fs

            # If text is wider than available space, expand svg width to fit (keeping a padding)
            required_w = int(text_w + 2 * padding)

            # No extra margin to focus on text
            extra_margin = 0
            required_w += extra_margin

            # Auto-resize width based on content
            width = required_w

            # Also, if measured text height exceeds available, reduce font size proportionally
            if text_h > max_h:
                scale_factor = max_h / float(text_h)
                fs = max(10, int(fs * scale_factor))

    finally:
        # clean up temp font file
        try:
            if temp_font_path:
                os.unlink(temp_font_path)
        except Exception:
            pass

    # Ensure font-size does not exceed bounding height
    fs = min(fs, max_h)

    # Build SVG
    if embed_font and font:
        # Generate vector paths
        cmap = font.getBestCmap()
        units_per_em = font['head'].unitsPerEm
        scale = fs / units_per_em
        ascent = font['hhea'].ascent * scale
        descent = font['hhea'].descent * scale
        baseline_y = height / 2 + (ascent + descent) / 2
        # Calculate total width for centering
        total_width = 0
        for char in text:
            code = ord(char)
            if code in cmap:
                glyph_name = cmap[code]
                advance = font['hmtx'][glyph_name][0] * scale
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
                advance = font['hmtx'][glyph_name][0] * scale
                x_pos += advance

        svg = f'''<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" overflow="visible">
  <rect width="100%" height="100%" fill="none" />
  <g>
    {''.join(paths)}
  </g>
</svg>
'''
        print(f"Created SVG for {font_name} (vector paths)")
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
        print(f"Created SVG for {font_name} (fallback to sans-serif - no glyphs for '{text}')")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(svg)


def main():
    os.makedirs('svgs', exist_ok=True)
    import re
    for url in font_urls:
        font_name = url.split('/')[-1].replace('.woff2', '')
        # Create a nicer display name: replace hyphens/underscores with spaces and strip common style suffixes
        display_name = re.sub(r"\b(regular|italic|bold|semibold|thin|light|medium|black)\b$", "", font_name.replace('-', ' ').replace('_', ' '), flags=re.I).strip()
        if not display_name:
            display_name = font_name
        output_path = f"svgs/{font_name}_thumbnail.svg"
        create_svg(url, output_path, text=display_name)


if __name__ == "__main__":
    main()
