# ui/base_screen.py
import pygame
from config import (WIDTH, HEIGHT, FONT_NAME, FONT_SIZE_MEDIUM, TEXT_COLOR,
                    TEXT_ON_LIGHT_BG_COLOR, BORDER_RADIUS_STD, PADDING_SMALL)

class BaseScreen:
    """
    Base class for all application screens (menu, game modes, etc.).
    Provides common functionality like font rendering and button handling.
    """
    def __init__(self, app_state_manager):
        self.app_state_manager = app_state_manager
        self.screen_width = WIDTH
        self.screen_height = HEIGHT
        # Default font for general text, can be overridden by specific screens
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

    def render_text(self, text, color=TEXT_COLOR, size=FONT_SIZE_MEDIUM, font_name=FONT_NAME, bold=False, italic=False):
        """Helper to render text surfaces with more options."""
        font = pygame.font.SysFont(font_name, size, bold=bold, italic=italic)
        return font.render(text, True, color)

    def create_button(self, text, rect, button_color, hover_color, action,
                      text_color=TEXT_ON_LIGHT_BG_COLOR, text_size=FONT_SIZE_MEDIUM, border_radius=BORDER_RADIUS_STD):
        """
        Helper to create a button with hover effect, rounded corners, and customizable text.
        Returns a tuple: (button_surface, button_rect, action)
        """
        mouse_pos = pygame.mouse.get_pos()
        current_color = hover_color if rect.collidepoint(mouse_pos) else button_color
        
        # Create a surface for the button with per-pixel alpha for rounded corners
        button_surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        
        # Draw rounded rectangle
        pygame.draw.rect(button_surface, current_color, button_surface.get_rect(), border_radius=border_radius)

        # Render text (using TEXT_ON_LIGHT_BG_COLOR for better contrast on typical button colors)
        text_surface = self.render_text(text, color=text_color, size=text_size)
        text_rect = text_surface.get_rect(center=(rect.width / 2, rect.height / 2))
        button_surface.blit(text_surface, text_rect)
        
        return button_surface, rect, action

    def draw_text_box(self, surface, text, rect, text_color=TEXT_COLOR, bg_color=(50,50,50),
                      border_color=(100,100,100), font_size=FONT_SIZE_MEDIUM, border_width=1,
                      padding=PADDING_SMALL, border_radius=BORDER_RADIUS_STD):
        """Draws a text box with optional border and background."""

        # Draw background with border radius
        pygame.draw.rect(surface, bg_color, rect, border_radius=border_radius)
        # Draw border
        if border_width > 0:
            pygame.draw.rect(surface, border_color, rect, border_width, border_radius=border_radius)

        # Render and blit text, considering padding
        text_surface = self.render_text(text, color=text_color, size=font_size)
        text_area_rect = rect.inflate(-padding*2, -padding*2) # Reduce rect for text area

        # Simple text centering within the padded area
        # For more complex alignment, a more sophisticated text layout function would be needed
        text_render_rect = text_surface.get_rect(center=text_area_rect.center)

        # Ensure text doesn't overflow the box (basic clipping)
        # A more robust solution might involve text wrapping or scrolling
        if not text_area_rect.contains(text_render_rect):
            text_render_rect.clamp_ip(text_area_rect) # Clamp to fit
            # Potentially add "..." if text is clipped

        surface.blit(text_surface, text_render_rect)


    def _draw_message_box(self, surface, message, message_font,
                            text_color=TEXT_COLOR,
                            bg_color=(70,70,70,200),
                            border_color=(150,150,150),
                            padding=15, border_radius=10):
        """
        Generalized message box drawing method, to be used by subclasses.
        `message_font` should be a pre-initialized pygame.font.Font object.
        """
        text_surface = message_font.render(message, True, text_color)
        text_rect = text_surface.get_rect(center=(self.screen_width / 2, self.screen_height / 2))

        # Inflate background rect based on text size and padding
        background_rect = text_rect.inflate(padding * 2, padding * 2)

        # Create a subsurface for transparency, if bg_color has alpha
        if len(bg_color) == 4 and bg_color[3] < 255:
            msg_box_surface = pygame.Surface(background_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(msg_box_surface, bg_color, msg_box_surface.get_rect(), border_radius=border_radius)
            if border_color:
                 pygame.draw.rect(msg_box_surface, border_color, msg_box_surface.get_rect(), 2, border_radius=border_radius) # Border
            msg_box_surface.blit(text_surface, text_surface.get_rect(center = (background_rect.width/2, background_rect.height/2)))
            surface.blit(msg_box_surface, background_rect)

        else: # Opaque background
            pygame.draw.rect(surface, bg_color, background_rect, border_radius=border_radius)
            if border_color:
                pygame.draw.rect(surface, border_color, background_rect, 2, border_radius=border_radius) # Border
            surface.blit(text_surface, text_rect)
