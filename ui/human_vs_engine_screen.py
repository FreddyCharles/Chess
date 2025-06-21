# ui/human_vs_engine_screen.py
import pygame
import chess
from ui.base_screen import BaseScreen
from game.chess_game_manager import ChessGameManager
from engine.stockfish_engine import StockfishEngine
from engine.simple_ai_engine import SimpleAIEngine
from engine.RandomMover import RandomMover
from engine.CapturePreferringEngine import CapturePreferringEngine # Import CapturePreferringEngine
from config import (LIGHT_COLOR, DARK_COLOR, HIGHLIGHT_COLOR, LEGAL_MOVE_HIGHLIGHT_COLOR, SQUARE_SIZE,
                    TEXT_COLOR, TEXT_ON_LIGHT_BG_COLOR, BACKGROUND_COLOR, FONT_NAME,
                    FONT_SIZE_XLARGE, FONT_SIZE_LARGE, FONT_SIZE_MEDIUM, FONT_SIZE_SMALL,
                    BUTTON_COLOR, BUTTON_HOVER_COLOR, PADDING_SMALL, PADDING_MEDIUM, PADDING_LARGE,
                    BUTTON_HEIGHT_STD, MESSAGE_BOX_BG_COLOR, MESSAGE_BOX_BORDER_COLOR, BORDER_RADIUS_STD)
from datetime import datetime
import os # For os.path.exists

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
        self.message_font = pygame.font.SysFont(FONT_NAME, FONT_SIZE_LARGE, bold=True) # Use FONT_SIZE_LARGE
        self.message = ""
        self.setup_message = "" # For messages on the setup screen

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
        """Creates UI elements for engine selection and start game, with improved layout."""
        self.selection_buttons = []
        x_center = self.screen_width // 2

        # Title and general layout
        top_offset = 150 # Space for title
        content_width = 500 # Width for the central content block
        element_spacing = PADDING_MEDIUM

        # Engine selection (display box + prev/next buttons)
        engine_select_y = top_offset
        engine_display_width = content_width - 140 # Accommodate prev/next buttons
        self.engine_display_rect = pygame.Rect(x_center - engine_display_width // 2, engine_select_y, engine_display_width, BUTTON_HEIGHT_STD)

        prev_button_width = 50
        prev_rect = pygame.Rect(self.engine_display_rect.left - prev_button_width - element_spacing, engine_select_y, prev_button_width, BUTTON_HEIGHT_STD)
        next_rect = pygame.Rect(self.engine_display_rect.right + element_spacing, engine_select_y, prev_button_width, BUTTON_HEIGHT_STD)
        self.selection_buttons.append({"text": "<", "rect": prev_rect, "action": "PREV_ENGINE", "size": FONT_SIZE_LARGE})
        self.selection_buttons.append({"text": ">", "rect": next_rect, "action": "NEXT_ENGINE", "size": FONT_SIZE_LARGE})

        # Choose color buttons (side-by-side)
        color_button_y = self.engine_display_rect.bottom + PADDING_LARGE
        color_button_width = (content_width - element_spacing) // 2
        white_rect = pygame.Rect(x_center - content_width // 2, color_button_y, color_button_width, BUTTON_HEIGHT_STD)
        black_rect = pygame.Rect(white_rect.right + element_spacing, color_button_y, color_button_width, BUTTON_HEIGHT_STD)
        self.selection_buttons.append({"text": "Play as White", "rect": white_rect, "action": "PLAY_WHITE"})
        self.selection_buttons.append({"text": "Play as Black", "rect": black_rect, "action": "PLAY_BLACK"})

        # Start game button (larger, centered below color selection)
        start_game_y = black_rect.bottom + PADDING_LARGE
        start_game_width = content_width // 1.5
        start_game_rect = pygame.Rect(x_center - start_game_width // 2, start_game_y, start_game_width, BUTTON_HEIGHT_STD + 10) # Slightly taller
        self.selection_buttons.append({"text": "Start Game", "rect": start_game_rect, "action": "START_GAME", "size": FONT_SIZE_LARGE})

        # Store the y position of the last button for drawing color choice text
        self.last_button_y = start_game_rect.bottom


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
        """Draws the engine selection and setup UI with improved styling."""
        surface.fill(BACKGROUND_COLOR)
        title_surface = self.render_text("Human vs. Engine Setup", color=TEXT_COLOR, size=FONT_SIZE_XLARGE, bold=True)
        title_rect = title_surface.get_rect(center=(self.screen_width // 2, PADDING_LARGE * 2))
        surface.blit(title_surface, title_rect)

        # Display selected engine name in a styled box
        current_engine_data = self.engines_available[self.selected_engine_idx] if self.engines_available else {"name": "No Engines Available"}
        engine_text = f"Engine: {current_engine_data['name']}"
        # Using a slightly lighter background for the display box for contrast with main BG
        self.draw_text_box(surface, engine_text, self.engine_display_rect,
                           text_color=TEXT_COLOR, bg_color=(60,60,60), border_color=(100,100,100),
                           font_size=FONT_SIZE_MEDIUM, border_radius=BORDER_RADIUS_STD)

        # Draw selection buttons
        for btn_data in self.selection_buttons:
            button_surface, button_rect, _ = self.create_button(
                btn_data["text"], btn_data["rect"], BUTTON_COLOR, BUTTON_HOVER_COLOR, btn_data["action"],
                text_color=TEXT_ON_LIGHT_BG_COLOR, text_size=btn_data.get("size", FONT_SIZE_MEDIUM)
            )
            surface.blit(button_surface, button_rect)
        
        # Display chosen color text
        color_choice_text = "Playing as: White" if self.human_color == chess.WHITE else "Playing as: Black"
        color_surface = self.render_text(color_choice_text, color=TEXT_COLOR, size=FONT_SIZE_MEDIUM)
        color_rect = color_surface.get_rect(center=(self.screen_width // 2, self.last_button_y + PADDING_LARGE + FONT_SIZE_MEDIUM // 2))
        surface.blit(color_surface, color_rect)

        # Display setup message if any (e.g., "No engines available")
        if self.setup_message:
            msg_surface = self.render_text(self.setup_message, color=(255,100,100), size=FONT_SIZE_SMALL) # Error/warning color
            msg_rect = msg_surface.get_rect(center=(self.screen_width // 2, color_rect.bottom + PADDING_MEDIUM + FONT_SIZE_SMALL // 2))
            surface.blit(msg_surface, msg_rect)


        # Back to menu button (top-left)
        back_button_width = 180
        back_button_rect = pygame.Rect(PADDING_MEDIUM, PADDING_MEDIUM, back_button_width, BUTTON_HEIGHT_STD)
        button_surface, _, _ = self.create_button(
            "Back to Menu", back_button_rect, BUTTON_COLOR, BUTTON_HOVER_COLOR, "MENU",
            text_color=TEXT_ON_LIGHT_BG_COLOR
        )
        surface.blit(button_surface, back_button_rect)


    def _draw_game_screen(self, surface):
        """Draws the game board, pieces, and game-related messages with new styling."""
        surface.fill(BACKGROUND_COLOR) # Ensure game screen also has BG color

        # Draw board (centered, or with padding if screen is larger than board)
        board_area_size = 8 * SQUARE_SIZE
        board_offset_x = (self.screen_width - board_area_size) // 2
        board_offset_y = (self.screen_height - board_area_size) // 2

        for row in range(8):
            for col in range(8):
                color = LIGHT_COLOR if (row + col) % 2 == 0 else DARK_COLOR
                pygame.draw.rect(surface, color, (board_offset_x + col * SQUARE_SIZE, board_offset_y + row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

        # Highlight selected square
        if self.selected_square is not None:
            self._highlight_square_on_board(surface, self.selected_square, HIGHLIGHT_COLOR, board_offset_x, board_offset_y)

        # Highlight legal moves from selected square
        if self.selected_square is not None:
            self._highlight_legal_moves_on_board(surface, self.selected_square, LEGAL_MOVE_HIGHLIGHT_COLOR, board_offset_x, board_offset_y)
            
        # Draw pieces (with board offset)
        self._draw_pieces_on_board(surface, board_offset_x, board_offset_y)

        # Draw game over message or "Engine thinking" message using generalized method
        message_to_draw = ""
        if self.game_over and self.message:
            message_to_draw = self.message
        elif self.waiting_for_engine:
            message_to_draw = "Engine is thinking..."

        if message_to_draw:
            super()._draw_message_box(surface, message_to_draw, self.message_font,
                                      text_color=TEXT_COLOR,
                                      bg_color=MESSAGE_BOX_BG_COLOR,
                                      border_color=MESSAGE_BOX_BORDER_COLOR,
                                      padding=PADDING_MEDIUM)


        # Draw "Back to Menu" button (top-right on game screen for consistency or specific placement)
        back_button_width = 180
        # Place it in the top right corner of the game screen
        game_back_button_rect = pygame.Rect(self.screen_width - back_button_width - PADDING_MEDIUM, PADDING_MEDIUM, back_button_width, BUTTON_HEIGHT_STD)
        button_surface, _, _ = self.create_button(
            "Back to Menu", game_back_button_rect, BUTTON_COLOR, BUTTON_HOVER_COLOR, "MENU_FROM_GAME",
             text_color=TEXT_ON_LIGHT_BG_COLOR
        ) # Different action if needed
        surface.blit(button_surface, game_back_button_rect)


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
            self.setup_message = "" # Clear previous messages

            # Back to menu button (top-left)
            back_button_width = 180
            back_button_rect = pygame.Rect(PADDING_MEDIUM, PADDING_MEDIUM, back_button_width, BUTTON_HEIGHT_STD)
            if back_button_rect.collidepoint(mouse_pos):
                self.app_state_manager.set_state("MENU")
                return True

            for btn_data in self.selection_buttons:
                if btn_data["rect"].collidepoint(mouse_pos):
                    action = btn_data["action"]
                    if action == "PREV_ENGINE":
                        if self.engines_available:
                            self.selected_engine_idx = (self.selected_engine_idx - 1 + len(self.engines_available)) % len(self.engines_available)
                        else: self.setup_message = "No engines loaded."
                    elif action == "NEXT_ENGINE":
                        if self.engines_available:
                            self.selected_engine_idx = (self.selected_engine_idx + 1) % len(self.engines_available)
                        else: self.setup_message = "No engines loaded."
                    elif action == "PLAY_WHITE":
                        self.human_color = chess.WHITE
                        self.engine_color = chess.BLACK
                    elif action == "PLAY_BLACK":
                        self.human_color = chess.BLACK
                        self.engine_color = chess.WHITE
                    elif action == "START_GAME":
                        if self.engines_available:
                            selected_engine_data = self.engines_available[self.selected_engine_idx]
                            engine_type = selected_engine_data.get('type', 'external')
                            engine_path = selected_engine_data.get('path')
                            engine_name = selected_engine_data['name']
                            engine_class_name = selected_engine_data.get('config_params', {}).get('class') if isinstance(selected_engine_data.get('config_params'), dict) else None


                            if engine_type == 'internal':
                                if engine_class_name == 'SimpleAIEngine':
                                    self.engine = SimpleAIEngine(name=engine_name)
                                elif engine_class_name == 'RandomMover':
                                    self.engine = RandomMover(name=engine_name)
                                elif engine_class_name == 'CapturePreferringEngine':
                                    self.engine = CapturePreferringEngine(name=engine_name)
                                else:
                                    # Fallback for older "Simple AI" entries that might not have 'class'
                                    # or if class name is missing from DB for some reason.
                                    if "SimpleAI" in engine_name: # General check
                                        self.engine = SimpleAIEngine(name=engine_name)
                                    elif "RandomMover" in engine_name:
                                        self.engine = RandomMover(name=engine_name)
                                    elif "CapturePreferringEngine" in engine_name:
                                         self.engine = CapturePreferringEngine(name=engine_name)
                                    else:
                                        self.setup_message = f"Unknown or misconfigured internal engine: {engine_name} (Class: {engine_class_name})"
                                        self.engine = None
                                        return True
                            elif engine_path and os.path.exists(engine_path): # External UCI engine
                                try:
                                    self.engine = StockfishEngine(engine_path, name=engine_name)
                                    if not self.engine.engine: # If stockfish process failed to start
                                        self.setup_message = f"Failed to start Stockfish: {engine_name}"
                                        self.engine = None
                                        return True
                                except Exception as e:
                                     self.setup_message = f"Error with Stockfish {engine_name}: {e}"
                                     self.engine = None
                                     return True
                            else:
                                self.setup_message = f"Engine '{engine_name}' type '{engine_type}' misconfigured or path missing/invalid."
                                self.engine = None
                                return True
                            
                            if self.engine:
                                self.setup_complete = True
                                self.reset_game()
                                print(f"Starting Human vs. {self.engine.name}. Human plays {'White' if self.human_color == chess.WHITE else 'Black'}")
                            # If self.engine is None here, setup_message should have been set.
                        else:
                            self.setup_message = "No engines available. Add one in Engine Dev screen."
                    return True
        return False


    def _handle_game_event(self, event):
        """Handles events during the human vs engine game."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Back to Menu button (top-right on game screen)
            back_button_width = 180
            game_back_button_rect = pygame.Rect(self.screen_width - back_button_width - PADDING_MEDIUM, PADDING_MEDIUM, back_button_width, BUTTON_HEIGHT_STD)
            if game_back_button_rect.collidepoint(event.pos):
                self.app_state_manager.set_state("MENU")
                self.reset_game() # Reset game logic
                self.setup_complete = False # Go back to setup screen appearance
                return True

            if self.game_over or self.waiting_for_engine: # No board interaction if game over or engine thinking
                return False

            # Board interaction
            board_area_size = 8 * SQUARE_SIZE
            board_offset_x = (self.screen_width - board_area_size) // 2
            board_offset_y = (self.screen_height - board_area_size) // 2

            col = (event.pos[0] - board_offset_x) // SQUARE_SIZE
            row = (event.pos[1] - board_offset_y) // SQUARE_SIZE

            if not (0 <= col < 8 and 0 <= row < 8): # Click outside board area
                return False

            clicked_square = chess.square(col, 7 - row)
            board = self.game_manager.get_board_object()

            if board.turn != self.human_color:
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

    # --- Helper drawing functions, adapted for board offset ---
    def _draw_pieces_on_board(self, surface, offset_x, offset_y):
        """Draws chess pieces on the board, correctly scaled, centered, and offset."""
        board = self.game_manager.get_board_object()
        piece_offset = (SQUARE_SIZE - self.piece_images['p'].get_width()) // 2
        
        for r in range(8): # Pygame row
            for c in range(8): # Pygame col
                square = chess.square(c, 7 - r) # Chess square
                piece = board.piece_at(square)
                if piece:
                    symbol = piece.symbol()
                    if symbol in self.piece_images:
                        surface.blit(self.piece_images[symbol],
                                     (offset_x + c * SQUARE_SIZE + piece_offset,
                                      offset_y + r * SQUARE_SIZE + piece_offset))
                    else:
                        print(f"Warning: Missing image for piece symbol: {symbol}")

    def _highlight_square_on_board(self, surface, square, color, offset_x, offset_y):
        """Highlights a specific square on the board, considering board offset."""
        if square is not None:
            # Convert chess square to Pygame col, row
            col = chess.square_file(square)
            row = 7 - chess.square_rank(square)

            highlight_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            highlight_surface.fill(color)
            surface.blit(highlight_surface, (offset_x + col * SQUARE_SIZE, offset_y + row * SQUARE_SIZE))

    def _highlight_legal_moves_on_board(self, surface, from_square, color, offset_x, offset_y):
        """Highlights all legal destination squares, considering board offset."""
        legal_destinations = self.game_manager.get_legal_moves_for_square(from_square)
        for to_square in legal_destinations:
            self._highlight_square_on_board(surface, to_square, color, offset_x, offset_y)

    # _draw_message_box is inherited from BaseScreen and used via super()._draw_message_box(...)
