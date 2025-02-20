# endpoints/study_activities.py
from fastapi import APIRouter, HTTPException, Depends, Query
from models.study_activites import StudyActivityResponse, PaginatedSessionResponse, StudyActivityLaunchResponse
import math
from lib.db import Database

router = APIRouter(prefix="/api/study-activities", tags=["study_activities"])

# Database Dependency
def get_db():
    db = Database()
    db.connect()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=List[StudyActivityResponse])
async def get_all_study_activities(db: Database = Depends(get_db)):
    try:
        cursor = db.connection.cursor()
        cursor.execute('SELECT id, name, url, preview_url FROM study_activities')
        activities = cursor.fetchall()
        
        return [{
            "id": activity["id"],
            "title": activity["name"],
            "launch_url": activity["url"],
            "preview_url": activity["preview_url"]
        } for activity in activities]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{activity_id}", response_model=StudyActivityResponse)
async def get_study_activity(activity_id: int, db: Database = Depends(get_db)):
    try:
        cursor = db.connection.cursor()
        cursor.execute(
            'SELECT id, name, url, preview_url FROM study_activities WHERE id = ?',
            (activity_id,)
        )
        activity = cursor.fetchone()
        
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")
            
        return {
            "id": activity["id"],
            "title": activity["name"],
            "launch_url": activity["url"],
            "preview_url": activity["preview_url"]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{activity_id}/sessions", response_model=PaginatedSessionResponse)
async def get_activity_sessions(
    activity_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: Database = Depends(get_db)
):
    try:
        cursor = db.connection.cursor()
        offset = (page - 1) * per_page

        # Verify activity exists
        cursor.execute('SELECT id FROM study_activities WHERE id = ?', (activity_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Activity not found")

        # Get total count
        cursor.execute('''
            SELECT COUNT(*) as count 
            FROM study_sessions ss
            JOIN groups g ON g.id = ss.group_id
            WHERE ss.study_activity_id = ?
        ''', (activity_id,))
        total_count = cursor.fetchone()['count']

        # Get paginated sessions
        cursor.execute('''
            SELECT 
                ss.id,
                ss.group_id,
                g.name as group_name,
                sa.name as activity_name,
                ss.created_at,
                ss.study_activity_id as activity_id,
                COUNT(wri.id) as review_items_count
            FROM study_sessions ss
            JOIN groups g ON g.id = ss.group_id
            JOIN study_activities sa ON sa.id = ss.study_activity_id
            LEFT JOIN word_review_items wri ON wri.study_session_id = ss.id
            WHERE ss.study_activity_id = ?
            GROUP BY ss.id, ss.group_id, g.name, sa.name, ss.created_at, ss.study_activity_id
            ORDER BY ss.created_at DESC
            LIMIT ? OFFSET ?
        ''', (activity_id, per_page, offset))
        
        sessions = cursor.fetchall()

        return {
            "items": [{
                "id": session["id"],
                "group_id": session["group_id"],
                "group_name": session["group_name"],
                "activity_id": session["activity_id"],
                "activity_name": session["activity_name"],
                "start_time": str(session["created_at"]),
                "end_time": str(session["created_at"]),
                "review_items_count": session["review_items_count"]
            } for session in sessions],
            "total": total_count,
            "page": page,
            "per_page": per_page,
            "total_pages": math.ceil(total_count / per_page) if total_count else 0
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{activity_id}/launch", response_model=StudyActivityLaunchResponse)
async def get_activity_launch_data(activity_id: int, db: Database = Depends(get_db)):
    try:
        cursor = db.connection.cursor()

        # Get activity details
        cursor.execute(
            'SELECT id, name, url, preview_url FROM study_activities WHERE id = ?',
            (activity_id,)
        )
        activity = cursor.fetchone()
        
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")

        # Get available groups
        cursor.execute('SELECT id, name FROM groups')
        groups = cursor.fetchall()

        return {
            "activity": {
                "id": activity["id"],
                "title": activity["name"],
                "launch_url": activity["url"],
                "preview_url": activity["preview_url"]
            },
            "groups": [{
                "id": group["id"],
                "name": group["name"]
            } for group in groups]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))