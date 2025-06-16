# Configuration constants
DEFAULT_SCREENSHOT_TIMESTAMP = 13
SUPPORTED_VIDEO_FORMATS = ['.mkv']
CSV_SEPARATORS = [';', ',']

# Date/time formats for parsing
DATETIME_FORMATS = [
    "%Y-%m-%d %H:%M:%S",  # Original format: 2025-06-12 23:49:33
    "%d/%m/%Y %H:%M",     # New format: 12/06/2025 23:58
    "%Y-%m-%d %H:%M",     # Alternative: 2025-06-12 23:49
    "%d/%m/%Y %H:%M:%S"   # Alternative: 12/06/2025 23:58:00
]
