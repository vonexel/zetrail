from datetime import datetime
from pydantic import BaseModel, Field


class Document(BaseModel):                                                                                              # A Logical Zotero Item
    library_id: int
    item_key: str
    item_type: str = "journalArticle"
    title: str = ""
    doi: str | None = None
    year: int | None = None
    creators: list[str] = Field(default_factory = list)
    collections: list[str] = Field(default_factory = list)
    tags: list[str] = Field(default_factory = list)
    updated_at: datetime | None = None

class Attachment(BaseModel):                                                                                            # A Zotero Attachment (PDF, Notes, Snapshots)
    attachment_key: str
    item_key: str
    content_hash: str = ""
    mime_type: str = "application/pdf"
    local_path_hash: str | None = None                                                                                  # Hash of the local path, never the raw path itself
    page_count: int | None = None
    indexted_at: datetime | None = None

class DocumentVersion(BaseModel):                                                                                       # A new hash of the same file produces a new document version: one content version of an attachment
    document_version: str
    library_id: int
    item_key: str
    attachment_key: str
    file_sha256: str