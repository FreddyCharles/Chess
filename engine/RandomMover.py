# engine/RandomMover.py
import chess
import random
from engine.base_engine import BaseChessEngine

class RandomMover(BaseChessEngine):
    """
    A simple chess engine that makes random legal moves.
    """
    def __init__(self, name="Random Mover", version="1.0"):
        super().__init__(name, version)

    def make_move(self) -> chess.Move | None:
        """
        Selects a random legal move from the current board position.
        Returns a chess.Move object if a legal move is available, otherwise None.
        """
        if self.board.is_game_over(claim_draw=True):
            # claim_draw=True considers three-fold repetition, fifty-move rule, etc.
            # as game over conditions, for which no move can be made.
            # print(f"{self.name}: Game is over, no moves to make.") # Optional: for debugging
            return None

        legal_moves = list(self.board.legal_moves)

        if not legal_moves:
            # This case should ideally be caught by is_game_over() if it's checkmate or stalemate.
            # However, it's good practice to handle it explicitly.
            # print(f"{self.name}: No legal moves available (e.g., stalemate or checkmate).") # Optional: for debugging
            return None

        random_move = random.choice(legal_moves)
        # print(f"{self.name} selected move: {random_move.uci()}") # Optional: for debugging
        return random_move

if __name__ == '__main__':
    # Example Usage / Simple Test:
    engine = RandomMover()
    board = chess.Board()
    print("RandomMover Engine - Example Usage")
    print("="*30)
    print("Initial board (FEN):")
    print(board.fen())
    print(board)

    for i in range(10): # Make up to 10 random moves for demonstration
        print(f"\n--- Turn {i+1} ({'White' if board.turn == chess.WHITE else 'Black'}) ---")
        if board.is_game_over(claim_draw=True):
            print("Game is over.")
            break

        engine.set_board(board) # Update engine's internal board with the current game board
        move = engine.make_move()

        if move:
            print(f"Engine proposes move: {move.uci()}")
            board.push(move) # Apply the move to the local board for this test
            print("Board after move (FEN):")
            print(board.fen())
            print(board)
        else:
            # This condition implies game over (checkmate/stalemate) or an unexpected issue.
            if board.is_checkmate():
                print("Checkmate!")
            elif board.is_stalemate():
                print("Stalemate!")
            elif board.is_insufficient_material():
                print("Draw due to insufficient material.")
            elif board.is_seventyfive_moves():
                print("Draw due to 75-move rule.")
            elif board.is_fivefold_repetition():
                print("Draw due to fivefold repetition.")
            else:
                print("Engine could not make a move (or game ended without specific known reason here).")
            break

    print("\n" + "="*30)
    result = board.result(claim_draw=True)
    print(f"Final game result: {result}")
    print(f"Is Checkmate: {board.is_checkmate()}")
    print(f"Is Stalemate: {board.is_stalemate()}")
    print(f"Is Insufficient Material: {board.is_insufficient_material()}")
