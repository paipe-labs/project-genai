from dataclasses import dataclass
from typing import Optional

@dataclass
class QueryValidationResult:
    is_ok: bool
    error_data: Optional[dict] = None
    error_code: Optional[int] = None