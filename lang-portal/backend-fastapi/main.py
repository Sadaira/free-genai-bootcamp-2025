import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import dashboard, study_activities, words, groups, study_sessions#, review
from lib.db import db


app = FastAPI()

@app.on_event("startup")
async def startup():
    # Initialize database connection
    db.connect()
    
@app.on_event("shutdown")
async def shutdown():
    # Cleanup database connection
    db.close()


origins = [
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


app.include_router(dashboard.router)
app.include_router(study_activities.router)
# app.include_router(words.router)
app.include_router(groups.router)
app.include_router(study_sessions.router)
# app.include_router(review.router)
