import asyncio
import logging
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.models import Game, Mistake, AnalysisStatus
from app.services.stockfish_analyzer import StockfishAnalyzer
from app.services.openai_analyzer import OpenAIAnalyzer

logger = logging.getLogger(__name__)


class AnalysisService:
    """Service for orchestrating game analysis"""
    
    def __init__(self):
        self.stockfish_analyzer = StockfishAnalyzer()
        self.openai_analyzer = OpenAIAnalyzer()
    
    async def create_games(self, db: AsyncSession, pgns: List[str]) -> List[int]:
        """
        Create game records in database.
        
        Args:
            db: Database session
            pgns: List of PGN strings
            
        Returns:
            List of created game IDs
        """
        game_ids = []
        
        for pgn in pgns:
            game = Game(
                pgn=pgn,
                status=AnalysisStatus.PENDING
            )
            db.add(game)
            await db.flush()
            game_ids.append(game.id)
        
        await db.commit()
        return game_ids
    
    async def analyze_and_store(self, db: AsyncSession, game_ids: List[int]):
        """
        Analyze games and store results asynchronously.
        
        Args:
            db: Database session
            game_ids: List of game IDs to analyze
        """
        for game_id in game_ids:
            try:
                # Get game from database
                result = await db.execute(
                    select(Game).where(Game.id == game_id)
                )
                game = result.scalar_one_or_none()
                
                if not game:
                    continue
                
                # Update status to processing
                game.status = AnalysisStatus.PROCESSING
                await db.commit()
                
                # Analyze game with Stockfish (sequential)
                mistakes = self.stockfish_analyzer.analyze_game(game.pgn)
                
                # Store mistakes in database
                mistake_objects = []
                for mistake_data in mistakes:
                    mistake = Mistake(
                        game_id=game.id,
                        move_number=mistake_data["move_number"],
                        move_san=mistake_data["move_san"],
                        eval_before=mistake_data["eval_before"],
                        eval_after=mistake_data["eval_after"],
                        eval_drop=mistake_data["eval_drop"],
                        fen_before=mistake_data["fen_before"]
                    )
                    db.add(mistake)
                    mistake_objects.append(mistake)
                
                await db.commit()
                
                # Get AI analysis for mistakes asynchronously in batches
                if mistakes:
                    analyses = await self.openai_analyzer.analyze_mistakes_batch(mistakes)
                    
                    # Update mistakes with AI analysis
                    for mistake_obj, analysis in zip(mistake_objects, analyses):
                        await db.refresh(mistake_obj)
                        mistake_obj.ai_analysis = analysis
                    
                    await db.commit()
                
                # Update game status to completed
                game.status = AnalysisStatus.COMPLETED
                await db.commit()
                
            except Exception as e:
                logger.error(f"Error analyzing game {game_id}: {e}")
                # Update status to failed
                result = await db.execute(
                    select(Game).where(Game.id == game_id)
                )
                game = result.scalar_one_or_none()
                if game:
                    game.status = AnalysisStatus.FAILED
                    await db.commit()
    
    async def get_game_with_mistakes(self, db: AsyncSession, game_id: int) -> Game:
        """
        Get game with all its mistakes.
        
        Args:
            db: Database session
            game_id: Game ID
            
        Returns:
            Game object with mistakes
        """
        result = await db.execute(
            select(Game).options(selectinload(Game.mistakes)).where(Game.id == game_id)
        )
        game = result.scalar_one_or_none()
        return game
    
    async def get_all_games(self, db: AsyncSession) -> List[Game]:
        """
        Get all games with their mistakes.
        
        Args:
            db: Database session
            
        Returns:
            List of Game objects
        """
        result = await db.execute(
            select(Game).options(selectinload(Game.mistakes))
        )
        games = result.scalars().all()
        return games
