# engine/base_engine.py
import abc
import chess

class BaseChessEngine(abc.ABC):
    """
    Abstract base class for all chess engines.
    Defines the common interface that all engines must implement.
    """
    def __init__(self, name="Unnamed Engine", version="1.0"):
        self.name = name
        self.version = version
        self.board = chess.Board() # Internal board state for the engine

    def set_board(self, board: chess.Board):
        """
        Sets the engine's internal board state to the current game board.
        This is crucial for the engine to know the current position.
        """
        self.board = board.copy() # Make a copy to avoid external modification issues

    @abc.abstractmethod
    def make_move(self) -> chess.Move:
        """
        Calculates and returns the best move for the current board state.
        This method must be implemented by concrete engine classes.
        Returns a chess.Move object.
        """
        pass
