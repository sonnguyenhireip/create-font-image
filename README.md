# Font Thumbnail Generator

This script generates small thumbnail images for fonts from URLs.

## Setup

1. Install dependencies:
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## Usage

1. Configure the number of fonts to generate:

   The script fetches fonts dynamically from the API. To change the number of fonts generated:

   - Set the environment variable `FONTS_API_LIMIT`:

     ```bash
     export FONTS_API_LIMIT=50
     ```

     This will generate thumbnails for 50 fonts.

   - Or edit `DEFAULT_LIMIT` in `urls.py` to change the default (currently 19).

   - To use a different API endpoint, set `FONTS_API_URL`:
     ```bash
     export FONTS_API_URL="http://your-api-endpoint/sample/fonts"
     ```

   The script only includes fonts with 'Regular' style. If the API fails, no thumbnails will be generated (empty fallback).

2. Customize thumbnail appearance (optional):

   Edit constants in `font_svg.py`:

   - `DEFAULT_TEXT`: The sample text (default: "Sample")
   - `DEFAULT_WIDTH`, `DEFAULT_HEIGHT`: Thumbnail size (default: 200x100)
   - `DEFAULT_FONT_SIZE`: Base font size (default: 100)
   - `PADDING`: Internal padding (default: 8)

3. Run the scripts:

   - Generate SVG thumbnails:

     ```bash
     ./run_svg.sh
     ```

   - Generate PNG thumbnails (if available):

     ```bash
     ./run_png.sh
     ```

   - Regenerate all (remove old files and re-run):

     ```bash
     ./regen.sh
     ```

   Thumbnails are saved in `svgs/` for SVGs and `thumbnails/` for PNGs.

## Output

- **SVG Thumbnails**: Saved in `svgs/` directory as `<font_name>_thumbnail.svg`
- **PNG Thumbnails**: Saved in `thumbnails/` directory as `<font_name>_thumbnail.png` (if `font_thumbnail.py` is available)
- Directories are created automatically if they don't exist.
- Use `./regen.sh` to clean and regenerate all outputs.
