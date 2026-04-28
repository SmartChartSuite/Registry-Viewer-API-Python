from sqlalchemy import Column, Integer, String, JSON
from ..base import Base

from app.config import VIEWER_SCHEMA, METADATA_TABLE

class Metadata(Base):
    __tablename__ = METADATA_TABLE
    __table_args__ = {"schema": VIEWER_SCHEMA}

    metadata_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    tag = Column(String, nullable=False, unique=True, index=True)
    viewer_config = Column(JSON, nullable=True)  # stored as JSONB in PostgreSQL
