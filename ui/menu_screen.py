# ui/menu_screen.py
import pygame
from ui.base_screen import BaseScreen
from config import (BACKGROUND_COLOR, BUTTON_COLOR, BUTTON_HOVER_COLOR, TEXT_COLOR,
                    FONT_NAME, FONT_SIZE_XLARGE, FONT_SIZE_MEDIUM, PADDING_LARGE, BUTTON_HEIGHT_STD, TEXT_ON_LIGHT_BG_COLOR)

class MenuScreen(BaseScreen):
    """
    The main menu screen of the chess application.
    Allows selection of different game modes and features.
    """
    def __init__(self, app_state_manager):
        super().__init__(app_state_manager)
        self.title_font = pygame.font.SysFont(FONT_NAME, FONT_SIZE_XLARGE, bold=True)
        self.buttons = []
        self._setup_buttons()

    def _setup_buttons(self):
        """
        Defines the buttons for the main menu.
        Each button has a text, position, size, and an associated action (state change).
        """
        button_width = 350  # Increased width for better text fit
        button_height = BUTTON_HEIGHT_STD
        spacing = PADDING_LARGE # Use PADDING_LARGE for spacing between buttons
        
        self.buttons_data = [
            {"text": "Human vs. Human", "action": "HUMAN_VS_HUMAN"},
            {"text": "Human vs. Engine", "action": "HUMAN_VS_ENGINE"},
            {"text": "Engine Development", "action": "ENGINE_DEV"},
            {"text": "View Statistics", "action": "VIEW_STATS"},
            {"text": "Exit", "action": "EXIT"}
        ]

        num_buttons = len(self.buttons_data)
        total_button_height = num_buttons * button_height + (num_buttons - 1) * spacing

        # Start Y position for the first button, considering title space
        title_space = 150 # Approximate space for title + top padding
        start_y = title_space + (self.screen_height - title_space - total_button_height) // 2


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
        title_surface = self.render_text("Chess Commander", color=TEXT_COLOR, size=FONT_SIZE_XLARGE, bold=True)
        title_rect = title_surface.get_rect(center=(self.screen_width // 2, 80)) # Adjusted Y for title
        surface.blit(title_surface, title_rect)

        # Draw Buttons
        for text, rect, action in self.buttons:
            # Use TEXT_ON_LIGHT_BG_COLOR for button text for better contrast
            button_surface, button_rect, _ = self.create_button(
                text, rect, BUTTON_COLOR, BUTTON_HOVER_COLOR, action,
                text_color=TEXT_ON_LIGHT_BG_COLOR, text_size=FONT_SIZE_MEDIUM
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
