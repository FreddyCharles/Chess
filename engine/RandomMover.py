import chess
import chess.engine
import random
import sys

class RandomMover:
    def __init__(self):
        self.board = chess.Board()

    def uci_loop(self):
        """Implements a basic UCI loop to communicate with a UCI GUI/tester."""
        while True:
            line = sys.stdin.readline().strip()
            if line == "uci":
                sys.stdout.write("id name RandomMover\n")
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
                            # This should ideally not happen if the UCI communication is correct
                            print(f"info string Illegal move received: {move_uci}", file=sys.stderr)
                else:
                    self.board = chess.Board(" ".join(parts[1:]))
            elif line.startswith("go"):
                # Find a random legal move
                legal_moves = list(self.board.legal_moves)
                if legal_moves:
                    chosen_move = random.choice(legal_moves)
                    sys.stdout.write(f"bestmove {chosen_move.uci()}\n")
                else:
                    # No legal moves means game over (checkmate, stalemate, etc.)
                    # Engines usually don't send 'bestmove none' but rather let the GUI handle game over
                    # For this simple engine, we can just print a message.
                    if self.board.is_checkmate():
                        sys.stdout.write("info string Checkmate!\n")
                    elif self.board.is_stalemate():
                        sys.stdout.write("info string Stalemate!\n")
                    # ... handle other draw conditions
                    sys.stdout.write("bestmove (none)\n") # Some GUIs might expect this for game over
                sys.stdout.flush()
            elif line == "quit":
                break
            else:
                # Optionally log unknown commands for debugging
                print(f"info string Unknown command: {line}", file=sys.stderr)

if __name__ == "__main__":
    engine = RandomMover()
    engine.uci_loop()