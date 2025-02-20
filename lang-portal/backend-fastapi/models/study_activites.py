# from common.models import PaginatedResponse
from pydantic import BaseModel
from datetime import datetime
from typing import List


# Pydantic Models
class StudyActivityResponse(BaseModel):
    id: int
    title: str
    launch_url: str
    preview_url: str

class StudySessionListItem(BaseModel):
    id: int
    group_id: int
    group_name: str
    activity_id: int
    activity_name: str
    start_time: str  # Using string for simplicity, could use datetime with proper formatting
    end_time: str
    review_items_count: int

class PaginatedSessionResponse(BaseModel):
    items: List[StudySessionListItem]
    total: int
    page: int
    per_page: int
    total_pages: int

class GroupResponse(BaseModel):
    id: int
    name: str

class StudyActivityLaunchResponse(BaseModel):
    activity: StudyActivityResponse
    groups: List[GroupResponse]