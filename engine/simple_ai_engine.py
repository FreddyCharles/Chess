# engine/simple_ai_engine.py
import chess
import random
import time # For simulating thinking time
from engine.base_engine import BaseChessEngine

class SimpleAIEngine(BaseChessEngine):
    """
    A very basic AI engine that makes random legal moves.
    Used for demonstration or as a fallback if no Stockfish is configured.
    """
    def __init__(self, name="Simple AI", version="1.0", delay_seconds=0.5):
        super().__init__(name, version)
        self.delay_seconds = delay_seconds # Simulate thinking time

    def make_move(self) -> chess.Move:
        """
        Chooses a random legal move from the current board state.
        Simulates thinking time with a delay.
        """
        time.sleep(self.delay_seconds) # Simulate thinking
        
        legal_moves = list(self.board.legal_moves)
        if legal_moves:
            return random.choice(legal_moves)
        return None # No legal moves (game over)
