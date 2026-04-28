import os
from dotenv import load_dotenv

# Load environment variables from a .env file (if present) at import time.
# This runs once when the package is imported, ensuring that all subsequent
# modules see the configured values without ever writing them back to source.
load_dotenv()

# Initialise logging configuration (import side‑effects configure the logger)
from .logging_config import logger  # noqa: F401
