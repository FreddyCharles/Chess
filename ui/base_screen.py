# ui/base_screen.py
import pygame
from config import WIDTH, HEIGHT, FONT_NAME, FONT_SIZE_MEDIUM, TEXT_COLOR

class BaseScreen:
    """
    Base class for all application screens (menu, game modes, etc.).
    Provides common functionality like font rendering and button handling.
    """
    def __init__(self, app_state_manager):
        self.app_state_manager = app_state_manager
        self.screen_width = WIDTH
        self.screen_height = HEIGHT
        self.font = pygame.font.SysFont(FONT_NAME, FONT_SIZE_MEDIUM)

    def draw(self, surface):
        """
        Abstract method to draw the screen's elements.
        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement 'draw' method")

    def handle_event(self, event):
        """
        Abstract method to handle Pygame events specific to the screen.
        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement 'handle_event' method")

    def update(self):
        """
        Optional method for screen logic updates (e.g., animations, game state changes).
        Can be overridden by subclasses.
        """
        pass

    def render_text(self, text, color=TEXT_COLOR, size=FONT_SIZE_MEDIUM):
        """Helper to render text surfaces."""
        font = pygame.font.SysFont(FONT_NAME, size)
        return font.render(text, True, color)

    def create_button(self, text, rect, button_color, hover_color, action):
        """
        Helper to create a button with hover effect.
        Returns a tuple: (text_surface, text_rect, button_rect, current_color, action)
        """
        mouse_pos = pygame.mouse.get_pos()
        current_color = hover_color if rect.collidepoint(mouse_pos) else button_color
        
        button_surface = pygame.Surface(rect.size)
        button_surface.fill(current_color)
        
        text_surface = self.render_text(text)
        text_rect = text_surface.get_rect(center=button_surface.get_rect().center)
        button_surface.blit(text_surface, text_rect)
        
        return button_surface, rect, action
