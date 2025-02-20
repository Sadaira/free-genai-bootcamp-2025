# endpoints/words.py
from fastapi import APIRouter, HTTPException, Depends, Query
from models.words import PaginatedWordsResponse, WordDetailResponse
import math
from lib.db import Database

router = APIRouter(prefix="/api/words", tags=["words"])

# Database Dependency
def get_db():
    db = Database()
    db.connect()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=PaginatedWordsResponse)
async def get_words(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    sort_by: str = Query("spanish", description="Sort by: spanish, english, correct_count, wrong_count"),
    order: str = Query("asc", description="Sort order: asc/desc"),
    db: Database = Depends(get_db)
):
    try:
        cursor = db.connection.cursor()
        offset = (page - 1) * per_page

        # Validate sorting parameters
        valid_columns = {"spanish", "english", "correct_count", "wrong_count"}
        sort_by = sort_by if sort_by in valid_columns else "spanish"
        order = order.lower() if order.lower() in {"asc", "desc"} else "asc"

        # Get total words count
        cursor.execute("SELECT COUNT(*) FROM words")
        total_words = cursor.fetchone()[0]
        total_pages = math.ceil(total_words / per_page) if total_words else 0

        # Get paginated words
        cursor.execute(f'''
            SELECT w.id, w.spanish, w.english,
                   COALESCE(SUM(wri.correct), 0) AS correct_count,
                   COALESCE(SUM(NOT wri.correct), 0) AS wrong_count
            FROM words w
            LEFT JOIN word_review_items wri ON w.id = wri.word_id
            GROUP BY w.id
            ORDER BY {sort_by} {order}
            LIMIT ? OFFSET ?
        ''', (per_page, offset))

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
            "current_page": page,
            "total_words": total_words
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{word_id}", response_model=WordDetailResponse)
async def get_word(word_id: int, db: Database = Depends(get_db)):
    try:
        cursor = db.connection.cursor()
        
        cursor.execute('''
            SELECT w.id, w.spanish, w.english,
                   COALESCE(SUM(wri.correct), 0) AS correct_count,
                   COALESCE(SUM(NOT wri.correct), 0) AS wrong_count,
                   GROUP_CONCAT(g.id || '::' || g.name) as groups
            FROM words w
            LEFT JOIN word_review_items wri ON w.id = wri.word_id
            LEFT JOIN word_groups wg ON w.id = wg.word_id
            LEFT JOIN groups g ON wg.group_id = g.id
            WHERE w.id = ?
            GROUP BY w.id
        ''', (word_id,))
        
        word = cursor.fetchone()
        
        if not word:
            raise HTTPException(status_code=404, detail="Word not found")

        # Parse groups
        groups = []
        if word["groups"]:
            for group_str in word["groups"].split(','):
                group_id, group_name = group_str.split('::')
                groups.append({
                    "id": int(group_id),
                    "name": group_name
                })

        return {
            "id": word["id"],
            "spanish": word["spanish"],
            "english": word["english"],
            "correct_count": word["correct_count"],
            "wrong_count": word["wrong_count"],
            "groups": groups
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))