# endpoints/study_sessions.py
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime
from models.study_sessions import StudySessionListResponse, StudySessionDetailResponse  
from pydantic import BaseModel
import math
from lib.db import Database

router = APIRouter(prefix="/api/study-sessions", tags=["study_sessions"])

# Database Dependency
def get_db():
    db = Database()
    db.connect()
    try:
        yield db
    finally:
        db.close()

# Endpoints
@router.get("/", response_model=StudySessionListResponse)
async def get_study_sessions(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: Database = Depends(get_db)
):
    try:
        cursor = db.connection.cursor()
        offset = (page - 1) * per_page

        # Get total count
        cursor.execute('''
            SELECT COUNT(*) as count 
            FROM study_sessions ss
            JOIN groups g ON g.id = ss.group_id
            JOIN study_activities sa ON sa.id = ss.study_activity_id
        ''')
        total_count = cursor.fetchone()['count']

        # Get paginated sessions
        cursor.execute('''
            SELECT 
                ss.id,
                ss.group_id,
                g.name as group_name,
                sa.id as activity_id,
                sa.name as activity_name,
                ss.created_at,
                COUNT(wri.id) as review_items_count
            FROM study_sessions ss
            JOIN groups g ON g.id = ss.group_id
            JOIN study_activities sa ON sa.id = ss.study_activity_id
            LEFT JOIN word_review_items wri ON wri.study_session_id = ss.id
            GROUP BY ss.id
            ORDER BY ss.created_at DESC
            LIMIT ? OFFSET ?
        ''', (per_page, offset))
        
        sessions = cursor.fetchall()

        return {
            "items": [{
                "id": session["id"],
                "group_id": session["group_id"],
                "group_name": session["group_name"],
                "activity_id": session["activity_id"],
                "activity_name": session["activity_name"],
                "start_time": session["created_at"],
                "end_time": session["created_at"],
                "review_items_count": session["review_items_count"]
            } for session in sessions],
            "total": total_count,
            "page": page,
            "per_page": per_page,
            "total_pages": math.ceil(total_count / per_page) if total_count else 0
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{session_id}", response_model=StudySessionDetailResponse)
async def get_study_session(
    session_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: Database = Depends(get_db)
):
    try:
        cursor = db.connection.cursor()
        offset = (page - 1) * per_page

        # Get session details
        cursor.execute('''
            SELECT 
                ss.id,
                ss.group_id,
                g.name as group_name,
                sa.id as activity_id,
                sa.name as activity_name,
                ss.created_at,
                COUNT(wri.id) as review_items_count
            FROM study_sessions ss
            JOIN groups g ON g.id = ss.group_id
            JOIN study_activities sa ON sa.id = ss.study_activity_id
            LEFT JOIN word_review_items wri ON wri.study_session_id = ss.id
            WHERE ss.id = ?
            GROUP BY ss.id
        ''', (session_id,))
        
        session = cursor.fetchone()
        if not session:
            raise HTTPException(status_code=404, detail="Study session not found")

        # Get words with stats
        cursor.execute('''
            SELECT 
                w.id,
                w.spanish,
                w.english,
                COALESCE(SUM(CASE WHEN wri.correct = 1 THEN 1 ELSE 0 END), 0) as correct_count,
                COALESCE(SUM(CASE WHEN wri.correct = 0 THEN 1 ELSE 0 END), 0) as wrong_count
            FROM words w
            JOIN word_review_items wri ON wri.word_id = w.id
            WHERE wri.study_session_id = ?
            GROUP BY w.id
            ORDER BY w.spanish
            LIMIT ? OFFSET ?
        ''', (session_id, per_page, offset))
        
        words = cursor.fetchall()

        # Get total words count
        cursor.execute('''
            SELECT COUNT(DISTINCT w.id) as count
            FROM words w
            JOIN word_review_items wri ON wri.word_id = w.id
            WHERE wri.study_session_id = ?
        ''', (session_id,))
        total_count = cursor.fetchone()['count']

        return {
            "session": {
                "id": session["id"],
                "group_id": session["group_id"],
                "group_name": session["group_name"],
                "activity_id": session["activity_id"],
                "activity_name": session["activity_name"],
                "start_time": session["created_at"],
                "end_time": session["created_at"],
                "review_items_count": session["review_items_count"]
            },
            "words": [{
                "id": word["id"],
                "spanish": word["spanish"],
                "english": word["english"],
                "correct_count": word["correct_count"],
                "wrong_count": word["wrong_count"]
            } for word in words],
            "total": total_count,
            "page": page,
            "per_page": per_page,
            "total_pages": math.ceil(total_count / per_page) if total_count else 0
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reset")
async def reset_study_sessions(db: Database = Depends(get_db)):
    try:
        cursor = db.connection.cursor()
        cursor.execute('DELETE FROM word_review_items')
        cursor.execute('DELETE FROM study_sessions')
        db.connection.commit()
        return {"message": "Study history cleared successfully"}
    except Exception as e:
        db.connection.rollback()
        raise HTTPException(status_code=500, detail=str(e))