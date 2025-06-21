# ui/stats_screen.py
import pygame
from ui.base_screen import BaseScreen
from database.db_manager import DBManager
from config import BACKGROUND_COLOR, BUTTON_COLOR, BUTTON_HOVER_COLOR, TEXT_COLOR, FONT_SIZE_LARGE, FONT_SIZE_MEDIUM, FONT_SIZE_SMALL

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
        # Back to Menu button
        self.buttons.append({
            "text": "Back to Menu", "rect": pygame.Rect(20, 20, 160, 40),
            "action": "BACK_TO_MENU"
        })

        # Pagination buttons
        button_width, button_height = 100, 40
        x_center = self.screen_width // 2
        y_bottom = self.screen_height - 60

        prev_page_rect = pygame.Rect(x_center - 120, y_bottom, button_width, button_height)
        self.buttons.append({"text": "Previous", "rect": prev_page_rect, "action": "PREV_PAGE"})

        next_page_rect = pygame.Rect(x_center + 20, y_bottom, button_width, button_height)
        self.buttons.append({"text": "Next", "rect": next_page_rect, "action": "NEXT_PAGE"})

    def draw(self, surface):
        surface.fill(BACKGROUND_COLOR)

        title_surface = self.render_text("Game History & Statistics", size=FONT_SIZE_LARGE)
        title_rect = title_surface.get_rect(center=(self.screen_width // 2, 50))
        surface.blit(title_surface, title_rect)

        # Draw buttons
        for btn_data in self.buttons:
            button_surface, button_rect, _ = self.create_button(
                btn_data["text"], btn_data["rect"], BUTTON_COLOR, BUTTON_HOVER_COLOR, btn_data["action"]
            )
            surface.blit(button_surface, button_rect)
        
        # Display game list
        self._display_game_list(surface)
        
        # Display pagination info
        page_info_text = f"Page {self.current_page + 1} of {self.total_pages if self.total_pages > 0 else 1}"
        page_info_surface = self.render_text(page_info_text, size=FONT_SIZE_SMALL)
        page_info_rect = page_info_surface.get_rect(center=(self.screen_width // 2, self.screen_height - 90))
        surface.blit(page_info_surface, page_info_rect)

    def _display_game_list(self, surface):
        start_index = self.current_page * self.games_per_page
        end_index = start_index + self.games_per_page
        games_to_display = self.game_history[start_index:end_index]

        y_offset = 120 # Starting Y position for game entries
        line_height = 30

        if not games_to_display:
            no_games_surface = self.render_text("No games recorded yet!", size=FONT_SIZE_MEDIUM)
            no_games_rect = no_games_surface.get_rect(center=(self.screen_width // 2, y_offset + 50))
            surface.blit(no_games_surface, no_games_rect)
            return

        # Draw header
        header_text = f"{'Date':<20} | {'White Player':<20} | {'Black Player':<20} | {'Result':<10} | {'Reason':<20}"
        header_surface = self.render_text(header_text, size=FONT_SIZE_SMALL, color=(200, 200, 200))
        surface.blit(header_surface, (50, y_offset))
        pygame.draw.line(surface, TEXT_COLOR, (50, y_offset + line_height - 5), (self.screen_width - 50, y_offset + line_height - 5), 1)

        y_offset += line_height + 5

        for i, game in enumerate(games_to_display):
            game_date = datetime.fromisoformat(game['start_time']).strftime('%Y-%m-%d %H:%M')
            result_str = game['winner'].upper() if game['winner'] else 'DRAW'
            reason_str = game['reason'].replace('_', ' ') if game['reason'] else 'N/A'
            
            display_text = (
                f"{game_date:<20} | "
                f"{game['white_player_name']:<20} | "
                f"{game['black_player_name']:<20} | "
                f"{result_str:<10} | "
                f"{reason_str:<20}"
            )
            game_surface = self.render_text(display_text, size=FONT_SIZE_SMALL)
            surface.blit(game_surface, (50, y_offset + i * line_height))


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
