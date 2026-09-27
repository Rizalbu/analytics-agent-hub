"""A trivial agent-authored module."""
from fastapi import APIRouter

router = APIRouter()

@router.get("/api/agent_features/ping")
def ping():
    return {"pong": True}