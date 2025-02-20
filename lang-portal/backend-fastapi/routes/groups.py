# endpoints/groups.py
from fastapi import APIRouter, HTTPException, Depends, Query
from models.groups import GroupResponse, PaginatedGroupResponse, PaginatedWordResponse, PaginatedSessionResponse
import math
from lib.db import Database

router = APIRouter(prefix="/api/groups", tags=["groups"])

# Database Dependency
def get_db():
    db = Database()
    db.connect()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=PaginatedGroupResponse)
async def get_groups(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    sort_by: str = Query("name", description="Sort by 'name' or 'words_count'"),
    order: str = Query("asc", description="Sort order: 'asc' or 'desc'"),
    db: Database = Depends(get_db)
):
    try:
        cursor = db.connection.cursor()
        offset = (page - 1) * per_page

        # Validate sorting parameters
        valid_columns = {"name", "words_count"}
        sort_by = sort_by if sort_by in valid_columns else "name"
        order = order.lower() if order.lower() in {"asc", "desc"} else "asc"

        # Get total groups count
        cursor.execute("SELECT COUNT(*) FROM groups")
        total_groups = cursor.fetchone()[0]
        total_pages = math.ceil(total_groups / per_page) if total_groups else 0

        # Get paginated groups
        cursor.execute(f'''
            SELECT id, name, words_count
            FROM groups
            ORDER BY {sort_by} {order}
            LIMIT ? OFFSET ?
        ''', (per_page, offset))

        groups = [{
            "id": group["id"],
            "group_name": group["name"],
            "word_count": group["words_count"]
        } for group in cursor.fetchall()]

        return {
            "groups": groups,
            "total_pages": total_pages,
            "current_page": page
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(group_id: int, db: Database = Depends(get_db)):
    try:
        cursor = db.connection.cursor()
        cursor.execute('''
            SELECT id, name, words_count
            FROM groups
            WHERE id = ?
        ''', (group_id,))
        
        group = cursor.fetchone()
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")

        return {
            "id": group["id"],
            "group_name": group["name"],
            "word_count": group["words_count"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{group_id}/words", response_model=PaginatedWordResponse)
async def get_group_words(
    group_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    sort_by: str = Query("spanish", description="Sort by: spanish, english, correct_count, wrong_count"),
    order: str = Query("asc", description="Sort order: asc/desc"),
    db: Database = Depends(get_db)
):
    try:
        cursor = db.connection.cursor()
        offset = (page - 1) * per_page

        # Validate group exists
        cursor.execute("SELECT name FROM groups WHERE id = ?", (group_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Group not found")

        # Validate sorting parameters
        valid_columns = {"spanish", "english", "correct_count", "wrong_count"}
        sort_by = sort_by if sort_by in valid_columns else "spanish"
        order = order.lower() if order.lower() in {"asc", "desc"} else "asc"

        # Get total words count
        cursor.execute("SELECT COUNT(*) FROM word_groups WHERE group_id = ?", (group_id,))
        total_words = cursor.fetchone()[0]
        total_pages = math.ceil(total_words / per_page) if total_words else 0

        # Get paginated words
        cursor.execute(f'''
            SELECT w.id, w.spanish, w.english,
                   COALESCE(SUM(wri.correct), 0) as correct_count,
                   COALESCE(SUM(NOT wri.correct), 0) as wrong_count
            FROM words w
            JOIN word_groups wg ON w.id = wg.word_id
            LEFT JOIN word_review_items wri ON w.id = wri.word_id
            WHERE wg.group_id = ?
            GROUP BY w.id
            ORDER BY {sort_by} {order}
            LIMIT ? OFFSET ?
        ''', (group_id, per_page, offset))

        words = [{
            "id": word["id"],
            "spanish": word["spanish"],
            "english": word["english"],
            "correct_count": word["correct_count"],
            "wrong_count": word["wrong_count"]
        } for word in cursor.fetchall()]

        return {
            "words": words,
            "total_pages": total_pages,
            "current_page": page
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{group_id}/study_sessions", response_model=PaginatedSessionResponse)
async def get_group_study_sessions(
    group_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    sort_by: str = Query("created_at", description="Sort by: created_at, last_activity_time, activity_name, group_name, review_count"),
    order: str = Query("desc", description="Sort order: asc/desc"),
    db: Database = Depends(get_db)
):
    try:
        cursor = db.connection.cursor()
        offset = (page - 1) * per_page

        # Validate group exists
        cursor.execute("SELECT name FROM groups WHERE id = ?", (group_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Group not found")

        # Map sort parameters
        sort_mapping = {
            "created_at": "s.created_at",
            "last_activity_time": "last_activity_time",
            "activity_name": "a.name",
            "group_name": "g.name",
            "review_count": "review_count"
        }
        sort_column = sort_mapping.get(sort_by, "s.created_at")
        order = order.lower() if order.lower() in {"asc", "desc"} else "desc"

        # Get total sessions count
        cursor.execute("SELECT COUNT(*) FROM study_sessions WHERE group_id = ?", (group_id,))
        total_sessions = cursor.fetchone()[0]
        total_pages = math.ceil(total_sessions / per_page) if total_sessions else 0

        # Get paginated sessions
        cursor.execute(f'''
            SELECT 
                s.id,
                s.group_id,
                g.name as group_name,
                s.study_activity_id,
                a.name as activity_name,
                s.created_at as start_time,
                MAX(wri.created_at) as last_activity_time,
                COUNT(wri.id) as review_count
            FROM study_sessions s
            JOIN study_activities a ON s.study_activity_id = a.id
            JOIN groups g ON s.group_id = g.id
            LEFT JOIN word_review_items wri ON s.id = wri.study_session_id
            WHERE s.group_id = ?
            GROUP BY s.id
            ORDER BY {sort_column} {order}
            LIMIT ? OFFSET ?
        ''', (group_id, per_page, offset))

        sessions = []
        for session in cursor.fetchall():
            end_time = session["last_activity_time"] or db.connection.execute(
                "SELECT datetime(?, '+30 minutes')", 
                (session["start_time"],)
            ).fetchone()[0]

            sessions.append({
                "id": session["id"],
                "group_id": session["group_id"],
                "group_name": session["group_name"],
                "study_activity_id": session["study_activity_id"],
                "activity_name": session["activity_name"],
                "start_time": session["start_time"],
                "end_time": end_time,
                "review_items_count": session["review_count"]
            })

        return {
            "study_sessions": sessions,
            "total_pages": total_pages,
            "current_page": page
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))