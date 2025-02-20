from common.models import PaginatedResponse
from pydantic import BaseModel
from datetime import datetime

# Review
class ReviewResponse(BaseModel):
    success: bool
    word_id: int
    study_session_id: int
    correct: bool
    created_at: datetime
