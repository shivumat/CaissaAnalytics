import asyncio
import uuid
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.api.schemas import (
    PGNAnalysisRequest,
    AnalysisJobResponse,
    GameResponse,
    GameStatusResponse
)
from app.database import get_db, AsyncSessionLocal
from app.services.analysis_service import AnalysisService
from app.models.models import Game


router = APIRouter(prefix="/api", tags=["analysis"])
analysis_service = AnalysisService()


async def background_analysis(game_ids: List[int]):
    """Background task for analyzing games"""
    async with AsyncSessionLocal() as db:
        await analysis_service.analyze_and_store(db, game_ids)


@router.post("/analyze", response_model=AnalysisJobResponse)
async def analyze_pgns(
    request: PGNAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze chess games from PGN strings.
    
    Accepts up to 100 PGNs per request. Games are processed sequentially using
    Stockfish to detect moves with significant evaluation drops. Key mistakes are
    batched and sent to OpenAI asynchronously for logic analysis. Results are stored
    in the database, allowing the UI to track progress independently of the analysis flow.
    
    Args:
        request: PGNAnalysisRequest containing list of PGN strings
        background_tasks: FastAPI background tasks
        db: Database session
        
    Returns:
        AnalysisJobResponse with job ID and game IDs
    """
    # Create games in database
    game_ids = await analysis_service.create_games(db, request.pgns)
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Schedule background analysis
    background_tasks.add_task(background_analysis, game_ids)
    
    return AnalysisJobResponse(
        job_id=job_id,
        message="Analysis started. Use game IDs to track progress.",
        games_count=len(game_ids),
        game_ids=game_ids
    )


@router.get("/games/{game_id}", response_model=GameResponse)
async def get_game(
    game_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get game details with all detected mistakes.
    
    Args:
        game_id: Game ID
        db: Database session
        
    Returns:
        GameResponse with game details and mistakes
    """
    game = await analysis_service.get_game_with_mistakes(db, game_id)
    
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    return game


@router.get("/games/{game_id}/status", response_model=GameStatusResponse)
async def get_game_status(
    game_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get game analysis status.
    
    Args:
        game_id: Game ID
        db: Database session
        
    Returns:
        GameStatusResponse with status and mistake count
    """
    result = await db.execute(
        select(Game).where(Game.id == game_id)
    )
    game = result.scalar_one_or_none()
    
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Count mistakes
    from app.models.models import Mistake
    result = await db.execute(
        select(Mistake).where(Mistake.game_id == game_id)
    )
    mistakes = result.scalars().all()
    
    return GameStatusResponse(
        game_id=game.id,
        status=game.status,
        mistakes_count=len(mistakes)
    )


@router.get("/games", response_model=List[GameResponse])
async def list_games(
    db: AsyncSession = Depends(get_db)
):
    """
    List all analyzed games.
    
    Args:
        db: Database session
        
    Returns:
        List of GameResponse objects
    """
    games = await analysis_service.get_all_games(db)
    return games
