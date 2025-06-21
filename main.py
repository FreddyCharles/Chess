# main.py
import pygame
import sys
from datetime import datetime

# Import configurations
from config import WIDTH, HEIGHT, BACKGROUND_COLOR, ASSETS_DIR, SQUARE_SIZE, PIECE_SCALE_FACTOR

# Import database manager
from database.db_manager import DBManager

# Import UI screens
from ui.menu_screen import MenuScreen
from ui.human_vs_human_screen import HumanVsHumanScreen # Will be created later
from ui.human_vs_engine_screen import HumanVsEngineScreen # Will be created later
from ui.engine_dev_screen import EngineDevScreen # Will be created later
from ui.stats_screen import StatsScreen # Will be created later

# --- Pygame Initialization ---
pygame.init()
# Add pygame.RESIZABLE flag to make the window resizable
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Chess Commander")
clock = pygame.time.Clock()

# --- Asset Loading (Centralized) ---
def load_piece_images():
    """
    Loads chess piece images from the 'assets' folder using Pygame's native SVG support
    and scales them down based on PIECE_SCALE_FACTOR.
    """
    pieces = {}
    piece_symbols = "pbnrqkPBNRQK" # lowercase for black, uppercase for white
    scaled_piece_size = int(SQUARE_SIZE * PIECE_SCALE_FACTOR)

    for symbol in piece_symbols:
        color_prefix = 'w' if symbol.isupper() else 'b'
        piece_type_suffix = symbol.upper() # SVG filenames typically use uppercase for piece type
        filename = f"{ASSETS_DIR}{color_prefix}{piece_type_suffix}.svg"
        try:
            image = pygame.image.load(filename)
            pieces[symbol] = pygame.transform.smoothscale(image, (scaled_piece_size, scaled_piece_size))
        except pygame.error as e:
            print(f"Error loading image {filename}: {e}")
            print("Ensure 'assets' folder with SVG piece images (e.g., wP.svg, bK.svg) exists.")
            sys.exit(1)
    return pieces

PIECE_IMAGES = load_piece_images()

# --- Application State Manager ---
class AppStateManager:
    """
    Manages the current screen/state of the application.
    This allows different UI screens to request state changes.
    """
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.current_state = "MENU" # Initial state
        self.screens = {} # Dictionary to hold instances of each screen
        self._initialize_screens()
        
    def _initialize_screens(self):
        """Initializes all screen instances."""
        self.screens["MENU"] = MenuScreen(self)
        # These will be initialized with necessary parameters when created
        self.screens["HUMAN_VS_HUMAN"] = HumanVsHumanScreen(self, PIECE_IMAGES)
        self.screens["HUMAN_VS_ENGINE"] = HumanVsEngineScreen(self, PIECE_IMAGES, self.db_manager)
        self.screens["ENGINE_DEV"] = EngineDevScreen(self, self.db_manager, PIECE_IMAGES)
        self.screens["VIEW_STATS"] = StatsScreen(self, self.db_manager)


    def set_state(self, new_state):
        """Changes the current application state (screen)."""
        if new_state == "EXIT":
            print("Exiting application...")
            pygame.quit()
            sys.exit()
        print(f"Changing state from {self.current_state} to {new_state}")
        self.current_state = new_state

    def get_current_screen(self):
        """Returns the currently active screen object."""
        return self.screens.get(self.current_state)


def main():
    """Main function to run the Chess Commander application."""
    db_manager = DBManager() # Initialize database manager

    app_state_manager = AppStateManager(db_manager)

    running = True
    while running:
        current_screen = app_state_manager.get_current_screen()
        if current_screen is None:
            # Fallback or error state
            print(f"Error: No screen found for state {app_state_manager.current_state}")
            running = False
            break

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE: # Handle window resize event
                # Update screen dimensions in config (if needed by other parts, though BaseScreen instances have their own)
                # config.WIDTH, config.HEIGHT = event.w, event.h
                # Recreate the screen surface with new dimensions
                # Note: This simple resize doesn't dynamically rescale UI elements.
                # UI elements will remain at their original pixel sizes and positions relative to top-left.
                # Proper UI rescaling would require significant changes in how UI elements are defined and drawn.
                global screen
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                # Optionally, notify screens of resize if they need to adjust internal layouts
                for scr in app_state_manager.screens.values():
                    if hasattr(scr, 'on_resize'):
                        scr.on_resize(event.w, event.h)
                    else: # Default update for BaseScreen derived classes
                        scr.screen_width = event.w
                        scr.screen_height = event.h

            else:
                # Delegate event handling to the current screen
                current_screen.handle_event(event)
        
        # Update game logic (for current screen)
        current_screen.update()

        # Drawing
        screen.fill(BACKGROUND_COLOR) # Clear screen
        current_screen.draw(screen)   # Draw current screen's elements

        pygame.display.flip() # Update the full display Surface to the screen
        clock.tick(60) # Limit frame rate to 60 FPS

    db_manager.close() # Close database connection before exiting
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
