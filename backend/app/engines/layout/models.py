from typing import Any, Literal, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict

from app.engines.ocr.models import BoundingBox, OCRLine, OCRWord


class LayoutRegion(BaseModel):
    """Base class for all logical layout regions in a page."""
    id: UUID = Field(default_factory=uuid4)
    type: str = Field(description="The type of the region (e.g. paragraph, table, signature)")
    bounding_box: BoundingBox
    polygon: list[tuple[float, float]] = Field(default_factory=list)
    rotation: float = 0.0
    confidence: float = 1.0
    
    # Graph relationships using IDs to avoid deep recursion issues
    parent_id: Optional[UUID] = None
    children_ids: list[UUID] = Field(default_factory=list)
    reading_order: Optional[int] = None
    
    # Association with OCR
    associated_words: list[OCRWord] = Field(default_factory=list)
    associated_lines: list[OCRLine] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")


class ParagraphRegion(LayoutRegion):
    type: Literal["paragraph"] = "paragraph"
    text: str = ""


class HeaderRegion(LayoutRegion):
    type: Literal["header"] = "header"
    text: str = ""
    level: int = 1


class TableCell(LayoutRegion):
    type: Literal["table_cell"] = "table_cell"
    row_index: int = 0
    col_index: int = 0
    row_span: int = 1
    col_span: int = 1
    is_header: bool = False
    text: str = ""


class TableRow(LayoutRegion):
    type: Literal["table_row"] = "table_row"
    row_index: int = 0
    cells: list[TableCell] = Field(default_factory=list)


class TableColumn(LayoutRegion):
    type: Literal["table_column"] = "table_column"
    col_index: int = 0
    cells: list[TableCell] = Field(default_factory=list)


class TableRegion(LayoutRegion):
    type: Literal["table"] = "table"
    rows: list[TableRow] = Field(default_factory=list)
    columns: list[TableColumn] = Field(default_factory=list)
    cells: list[TableCell] = Field(default_factory=list)


class SignatureRegion(LayoutRegion):
    type: Literal["signature"] = "signature"
    is_electronic: bool = False
    is_handwritten: bool = True


class StampRegion(LayoutRegion):
    type: Literal["stamp"] = "stamp"
    shape: str = "unknown"  # circular, rectangular
    color: Optional[str] = None


class ImageRegion(LayoutRegion):
    type: Literal["image"] = "image"
    caption: Optional[str] = None


class CheckboxRegion(LayoutRegion):
    type: Literal["checkbox"] = "checkbox"
    is_checked: bool = False
    checkbox_type: str = "box"  # box, radio, circle


class FormFieldRegion(LayoutRegion):
    type: Literal["form_field"] = "form_field"
    label: Optional[str] = None
    value: Optional[str] = None
    label_region_id: Optional[UUID] = None
    value_region_id: Optional[UUID] = None


class LayoutPage(BaseModel):
    """Logical representation of a single page."""
    page_index: int = 0
    width: int
    height: int
    regions: list[LayoutRegion] = Field(default_factory=list)
    
    # Specific collections for easier extraction
    tables: list[TableRegion] = Field(default_factory=list)
    paragraphs: list[ParagraphRegion] = Field(default_factory=list)
    headers: list[HeaderRegion] = Field(default_factory=list)
    signatures: list[SignatureRegion] = Field(default_factory=list)
    stamps: list[StampRegion] = Field(default_factory=list)
    checkboxes: list[CheckboxRegion] = Field(default_factory=list)
    form_fields: list[FormFieldRegion] = Field(default_factory=list)
    images: list[ImageRegion] = Field(default_factory=list)
    
    processing_time_ms: int = 0


class LayoutDocument(BaseModel):
    """Complete logical representation of a document."""
    pages: list[LayoutPage] = Field(default_factory=list)


class LayoutAnalysisResult(BaseModel):
    """Output payload from the Layout Analysis Engine."""
    document: LayoutDocument
    global_confidence: float = 1.0
    detected_language: Optional[str] = None
