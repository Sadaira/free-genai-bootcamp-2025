from pydantic import BaseModel
from typing import List

class GroupResponse(BaseModel):
    id: int
    group_name: str
    word_count: int

class PaginatedGroupResponse(BaseModel):
    groups: List[GroupResponse]
    total_pages: int
    current_page: int

class GroupWordResponse(BaseModel):
    id: int
    spanish: str
    english: str
    correct_count: int
    wrong_count: int

class PaginatedWordResponse(BaseModel):
    words: List[GroupWordResponse]
    total_pages: int
    current_page: int

class StudySessionResponse(BaseModel):
    id: int
    group_id: int
    group_name: str
    study_activity_id: int
    activity_name: str
    start_time: str
    end_time: str
    review_items_count: int

class PaginatedSessionResponse(BaseModel):
    study_sessions: List[StudySessionResponse]
    total_pages: int
    current_page: int