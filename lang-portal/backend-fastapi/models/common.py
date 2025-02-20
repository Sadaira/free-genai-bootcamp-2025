from pydantic import BaseModel
from typing import List, TypeVar, Generic


# Common Models (resuable)
# For paginated responses
class Pagination(BaseModel):
    current_page: int
    total_pages: int
    total_items: int
    items_per_page: int

T = TypeVar("T")
class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    pagination: Pagination


# For success responses
class SuccessResponse(BaseModel):
    success: bool
    message: str