# config.py

# Screen dimensions
WIDTH, HEIGHT = 800, 800 # Slightly larger for better UI
SQUARE_SIZE = WIDTH // 8

# Colors
LIGHT_COLOR = (240, 217, 181)
DARK_COLOR = (181, 136, 99)
HIGHLIGHT_COLOR = (100, 130, 100, 150) # Semi-transparent highlight
TEXT_COLOR = (50, 50, 50)
BUTTON_COLOR = (70, 130, 180) # Steel Blue
BUTTON_HOVER_COLOR = (100, 160, 200)
BACKGROUND_COLOR = (60, 60, 60)

# Paths
ASSETS_DIR = "assets/"
DATABASE_NAME = "chess_database.db"

# Piece Scaling
PIECE_SCALE_FACTOR = 0.9 # Pieces will be 90% of square size

# Fonts
FONT_SIZE_LARGE = 48
FONT_SIZE_MEDIUM = 32
FONT_SIZE_SMALL = 24
FONT_NAME = "Arial" # Default font, change if you have a custom .ttf in assets/
