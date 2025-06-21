# config.py

# Screen dimensions
WIDTH, HEIGHT = 800, 800
SQUARE_SIZE = WIDTH // 8

# Colors - Updated for better contrast and a more modern feel
LIGHT_COLOR = (238, 238, 210)  # Creamy white for light squares
DARK_COLOR = (118, 150, 86)    # Earthy green for dark squares
HIGHLIGHT_COLOR = (255, 255, 50, 120) # Brighter, slightly more transparent yellow for selection
LEGAL_MOVE_HIGHLIGHT_COLOR = (0, 0, 0, 60) # Subtle dark overlay for legal moves

TEXT_COLOR = (230, 230, 230)       # Light gray/off-white for text on dark backgrounds
TEXT_ON_LIGHT_BG_COLOR = (20, 20, 20) # Dark gray for text on light backgrounds (like buttons)
BUTTON_COLOR = (85, 107, 47)     # Dark Olive Green for buttons
BUTTON_HOVER_COLOR = (107, 142, 35) # Lighter Olive Green for hover
BACKGROUND_COLOR = (49, 46, 43)    # Dark Slate Gray for general background
MESSAGE_BOX_BG_COLOR = (70, 70, 70, 220) # Semi-transparent dark gray for message boxes
MESSAGE_BOX_BORDER_COLOR = (150, 150, 150)

# Paths
ASSETS_DIR = "assets/"
DATABASE_NAME = "chess_database.db"

# Piece Scaling
PIECE_SCALE_FACTOR = 0.85 # Slightly smaller pieces for more board visibility

# Fonts
FONT_SIZE_XLARGE = 56 # For main titles
FONT_SIZE_LARGE = 40
FONT_SIZE_MEDIUM = 28
FONT_SIZE_SMALL = 20
FONT_NAME = "sans-serif" # Using a generic sans-serif font for broader compatibility

# UI Spacing
PADDING_SMALL = 8
PADDING_MEDIUM = 16
PADDING_LARGE = 24
BUTTON_HEIGHT_STD = 50
INPUT_HEIGHT_STD = 40
BORDER_RADIUS_STD = 8
