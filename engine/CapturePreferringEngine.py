# engine/CapturePreferringEngine.py
import chess
import random
from engine.base_engine import BaseChessEngine

class CapturePreferringEngine(BaseChessEngine):
    """
    A simple chess engine that prefers making capturing moves.
    If multiple capture moves are available, it picks one randomly.
    If no capture moves are available, it makes a random legal move.
    """
    def __init__(self, name="CapturePreferringEngine", version="1.0"):
        super().__init__(name, version)

    def make_move(self) -> chess.Move | None:
        """
        Selects a move based on the following preference:
        1. Random capturing move.
        2. Random non-capturing legal move.
        Returns a chess.Move object if a legal move is available, otherwise None.
        """
        if self.board.is_game_over(claim_draw=True):
            return None

        legal_moves = list(self.board.legal_moves)
        if not legal_moves:
            return None

        capturing_moves = [move for move in legal_moves if self.board.is_capture(move)]

        if capturing_moves:
            # print(f"{self.name} found capturing moves: {[m.uci() for m in capturing_moves]}")
            selected_move = random.choice(capturing_moves)
            # print(f"{self.name} selected capturing move: {selected_move.uci()}")
            return selected_move
        else:
            # No capturing moves, make any random legal move
            selected_move = random.choice(legal_moves)
            # print(f"{self.name} selected non-capturing move: {selected_move.uci()}")
            return selected_move

if __name__ == '__main__':
    # Example Usage / Simple Test:
    engine = CapturePreferringEngine()

    # Test scenario 1: Obvious capture available
    board1 = chess.Board("rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2") # e4 d5
    engine.set_board(board1)
    print("Board 1 (Capture available for White: exd5):")
    print(board1)
    move1 = engine.make_move()
    if move1:
        print(f"Engine proposed move: {move1.uci()} (Expected: exd5 or similar capture if others existed)\n")
        assert board1.is_capture(move1)
    else:
        print("Engine made no move on Board 1.\n")

    # Test scenario 2: No capture, only other moves
    board2 = chess.Board("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1") # Initial position
    engine.set_board(board2)
    print("Board 2 (No captures, initial position):")
    print(board2)
    move2 = engine.make_move()
    if move2:
        print(f"Engine proposed move: {move2.uci()} (Expected: any legal non-capturing move)\n")
        assert not board2.is_capture(move2)
    else:
        print("Engine made no move on Board 2.\n")

    # Test scenario 3: Multiple captures
    board3 = chess.Board("1k1r4/1pp4p/p7/P3np2/1P3N2/2R1P1P1/4K2P/8 b - - 0 1") # Black to move, can take c3 or f4
    # Possible captures for black: Rxc3, Nxf4
    engine.set_board(board3)
    print("Board 3 (Multiple captures for Black: ...Rxc3 or ...Nxf4):")
    print(board3)
    move3 = engine.make_move()
    if move3:
        print(f"Engine proposed move: {move3.uci()} (Expected: a capturing move)\n")
        assert board3.is_capture(move3)
    else:
        print("Engine made no move on Board 3.\n")

    # Test scenario 4: Forced non-capture (e.g., only one legal move, not a capture)
    board4 = chess.Board("7k/8/8/8/8/8/7P/R6K w - - 0 1") # White to play, Ra1h1 is not a capture
    engine.set_board(board4) # White has Ra2, Ra3 ... Rh1, Kg2.
    print("Board 4 (White to play, many non-captures):")
    print(board4)
    move4 = engine.make_move()
    if move4:
        print(f"Engine proposed move: {move4.uci()}\n")
        assert not board4.is_capture(move4) # Should be a non-capture
    else:
        print("Engine made no move on Board 4.\n")

    # Test scenario 5: Checkmate (no moves)
    board5 = chess.Board("rnb1kbnr/pppp1ppp/8/4p3/5PPq/8/PPPPP2P/RNBQKBNR w KQkq - 1 3") # Black has checkmated White
    engine.set_board(board5)
    print("Board 5 (White is checkmated):")
    print(board5)
    move5 = engine.make_move()
    if move5:
        print(f"Engine proposed move: {move5.uci()} (ERROR, should be None)\n")
    else:
        print("Engine made no move (Correct for checkmate).\n")
        assert board5.is_checkmate()
