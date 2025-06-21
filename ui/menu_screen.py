# ui/menu_screen.py
import pygame
from ui.base_screen import BaseScreen
from config import BACKGROUND_COLOR, BUTTON_COLOR, BUTTON_HOVER_COLOR, TEXT_COLOR, FONT_SIZE_LARGE, FONT_NAME # Import FONT_NAME

class MenuScreen(BaseScreen):
    """
    The main menu screen of the chess application.
    Allows selection of different game modes and features.
    """
    def __init__(self, app_state_manager):
        super().__init__(app_state_manager)
        # Corrected: Use FONT_NAME directly as it's the string 'Arial'
        self.title_font = pygame.font.SysFont(FONT_NAME, FONT_SIZE_LARGE, bold=True)
        self.buttons = []
        self._setup_buttons()

    def _setup_buttons(self):
        """
        Defines the buttons for the main menu.
        Each button has a text, position, size, and an associated action (state change).
        """
        button_width = 300
        button_height = 60
        spacing = 20
        
        # Calculate starting Y position to center buttons vertically
        total_button_height = 4 * button_height + 3 * spacing # 4 buttons, 3 spaces
        start_y = (self.screen_height - total_button_height) // 2

        self.buttons_data = [
            {"text": "Human vs. Human", "action": "HUMAN_VS_HUMAN"},
            {"text": "Human vs. Engine", "action": "HUMAN_VS_ENGINE"},
            {"text": "Engine Development", "action": "ENGINE_DEV"},
            {"text": "View Statistics", "action": "VIEW_STATS"},
            {"text": "Exit", "action": "EXIT"}
        ]

        for i, data in enumerate(self.buttons_data):
            x = (self.screen_width - button_width) // 2
            y = start_y + i * (button_height + spacing)
            rect = pygame.Rect(x, y, button_width, button_height)
            self.buttons.append((data["text"], rect, data["action"]))

    def draw(self, surface):
        """
        Draws the main menu screen, including title and buttons.
        """
        surface.fill(BACKGROUND_COLOR)

        # Draw Title
        title_surface = self.title_font.render("Chess Commander", True, TEXT_COLOR)
        title_rect = title_surface.get_rect(center=(self.screen_width // 2, 100))
        surface.blit(title_surface, title_rect)

        # Draw Buttons
        for text, rect, action in self.buttons:
            button_surface, button_rect, _ = self.create_button(
                text, rect, BUTTON_COLOR, BUTTON_HOVER_COLOR, action
            )
            surface.blit(button_surface, button_rect)

    def handle_event(self, event):
        """
        Handles events for the menu screen, primarily button clicks.
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            for text, rect, action in self.buttons:
                if rect.collidepoint(mouse_pos):
                    # Change application state based on button clicked
                    if action == "EXIT":
                        self.app_state_manager.set_state("EXIT")
                    else:
                        self.app_state_manager.set_state(action)
                    return True # Event handled
        return False # Event not handled by this screen
