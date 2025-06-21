# engine/stockfish_engine.py
import chess
import chess.engine
import sys
from engine.base_engine import BaseChessEngine

class StockfishEngine(BaseChessEngine):
    """
    A wrapper for the Stockfish chess engine (or any UCI-compatible engine).
    Requires the Stockfish executable to be downloaded and its path provided.
    """
    def __init__(self, path_to_engine: str, name="Stockfish", version="15", skill_level=20):
        super().__init__(name, version)
        self.path_to_engine = path_to_engine
        self.skill_level = skill_level
        self.engine = None
        self._connect_engine()

    def _connect_engine(self):
        """Attempts to connect to the Stockfish engine executable."""
        try:
            # `chess.engine.popen_uci` starts the engine process
            # `debug=True` can be useful for debugging communication
            self.engine = chess.engine.popen_uci(self.path_to_engine)
            self.engine.configure({"Skill Level": self.skill_level})
            print(f"Connected to {self.name} engine at {self.path_to_engine}")
        except FileNotFoundError:
            print(f"Error: Engine executable not found at {self.path_to_engine}", file=sys.stderr)
            print("Please ensure Stockfish (or your chosen UCI engine) is downloaded and the path is correct.", file=sys.stderr)
            self.engine = None
        except Exception as e:
            print(f"Error connecting to engine: {e}", file=sys.stderr)
            self.engine = None

    def make_move(self) -> chess.Move:
        """
        Asks the Stockfish engine to calculate and return the best move.
        Requires the board state to be set beforehand using set_board().
        """
        if not self.engine:
            print(f"Engine {self.name} is not connected. Cannot make move.", file=sys.stderr)
            return None

        try:
            # `self.engine.play(board, limit)` asks the engine to find a move
            # `chess.engine.Limit(time=2.0)` limits thinking time to 2 seconds
            # You can also use `depth`, `nodes`, etc.
            result = self.engine.play(self.board, chess.engine.Limit(time=0.5)) # 0.5 seconds thinking time
            return result.move
        except chess.engine.EngineError as e:
            print(f"Engine error during move calculation: {e}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"Unexpected error in engine.make_move: {e}", file=sys.stderr)
            return None

    def quit(self):
        """Terminates the engine process."""
        if self.engine:
            print(f"Quitting {self.name} engine.")
            self.engine.quit()
            self.engine = None

# Remember to call engine.quit() when your application exits!
# Example usage (for testing):
if __name__ == "__main__":
    # IMPORTANT: Replace with the actual path to your Stockfish executable!
    stockfish_path = "/usr/local/bin/stockfish" # Example for Linux/macOS
    # stockfish_path = "C:\\Stockfish\\stockfish-windows-x86-64-avx2.exe" # Example for Windows

    engine = StockfishEngine(stockfish_path, skill_level=10)
    if engine.engine:
        board = chess.Board()
        print("Initial board:")
        print(board)
        
        engine.set_board(board)
        move = engine.make_move()
        if move:
            print(f"Engine's first move: {move.uci()}")
            board.push(move)
            print("Board after engine move:")
            print(board)
        
        # Simulate a few more moves
        board.push_san("e5")
        engine.set_board(board)
        move2 = engine.make_move()
        if move2:
            print(f"Engine's second move: {move2.uci()}")
            board.push(move2)
            print("Board after second engine move:")
            print(board)

    engine.quit()
