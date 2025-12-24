import chess
import chess.pgn
from io import StringIO
from typing import List, Tuple, Optional
from stockfish import Stockfish
from app.config import settings


class StockfishAnalyzer:
    """Service for analyzing chess games with Stockfish"""
    
    def __init__(self):
        self.stockfish_path = settings.stockfish_path
        self.depth = settings.stockfish_depth
        self.time_limit = settings.stockfish_time_limit
        self.mistake_threshold = settings.mistake_threshold
    
    def _get_stockfish(self) -> Stockfish:
        """Get a Stockfish instance"""
        return Stockfish(
            path=self.stockfish_path,
            depth=self.depth,
            parameters={
                "Threads": 1,
                "Hash": 16
            }
        )
    
    def analyze_game(self, pgn_string: str) -> List[dict]:
        """
        Analyze a single game and detect mistakes.
        
        Args:
            pgn_string: PGN string of the game
            
        Returns:
            List of dictionaries containing mistake information
        """
        mistakes = []
        
        try:
            # Parse PGN
            pgn = StringIO(pgn_string)
            game = chess.pgn.read_game(pgn)
            
            if not game:
                return mistakes
            
            # Initialize Stockfish
            stockfish = self._get_stockfish()
            
            # Get the mainline of the game
            board = game.board()
            move_number = 1
            
            for move in game.mainline_moves():
                # Get evaluation before the move
                stockfish.set_fen_position(board.fen())
                eval_info = stockfish.get_evaluation()
                
                # Convert evaluation to centipawns from white's perspective
                if eval_info["type"] == "cp":
                    current_eval = eval_info["value"]
                elif eval_info["type"] == "mate":
                    # Mate scores: positive = white winning, negative = black winning
                    mate_in = eval_info["value"]
                    current_eval = 10000 if mate_in > 0 else -10000
                else:
                    current_eval = 0
                
                # Apply the move
                fen_before = board.fen()
                move_san = board.san(move)
                board.push(move)
                
                # Get evaluation after the move
                stockfish.set_fen_position(board.fen())
                eval_info_after = stockfish.get_evaluation()
                
                if eval_info_after["type"] == "cp":
                    eval_after = eval_info_after["value"]
                elif eval_info_after["type"] == "mate":
                    mate_in = eval_info_after["value"]
                    eval_after = 10000 if mate_in > 0 else -10000
                else:
                    eval_after = 0
                
                # Detect mistakes based on evaluation drop
                # Evaluations are from white's perspective
                # After a move, we check if the position got worse for the player who moved
                is_white_move = board.turn == chess.BLACK  # After move, turn changes
                
                if is_white_move:
                    # White's move - drop is when eval decreases (from white's perspective)
                    eval_drop = current_eval - eval_after
                else:
                    # Black's move - drop is when eval increases (getting better for white = worse for black)
                    # From black's perspective, we flip the signs
                    eval_drop = (-current_eval) - (-eval_after)  # = eval_after - current_eval
                
                # If eval drop is significant, record as mistake
                if eval_drop >= self.mistake_threshold:
                    mistakes.append({
                        "move_number": move_number,
                        "move_san": move_san,
                        "eval_before": current_eval,
                        "eval_after": eval_after,
                        "eval_drop": eval_drop,
                        "fen_before": fen_before
                    })
                
                move_number += 1
            
            del stockfish
            
        except Exception as e:
            print(f"Error analyzing game: {e}")
            return []
        
        return mistakes
    
    def analyze_games(self, pgn_strings: List[str]) -> dict:
        """
        Analyze multiple games sequentially.
        
        Args:
            pgn_strings: List of PGN strings
            
        Returns:
            Dictionary mapping game index to list of mistakes
        """
        results = {}
        
        for idx, pgn_string in enumerate(pgn_strings):
            mistakes = self.analyze_game(pgn_string)
            results[idx] = mistakes
        
        return results
