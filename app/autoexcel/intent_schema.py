from pydantic import BaseModel, Field
from typing import List, Tuple, Optional, Dict

class Intent(BaseModel):
    action: str = "pivot_create"
    rows: List[str] = Field(default_factory=list)
    columns: List[str] = Field(default_factory=list)
    values: List[Tuple[str,str]] = Field(default_factory=list)  # (col, agg)
    filters: Dict[str, list] = Field(default_factory=dict)
    chart: Optional[str] = None  # "bar|line|pie"
