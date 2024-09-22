from pydantic import BaseModel
from typing import List, Optional

class DocumentIngestionRequest(BaseModel):
    document_title: str
    document_content: str
    source_type: str
    doc_updated_at: Optional[int] = None
    primary_owners: Optional[List[str]] = []
    secondary_owners: Optional[List[str]] = []
    metadata_list: Optional[List[str]] = []
    access_control_list: Optional[dict] = {}
    document_sets: Optional[dict] = {}
