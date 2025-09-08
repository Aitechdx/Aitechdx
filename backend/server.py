from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, date

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models for Health Reminders
class HealthSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = "default_user"  # For simplicity, using default user
    session_date: date
    sitting_duration: int  # in minutes
    activity_duration: int  # in minutes
    completed: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class HealthSessionCreate(BaseModel):
    sitting_duration: int
    activity_duration: int
    completed: bool = False

class DailyProgress(BaseModel):
    date: date
    total_sessions: int
    total_sitting_time: int  # in minutes
    total_activity_time: int  # in minutes
    sessions: List[HealthSession]

class UserSettings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = "default_user"
    sitting_reminder_minutes: int = 50
    activity_break_minutes: int = 10
    notifications_enabled: bool = True
    sound_alerts_enabled: bool = True
    daily_goal_sessions: int = 8  # 8 cycles per day (approx 8 hours)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class UserSettingsUpdate(BaseModel):
    sitting_reminder_minutes: Optional[int] = None
    activity_break_minutes: Optional[int] = None
    notifications_enabled: Optional[bool] = None
    sound_alerts_enabled: Optional[bool] = None
    daily_goal_sessions: Optional[int] = None

# Health reminder endpoints
@api_router.get("/")
async def root():
    return {"message": "Health Reminder API", "status": "active"}

@api_router.post("/sessions", response_model=HealthSession)
async def create_session(session: HealthSessionCreate):
    """Create a new health session"""
    session_dict = session.dict()
    session_dict['session_date'] = date.today()
    session_obj = HealthSession(**session_dict)
    
    # Convert date objects to strings for MongoDB storage
    session_data = session_obj.dict()
    session_data['session_date'] = session_data['session_date'].isoformat()
    
    await db.health_sessions.insert_one(session_data)
    return session_obj

@api_router.get("/sessions/today", response_model=List[HealthSession])
async def get_today_sessions():
    """Get all sessions for today"""
    today = date.today()
    sessions = await db.health_sessions.find({"session_date": today.isoformat()}).to_list(100)
    return [HealthSession(**session) for session in sessions]

@api_router.get("/sessions/progress")
async def get_daily_progress():
    """Get daily progress summary"""
    today = date.today()
    sessions = await db.health_sessions.find({"session_date": today.isoformat()}).to_list(100)
    
    total_sessions = len(sessions)
    completed_sessions = len([s for s in sessions if s.get('completed', False)])
    total_sitting_time = sum(s.get('sitting_duration', 0) for s in sessions)
    total_activity_time = sum(s.get('activity_duration', 0) for s in sessions)
    
    return {
        "date": today,
        "total_sessions": total_sessions,
        "completed_sessions": completed_sessions,
        "total_sitting_time": total_sitting_time,
        "total_activity_time": total_activity_time,
        "sessions": [HealthSession(**session) for session in sessions]
    }

@api_router.get("/sessions/weekly")
async def get_weekly_progress():
    """Get weekly progress summary"""
    from datetime import timedelta
    
    today = date.today()
    week_ago = today - timedelta(days=7)
    
    sessions = await db.health_sessions.find({
        "session_date": {"$gte": week_ago.isoformat(), "$lte": today.isoformat()}
    }).to_list(1000)
    
    # Group sessions by date
    daily_stats = {}
    for session in sessions:
        session_date = session.get('session_date')
        if session_date not in daily_stats:
            daily_stats[session_date] = {
                "date": session_date,
                "total_sessions": 0,
                "completed_sessions": 0,
                "total_sitting_time": 0,
                "total_activity_time": 0
            }
        
        daily_stats[session_date]["total_sessions"] += 1
        if session.get('completed', False):
            daily_stats[session_date]["completed_sessions"] += 1
        daily_stats[session_date]["total_sitting_time"] += session.get('sitting_duration', 0)
        daily_stats[session_date]["total_activity_time"] += session.get('activity_duration', 0)
    
    return {
        "week_start": week_ago,
        "week_end": today,
        "daily_progress": list(daily_stats.values())
    }

@api_router.post("/sessions/{session_id}/complete")
async def complete_session(session_id: str):
    """Mark a session as completed"""
    result = await db.health_sessions.update_one(
        {"id": session_id},
        {"$set": {"completed": True, "timestamp": datetime.utcnow().isoformat()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get updated session
    session = await db.health_sessions.find_one({"id": session_id})
    return HealthSession(**session)

@api_router.get("/settings", response_model=UserSettings)
async def get_user_settings():
    """Get user settings"""
    settings = await db.user_settings.find_one({"user_id": "default_user"})
    
    if not settings:
        # Create default settings
        default_settings = UserSettings()
        settings_data = default_settings.dict()
        settings_data['timestamp'] = settings_data['timestamp'].isoformat()
        await db.user_settings.insert_one(settings_data)
        return default_settings
    
    return UserSettings(**settings)

@api_router.put("/settings", response_model=UserSettings)
async def update_user_settings(settings_update: UserSettingsUpdate):
    """Update user settings"""
    update_data = {k: v for k, v in settings_update.dict().items() if v is not None}
    update_data["timestamp"] = datetime.utcnow().isoformat()
    
    result = await db.user_settings.update_one(
        {"user_id": "default_user"},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        # Create new settings if none exist
        new_settings = UserSettings(**update_data)
        settings_data = new_settings.dict()
        settings_data['timestamp'] = settings_data['timestamp'].isoformat()
        await db.user_settings.insert_one(settings_data)
        return new_settings
    
    # Get updated settings
    settings = await db.user_settings.find_one({"user_id": "default_user"})
    return UserSettings(**settings)

# Legacy endpoints (keeping for compatibility)
@api_router.post("/status", response_model=dict)
async def create_status_check(input: dict):
    """Legacy status check endpoint"""
    return {"message": "Health Reminder API is active", "timestamp": datetime.utcnow()}

@api_router.get("/status", response_model=dict)
async def get_status_checks():
    """Legacy status check endpoint"""
    return {"message": "Health Reminder API is active", "timestamp": datetime.utcnow()}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()