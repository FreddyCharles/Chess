# ui/human_vs_engine_screen.py
import pygame
import chess
from ui.base_screen import BaseScreen
from game.chess_game_manager import ChessGameManager
from engine.stockfish_engine import StockfishEngine # Example engine
from config import LIGHT_COLOR, DARK_COLOR, HIGHLIGHT_COLOR, SQUARE_SIZE, TEXT_COLOR, BACKGROUND_COLOR
from datetime import datetime

class HumanVsEngineScreen(BaseScreen):
    """
    Screen for a human vs. AI engine chess game.
    Allows selecting engine and playing against it.
    """
    def __init__(self, app_state_manager, piece_images, db_manager):
        super().__init__(app_state_manager)
        self.db_manager = db_manager
        self.game_manager = ChessGameManager()
        self.piece_images = piece_images
        self.engine = None # Will be initialized upon game start or selection
        self.selected_square = None
        self.game_over = False
        self.start_time = None
        self.end_time = None
        self.human_color = chess.WHITE # Default human plays white
        self.engine_color = chess.BLACK
        self.waiting_for_engine = False # Flag to prevent human input while engine thinks

        # Message display
        self.message_font = pygame.font.SysFont(self.font.name, 40, bold=True)
        self.message = ""

        self.setup_complete = False # Flag to indicate if engine selection is done

        # UI elements for engine selection (simplified for now)
        self.engines_available = []
        self.selected_engine_idx = 0
        self._load_available_engines()
        self._create_selection_buttons()

    def _load_available_engines(self):
        """Loads engines from the database."""
        self.engines_available = self.db_manager.get_all_engines()
        if not self.engines_available:
            # Fallback if no engines in DB, add a dummy one
            self.db_manager.add_engine("Simple AI", "1.0", "internal", {"depth": 2})
            self.engines_available = self.db_manager.get_all_engines()
        
    def _create_selection_buttons(self):
        """Creates UI elements for engine selection and start game."""
        self.selection_buttons = []
        button_width, button_height = 180, 50
        x_center = self.screen_width // 2
        y_start = self.screen_height // 2 - 100

        # Engine selection display
        self.engine_display_rect = pygame.Rect(x_center - 200, y_start, 400, 60)

        # Prev/Next engine buttons
        prev_rect = pygame.Rect(self.engine_display_rect.left - 60, y_start, 50, 60)
        next_rect = pygame.Rect(self.engine_display_rect.right + 10, y_start, 50, 60)
        self.selection_buttons.append({"text": "<", "rect": prev_rect, "action": "PREV_ENGINE"})
        self.selection_buttons.append({"text": ">", "rect": next_rect, "action": "NEXT_ENGINE"})

        # Start game button
        start_game_rect = pygame.Rect(x_center - 100, y_start + 100, 200, 60)
        self.selection_buttons.append({"text": "Start Game", "rect": start_game_rect, "action": "START_GAME"})

        # Choose color buttons
        white_rect = pygame.Rect(x_center - 150, y_start + 180, 140, 50)
        black_rect = pygame.Rect(x_center + 10, y_start + 180, 140, 50)
        self.selection_buttons.append({"text": "Play White", "rect": white_rect, "action": "PLAY_WHITE"})
        self.selection_buttons.append({"text": "Play Black", "rect": black_rect, "action": "PLAY_BLACK"})

    def reset_game(self):
        """Resets the game state for a new human vs. engine game."""
        self.game_manager.reset_game()
        self.selected_square = None
        self.game_over = False
        self.start_time = datetime.now()
        self.end_time = None
        self.message = ""
        self.waiting_for_engine = False
        if self.engine:
            self.engine.set_board(self.game_manager.get_board_object()) # Sync engine's board
        
        # If engine plays white, make its first move
        if self.engine_color == chess.WHITE:
            self.waiting_for_engine = True # Start waiting for engine immediately
            # Schedule engine move after a tiny delay for UI to render
            pygame.time.set_timer(pygame.USEREVENT + 1, 100) # Custom event for engine move

    def draw(self, surface):
        """Draws the human vs. engine screen."""
        if not self.setup_complete:
            self._draw_setup_screen(surface)
        else:
            self._draw_game_screen(surface)

    def _draw_setup_screen(self, surface):
        """Draws the engine selection and setup UI."""
        surface.fill(BACKGROUND_COLOR)
        title_surface = self.render_text("Human vs. Engine Setup", size=FONT_SIZE_LARGE)
        title_rect = title_surface.get_rect(center=(self.screen_width // 2, 100))
        surface.blit(title_surface, title_rect)

        # Display selected engine name
        current_engine = self.engines_available[self.selected_engine_idx] if self.engines_available else {"name": "No Engines"}
        engine_name_surface = self.render_text(f"Engine: {current_engine['name']}", size=FONT_SIZE_MEDIUM)
        engine_name_rect = engine_name_surface.get_rect(center=self.engine_display_rect.center)
        pygame.draw.rect(surface, (200, 200, 200), self.engine_display_rect, border_radius=10)
        surface.blit(engine_name_surface, engine_name_rect)

        # Draw selection buttons
        for btn_data in self.selection_buttons:
            button_surface, button_rect, _ = self.create_button(
                btn_data["text"], btn_data["rect"], BUTTON_COLOR, BUTTON_HOVER_COLOR, btn_data["action"]
            )
            surface.blit(button_surface, button_rect)
        
        # Display chosen color
        color_text = "You play: White" if self.human_color == chess.WHITE else "You play: Black"
        color_surface = self.render_text(color_text, size=FONT_SIZE_SMALL)
        color_rect = color_surface.get_rect(center=(self.screen_width // 2, self.engine_display_rect.bottom + 250))
        surface.blit(color_surface, color_rect)

        # Back to menu button
        back_button_rect = pygame.Rect(20, 20, 160, 40)
        button_surface, _, _ = self.create_button("Back to Menu", back_button_rect, (200, 50, 50), (255, 80, 80), "MENU")
        surface.blit(button_surface, back_button_rect)


    def _draw_game_screen(self, surface):
        """Draws the game board and pieces."""
        # Draw board
        for row in range(8):
            for col in range(8):
                color = LIGHT_COLOR if (row + col) % 2 == 0 else DARK_COLOR
                pygame.draw.rect(surface, color, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

        # Highlight selected square
        if self.selected_square is not None:
            self._highlight_square(surface, self.selected_square, (255, 255, 0, 100)) # Yellow highlight

        # Highlight legal moves from selected square
        if self.selected_square is not None:
            self._highlight_legal_moves(surface, self.selected_square, HIGHLIGHT_COLOR)
            
        # Draw pieces
        self._draw_pieces(surface)

        # Draw game over message if applicable
        if self.game_over and self.message:
            self._draw_message_box(surface, self.message)
        elif self.waiting_for_engine:
            self._draw_message_box(surface, "Engine is thinking...")

        # Draw "Back to Menu" button
        back_button_rect = pygame.Rect(self.screen_width - 180, 20, 160, 40)
        button_surface, _, _ = self.create_button("Back to Menu", back_button_rect, (200, 50, 50), (255, 80, 80), "MENU")
        surface.blit(button_surface, back_button_rect)


    def handle_event(self, event):
        """Handles events for the human vs engine game."""
        if not self.setup_complete:
            return self._handle_setup_event(event)
        else:
            return self._handle_game_event(event)

    def _handle_setup_event(self, event):
        """Handles events on the setup screen."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            # Back to menu button
            back_button_rect = pygame.Rect(20, 20, 160, 40)
            if back_button_rect.collidepoint(mouse_pos):
                self.app_state_manager.set_state("MENU")
                return True

            for btn_data in self.selection_buttons:
                if btn_data["rect"].collidepoint(mouse_pos):
                    action = btn_data["action"]
                    if action == "PREV_ENGINE":
                        self.selected_engine_idx = (self.selected_engine_idx - 1 + len(self.engines_available)) % len(self.engines_available)
                    elif action == "NEXT_ENGINE":
                        self.selected_engine_idx = (self.selected_engine_idx + 1) % len(self.engines_available)
                    elif action == "PLAY_WHITE":
                        self.human_color = chess.WHITE
                        self.engine_color = chess.BLACK
                    elif action == "PLAY_BLACK":
                        self.human_color = chess.BLACK
                        self.engine_color = chess.WHITE
                    elif action == "START_GAME":
                        if self.engines_available:
                            selected_engine_data = self.engines_available[self.selected_engine_idx]
                            # For simplicity, always use StockfishEngine for external, or SimpleAI for internal
                            if selected_engine_data.get('path'): # Assumes path means external UCI
                                self.engine = StockfishEngine(selected_engine_data['path'], name=selected_engine_data['name'])
                            else: # Assume internal/dummy if no path
                                from engine.simple_ai_engine import SimpleAIEngine
                                self.engine = SimpleAIEngine(name=selected_engine_data['name'])
                            
                            self.setup_complete = True
                            self.reset_game() # Start the actual game
                            print(f"Starting Human vs. {self.engine.name}. Human plays {'White' if self.human_color == chess.WHITE else 'Black'}")
                        else:
                            self.message = "No engines available. Add one in Engine Dev mode."
                    return True
        return False


    def _handle_game_event(self, event):
        """Handles events during the human vs engine game."""
        if event.type == pygame.MOUSEBUTTONDOWN and not self.game_over and not self.waiting_for_engine:
            # Check for "Back to Menu" button click
            back_button_rect = pygame.Rect(self.screen_width - 180, 20, 160, 40)
            if back_button_rect.collidepoint(event.pos):
                self.app_state_manager.set_state("MENU")
                self.reset_game()
                self.setup_complete = False # Go back to setup screen
                return True

            col = event.pos[0] // SQUARE_SIZE
            row = event.pos[1] // SQUARE_SIZE
            clicked_square = chess.square(col, 7 - row)

            board = self.game_manager.get_board_object()

            if board.turn != self.human_color: # Only allow human moves on human's turn
                return False

            if self.selected_square is None:
                piece_on_clicked_square = board.piece_at(clicked_square)
                if piece_on_clicked_square and piece_on_clicked_square.color == self.human_color:
                    self.selected_square = clicked_square
            else:
                from_square = self.selected_square
                to_square = clicked_square

                promotion_piece = None
                piece_on_from_square = board.piece_at(from_square)
                if piece_on_from_square and piece_on_from_square.piece_type == chess.PAWN:
                    if (piece_on_from_square.color == chess.WHITE and chess.square_rank(to_square) == 7) or \
                       (piece_on_from_square.color == chess.BLACK and chess.square_rank(to_square) == 0):
                        promotion_piece = chess.QUEEN

                move = chess.Move(from_square, to_square, promotion=promotion_piece)

                if move in board.legal_moves:
                    if self.game_manager.make_move(move.uci()):
                        self.selected_square = None
                        # Human made a move, now it's engine's turn
                        self.waiting_for_engine = True
                        # Use a timer to trigger engine's move after a short delay
                        pygame.time.set_timer(pygame.USEREVENT + 1, 500) # 0.5 second delay
                elif board.piece_at(clicked_square) and board.piece_at(clicked_square).color == self.human_color:
                    self.selected_square = clicked_square
                else:
                    self.selected_square = None
            return True
        
        elif event.type == pygame.USEREVENT + 1: # Custom event for engine move
            if not self.game_over and self.waiting_for_engine and self.game_manager.get_board_object().turn == self.engine_color:
                pygame.time.set_timer(pygame.USEREVENT + 1, 0) # Stop the timer
                print(f"{self.engine.name} is thinking...")
                # Sync engine's board with game manager's board
                self.engine.set_board(self.game_manager.get_board_object())
                engine_move = self.engine.make_move()
                if engine_move:
                    print(f"Engine made move: {engine_move.uci()}")
                    self.game_manager.make_move(engine_move.uci())
                else:
                    print("Engine failed to make a move.") # Should not happen with robust engine
                self.waiting_for_engine = False
            return True

        return False

    def update(self):
        """Updates game state, checks for game over."""
        if self.setup_complete and not self.game_over and self.game_manager.is_game_over():
            self.game_over = True
            self.end_time = datetime.now()
            winner, reason = self.game_manager.get_game_result()
            if winner:
                winner_name = "Human" if (winner == 'white' and self.human_color == chess.WHITE) or \
                                         (winner == 'black' and self.human_color == chess.BLACK) else self.engine.name
                loser_name = self.engine.name if winner_name == "Human" else "Human"

                self.message = f"{winner_name} wins by {reason.replace('_', ' ')}!"
            else:
                self.message = f"Game Over: {reason.replace('_', ' ')}!"
            
            self._save_game_to_db(winner, reason)

    def _save_game_to_db(self, winner, reason):
        """Saves the completed human vs. engine game to the database."""
        # Determine player names and engine IDs based on colors
        white_player_name = "Human" if self.human_color == chess.WHITE else self.engine.name
        black_player_name = "Human" if self.human_color == chess.BLACK else self.engine.name
        
        white_player_type = 'human' if self.human_color == chess.WHITE else 'engine'
        black_player_type = 'human' if self.human_color == chess.BLACK else 'engine'

        engine_white_id = self.db_manager.get_engine_id(self.engine.name) if self.engine_color == chess.WHITE else None
        engine_black_id = self.db_manager.get_engine_id(self.engine.name) if self.engine_color == chess.BLACK else None

        game_data = {
            'start_time': self.start_time.isoformat() if self.start_time else datetime.now().isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else datetime.now().isoformat(),
            'winner': winner,
            'reason': reason,
            'pgn': self.game_manager.get_pgn(),
            'white_player_type': white_player_type,
            'black_player_type': black_player_type,
            'white_player_name': white_player_name,
            'black_player_name': black_player_name,
            'engine_white_id': engine_white_id,
            'engine_black_id': engine_black_id,
            'tournament_id': None # Not part of a tournament
        }
        self.app_state_manager.db_manager.save_game(game_data)
        print("Human vs. Engine game saved to database.")

    # --- Helper drawing functions (reused from HumanVsHumanScreen) ---
    def _draw_pieces(self, surface):
        """Draws chess pieces on the board, correctly scaled and centered."""
        board = self.game_manager.get_board_object()
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

    def _draw_message_box(self, surface, message):
        """Draws a message box in the center of the screen."""
        text_surface = self.message_font.render(message, True, TEXT_COLOR)
        text_rect = text_surface.get_rect(center=(self.screen_width / 2, self.screen_height / 2))
        
        background_rect = text_rect.inflate(40, 30)
        pygame.draw.rect(surface, (255, 255, 255, 200), background_rect, border_radius=15)
        pygame.draw.rect(surface, (0, 0, 0), background_rect, 2, border_radius=15)
        
        surface.blit(text_surface, text_rect)
