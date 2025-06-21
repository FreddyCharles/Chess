# game/chess_game_manager.py
import chess

class ChessGameManager:
    """
    Manages the core chess game logic using the python-chess library.
    Handles board state, moves, game termination, and PGN generation.
    """
    def __init__(self):
        self.board = chess.Board()
        self.moves_history = [] # To store actual moves played

    def reset_game(self):
        """Resets the board to the initial chess position."""
        self.board.reset()
        self.moves_history = []

    def make_move(self, uci_move_str):
        """
        Attempts to make a move on the board given a UCI string (e.g., 'e2e4').
        Returns True if the move was legal and made, False otherwise.
        """
        try:
            move = chess.Move.from_uci(uci_move_str)
            if move in self.board.legal_moves:
                # Handle promotions if the move is a pawn promotion and 'promotion' field is missing
                # For human input, you might need a dialog to ask for promotion piece
                # For engine input, UCI move string usually includes promotion (e.g., 'e7e8q')
                if self.board.piece_at(move.from_square).piece_type == chess.PAWN and \
                   (move.to_square == chess.A8 or move.to_square == chess.H8 or \
                    move.to_square == chess.A1 or move.to_square == chess.H1) and \
                   move.promotion is None:
                    # This case should ideally be handled by UI for human or engine
                    # providing the full UCI move (e.g., e7e8q)
                    print("Warning: Promotion move without specified promotion piece. Defaulting to Queen.")
                    move.promotion = chess.QUEEN # Default to Queen for simplicity
                
                self.board.push(move)
                self.moves_history.append(move) # Store the actual move object
                return True
            else:
                print(f"Illegal move attempted: {uci_move_str}")
                return False
        except ValueError:
            print(f"Invalid UCI move string: {uci_move_str}")
            return False

    def get_board_fen(self):
        """Returns the current board state in FEN format."""
        return self.board.fen()

    def get_board_object(self):
        """Returns the actual python-chess Board object."""
        return self.board

    def get_legal_moves_for_square(self, square):
        """
        Returns a list of legal destination squares (chess.Square integers)
        for a piece on the given square.
        """
        moves = []
        for move in self.board.legal_moves:
            if move.from_square == square:
                moves.append(move.to_square)
        return moves

    def is_game_over(self):
        """Checks if the current game is over (checkmate, stalemate, draw, etc.)."""
        return self.board.is_game_over()

    def get_game_result(self):
        """
        Returns the game result and reason if the game is over.
        Returns a tuple (winner, reason) or (None, None) if not over.
        Winner: 'white', 'black', 'draw'
        Reason: 'checkmate', 'stalemate', 'insufficient material', '50-move rule', '75-move rule', 'repetition', 'resignation'
        """
        if not self.board.is_game_over():
            return None, None
        
        result_string = self.board.result(claim_draw=True) # e.g., '1-0', '0-1', '1/2-1/2'
        
        winner = None
        if result_string == '1-0':
            winner = 'white'
        elif result_string == '0-1':
            winner = 'black'
        elif result_string == '1/2-1/2':
            winner = 'draw'

        reason = None
        if self.board.is_checkmate():
            reason = 'checkmate'
        elif self.board.is_stalemate():
            reason = 'stalemate'
        elif self.board.is_insufficient_material():
            reason = 'insufficient material'
        elif self.board.is_fivefold_repetition():
            reason = '75-move rule' # 5-fold repetition implies 75-move rule
        elif self.board.is_seventyfive_moves():
            reason = '75-move rule'
        elif self.board.is_fifty_moves():
            reason = '50-move rule'
        elif self.board.is_fivefold_repetition(): # 5-fold repetition is technically part of 75-move rule.
            reason = 'repetition'
        elif self.board.is_repetition(): # 3-fold repetition, claimable draw
            reason = 'repetition'
        # Add a reason for resignation if you implement a resign button
        
        return winner, reason

    def get_pgn(self):
        """Returns the game history in PGN format."""
        game = chess.pgn.Game.from_board(chess.Board())
        for move in self.moves_history:
            game.add_variation(move)
        exporter = chess.pgn.StringExporter(headers=True, variations=True, comments=True)
        return game.accept(exporter)

    def get_current_turn_color(self):
        """Returns the color of the current player to move."""
        return self.board.turn # chess.WHITE or chess.BLACK
