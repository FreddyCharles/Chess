# ui/human_vs_human_screen.py
import pygame
import chess
from ui.base_screen import BaseScreen
from game.chess_game_manager import ChessGameManager
from config import (LIGHT_COLOR, DARK_COLOR, HIGHLIGHT_COLOR, LEGAL_MOVE_HIGHLIGHT_COLOR, SQUARE_SIZE,
                    TEXT_COLOR, BACKGROUND_COLOR, FONT_NAME, FONT_SIZE_LARGE, BUTTON_COLOR,
                    BUTTON_HOVER_COLOR, PADDING_MEDIUM, BUTTON_HEIGHT_STD, TEXT_ON_LIGHT_BG_COLOR,
                    MESSAGE_BOX_BG_COLOR, MESSAGE_BOX_BORDER_COLOR)
from datetime import datetime

class HumanVsHumanScreen(BaseScreen):
    """
    Screen for a two-player human vs. human chess game.
    """
    def __init__(self, app_state_manager, piece_images):
        super().__init__(app_state_manager)
        self.game_manager = ChessGameManager()
        self.piece_images = piece_images
        self.selected_square = None
        self.game_over = False
        self.start_time = None
        self.end_time = None
        
        # For displaying messages (e.g., game over)
        self.message_font = pygame.font.SysFont(FONT_NAME, FONT_SIZE_LARGE, bold=True) # Use FONT_SIZE_LARGE from config
        self.message = ""

    def reset_game(self):
        """Resets the game state for a new game."""
        self.game_manager.reset_game()
        self.selected_square = None
        self.game_over = False
        self.start_time = datetime.now()
        self.end_time = None
        self.message = ""

    def draw(self, surface):
        """Draws the chessboard, pieces, highlights, and any messages."""
        # Draw board
        for row in range(8):
            for col in range(8):
                color = LIGHT_COLOR if (row + col) % 2 == 0 else DARK_COLOR
                pygame.draw.rect(surface, color, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

        # Highlight selected square
        if self.selected_square is not None:
            self._highlight_square(surface, self.selected_square, HIGHLIGHT_COLOR)

        # Highlight legal moves from selected square
        if self.selected_square is not None:
            self._highlight_legal_moves(surface, self.selected_square, LEGAL_MOVE_HIGHLIGHT_COLOR)
            
        # Draw pieces
        self._draw_pieces(surface)

        # Draw game over message if applicable
        if self.game_over and self.message:
            # Use the generalized message box from BaseScreen
            super()._draw_message_box(surface, self.message, self.message_font,
                                      text_color=TEXT_COLOR,
                                      bg_color=MESSAGE_BOX_BG_COLOR,
                                      border_color=MESSAGE_BOX_BORDER_COLOR,
                                      padding=PADDING_MEDIUM)


        # Draw a "Back to Menu" button - improved styling and positioning
        back_button_width = 180
        back_button_rect = pygame.Rect(self.screen_width - back_button_width - PADDING_MEDIUM, PADDING_MEDIUM, back_button_width, BUTTON_HEIGHT_STD)
        # Using standard button colors from config
        button_surface, _, _ = self.create_button(
            "Back to Menu", back_button_rect, BUTTON_COLOR, BUTTON_HOVER_COLOR, "MENU",
            text_color=TEXT_ON_LIGHT_BG_COLOR
        )
        surface.blit(button_surface, back_button_rect)


    def handle_event(self, event):
        """Handles events specific to the human vs human game."""
        if event.type == pygame.MOUSEBUTTONDOWN: # Process clicks even if game_over (for back button)

            # Check for "Back to Menu" button click first
            back_button_width = 180
            back_button_rect = pygame.Rect(self.screen_width - back_button_width - PADDING_MEDIUM, PADDING_MEDIUM, back_button_width, BUTTON_HEIGHT_STD)
            if back_button_rect.collidepoint(event.pos):
                self.app_state_manager.set_state("MENU")
                self.reset_game() # Reset game when going back to menu
                return True

            if self.game_over: # If game is over, only back button is active on this screen
                return False

            # Get clicked square (only if game is not over)
            col = event.pos[0] // SQUARE_SIZE
            row = event.pos[1] // SQUARE_SIZE
            # Ensure click is within the board boundaries
            if not (0 <= col < 8 and 0 <= row < 8):
                return False # Click was outside the board
            clicked_square = chess.square(col, 7 - row) # Convert Pygame row to chess rank

            board = self.game_manager.get_board_object()

            # This is the corrected logic block
            if self.selected_square is None:
                # No square selected, select if it has a piece of the current turn's color
                piece_on_clicked_square = board.piece_at(clicked_square)
                if piece_on_clicked_square and piece_on_clicked_square.color == board.turn:
                    self.selected_square = clicked_square
            else:
                # A square is already selected, try to make a move
                from_square = self.selected_square
                to_square = clicked_square

                # Handle promotion: In a real UI, you'd show a dialog for this
                # For simplicity, we'll auto-promote to Queen for human vs human
                promotion_piece = None
                piece_on_from_square = board.piece_at(from_square)
                if piece_on_from_square and piece_on_from_square.piece_type == chess.PAWN:
                    if (piece_on_from_square.color == chess.WHITE and chess.square_rank(to_square) == 7) or \
                       (piece_on_from_square.color == chess.BLACK and chess.square_rank(to_square) == 0):
                        promotion_piece = chess.QUEEN # Default to Queen

                move = chess.Move(from_square, to_square, promotion=promotion_piece)

                if move in board.legal_moves:
                    # Make the move
                    self.game_manager.make_move(move.uci())
                    self.selected_square = None # Deselect
                elif board.piece_at(clicked_square) and board.piece_at(clicked_square).color == board.turn:
                    # Clicked on another piece of own color, change selection
                    self.selected_square = clicked_square
                else:
                    # Invalid move or clicked empty square, deselect
                    self.selected_square = None
            return True # Event handled

        return False # Event not handled by this screen

    def update(self):
        """Updates game state, checks for game over."""
        if not self.game_over and self.game_manager.is_game_over():
            self.game_over = True
            self.end_time = datetime.now()
            winner, reason = self.game_manager.get_game_result()
            if winner:
                self.message = f"{winner.capitalize()} wins by {reason.replace('_', ' ')}!"
            else:
                self.message = f"Game Over: {reason.replace('_', ' ')}!"
            
            # Save game to database
            self._save_game_to_db(winner, reason)


    def _save_game_to_db(self, winner, reason):
        """Saves the completed game's data to the database."""
        game_data = {
            'start_time': self.start_time.isoformat() if self.start_time else datetime.now().isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else datetime.now().isoformat(),
            'winner': winner,
            'reason': reason,
            'pgn': self.game_manager.get_pgn(),
            'white_player_type': 'human',
            'black_player_type': 'human',
            'white_player_name': 'Player 1', # You might want to let users input names
            'black_player_name': 'Player 2'
        }
        self.app_state_manager.db_manager.save_game(game_data)
        print("Game saved to database.")


    # --- Helper drawing functions (adapted from your original code) ---
    def _draw_pieces(self, surface):
        """Draws chess pieces on the board, correctly scaled and centered."""
        board = self.game_manager.get_board_object()
        # Calculate offset for centering the scaled piece within the square
        # Use a dummy piece to get the scaled size, all pieces are scaled equally
        offset = (SQUARE_SIZE - self.piece_images['p'].get_width()) // 2
        
        for row in range(8):
            for col in range(8):
                square = chess.square(col, 7 - row)
                piece = board.piece_at(square)
                if piece:
                    symbol = piece.symbol()
                    if symbol in self.piece_images:
                        surface.blit(self.piece_images[symbol], (col * SQUARE_SIZE + offset, row * SQUARE_SIZE + offset))
                    else:
                        print(f"Warning: Missing image for piece symbol: {symbol}")

    def _highlight_square(self, surface, square, color):
        """Highlights a specific square on the board."""
        if square is not None:
            col, row = chess.square_file(square), 7 - chess.square_rank(square)
            highlight = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            highlight.fill(color)
            surface.blit(highlight, (col * SQUARE_SIZE, row * SQUARE_SIZE))

    def _highlight_legal_moves(self, surface, from_square, color):
        """Highlights all legal destination squares for a piece on from_square."""
        legal_destinations = self.game_manager.get_legal_moves_for_square(from_square)
        for to_square in legal_destinations:
            self._highlight_square(surface, to_square, color)

    # Removed: def _draw_message_box(self, surface, message):
    # This is now handled by the BaseScreen._draw_message_box method
    # and called via super()._draw_message_box(...) in the draw method.
