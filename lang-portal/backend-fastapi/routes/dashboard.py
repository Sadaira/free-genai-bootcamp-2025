from fastapi import APIRouter, HTTPException, Depends
from models.dashboard import LastStudySessionResponse, QuickStatsResponse#,StudyProgressResponse
import sqlite3
from lib.db import Database


# Database connection dependency
# def get_db():
#     db = sqlite3.connect("words.db")
#     db.row_factory = sqlite3.Row  # Enable dictionary-like access
#     try:
#         yield db
#     finally:
#         db.close()

# Database Dependency
def get_db():
    db = Database()
    db.connect()
    try:
        yield db
    finally:
        db.close()


router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

# Endpoint: /recent-session
@router.get("/recent-session", response_model=LastStudySessionResponse)
def get_recent_session(db: sqlite3.Connection = Depends(get_db)):
    try:
        cursor = db.cursor()
        
        # Get the most recent study session with activity name and results
        cursor.execute('''
            SELECT 
                ss.id,
                ss.group_id,
                sa.name as activity_name,
                ss.created_at,
                COUNT(CASE WHEN wri.correct = 1 THEN 1 END) as correct_count,
                COUNT(CASE WHEN wri.correct = 0 THEN 1 END) as wrong_count
            FROM study_sessions ss
            JOIN study_activities sa ON ss.study_activity_id = sa.id
            LEFT JOIN word_review_items wri ON ss.id = wri.study_session_id
            GROUP BY ss.id
            ORDER BY ss.created_at DESC
            LIMIT 1
        ''')
        
        session = cursor.fetchone()
        
        if not session:
            raise HTTPException(status_code=404, detail="No recent session found")
        
        return session  # FastAPI automatically converts sqlite3.Row to JSON
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint: /dashboard/quick_stats
@router.get("/quick_stats", response_model=QuickStatsResponse)
def get_study_stats(db: sqlite3.Connection = Depends(get_db)):
    try:
        cursor = db.cursor()
        
        # Get total vocabulary count
        cursor.execute('SELECT COUNT(*) as total_vocabulary FROM words')
        total_vocabulary = cursor.fetchone()["total_vocabulary"]

        # Get total unique words studied
        cursor.execute('''
            SELECT COUNT(DISTINCT word_id) as total_words
            FROM word_review_items wri
            JOIN study_sessions ss ON wri.study_session_id = ss.id
        ''')
        total_words = cursor.fetchone()["total_words"]
        
        # Get mastered words (words with >80% success rate and at least 5 attempts)
        cursor.execute('''
            WITH word_stats AS (
                SELECT 
                    word_id,
                    COUNT(*) as total_attempts,
                    SUM(CASE WHEN correct = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as success_rate
                FROM word_review_items wri
                JOIN study_sessions ss ON wri.study_session_id = ss.id
                GROUP BY word_id
                HAVING total_attempts >= 5
            )
            SELECT COUNT(*) as mastered_words
            FROM word_stats
            WHERE success_rate >= 0.8
        ''')
        mastered_words = cursor.fetchone()["mastered_words"]
        
        # Get overall success rate
        cursor.execute('''
            SELECT 
                SUM(CASE WHEN correct = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as success_rate
            FROM word_review_items wri
            JOIN study_sessions ss ON wri.study_session_id = ss.id
        ''')
        success_rate = cursor.fetchone()["success_rate"] or 0
        
        # Get total number of study sessions
        cursor.execute('SELECT COUNT(*) as total_sessions FROM study_sessions')
        total_sessions = cursor.fetchone()["total_sessions"]
        
        # Get number of groups with activity in the last 30 days
        cursor.execute('''
            SELECT COUNT(DISTINCT group_id) as active_groups
            FROM study_sessions
            WHERE created_at >= date('now', '-30 days')
        ''')
        active_groups = cursor.fetchone()["active_groups"]
        
        # Calculate current streak (consecutive days with at least one study session)
        cursor.execute('''
            WITH daily_sessions AS (
                SELECT 
                    date(created_at) as study_date,
                    COUNT(*) as session_count
                FROM study_sessions
                GROUP BY date(created_at)
            ),
            streak_calc AS (
                SELECT 
                    study_date,
                    julianday(study_date) - julianday(lag(study_date, 1) over (order by study_date)) as days_diff
                FROM daily_sessions
            )
            SELECT COUNT(*) as streak
            FROM (
                SELECT study_date
                FROM streak_calc
                WHERE days_diff = 1 OR days_diff IS NULL
                ORDER BY study_date DESC
            )
        ''')
        current_streak = cursor.fetchone()["streak"]
        
        return {
            "total_vocabulary": total_vocabulary,
            "total_words_studied": total_words,
            # "mastered_words": mastered_words,
            "success_rate": success_rate,
            "total_sessions": total_sessions,
            "active_groups": active_groups,
            "current_streak": current_streak
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
