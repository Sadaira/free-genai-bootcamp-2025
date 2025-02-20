from pydantic import BaseModel
from typing import List, Optional

class WordResponse(BaseModel):
    id: int
    spanish: str
    english: str
    correct_count: int
    wrong_count: int

class PaginatedWordsResponse(BaseModel):
    words: List[WordResponse]
    total_pages: int
    current_page: int
    total_words: int

class WordGroupResponse(BaseModel):
    id: int
    name: str

class WordDetailResponse(BaseModel):
    id: int
    spanish: str
    english: str
    correct_count: int
    wrong_count: int
    groups: List[WordGroupResponse]