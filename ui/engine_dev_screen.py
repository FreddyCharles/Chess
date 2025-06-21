# ui/engine_dev_screen.py
import pygame
from ui.base_screen import BaseScreen
from database.db_manager import DBManager
from engine.stockfish_engine import StockfishEngine # To potentially add Stockfish
from engine.simple_ai_engine import SimpleAIEngine  # To potentially add Simple AI
from tournament.swiss_tournament import SwissTournament
from config import BACKGROUND_COLOR, BUTTON_COLOR, BUTTON_HOVER_COLOR, TEXT_COLOR, FONT_SIZE_LARGE, FONT_SIZE_MEDIUM, FONT_SIZE_SMALL
import os # For checking file existence

class EngineDevScreen(BaseScreen):
    """
    Screen for engine development mode.
    Allows adding/managing engines, configuring and running Swiss tournaments.
    """
    def __init__(self, app_state_manager, db_manager, piece_images):
        super().__init__(app_state_manager)
        self.db_manager = db_manager
        self.piece_images = piece_images # Passed for consistency, though not directly used here
        self.engines_in_db = []
        self.selected_engine_idx = -1 # Index of engine selected in UI
        self.tournament = None
        self.tournament_running = False
        self.tournament_message = ""

        self._load_engines_from_db()
        self._setup_ui_elements()

    def _load_engines_from_db(self):
        self.engines_in_db = self.db_manager.get_all_engines()
        if self.engines_in_db:
            self.selected_engine_idx = 0 # Select the first engine by default

    def _setup_ui_elements(self):
        """Defines the buttons and input areas for this screen."""
        self.buttons = []
        button_width, button_height = 200, 50
        x_center = self.screen_width // 2
        y_start_buttons = 100

        # Back to Menu button
        self.buttons.append({
            "text": "Back to Menu", "rect": pygame.Rect(20, 20, 160, 40),
            "action": "BACK_TO_MENU"
        })

        # Engine Management Section
        add_simple_ai_rect = pygame.Rect(x_center - 250, y_start_buttons, button_width, button_height)
        self.buttons.append({"text": "Add Simple AI", "rect": add_simple_ai_rect, "action": "ADD_SIMPLE_AI"})

        # Placeholder for 'Add Stockfish' button/input
        # In a real app, this might involve a text input for path
        add_stockfish_rect = pygame.Rect(x_center + 50, y_start_buttons, button_width, button_height)
        self.buttons.append({"text": "Add Stockfish", "rect": add_stockfish_rect, "action": "ADD_STOCKFISH"})
        
        # Engine display area
        self.engine_display_rect = pygame.Rect(x_center - 250, y_start_buttons + 70, 500, 50)
        self.prev_engine_btn_rect = pygame.Rect(self.engine_display_rect.left - 60, self.engine_display_rect.top, 50, 50)
        self.next_engine_btn_rect = pygame.Rect(self.engine_display_rect.right + 10, self.engine_display_rect.top, 50, 50)
        
        # Tournament Management Section
        self.tournament_name_input = "" # For user input
        self.num_rounds_input = "3" # Default rounds

        self.tournament_name_rect = pygame.Rect(x_center - 250, y_start_buttons + 180, 500, 40)
        self.num_rounds_rect = pygame.Rect(x_center - 250, y_start_buttons + 230, 240, 40)

        start_tournament_rect = pygame.Rect(x_center - 150, y_start_buttons + 290, 300, button_height)
        self.buttons.append({"text": "Start Tournament", "rect": start_tournament_rect, "action": "START_TOURNAMENT"})

        view_tournaments_rect = pygame.Rect(x_center - 150, y_start_buttons + 360, 300, button_height)
        self.buttons.append({"text": "View Tournament History", "rect": view_tournaments_rect, "action": "VIEW_TOURNAMENT_HISTORY"})

        # Input box focus
        self.active_input_box = None # 'tournament_name' or 'num_rounds'

    def draw(self, surface):
        surface.fill(BACKGROUND_COLOR)

        title_surface = self.render_text("Engine Development & Tournaments", size=FONT_SIZE_LARGE)
        title_rect = title_surface.get_rect(center=(self.screen_width // 2, 50))
        surface.blit(title_surface, title_rect)

        # Draw buttons
        for btn_data in self.buttons:
            button_surface, button_rect, _ = self.create_button(
                btn_data["text"], btn_data["rect"], BUTTON_COLOR, BUTTON_HOVER_COLOR, btn_data["action"]
            )
            surface.blit(button_surface, button_rect)
        
        # Draw Engine Display
        pygame.draw.rect(surface, (200, 200, 200), self.engine_display_rect, border_radius=5)
        engine_text = "No Engines Added"
        if self.engines_in_db:
            engine_text = self.engines_in_db[self.selected_engine_idx]['name']
        engine_name_surface = self.render_text(engine_text, size=FONT_SIZE_MEDIUM)
        engine_name_rect = engine_name_surface.get_rect(center=self.engine_display_rect.center)
        surface.blit(engine_name_surface, engine_name_rect)

        # Prev/Next Engine Buttons
        prev_btn_surface, _, _ = self.create_button("<", self.prev_engine_btn_rect, BUTTON_COLOR, BUTTON_HOVER_COLOR, "PREV_ENGINE")
        next_btn_surface, _, _ = self.create_button(">", self.next_engine_btn_rect, BUTTON_COLOR, BUTTON_HOVER_COLOR, "NEXT_ENGINE")
        surface.blit(prev_btn_surface, self.prev_engine_btn_rect)
        surface.blit(next_btn_surface, self.next_engine_btn_rect)

        # Draw Tournament Inputs
        surface.blit(self.render_text("Tournament Name:", size=FONT_SIZE_SMALL), (self.tournament_name_rect.x, self.tournament_name_rect.y - 25))
        pygame.draw.rect(surface, (255, 255, 255), self.tournament_name_rect, border_radius=5)
        pygame.draw.rect(surface, TEXT_COLOR if self.active_input_box == 'tournament_name' else (150,150,150), self.tournament_name_rect, 2, border_radius=5)
        name_input_surface = self.render_text(self.tournament_name_input + ("|" if self.active_input_box == 'tournament_name' else ""), size=FONT_SIZE_MEDIUM, color=(0,0,0))
        surface.blit(name_input_surface, self.tournament_name_rect.move(5, 5))

        surface.blit(self.render_text("Number of Rounds:", size=FONT_SIZE_SMALL), (self.num_rounds_rect.x, self.num_rounds_rect.y - 25))
        pygame.draw.rect(surface, (255, 255, 255), self.num_rounds_rect, border_radius=5)
        pygame.draw.rect(surface, TEXT_COLOR if self.active_input_box == 'num_rounds' else (150,150,150), self.num_rounds_rect, 2, border_radius=5)
        rounds_input_surface = self.render_text(self.num_rounds_input + ("|" if self.active_input_box == 'num_rounds' else ""), size=FONT_SIZE_MEDIUM, color=(0,0,0))
        surface.blit(rounds_input_surface, self.num_rounds_rect.move(5, 5))

        # Tournament progress/message display
        if self.tournament_running:
            progress_text = f"Round {self.tournament.get_current_round()} of {self.tournament.get_num_rounds()}"
            progress_surface = self.render_text(progress_text, size=FONT_SIZE_MEDIUM, color=(0,150,0))
            progress_rect = progress_surface.get_rect(center=(x_center, self.screen_height - 150))
            surface.blit(progress_surface, progress_rect)

            # Display scores
            scores_y = progress_rect.bottom + 10
            for i, (engine_name, data) in enumerate(self.tournament.get_standings().items()): # Need a method to get sorted scores
                score_text = f"{engine_name}: {data['points']} pts"
                score_surface = self.render_text(score_text, size=FONT_SIZE_SMALL)
                score_rect = score_surface.get_rect(center=(x_center, scores_y + i * 30))
                surface.blit(score_surface, score_rect)
        elif self.tournament_message:
            self._draw_message_box(surface, self.tournament_message)


    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            
            # Check input box clicks
            if self.tournament_name_rect.collidepoint(mouse_pos):
                self.active_input_box = 'tournament_name'
            elif self.num_rounds_rect.collidepoint(mouse_pos):
                self.active_input_box = 'num_rounds'
            else:
                self.active_input_box = None

            for btn_data in self.buttons:
                if btn_data["rect"].collidepoint(mouse_pos):
                    self._handle_button_click(btn_data["action"])
                    return True
            
            if self.prev_engine_btn_rect.collidepoint(mouse_pos) and self.engines_in_db:
                self.selected_engine_idx = (self.selected_engine_idx - 1 + len(self.engines_in_db)) % len(self.engines_in_db)
                return True
            if self.next_engine_btn_rect.collidepoint(mouse_pos) and self.engines_in_db:
                self.selected_engine_idx = (self.selected_engine_idx + 1) % len(self.engines_in_db)
                return True

        elif event.type == pygame.KEYDOWN and self.active_input_box:
            if event.key == pygame.K_BACKSPACE:
                if self.active_input_box == 'tournament_name':
                    self.tournament_name_input = self.tournament_name_input[:-1]
                elif self.active_input_box == 'num_rounds':
                    self.num_rounds_input = self.num_rounds_input[:-1]
            elif event.key == pygame.K_RETURN:
                self.active_input_box = None # Deselect on Enter
            else:
                if self.active_input_box == 'tournament_name':
                    self.tournament_name_input += event.unicode
                elif self.active_input_box == 'num_rounds':
                    if event.unicode.isdigit(): # Only allow digits for rounds
                        self.num_rounds_input += event.unicode
            return True

        return False

    def _handle_button_click(self, action):
        if action == "BACK_TO_MENU":
            if self.tournament_running and self.tournament:
                self.tournament._end_tournament() # Ensure engines are quit
            self.app_state_manager.set_state("MENU")
        elif action == "ADD_SIMPLE_AI":
            # Simple AI needs no path, just a name
            name = f"SimpleAI-{len(self.engines_in_db) + 1}"
            self.db_manager.add_engine(name, "1.0", None, {"type": "simple"})
            self._load_engines_from_db() # Reload to show new engine
            self.tournament_message = f"Added {name}!"
        elif action == "ADD_STOCKFISH":
            # For adding Stockfish, you'd need a way to input its path.
            # For simplicity, let's hardcode a common path for demo.
            # In a real app, implement a file dialog or text input for path.
            stockfish_path = "/usr/local/bin/stockfish" # Example Linux/macOS path
            # stockfish_path = "C:\\Stockfish\\stockfish-windows-x86-64-avx2.exe" # Example Windows path
            
            if os.path.exists(stockfish_path):
                self.db_manager.add_engine("Stockfish", "15", stockfish_path, {"type": "uci"})
                self._load_engines_from_db()
                self.tournament_message = "Added Stockfish!"
            else:
                self.tournament_message = f"Stockfish executable not found at '{stockfish_path}'. Please check path."
        elif action == "START_TOURNAMENT":
            self._start_tournament()
        elif action == "VIEW_TOURNAMENT_HISTORY":
            self.app_state_manager.set_state("VIEW_STATS") # Can reuse stats screen for this

    def _start_tournament(self):
        if len(self.engines_in_db) < 2:
            self.tournament_message = "Need at least 2 engines for a tournament!"
            return

        tournament_name = self.tournament_name_input.strip()
        if not tournament_name:
            tournament_name = f"Tournament {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        try:
            num_rounds = int(self.num_rounds_input)
            if num_rounds <= 0:
                raise ValueError
        except ValueError:
            self.tournament_message = "Number of rounds must be a positive integer!"
            return

        # Create actual engine instances from DB data
        active_engines_for_tournament = []
        for eng_data in self.engines_in_db:
            if eng_data.get('path') and os.path.exists(eng_data['path']):
                try:
                    engine_instance = StockfishEngine(eng_data['path'], name=eng_data['name'], version=eng_data['version'])
                    if engine_instance.engine: # Check if connection was successful
                        active_engines_for_tournament.append(engine_instance)
                    else:
                        print(f"Failed to connect to {eng_data['name']} at {eng_data['path']}. Skipping.")
                except Exception as e:
                    print(f"Error initializing Stockfish engine {eng_data['name']}: {e}")
            else: # Assume it's a simple AI if no path or path doesn't exist
                 active_engines_for_tournament.append(SimpleAIEngine(name=eng_data['name'], version=eng_data['version']))

        if len(active_engines_for_tournament) < 2:
            self.tournament_message = "Not enough *working* engines to start a tournament. Check paths."
            # Also clean up any partially initialized Stockfish engines
            for eng in active_engines_for_tournament:
                if hasattr(eng, 'quit'): eng.quit()
            return
            
        self.tournament = SwissTournament(tournament_name, active_engines_for_tournament, num_rounds, self.db_manager)
        self.tournament.start_tournament()
        self.tournament_running = True
        self.tournament_message = "" # Clear previous messages

    def update(self):
        """Updates tournament state if running."""
        if self.tournament_running and self.tournament:
            # For a UI, you might want to call a method like
            # self.tournament.play_next_game_in_round() and update status
            # based on its return. For simplicity here, we assume it runs rounds quickly.
            # In a real-time UI, you'd likely have a separate thread for the tournament.
            if not self.tournament.is_tournament_running: # Checks if tournament completed all its rounds
                self.tournament_running = False
                self.tournament_message = "Tournament Completed!"
                print("Tournament finished updating in UI.")
            else:
                 # In a real application, you would manage the tournament games
                 # here, potentially one by one, to show progress.
                 # For now, SwissTournament.run_next_round() directly runs games.
                 pass

    def _draw_message_box(self, surface, message):
        """Draws a message box in the center of the screen."""
        text_surface = self.render_text(message, size=FONT_SIZE_MEDIUM)
        text_rect = text_surface.get_rect(center=(self.screen_width / 2, self.screen_height / 2))
        
        background_rect = text_rect.inflate(40, 30)
        pygame.draw.rect(surface, (255, 255, 255, 200), background_rect, border_radius=15)
        pygame.draw.rect(surface, (0, 0, 0), background_rect, 2, border_radius=15)
        
        surface.blit(text_surface, text_rect)

    def __del__(self):
        # Ensure engines are quit when screen is no longer needed (e.g. app exit)
        if self.tournament and hasattr(self.tournament, '_end_tournament'):
            self.tournament._end_tournament()
