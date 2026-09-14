from pydantic import BaseModel


class TextBlock(BaseModel):
    page: int
    section: str | None = None
    text: str
    block_type: str = "paragraph"