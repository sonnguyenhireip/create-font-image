# Configuration constants (change here to alter behaviour) 🔧
import os

# Base URL where fonts are served (used to normalize API-relative paths)
BASE_FONT_URL = os.environ.get('BASE_FONT_URL', 'https://fonts.hiresdot.com/')
# Fonts API (no query parameters). Use env FONTS_API_URL to override the full API URL.
FONTS_API_URL_BASE = os.environ.get('FONTS_API_URL', 'http://primary.hiresdot.com:8955/sample/fonts')
# Default number of fonts to request from the API
DEFAULT_LIMIT = int(os.environ.get('FONTS_API_LIMIT', '500'))
# Request timeout (seconds)
REQUEST_TIMEOUT = int(os.environ.get('FONTS_REQUEST_TIMEOUT', '10'))
# Which styles to include when parsing API results (lowercase)
INCLUDE_STYLES = ('regular',)


# List of font URLs to generate thumbnails for (empty fallback if API unavailable)
font_urls = []

# Try to fetch latest font list from API and replace the list at import time.
# If API fails, font_urls remains empty and no thumbnails will be generated.
import os


def fetch_font_urls(limit=None, api_url=None, base_url=BASE_FONT_URL):
    """Fetch fonts from the samples API and return a list of absolute font URLs.

    Parameters:
      - limit: int number of items to request from the API (falls back to DEFAULT_LIMIT)
      - api_url: full API URL (overrides the configured FONTS_API_URL_BASE if provided)
      - base_url: base URL used to normalize relative font paths (defaults to BASE_FONT_URL)

    Returns None on any error so caller can gracefully fall back to the hardcoded list.
    """
    if api_url is None:
        # Allow overriding the entire API URL via env; otherwise build URL with limit
        env_api = os.environ.get('FONTS_API_URL')
        limit = limit or DEFAULT_LIMIT
        if env_api:
            api_url = env_api
        else:
            api_url = f"{FONTS_API_URL_BASE}?limit={limit}"
    try:
        import requests
        resp = requests.get(api_url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        items = data.get('items', []) if isinstance(data, dict) else []
        urls = []
        for item in items:
            for f in item.get('fonts', []):
                style = (f.get('style') or '').lower()
                urls_in_font = f.get('urls', []) or []

                # If the font entry has a style and it's not one of the configured
                # INCLUDE_STYLES, skip the whole font (unless filenames indicate an included style)
                if style and style not in INCLUDE_STYLES:
                    has_match = any(any(s.capitalize() in os.path.basename(u) for s in INCLUDE_STYLES) for u in urls_in_font)
                    if not has_match:
                        continue

                for u in urls_in_font:
                    # If style missing or different, only pick urls whose filename contains an included style
                    if (not style or style not in INCLUDE_STYLES) and not any(s.capitalize() in os.path.basename(u) for s in INCLUDE_STYLES):
                        continue

                    if u.startswith('http://') or u.startswith('https://'):
                        urls.append(u)
                    else:
                        path = u.lstrip('/')
                        # Normalize API paths: some entries start with 'fonts/...' while our
                        # existing URLs use the top-level '<family>/<file>.woff2' shape.
                        if path.startswith('fonts/'):
                            path = path[len('fonts/'):]
                        urls.append(base_url.rstrip('/') + '/' + path)
        # dedupe while preserving order
        seen = set()
        uniq = []
        for u in urls:
            if u not in seen:
                seen.add(u)
                uniq.append(u)
        return uniq
    except Exception:
        return None


# Replace font_urls with fetched list if available
try:
    fetched = fetch_font_urls()
    if fetched:
        font_urls = fetched
except Exception:
    pass
