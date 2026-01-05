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

2. Run the script:

   ```bash
   ./run.sh
   ```

   Or manually:

   ```bash
   source venv/bin/activate
   python font_thumbnail.py
   ```

Thumbnails will be saved as `<font_name>_thumbnail.png` in the `thumbnails/` directory.
