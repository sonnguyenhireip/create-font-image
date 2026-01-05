# Font Thumbnail Generator

This script generates small thumbnail images for fonts from URLs.

## Setup

1. Install dependencies:
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## Usage

1. Add font URLs to `urls.py`:

   ```python
   font_urls = [
       'https://fonts.hiresdot.com/Akronim/Akronim-Regular.woff2',
       # Add more URLs here
   ]
   ```

2. Run the scripts:

   - Generate PNG thumbnails (existing behavior):

     ```bash
     ./run
     ```

   - Generate SVG thumbnails (new):

     ```bash
     ./run_svg
     ```

   - Recreate both outputs (remove and re-run):

     ```bash
     ./regen
     ```

Thumbnails will be saved as `<font_name>_thumbnail.png` in the `thumbnails/` directory and SVGs as `<font_name>_thumbnail.svg` in the `svgs/` directory.
