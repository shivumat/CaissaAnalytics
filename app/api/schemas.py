from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime
from app.models.models import AnalysisStatus


class PGNAnalysisRequest(BaseModel):
    """Request model for PGN analysis"""
    
    pgns: List[str] = Field(..., min_length=1, max_length=100, description="List of PGN strings to analyze")
    
    @field_validator('pgns')
    @classmethod
    def validate_pgns(cls, v):
        if not v:
            raise ValueError("At least one PGN is required")
        if len(v) > 100:
            raise ValueError("Maximum 100 PGNs allowed per request")
        return v


class MistakeResponse(BaseModel):
    """Response model for a mistake"""
    
    id: int
    move_number: int
    move_san: str
    eval_before: float
    eval_after: float
    eval_drop: float
    fen_before: str
    ai_analysis: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class GameResponse(BaseModel):
    """Response model for a game"""
    
    id: int
    pgn: str
    status: AnalysisStatus
    created_at: datetime
    updated_at: datetime
    mistakes: List[MistakeResponse] = []
    
    class Config:
        from_attributes = True


class AnalysisJobResponse(BaseModel):
    """Response model for analysis job submission"""
    
    job_id: str
    message: str
    games_count: int
    game_ids: List[int]


class GameStatusResponse(BaseModel):
    """Response model for game status"""
    
    game_id: int
    status: AnalysisStatus
    mistakes_count: int
