# ui/engine_dev_screen.py
import pygame
from ui.base_screen import BaseScreen
from database.db_manager import DBManager
from engine.stockfish_engine import StockfishEngine
from engine.simple_ai_engine import SimpleAIEngine
from engine.RandomMover import RandomMover
from engine.CapturePreferringEngine import CapturePreferringEngine # Import CapturePreferringEngine
from tournament.swiss_tournament import SwissTournament
from config import (BACKGROUND_COLOR, BUTTON_COLOR, BUTTON_HOVER_COLOR, TEXT_COLOR, TEXT_ON_LIGHT_BG_COLOR,
                    FONT_NAME, FONT_SIZE_XLARGE, FONT_SIZE_LARGE, FONT_SIZE_MEDIUM, FONT_SIZE_SMALL,
                    PADDING_SMALL, PADDING_MEDIUM, PADDING_LARGE, BUTTON_HEIGHT_STD, INPUT_HEIGHT_STD,
                    BORDER_RADIUS_STD, MESSAGE_BOX_BG_COLOR, MESSAGE_BOX_BORDER_COLOR)
import os
import importlib
import inspect
from engine.base_engine import BaseChessEngine # For class type checking
from datetime import datetime # For default tournament name

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
        """Defines the buttons and input areas for this screen with improved layout."""
        self.buttons = []
        x_center = self.screen_width // 2
        content_width = self.screen_width * 0.8  # Use 80% of screen width for content
        left_align = x_center - content_width // 2

        current_y = PADDING_LARGE * 3 # Start below title space

        # Back to Menu button (Top Left)
        back_button_width = 200
        self.buttons.append({
            "text": "Back to Menu",
            "rect": pygame.Rect(PADDING_MEDIUM, PADDING_MEDIUM, back_button_width, BUTTON_HEIGHT_STD),
            "action": "BACK_TO_MENU"
        })

        # --- Engine Management Section ---
        section_spacing = PADDING_LARGE * 2
        
        # Add Engine Buttons (Now four, potentially wrapped or in two rows if too wide)
        # For simplicity, let's try to fit them. If not, this layout needs adjustment.
        num_add_buttons = 4
        add_button_width = (content_width - PADDING_MEDIUM * (num_add_buttons - 1)) // num_add_buttons
        
        add_simple_ai_rect = pygame.Rect(left_align, current_y, add_button_width, BUTTON_HEIGHT_STD)
        self.buttons.append({"text": "Add Simple AI", "rect": add_simple_ai_rect, "action": "ADD_SIMPLE_AI"})

        add_random_mover_rect = pygame.Rect(add_simple_ai_rect.right + PADDING_MEDIUM, current_y, add_button_width, BUTTON_HEIGHT_STD)
        self.buttons.append({"text": "Add Random Mover", "rect": add_random_mover_rect, "action": "ADD_RANDOM_MOVER"})

        add_capture_engine_rect = pygame.Rect(add_random_mover_rect.right + PADDING_MEDIUM, current_y, add_button_width, BUTTON_HEIGHT_STD)
        self.buttons.append({"text": "Add Capture Engine", "rect": add_capture_engine_rect, "action": "ADD_CAPTURE_ENGINE"})

        add_stockfish_rect = pygame.Rect(add_capture_engine_rect.right + PADDING_MEDIUM, current_y, add_button_width, BUTTON_HEIGHT_STD)
        self.buttons.append({"text": "Add Stockfish (Local)", "rect": add_stockfish_rect, "action": "ADD_STOCKFISH"})
        current_y += BUTTON_HEIGHT_STD + PADDING_MEDIUM

        # Engine Display Area (Prev/Display/Next)
        engine_nav_button_width = 60
        engine_display_box_width = content_width - (engine_nav_button_width * 2) - (PADDING_SMALL * 2)

        self.prev_engine_btn_rect = pygame.Rect(left_align, current_y, engine_nav_button_width, BUTTON_HEIGHT_STD)
        self.engine_display_rect = pygame.Rect(self.prev_engine_btn_rect.right + PADDING_SMALL, current_y, engine_display_box_width, BUTTON_HEIGHT_STD)
        self.next_engine_btn_rect = pygame.Rect(self.engine_display_rect.right + PADDING_SMALL, current_y, engine_nav_button_width, BUTTON_HEIGHT_STD)
        current_y += BUTTON_HEIGHT_STD + section_spacing

        # --- Tournament Management Section ---
        self.tournament_name_input = ""
        self.num_rounds_input = "3"

        # Tournament Name Input
        self.tournament_name_label_pos = (left_align, current_y)
        current_y += FONT_SIZE_SMALL + PADDING_SMALL # Space for label
        self.tournament_name_rect = pygame.Rect(left_align, current_y, content_width, INPUT_HEIGHT_STD)
        current_y += INPUT_HEIGHT_STD + PADDING_MEDIUM

        # Number of Rounds Input
        self.num_rounds_label_pos = (left_align, current_y)
        current_y += FONT_SIZE_SMALL + PADDING_SMALL # Space for label
        self.num_rounds_rect = pygame.Rect(left_align, current_y, content_width // 2, INPUT_HEIGHT_STD) # Half width
        current_y += INPUT_HEIGHT_STD + PADDING_LARGE

        # Start Tournament Button
        start_tournament_width = content_width // 1.5
        start_tournament_rect = pygame.Rect(x_center - start_tournament_width // 2, current_y, start_tournament_width, BUTTON_HEIGHT_STD + 10)
        self.buttons.append({"text": "Start Tournament", "rect": start_tournament_rect, "action": "START_TOURNAMENT", "size": FONT_SIZE_LARGE})
        current_y += BUTTON_HEIGHT_STD + 10 + PADDING_MEDIUM

        # View Tournament History Button
        view_history_width = content_width // 1.5
        view_tournaments_rect = pygame.Rect(x_center - view_history_width // 2, current_y, view_history_width, BUTTON_HEIGHT_STD)
        self.buttons.append({"text": "View Tournament History", "rect": view_tournaments_rect, "action": "VIEW_TOURNAMENT_HISTORY"})

        self.tournament_message_y = view_tournaments_rect.bottom + PADDING_LARGE # For messages below buttons
        self.active_input_box = None

    def draw(self, surface):
        surface.fill(BACKGROUND_COLOR)

        # Title
        title_surface = self.render_text("Engine Development & Tournaments", color=TEXT_COLOR, size=FONT_SIZE_XLARGE, bold=True)
        title_rect = title_surface.get_rect(center=(self.screen_width // 2, PADDING_LARGE))
        surface.blit(title_surface, title_rect)

        # Draw Buttons (general ones)
        for btn_data in self.buttons:
            button_surface, button_rect, _ = self.create_button(
                btn_data["text"], btn_data["rect"], BUTTON_COLOR, BUTTON_HOVER_COLOR, btn_data["action"],
                text_color=TEXT_ON_LIGHT_BG_COLOR, text_size=btn_data.get("size", FONT_SIZE_MEDIUM)
            )
            surface.blit(button_surface, button_rect)
        
        # Draw Engine Display Box (using draw_text_box for consistency)
        engine_text = "No Engines Added"
        if self.engines_in_db and self.selected_engine_idx >= 0:
            engine_text = f"Selected: {self.engines_in_db[self.selected_engine_idx]['name']}"
        elif not self.engines_in_db:
             engine_text = "No Engines in DB"

        self.draw_text_box(surface, engine_text, self.engine_display_rect,
                           text_color=TEXT_COLOR, bg_color=(60,60,60), border_color=(100,100,100),
                           font_size=FONT_SIZE_MEDIUM, border_radius=BORDER_RADIUS_STD)

        # Prev/Next Engine Buttons (specific styling for arrows if needed)
        prev_btn_surface, _, _ = self.create_button("<", self.prev_engine_btn_rect, BUTTON_COLOR, BUTTON_HOVER_COLOR, "PREV_ENGINE", text_size=FONT_SIZE_LARGE)
        next_btn_surface, _, _ = self.create_button(">", self.next_engine_btn_rect, BUTTON_COLOR, BUTTON_HOVER_COLOR, "NEXT_ENGINE", text_size=FONT_SIZE_LARGE)
        surface.blit(prev_btn_surface, self.prev_engine_btn_rect)
        surface.blit(next_btn_surface, self.next_engine_btn_rect)

        # Draw Tournament Input Fields with Labels
        # Tournament Name
        surface.blit(self.render_text("Tournament Name:", color=TEXT_COLOR, size=FONT_SIZE_SMALL), self.tournament_name_label_pos)
        self.draw_input_box(surface, self.tournament_name_input, self.tournament_name_rect, 'tournament_name')

        # Number of Rounds
        surface.blit(self.render_text("Number of Rounds:", color=TEXT_COLOR, size=FONT_SIZE_SMALL), self.num_rounds_label_pos)
        self.draw_input_box(surface, self.num_rounds_input, self.num_rounds_rect, 'num_rounds')

        # Tournament progress/message display
        if self.tournament_running:
            current_round_info = self.tournament.get_current_round_info() if self.tournament else "N/A"
            progress_text = f"Tournament: '{self.tournament.name}' - Round {current_round_info}"
            progress_surface = self.render_text(progress_text, color=(180, 255, 180), size=FONT_SIZE_MEDIUM) # Light green
            progress_rect = progress_surface.get_rect(center=(self.screen_width // 2, self.tournament_message_y))
            surface.blit(progress_surface, progress_rect)

            # Display standings (simplified)
            standings = self.tournament.get_standings() if self.tournament else {}
            scores_y = progress_rect.bottom + PADDING_MEDIUM
            for i, (engine_name, data) in enumerate(standings.items()):
                score_text = f"{engine_name}: {data['points']} pts, Played: {data['played']}"
                score_surface = self.render_text(score_text, color=TEXT_COLOR, size=FONT_SIZE_SMALL)
                score_rect = score_surface.get_rect(midtop=(self.screen_width // 2, scores_y + i * (FONT_SIZE_SMALL + PADDING_SMALL)))
                surface.blit(score_surface, score_rect)

        elif self.tournament_message:
            # Use the generalized message box from BaseScreen
            super()._draw_message_box(surface, self.tournament_message,
                                      self.font, # Use default medium font from base
                                      text_color=TEXT_COLOR,
                                      bg_color=MESSAGE_BOX_BG_COLOR,
                                      border_color=MESSAGE_BOX_BORDER_COLOR,
                                      padding=PADDING_MEDIUM)

    def draw_input_box(self, surface, text, rect, input_name):
        """Helper to draw a styled input box."""
        bg_color = (220, 220, 220) # Light gray for input background
        text_color_input = (10,10,10) # Dark text for input
        border_color_active = BUTTON_HOVER_COLOR
        border_color_inactive = (150,150,150)

        pygame.draw.rect(surface, bg_color, rect, border_radius=BORDER_RADIUS_STD)
        border_col = border_color_active if self.active_input_box == input_name else border_color_inactive
        pygame.draw.rect(surface, border_col, rect, 2, border_radius=BORDER_RADIUS_STD)

        display_text = text + ("|" if self.active_input_box == input_name else "")
        input_surface = self.render_text(display_text, color=text_color_input, size=FONT_SIZE_MEDIUM)
        # Position text with small padding
        surface.blit(input_surface, rect.move(PADDING_SMALL, (rect.height - input_surface.get_height()) // 2))


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
            # Simple AI needs no path, just a name, type 'internal'
            name = f"SimpleAI-{sum(1 for e in self.engines_in_db if e['name'].startswith('SimpleAI')) + 1}"
            self.db_manager.add_engine(name, "1.0", None, {"type": "internal", "class": "SimpleAIEngine"})
            self._load_engines_from_db()
            self.tournament_message = f"Added {name}!"
        elif action == "ADD_RANDOM_MOVER":
            name = f"RandomMover-{sum(1 for e in self.engines_in_db if e['name'].startswith('RandomMover')) + 1}"
            self.db_manager.add_engine(name, "1.0", None, {"type": "internal", "class": "RandomMover"})
            self._load_engines_from_db()
            self.tournament_message = f"Added {name}!"
        elif action == "ADD_CAPTURE_ENGINE":
            name = f"CapturePreferringEngine-{sum(1 for e in self.engines_in_db if e['name'].startswith('CapturePreferringEngine')) + 1}"
            self.db_manager.add_engine(name, "1.0", None, {"type": "internal", "class": "CapturePreferringEngine"})
            self._load_engines_from_db()
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
            self._discover_and_register_engines() # Discover before starting
            self._start_tournament()
        elif action == "VIEW_TOURNAMENT_HISTORY":
            self.app_state_manager.set_state("VIEW_STATS") # Can reuse stats screen for this

    def _discover_and_register_engines(self):
        """Scans the 'engine' directory for Python-based engines and registers them if new."""
        engine_dir = "engine"
        discovered_engine_classes = []
        engine_files = [f for f in os.listdir(engine_dir) if f.endswith(".py") and f != "__init__.py" and f != "base_engine.py"]

        for file_name in engine_files:
            module_name = f"{engine_dir}.{file_name[:-3]}"
            try:
                module = importlib.import_module(module_name)
                for attribute_name in dir(module):
                    attribute = getattr(module, attribute_name)
                    if inspect.isclass(attribute) and \
                       issubclass(attribute, BaseChessEngine) and \
                       attribute is not BaseChessEngine and \
                       attribute is not StockfishEngine: # Exclude Stockfish as it's handled differently
                        discovered_engine_classes.append(attribute)
            except ImportError as e:
                print(f"Error importing engine module {module_name}: {e}")

        if not discovered_engine_classes:
            print("No new Python engine classes found in engine directory.")
            # self.tournament_message = "No Python engines found for auto-discovery." # Optional message
            return

        self._load_engines_from_db() # Refresh current DB list
        db_engine_names = {eng['name'] for eng in self.engines_in_db}
        db_engine_classes = {eng['parameters'].get('class') for eng in self.engines_in_db if isinstance(eng.get('parameters'), dict)}


        added_new = False
        for eng_class in discovered_engine_classes:
            class_name = eng_class.__name__
            # Try to create a unique-ish default name
            default_engine_name = f"{class_name}-{sum(1 for name in db_engine_names if name.startswith(class_name)) + 1}"

            # Check if this class is already represented in the DB
            if class_name not in db_engine_classes:
                print(f"Discovered new engine class: {class_name}. Registering as '{default_engine_name}'.")
                self.db_manager.add_engine(
                    name=default_engine_name,
                    version="1.0",  # Default version
                    path=None,      # Internal engines have no path
                    parameters={"type": "internal", "class": class_name}
                )
                added_new = True
            # else:
                # print(f"Engine class {class_name} seems to be already registered.")

        if added_new:
            self._load_engines_from_db() # Reload to reflect newly added engines
            self.tournament_message = "New local engines discovered and registered!"
        # else:
            # self.tournament_message = "All local engines already registered."


    def _start_tournament(self):
        # Engines are now loaded/reloaded after discovery if any were added.
        # The tournament will use all engines currently in self.engines_in_db.
        if len(self.engines_in_db) < 2:
            self.tournament_message = "Need at least 2 registered engines for a tournament!"
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
            engine_instance = None
            engine_type = eng_data.get('type', 'external') # Default to external if not specified
            engine_class_name = eng_data.get('class') # For internal engines

            if engine_type == 'internal':
                if engine_class_name == 'SimpleAIEngine':
                    engine_instance = SimpleAIEngine(name=eng_data['name'], version=eng_data['version'])
                elif engine_class_name == 'RandomMover':
                    engine_instance = RandomMover(name=eng_data['name'], version=eng_data['version'])
                elif engine_class_name == 'CapturePreferringEngine':
                    engine_instance = CapturePreferringEngine(name=eng_data['name'], version=eng_data['version'])
                else:
                    print(f"Unknown internal engine class: {engine_class_name} for {eng_data['name']}. Skipping.")
            elif eng_data.get('path') and os.path.exists(eng_data['path']): # External UCI
                try:
                    stockfish_instance = StockfishEngine(eng_data['path'], name=eng_data['name'], version=eng_data['version'])
                    if stockfish_instance.engine: # Check if connection was successful
                        engine_instance = stockfish_instance
                    else:
                        print(f"Failed to connect to external engine {eng_data['name']} at {eng_data['path']}. Skipping.")
                except Exception as e:
                    print(f"Error initializing Stockfish engine {eng_data['name']}: {e}")
            else:
                print(f"Engine {eng_data['name']} has no valid path for external type or unrecognized internal type. Skipping.")

            if engine_instance:
                active_engines_for_tournament.append(engine_instance)

        if len(active_engines_for_tournament) < 2:
            self.tournament_message = "Not enough *working* engines (min 2) to start a tournament. Check paths or add internal engines."
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
            # Potentially save final standings or trigger other completion logic
            # self.tournament.save_final_results() # Example
            self.tournament = None # Clear the tournament object
        elif self.tournament and self.tournament.is_round_complete():
            # If a round is complete, you might want to display a message or auto-proceed
            # For this version, we assume the tournament manager handles round progression internally
            # or would be triggered by another UI element not yet implemented (e.g., "Next Round" button).
            # self.tournament.play_next_game_or_round() # Or similar logic
            pass

    # _draw_message_box is inherited from BaseScreen and used via super()._draw_message_box(...)

    def __del__(self):
        # Ensure engines are quit when screen is no longer needed or app exits.
        if self.tournament and hasattr(self.tournament, '_end_tournament'):
            self.tournament._end_tournament()
