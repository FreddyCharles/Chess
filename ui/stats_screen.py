# ui/stats_screen.py
import pygame
from ui.base_screen import BaseScreen
from database.db_manager import DBManager # Unchanged, assuming it's fine
from config import (BACKGROUND_COLOR, BUTTON_COLOR, BUTTON_HOVER_COLOR, TEXT_COLOR, TEXT_ON_LIGHT_BG_COLOR,
                    FONT_NAME, FONT_SIZE_XLARGE, FONT_SIZE_LARGE, FONT_SIZE_MEDIUM, FONT_SIZE_SMALL,
                    PADDING_SMALL, PADDING_MEDIUM, PADDING_LARGE, BUTTON_HEIGHT_STD)

class StatsScreen(BaseScreen):
    """
    Screen for viewing game statistics, history, and tournament results.
    """
    def __init__(self, app_state_manager, db_manager):
        super().__init__(app_state_manager)
        self.db_manager = db_manager
        self.game_history = []
        self.current_page = 0
        self.games_per_page = 10 # Number of games to display per page
        self._load_game_history()
        self._setup_buttons()

    def _load_game_history(self):
        self.game_history = self.db_manager.get_games_history(limit=1000) # Load a large number, then paginate
        self.total_pages = (len(self.game_history) + self.games_per_page - 1) // self.games_per_page

    def _setup_buttons(self):
        self.buttons = []

        # Back to Menu button (Top Left)
        back_button_width = 200
        self.buttons.append({
            "text": "Back to Menu",
            "rect": pygame.Rect(PADDING_MEDIUM, PADDING_MEDIUM, back_button_width, BUTTON_HEIGHT_STD),
            "action": "BACK_TO_MENU"
        })

        # Pagination buttons (Bottom Centered)
        pagination_button_width = 150
        y_bottom_buttons = self.screen_height - BUTTON_HEIGHT_STD - PADDING_LARGE

        prev_page_rect = pygame.Rect(
            self.screen_width // 2 - pagination_button_width - PADDING_SMALL,
            y_bottom_buttons,
            pagination_button_width,
            BUTTON_HEIGHT_STD
        )
        self.buttons.append({"text": "Previous", "rect": prev_page_rect, "action": "PREV_PAGE"})

        next_page_rect = pygame.Rect(
            self.screen_width // 2 + PADDING_SMALL,
            y_bottom_buttons,
            pagination_button_width,
            BUTTON_HEIGHT_STD
        )
        self.buttons.append({"text": "Next", "rect": next_page_rect, "action": "NEXT_PAGE"})

        # Y position for page info text, above pagination buttons
        self.page_info_y = y_bottom_buttons - FONT_SIZE_MEDIUM - PADDING_SMALL


    def draw(self, surface):
        surface.fill(BACKGROUND_COLOR)

        # Title
        title_surface = self.render_text("Game History & Statistics", color=TEXT_COLOR, size=FONT_SIZE_XLARGE, bold=True)
        title_rect = title_surface.get_rect(center=(self.screen_width // 2, PADDING_LARGE * 2))
        surface.blit(title_surface, title_rect)

        # Draw buttons
        for btn_data in self.buttons:
            button_surface, button_rect, _ = self.create_button(
                btn_data["text"], btn_data["rect"], BUTTON_COLOR, BUTTON_HOVER_COLOR, btn_data["action"],
                text_color=TEXT_ON_LIGHT_BG_COLOR # Ensure good contrast for button text
            )
            surface.blit(button_surface, button_rect)
        
        # Display game list
        self._display_game_list(surface)
        
        # Display pagination info
        page_info_text = f"Page {self.current_page + 1} of {self.total_pages if self.total_pages > 0 else 1}"
        page_info_surface = self.render_text(page_info_text, color=TEXT_COLOR, size=FONT_SIZE_MEDIUM)
        page_info_rect = page_info_surface.get_rect(center=(self.screen_width // 2, self.page_info_y))
        surface.blit(page_info_surface, page_info_rect)

    def _display_game_list(self, surface):
        start_index = self.current_page * self.games_per_page
        end_index = start_index + self.games_per_page
        games_to_display = self.game_history[start_index:end_index]

        # Calculate available height for list, considering title and pagination
        list_top_y = PADDING_LARGE * 2 + FONT_SIZE_XLARGE + PADDING_LARGE # Below title
        list_bottom_y = self.page_info_y - FONT_SIZE_MEDIUM - PADDING_LARGE # Above page info

        y_offset = list_top_y
        line_height = FONT_SIZE_SMALL + PADDING_SMALL # Dynamic line height

        if not games_to_display:
            no_games_surface = self.render_text("No games recorded yet!", color=TEXT_COLOR, size=FONT_SIZE_MEDIUM)
            no_games_rect = no_games_surface.get_rect(center=(self.screen_width // 2, y_offset + (list_bottom_y - list_top_y) // 2))
            surface.blit(no_games_surface, no_games_rect)
            return

        # Column widths (approximate, adjust as needed)
        col_widths = {
            "date": self.screen_width * 0.20,
            "white": self.screen_width * 0.20,
            "black": self.screen_width * 0.20,
            "result": self.screen_width * 0.10,
            "reason": self.screen_width * 0.25, # Remaining
        }
        start_x = PADDING_LARGE

        # Draw header
        header_font_color = (210, 210, 210) # Slightly lighter for header

        current_x = start_x
        pygame.draw.line(surface, TEXT_COLOR, (start_x, y_offset + line_height - PADDING_SMALL // 2),
                         (self.screen_width - start_x, y_offset + line_height - PADDING_SMALL // 2), 1)

        for i, (key, text) in enumerate([("date", "Date"), ("white", "White"), ("black", "Black"), ("result", "Result"), ("reason", "Reason")]):
            header_surface = self.render_text(text, color=header_font_color, size=FONT_SIZE_SMALL, bold=True)
            surface.blit(header_surface, (current_x, y_offset))
            if i < 4 : # Draw column separators
                 pygame.draw.line(surface, (100,100,100), (current_x + col_widths[key] - PADDING_SMALL, y_offset - PADDING_SMALL//2),
                                  (current_x + col_widths[key] - PADDING_SMALL, list_bottom_y), 1)
            current_x += col_widths[key]

        y_offset += line_height + PADDING_SMALL


        for i, game in enumerate(games_to_display):
            if y_offset + line_height > list_bottom_y: # Stop if exceeding available space
                break

            game_date_obj = datetime.fromisoformat(game['start_time'])
            game_date = game_date_obj.strftime('%Y-%m-%d %H:%M')
            result_str = game['winner'].upper() if game['winner'] else 'DRAW'
            reason_str = game['reason'].replace('_', ' ') if game['reason'] else 'N/A'
            
            game_details = {
                "date": game_date,
                "white": game['white_player_name'][:18], # Truncate if too long
                "black": game['black_player_name'][:18],
                "result": result_str,
                "reason": reason_str[:25]
            }

            current_x = start_x
            for key in ["date", "white", "black", "result", "reason"]:
                detail_surface = self.render_text(game_details[key], color=TEXT_COLOR, size=FONT_SIZE_SMALL)
                surface.blit(detail_surface, (current_x, y_offset + i * line_height))
                current_x += col_widths[key]

            # Row separator
            if i < len(games_to_display) -1 :
                pygame.draw.line(surface, (70,70,70), (start_x, y_offset + (i+1) * line_height - PADDING_SMALL//2),
                                 (self.screen_width - start_x, y_offset + (i+1) * line_height - PADDING_SMALL//2), 1)


    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            for btn_data in self.buttons:
                if btn_data["rect"].collidepoint(mouse_pos):
                    action = btn_data["action"]
                    if action == "BACK_TO_MENU":
                        self.app_state_manager.set_state("MENU")
                    elif action == "PREV_PAGE":
                        if self.current_page > 0:
                            self.current_page -= 1
                    elif action == "NEXT_PAGE":
                        if self.current_page < self.total_pages - 1:
                            self.current_page += 1
                    return True
        return False

    def update(self):
        # Stats screen doesn't require continuous updates beyond initial load
        pass
