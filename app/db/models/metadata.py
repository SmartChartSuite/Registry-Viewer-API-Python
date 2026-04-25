from sqlalchemy import Column, Integer, String, JSON
from ..base import Base

class Metadata(Base):
    __tablename__ = "metadata"

    metadata_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    tag = Column(String, nullable=False, unique=True, index=True)
    viewer_config = Column(JSON, nullable=True)  # stored as JSONB in PostgreSQL
