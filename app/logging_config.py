import os
import logging
import warnings
from logging.handlers import TimedRotatingFileHandler

# Ensure the logs directory exists (create if missing)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
LOG_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, 'app.log')

def mask_url(url: str) -> str:
    """Mask password portion of a DB URL for safe logging.
    Example: postgresql+asyncpg://user:secret@host/db -> postgresql+asyncpg://user:******@host/db
    """
    from urllib.parse import urlparse, urlunparse
    try:
        parsed = urlparse(url)
        if parsed.password:
            # Rebuild netloc with masked password
            netloc = f"{parsed.username}:******@{parsed.hostname}"
            if parsed.port:
                netloc += f":{parsed.port}"
            # Preserve other components (scheme, path, params, query, fragment)
            return urlunparse(parsed._replace(netloc=netloc))
        return url
    except Exception:
        # If parsing fails, return original URL unmodified
        return url

# Formatter: timestamp level logger-name message
_formatter = logging.Formatter(
    fmt='%(asctime)s %(levelname)s %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Console handler – INFO and above
_console = logging.StreamHandler()
_console.setLevel(logging.INFO)
_console.setFormatter(_formatter)

# File handler – rotates daily, keeps 3 backups (3‑day retention)
_file_handler = TimedRotatingFileHandler(
    LOG_FILE, when='D', interval=1, backupCount=3, encoding='utf-8'
)
_file_handler.setLevel(logging.WARNING)  # warnings & errors go to file
_file_handler.setFormatter(_formatter)

# Configure root logger (applies to all loggers unless overridden)
logging.basicConfig(level=logging.INFO, handlers=[_console, _file_handler])

# Export a module‑level logger for convenient imports
logger = logging.getLogger(__name__)

# Capture Python warnings via logging (but suppress deprecation warnings)
logging.captureWarnings(True)
warnings.filterwarnings('ignore', category=DeprecationWarning)
