"""Auto-authored: top studios by revenue endpoint."""
from fastapi import APIRouter
from app import queries

router = APIRouter()

@router.get("/api/agent_features/top_studios")
def top_studios():
    return {"league": queries.studio_league({})[:5]}