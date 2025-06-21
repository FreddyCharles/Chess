import chess
import chess.engine
import sys

# Define piece values
PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 300,
    chess.BISHOP: 300,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0 # King value is handled by checkmate/game over, not material
}

class MaterialEvaluator:
    def __init__(self):
        self.board = chess.Board()

    def evaluate_board(self, board):
        """
        Simple material evaluation.
        Positive score favors White, negative favors Black.
        """
        score = 0
        for piece_type in PIECE_VALUES:
            score += len(board.pieces(piece_type, chess.WHITE)) * PIECE_VALUES[piece_type]
            score -= len(board.pieces(piece_type, chess.BLACK)) * PIECE_VALUES[piece_type]
        return score

    def find_best_move(self):
        """
        Finds the best move by looking one ply ahead (evaluates after opponent's move is made).
        This is a very simplistic "minimax" of depth 1.
        """
        if self.board.is_game_over():
            return None

        # Determine if we are maximizing (White) or minimizing (Black)
        if self.board.turn == chess.WHITE:
            best_score = -float('inf')
        else: # Black to move
            best_score = float('inf')

        best_move = None

        for move in self.board.legal_moves:
            self.board.push(move)
            
            # Opponent's turn: They will try to minimize our score (maximize theirs)
            # Find the best response from the opponent based on material
            if self.board.is_game_over(): # Check if our move led to game over
                 if self.board.is_checkmate():
                     # If we checkmated, this is a winning move!
                     score_after_move = float('inf') if self.board.turn == chess.BLACK else -float('inf')
                 else: # Draw condition
                     score_after_move = 0
            else:
                opponent_moves = list(self.board.legal_moves)
                if not opponent_moves: # Opponent has no moves (stalemate)
                    score_after_move = 0
                else:
                    if self.board.turn == chess.WHITE: # Opponent is White, they maximize
                        opponent_best_score = -float('inf')
                        for opp_move in opponent_moves:
                            self.board.push(opp_move)
                            opponent_best_score = max(opponent_best_score, self.evaluate_board(self.board))
                            self.board.pop()
                        score_after_move = opponent_best_score
                    else: # Opponent is Black, they minimize
                        opponent_best_score = float('inf')
                        for opp_move in opponent_moves:
                            self.board.push(opp_move)
                            opponent_best_score = min(opponent_best_score, self.evaluate_board(self.board))
                            self.board.pop()
                        score_after_move = opponent_best_score
            
            self.board.pop() # Undo our move

            if self.board.turn == chess.WHITE: # We are White, we maximize
                if score_after_move > best_score:
                    best_score = score_after_move
                    best_move = move
            else: # We are Black, we minimize
                if score_after_move < best_score:
                    best_score = score_after_move
                    best_move = move

        return best_move

    def uci_loop(self):
        """Implements a basic UCI loop to communicate with a UCI GUI/tester."""
        while True:
            line = sys.stdin.readline().strip()
            if line == "uci":
                sys.stdout.write("id name MaterialEvaluator\n")
                sys.stdout.write("id author YourName\n")
                sys.stdout.write("uciok\n")
                sys.stdout.flush()
            elif line == "isready":
                sys.stdout.write("readyok\n")
                sys.stdout.flush()
            elif line == "ucinewgame":
                self.board = chess.Board()
            elif line.startswith("position"):
                parts = line.split()
                if "moves" in parts:
                    moves_index = parts.index("moves")
                    fen_part = " ".join(parts[1:moves_index])
                    self.board = chess.Board(fen_part)
                    for move_uci in parts[moves_index + 1:]:
                        move = chess.Move.from_uci(move_uci)
                        if move in self.board.legal_moves:
                            self.board.push(move)
                        else:
                            print(f"info string Illegal move received: {move_uci}", file=sys.stderr)
                else:
                    self.board = chess.Board(" ".join(parts[1:]))
            elif line.startswith("go"):
                chosen_move = self.find_best_move()
                if chosen_move:
                    sys.stdout.write(f"bestmove {chosen_move.uci()}\n")
                else:
                    sys.stdout.write("bestmove (none)\n")
                sys.stdout.flush()
            elif line == "quit":
                break
            else:
                print(f"info string Unknown command: {line}", file=sys.stderr)

if __name__ == "__main__":
    engine = MaterialEvaluator()
    engine.uci_loop()