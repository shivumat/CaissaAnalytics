from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database.db import Base


class AnalysisStatus(str, enum.Enum):
    """Analysis status enum"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Game(Base):
    """Game model for storing chess games"""
    
    __tablename__ = "games"
    
    id = Column(Integer, primary_key=True, index=True)
    pgn = Column(Text, nullable=False)
    status = Column(Enum(AnalysisStatus), default=AnalysisStatus.PENDING, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    mistakes = relationship("Mistake", back_populates="game", cascade="all, delete-orphan")


class Mistake(Base):
    """Mistake model for storing detected mistakes"""
    
    __tablename__ = "mistakes"
    
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=False)
    move_number = Column(Integer, nullable=False)
    move_san = Column(String(10), nullable=False)
    eval_before = Column(Float, nullable=False)
    eval_after = Column(Float, nullable=False)
    eval_drop = Column(Float, nullable=False)
    fen_before = Column(Text, nullable=False)
    ai_analysis = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    game = relationship("Game", back_populates="mistakes")
