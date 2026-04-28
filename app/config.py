"""Application configuration loaded from environment variables.

Provides defaults for optional settings that can be overridden via a .env file.
"""
import os

# Schema that holds viewer tables (default matches current DB setup)
VIEWER_SCHEMA: str = os.getenv("VIEWER_SCHEMA", "viewer")

# Table name for the metadata view/table (default matches existing model)
METADATA_TABLE: str = os.getenv("METADATA_TABLE", "metadata")

# Additional schema names for vocabularies and SCD data
VOCABULARY_SCHEMA: str = os.getenv("VOCABULARY_SCHEMA", "")
DATA_SCHEMA: str = os.getenv("DATA_SCHEMA", "")
SCD_DATA_SCHEMA: str = os.getenv("SCD_DATA_SCHEMA", "")
