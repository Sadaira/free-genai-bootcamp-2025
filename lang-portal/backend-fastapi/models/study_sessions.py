# from common.models import PaginatedResponse
from typing import List
from pydantic import BaseModel
from datetime import datetime
from study_activites import StudySessionItem

# Pydantic Models
class StudySessionListItem(BaseModel):
    id: int
    group_id: int
    group_name: str
    activity_id: int
    activity_name: str
    start_time: datetime
    end_time: datetime
    review_items_count: int

class StudySessionListResponse(BaseModel):
    items: List[StudySessionListItem]
    total: int
    page: int
    per_page: int
    total_pages: int

class SessionWordStats(BaseModel):
    id: int
    spanish: str
    english: str
    correct_count: int
    wrong_count: int

class StudySessionDetailResponse(BaseModel):
    session: StudySessionListItem
    words: List[SessionWordStats]
    total: int
    page: int
    per_page: int
    total_pages: int