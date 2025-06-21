# ui/stats_screen.py
import pygame
from ui.base_screen import BaseScreen
from database.db_manager import DBManager
from config import (BACKGROUND_COLOR, BUTTON_COLOR, BUTTON_HOVER_COLOR, TEXT_COLOR, TEXT_ON_LIGHT_BG_COLOR,
                    FONT_NAME, FONT_SIZE_XLARGE, FONT_SIZE_LARGE, FONT_SIZE_MEDIUM, FONT_SIZE_SMALL,
                    PADDING_SMALL, PADDING_MEDIUM, PADDING_LARGE, BUTTON_HEIGHT_STD, BORDER_RADIUS_STD)
from datetime import datetime # For parsing dates if needed, though already done in DB manager for game history

class StatsScreen(BaseScreen):
    """
    Screen for viewing game statistics, history, and tournament results.
    Supports multiple views: General Game History, Tournament List, Tournament Details.
    """
    def __init__(self, app_state_manager, db_manager):
        super().__init__(app_state_manager)
        self.db_manager = db_manager

        self.current_view = "TOURNAMENT_LIST" # "GAME_HISTORY", "TOURNAMENT_LIST", "TOURNAMENT_DETAILS"

        # Game History specific
        self.game_history = []
        self.current_gh_page = 0
        self.games_per_page = 10
        self.total_gh_pages = 0

        # Tournament List specific
        self.tournaments_list = []
        self.current_tl_page = 0
        self.tournaments_per_page = 10
        self.total_tl_pages = 0

        # Tournament Details specific
        self.selected_tournament_id = None
        self.selected_tournament_name = ""
        self.tournament_engine_stats = [] # Stats for engines in the selected tournament
        self.tournament_games = [] # Games from the selected tournament
        self.current_td_games_page = 0
        self.total_td_games_pages = 0

        self._load_data_for_current_view()
        self._setup_buttons() # Buttons might change based on view

    def _switch_view(self, new_view, tournament_id=None, tournament_name=None):
        self.current_view = new_view
        self.selected_tournament_id = tournament_id
        self.selected_tournament_name = tournament_name
        self._load_data_for_current_view()
        self._setup_buttons() # Re-setup buttons for the new view

    def _load_data_for_current_view(self):
        if self.current_view == "GAME_HISTORY":
            self.game_history = self.db_manager.get_games_history(limit=1000)
            self.total_gh_pages = (len(self.game_history) + self.games_per_page - 1) // self.games_per_page
            self.current_gh_page = 0
        elif self.current_view == "TOURNAMENT_LIST":
            self.tournaments_list = self.db_manager.get_all_tournaments()
            self.total_tl_pages = (len(self.tournaments_list) + self.tournaments_per_page - 1) // self.tournaments_per_page
            self.current_tl_page = 0
        elif self.current_view == "TOURNAMENT_DETAILS" and self.selected_tournament_id is not None:
            self.tournament_engine_stats = self.db_manager.get_tournament_engine_stats(self.selected_tournament_id)
            self.tournament_games = self.db_manager.get_tournament_games(self.selected_tournament_id) # Assuming games_per_page for this too
            self.total_td_games_pages = (len(self.tournament_games) + self.games_per_page - 1) // self.games_per_page
            self.current_td_games_page = 0
        # Reset pages for other views if necessary
        if self.current_view != "GAME_HISTORY": self.current_gh_page = 0
        if self.current_view != "TOURNAMENT_LIST": self.current_tl_page = 0
        if self.current_view != "TOURNAMENT_DETAILS": self.current_td_games_page = 0


    def _setup_buttons(self):
        self.buttons = [] # Clear existing buttons
        self.clickable_list_items = [] # For tournament selection

        # Back to Menu button (Top Left)
        back_button_width = 200
        self.buttons.append({
            "text": "Back to Menu",
            "rect": pygame.Rect(PADDING_MEDIUM, PADDING_MEDIUM, back_button_width, BUTTON_HEIGHT_STD),
            "action": "BACK_TO_MENU"
        })

        # View Toggle Buttons (Top Right-ish)
        view_button_width = 220
        view_button_y = PADDING_MEDIUM
        view_gh_rect = pygame.Rect(self.screen_width - (view_button_width * 2) - (PADDING_MEDIUM * 2) , view_button_y, view_button_width, BUTTON_HEIGHT_STD)
        self.buttons.append({"text": "View Game History", "rect": view_gh_rect, "action": "VIEW_GAME_HISTORY"})

        view_tl_rect = pygame.Rect(self.screen_width - view_button_width - PADDING_MEDIUM, view_button_y, view_button_width, BUTTON_HEIGHT_STD)
        self.buttons.append({"text": "View Tournaments", "rect": view_tl_rect, "action": "VIEW_TOURNAMENT_LIST"})


        # Pagination buttons (Bottom Centered) - common for all views that need them
        pagination_button_width = 150
        self.y_bottom_buttons = self.screen_height - BUTTON_HEIGHT_STD - PADDING_LARGE

        prev_page_rect = pygame.Rect(
            self.screen_width // 2 - pagination_button_width - PADDING_SMALL,
            self.y_bottom_buttons,
            pagination_button_width,
            BUTTON_HEIGHT_STD
        )
        self.buttons.append({"text": "Previous", "rect": prev_page_rect, "action": "PREV_PAGE"})

        next_page_rect = pygame.Rect(
            self.screen_width // 2 + PADDING_SMALL,
            self.y_bottom_buttons,
            pagination_button_width,
            BUTTON_HEIGHT_STD
        )
        self.buttons.append({"text": "Next", "rect": next_page_rect, "action": "NEXT_PAGE"})

        # Y position for page info text, above pagination buttons
        self.page_info_y = self.y_bottom_buttons - FONT_SIZE_MEDIUM - PADDING_SMALL


    def draw(self, surface):
        surface.fill(BACKGROUND_COLOR)
        title_text = "Statistics"
        if self.current_view == "GAME_HISTORY": title_text = "Game History"
        elif self.current_view == "TOURNAMENT_LIST": title_text = "Tournament List"
        elif self.current_view == "TOURNAMENT_DETAILS": title_text = f"Details: {self.selected_tournament_name}"


        # Title
        title_surface = self.render_text(title_text, color=TEXT_COLOR, size=FONT_SIZE_XLARGE, bold=True)
        title_rect = title_surface.get_rect(center=(self.screen_width // 2, PADDING_LARGE * 2))
        surface.blit(title_surface, title_rect)

        # Draw buttons (general ones like Back, View Toggles)
        for btn_data in self.buttons:
            # Highlight active view toggle button
            is_active_toggle = (btn_data["action"] == "VIEW_GAME_HISTORY" and self.current_view == "GAME_HISTORY") or \
                               (btn_data["action"] == "VIEW_TOURNAMENT_LIST" and (self.current_view == "TOURNAMENT_LIST" or self.current_view == "TOURNAMENT_DETAILS"))

            current_button_color = BUTTON_HOVER_COLOR if is_active_toggle else BUTTON_COLOR
            current_hover_color = BUTTON_HOVER_COLOR # Keep hover consistent or make it brighter

            button_surface, button_rect, _ = self.create_button(
                btn_data["text"], btn_data["rect"], current_button_color, current_hover_color, btn_data["action"],
                text_color=TEXT_ON_LIGHT_BG_COLOR
            )
            surface.blit(button_surface, button_rect)
        
        # Display content based on current view
        if self.current_view == "GAME_HISTORY":
            self._display_game_history_list(surface)
            self._draw_pagination_info(surface, self.current_gh_page, self.total_gh_pages)
        elif self.current_view == "TOURNAMENT_LIST":
            self._display_tournament_list(surface)
            self._draw_pagination_info(surface, self.current_tl_page, self.total_tl_pages)
        elif self.current_view == "TOURNAMENT_DETAILS":
            self._display_tournament_details(surface)
            # Pagination for tournament games list can be added if needed, similar to game history
            # For now, assuming all games of a tournament and all engine stats fit on one screen or scrollable area (not implemented yet)
            # self._draw_pagination_info(surface, self.current_td_games_page, self.total_td_games_pages, for_tournament_games=True)


    def _draw_pagination_info(self, surface, current_page, total_pages, for_tournament_games=False):
        if total_pages > 0:
            page_info_text = f"Page {current_page + 1} of {total_pages}"
            page_info_surface = self.render_text(page_info_text, color=TEXT_COLOR, size=FONT_SIZE_MEDIUM)
            # Adjust y if it's for a sub-list within tournament details
            y_pos = self.page_info_y
            if for_tournament_games: # Example: position it differently if it's for games within details view
                 y_pos = self.screen_height - BUTTON_HEIGHT_STD - PADDING_LARGE - FONT_SIZE_MEDIUM - PADDING_LARGE # Further up
            page_info_rect = page_info_surface.get_rect(center=(self.screen_width // 2, y_pos))
            surface.blit(page_info_surface, page_info_rect)


    def _display_game_history_list(self, surface):
        start_index = self.current_gh_page * self.games_per_page
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

    def _display_tournament_list(self, surface):
        """Displays a list of tournaments, making them clickable."""
        self.clickable_list_items = [] # Reset before drawing
        list_top_y = PADDING_LARGE * 2 + FONT_SIZE_XLARGE + PADDING_LARGE # Below title
        list_bottom_y = self.y_bottom_buttons - PADDING_LARGE # Above pagination buttons

        y_offset = list_top_y
        item_height = FONT_SIZE_MEDIUM + PADDING_MEDIUM

        if not self.tournaments_list:
            no_items_surface = self.render_text("No tournaments recorded yet!", color=TEXT_COLOR, size=FONT_SIZE_MEDIUM)
            no_items_rect = no_items_surface.get_rect(center=(self.screen_width // 2, y_offset + (list_bottom_y - list_top_y) // 2))
            surface.blit(no_items_surface, no_items_rect)
            return

        start_index = self.current_tl_page * self.tournaments_per_page
        end_index = start_index + self.tournaments_per_page
        tournaments_to_display = self.tournaments_list[start_index:end_index]

        col_widths = {
            "name": self.screen_width * 0.50,
            "date": self.screen_width * 0.25,
            "status": self.screen_width * 0.20,
        }
        start_x = PADDING_LARGE
        header_font_color = (210, 210, 210)

        # Draw header
        current_x = start_x
        pygame.draw.line(surface, TEXT_COLOR, (start_x, y_offset + item_height - PADDING_SMALL //2),
                         (self.screen_width - start_x, y_offset + item_height - PADDING_SMALL//2),1)
        for i_col, (key, text) in enumerate([("name", "Tournament Name"), ("date", "Start Date"), ("status", "Status")]):
            header_surface = self.render_text(text, color=header_font_color, size=FONT_SIZE_SMALL, bold=True)
            surface.blit(header_surface, (current_x, y_offset + PADDING_SMALL))
            if i_col < 2:
                 pygame.draw.line(surface, (100,100,100), (current_x + col_widths[key] - PADDING_SMALL, y_offset - PADDING_SMALL//2),
                                  (current_x + col_widths[key] - PADDING_SMALL, list_bottom_y), 1)
            current_x += col_widths[key]
        y_offset += item_height + PADDING_SMALL


        for i, t_data in enumerate(tournaments_to_display):
            if y_offset + item_height > list_bottom_y: break

            item_rect = pygame.Rect(start_x, y_offset + i * item_height, self.screen_width - 2 * PADDING_LARGE, item_height - PADDING_SMALL)

            # Highlight on hover
            mouse_pos = pygame.mouse.get_pos()
            if item_rect.collidepoint(mouse_pos):
                pygame.draw.rect(surface, BUTTON_HOVER_COLOR, item_rect, border_radius=BORDER_RADIUS_STD)

            self.clickable_list_items.append({
                "rect": item_rect,
                "action": "VIEW_TOURNAMENT_DETAILS",
                "id": t_data['tournament_id'],
                "name": t_data['name']
            })

            t_date = datetime.fromisoformat(t_data['start_date']).strftime('%Y-%m-%d')
            details = {"name": t_data['name'][:45], "date": t_date, "status": t_data['status']}

            current_x = start_x + PADDING_SMALL # Indent text slightly
            for key in ["name", "date", "status"]:
                detail_surface = self.render_text(details[key], color=TEXT_COLOR, size=FONT_SIZE_MEDIUM)
                surface.blit(detail_surface, (current_x, y_offset + i * item_height + (item_height - detail_surface.get_height()) // 2 - PADDING_SMALL//2))
                current_x += col_widths[key]

            if i < len(tournaments_to_display) -1 :
                pygame.draw.line(surface, (70,70,70), (start_x, y_offset + (i+1) * item_height - PADDING_SMALL*1.5),
                                 (self.screen_width - start_x, y_offset + (i+1) * item_height - PADDING_SMALL*1.5), 1)


    def _display_tournament_details(self, surface):
        """Displays details for the selected tournament including engine stats and game list."""
        list_top_y = PADDING_LARGE * 2 + FONT_SIZE_XLARGE + PADDING_LARGE # Below title
        y_offset = list_top_y
        line_height = FONT_SIZE_SMALL + PADDING_SMALL

        # Display Engine Standings
        standings_title = self.render_text("Engine Performance:", color=TEXT_COLOR, size=FONT_SIZE_LARGE, bold=True)
        surface.blit(standings_title, (PADDING_LARGE, y_offset))
        y_offset += FONT_SIZE_LARGE + PADDING_MEDIUM

        # Header for engine stats
        stat_col_widths = {"rank": 50, "name": 250, "init_elo": 100, "final_elo": 100, "elo_chg": 100, "wld": 120, "pts": 80}
        current_x = PADDING_LARGE
        pygame.draw.line(surface, TEXT_COLOR, (current_x, y_offset + line_height - PADDING_SMALL // 2),
                         (self.screen_width - PADDING_LARGE, y_offset + line_height - PADDING_SMALL // 2), 1)

        for i_col, (key, text) in enumerate([("rank", "Rank"),("name", "Engine"), ("init_elo", "Initial Elo"), ("final_elo", "Final Elo"), ("elo_chg", "Elo Change"), ("wld", "W-L-D"), ("pts", "Points")]):
            header_surface = self.render_text(text, color=(210,210,210), size=FONT_SIZE_SMALL, bold=True)
            surface.blit(header_surface, (current_x, y_offset))
            if i_col < len(stat_col_widths) -1:
                 pygame.draw.line(surface, (100,100,100), (current_x + stat_col_widths[key] - PADDING_SMALL, y_offset - PADDING_SMALL//2),
                                  (current_x + stat_col_widths[key] - PADDING_SMALL, self.y_bottom_buttons - PADDING_LARGE), 1) # Rough bottom
            current_x += stat_col_widths[key]
        y_offset += line_height + PADDING_SMALL


        for rank, stats in enumerate(self.tournament_engine_stats):
            elo_change = stats['final_elo'] - stats['initial_elo']
            elo_change_str = f"+{elo_change}" if elo_change >= 0 else str(elo_change)
            wld_str = f"{stats['wins']}-{stats['losses']}-{stats['draws']}"

            details = {
                "rank": str(rank + 1),
                "name": stats['engine_name'][:20],
                "init_elo": str(stats['initial_elo']),
                "final_elo": str(stats['final_elo']),
                "elo_chg": elo_change_str,
                "wld": wld_str,
                "pts": f"{stats['points_scored']:.1f}"
            }
            current_x = PADDING_LARGE
            for key in ["rank","name", "init_elo", "final_elo", "elo_chg", "wld", "pts"]:
                detail_surface = self.render_text(details[key], color=TEXT_COLOR, size=FONT_SIZE_SMALL)
                surface.blit(detail_surface, (current_x, y_offset))
                current_x += stat_col_widths[key]
            y_offset += line_height
            if rank < len(self.tournament_engine_stats) -1 :
                 pygame.draw.line(surface, (70,70,70), (PADDING_LARGE, y_offset - PADDING_SMALL//2),
                                 (self.screen_width - PADDING_LARGE, y_offset - PADDING_SMALL//2), 1)


        # Optionally, display list of games from this tournament below engine stats
        # This would be similar to _display_game_history_list but use self.tournament_games
        # and its own pagination (self.current_td_games_page, self.total_td_games_pages)
        # For now, this part is omitted for brevity but would follow the same pattern.
        # self._display_tournament_game_list(surface, y_offset + PADDING_LARGE)


    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos

            # Check clickable list items first (e.g., tournament names)
            if self.current_view == "TOURNAMENT_LIST":
                for item_data in self.clickable_list_items:
                    if item_data["rect"].collidepoint(mouse_pos):
                        if item_data["action"] == "VIEW_TOURNAMENT_DETAILS":
                            self._switch_view("TOURNAMENT_DETAILS", item_data["id"], item_data["name"])
                            return True

            # Then check standard buttons
            for btn_data in self.buttons:
                if btn_data["rect"].collidepoint(mouse_pos):
                    action = btn_data["action"]
                    if action == "BACK_TO_MENU":
                        self.app_state_manager.set_state("MENU")
                    elif action == "VIEW_GAME_HISTORY":
                        self._switch_view("GAME_HISTORY")
                    elif action == "VIEW_TOURNAMENT_LIST":
                        self._switch_view("TOURNAMENT_LIST")
                    elif action == "PREV_PAGE":
                        if self.current_view == "GAME_HISTORY" and self.current_gh_page > 0:
                            self.current_gh_page -= 1
                        elif self.current_view == "TOURNAMENT_LIST" and self.current_tl_page > 0:
                            self.current_tl_page -= 1
                        # Add for TOURNAMENT_DETAILS games list if paginated
                    elif action == "NEXT_PAGE":
                        if self.current_view == "GAME_HISTORY" and self.current_gh_page < self.total_gh_pages - 1:
                            self.current_gh_page += 1
                        elif self.current_view == "TOURNAMENT_LIST" and self.current_tl_page < self.total_tl_pages - 1:
                            self.current_tl_page += 1
                        # Add for TOURNAMENT_DETAILS games list if paginated
                    return True
        return False

    def update(self):
        # Stats screen doesn't require continuous updates beyond initial load
        pass
