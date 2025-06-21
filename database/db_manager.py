# database/db_manager.py
import sqlite3
import json
from datetime import datetime
from config import DATABASE_NAME

class DBManager:
    """
    Manages the SQLite database for storing game history, player data,
    engine details, and tournament results.
    """
    def __init__(self):
        self.conn = None
        self.cursor = None
        self._connect()
        self._create_tables()

    def _connect(self):
        """Establishes a connection to the SQLite database."""
        try:
            self.conn = sqlite3.connect(DATABASE_NAME)
            self.cursor = self.conn.cursor()
            print(f"Connected to database: {DATABASE_NAME}")
        except sqlite3.Error as e:
            print(f"Database connection error: {e}")
            # In a real app, you might want to exit or show an error to the user
            exit()

    def _create_tables(self):
        """
        Creates necessary tables if they don't already exist.
        Tables:
        - games: Stores details of each chess game played.
        - players: Stores human player names.
        - engines: Stores details of AI engines.
        - tournaments: Stores details of each tournament.
        - tournament_games: Links games to tournaments and stores specific results for engine comparison.
        """
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS games (
                    game_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    winner TEXT,          -- 'white', 'black', 'draw'
                    reason TEXT,          -- 'checkmate', 'stalemate', 'resignation', 'draw', etc.
                    pgn TEXT NOT NULL,    -- Full PGN of the game
                    white_player_type TEXT, -- 'human', 'engine'
                    black_player_type TEXT, -- 'human', 'engine'
                    white_player_name TEXT, -- Name of human player or engine
                    black_player_name TEXT, -- Name of human player or engine
                    engine_white_id INTEGER, -- FK to engines table if engine
                    engine_black_id INTEGER, -- FK to engines table if engine
                    tournament_id INTEGER,   -- FK to tournaments table if part of a tournament
                    FOREIGN KEY (engine_white_id) REFERENCES engines(engine_id),
                    FOREIGN KEY (engine_black_id) REFERENCES engines(engine_id),
                    FOREIGN KEY (tournament_id) REFERENCES tournaments(tournament_id)
                )
            ''')

            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS players (
                    player_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL
                )
            ''')

            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS engines (
                    engine_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    version TEXT,
                    path TEXT,            -- Path to the engine executable (e.g., Stockfish)
                    parameters TEXT       -- JSON string of engine parameters (e.g., {"Skill Level": 10})
                )
            ''')
            
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS tournaments (
                    tournament_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT,
                    rounds INTEGER,
                    status TEXT,          -- 'planned', 'ongoing', 'completed'
                    config TEXT           -- JSON string of tournament settings (e.g., participating engines)
                )
            ''')

            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS tournament_games (
                    tournament_game_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tournament_id INTEGER NOT NULL,
                    game_id INTEGER NOT NULL,
                    round_number INTEGER NOT NULL,
                    white_engine_id INTEGER,
                    black_engine_id INTEGER,
                    result TEXT,          -- 'white_win', 'black_win', 'draw'
                    FOREIGN KEY (tournament_id) REFERENCES tournaments(tournament_id),
                    FOREIGN KEY (game_id) REFERENCES games(game_id),
                    FOREIGN KEY (white_engine_id) REFERENCES engines(engine_id),
                    FOREIGN KEY (black_engine_id) REFERENCES engines(engine_id)
                )
            ''')

            self.conn.commit()
            print("Database tables checked/created successfully.")
        except sqlite3.Error as e:
            print(f"Error creating tables: {e}")

    def add_player(self, name):
        """Adds a new human player if they don't already exist."""
        try:
            self.cursor.execute("INSERT OR IGNORE INTO players (name) VALUES (?)", (name,))
            self.conn.commit()
            return self.cursor.lastrowid if self.cursor.rowcount > 0 else self.get_player_id(name)
        except sqlite3.Error as e:
            print(f"Error adding player {name}: {e}")
            return None

    def get_player_id(self, name):
        """Retrieves the ID of a player by name."""
        self.cursor.execute("SELECT player_id FROM players WHERE name = ?", (name,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def add_engine(self, name, version=None, path=None, parameters=None):
        """Adds or updates an engine's details."""
        try:
            params_json = json.dumps(parameters) if parameters else None
            self.cursor.execute("""
                INSERT INTO engines (name, version, path, parameters) VALUES (?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET version=excluded.version, path=excluded.path, parameters=excluded.parameters
            """, (name, version, path, params_json))
            self.conn.commit()
            return self.cursor.lastrowid if self.cursor.rowcount > 0 else self.get_engine_id(name)
        except sqlite3.Error as e:
            print(f"Error adding/updating engine {name}: {e}")
            return None

    def get_engine_id(self, name):
        """Retrieves the ID of an engine by name."""
        self.cursor.execute("SELECT engine_id FROM engines WHERE name = ?", (name,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def get_all_engines(self):
        """Retrieves all stored engine details."""
        self.cursor.execute("SELECT engine_id, name, version, path, parameters FROM engines")
        return [{
            'engine_id': row[0],
            'name': row[1],
            'version': row[2],
            'path': row[3],
            'parameters': json.loads(row[4]) if row[4] else {}
        } for row in self.cursor.fetchall()]

    def save_game(self, game_data):
        """
        Saves a completed game to the database.
        game_data should be a dictionary with keys:
        'start_time', 'end_time', 'winner', 'reason', 'pgn',
        'white_player_type', 'black_player_type',
        'white_player_name', 'black_player_name',
        'engine_white_id' (optional), 'engine_black_id' (optional),
        'tournament_id' (optional)
        """
        try:
            # Ensure players/engines exist to get their IDs for FKs
            white_player_id = None
            if game_data['white_player_type'] == 'human':
                white_player_id = self.add_player(game_data['white_player_name'])
            elif game_data['white_player_type'] == 'engine' and 'engine_white_id' not in game_data:
                 game_data['engine_white_id'] = self.get_engine_id(game_data['white_player_name'])

            black_player_id = None
            if game_data['black_player_type'] == 'human':
                black_player_id = self.add_player(game_data['black_player_name'])
            elif game_data['black_player_type'] == 'engine' and 'engine_black_id' not in game_data:
                game_data['engine_black_id'] = self.get_engine_id(game_data['black_player_name'])

            self.cursor.execute("""
                INSERT INTO games (
                    start_time, end_time, winner, reason, pgn,
                    white_player_type, black_player_type,
                    white_player_name, black_player_name,
                    engine_white_id, engine_black_id, tournament_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                game_data['start_time'], game_data['end_time'], game_data['winner'],
                game_data['reason'], game_data['pgn'],
                game_data['white_player_type'], game_data['black_player_type'],
                game_data['white_player_name'], game_data['black_player_name'],
                game_data.get('engine_white_id'), game_data.get('engine_black_id'),
                game_data.get('tournament_id')
            ))
            self.conn.commit()
            print(f"Game saved with ID: {self.cursor.lastrowid}")
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error saving game: {e}")
            return None

    def get_games_history(self, limit=100, offset=0, player_name=None, engine_name=None, tournament_id=None):
        """Retrieves game history based on filters."""
        query = "SELECT * FROM games WHERE 1=1"
        params = []
        if player_name:
            query += " AND (white_player_name = ? OR black_player_name = ?)"
            params.extend([player_name, player_name])
        if engine_name:
            query += " AND (white_player_name = ? OR black_player_name = ?)"
            params.extend([engine_name, engine_name])
        if tournament_id:
            query += " AND tournament_id = ?"
            params.append(tournament_id)
        
        query += " ORDER BY start_time DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        self.cursor.execute(query, tuple(params))
        columns = [description[0] for description in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

    def save_tournament(self, tournament_data):
        """
        Saves tournament details.
        tournament_data should be a dictionary with keys:
        'name', 'start_date', 'end_date' (optional), 'rounds', 'status', 'config'
        """
        try:
            self.cursor.execute("""
                INSERT INTO tournaments (name, start_date, end_date, rounds, status, config)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                tournament_data['name'],
                tournament_data['start_date'],
                tournament_data.get('end_date'),
                tournament_data['rounds'],
                tournament_data['status'],
                json.dumps(tournament_data['config'])
            ))
            self.conn.commit()
            print(f"Tournament saved with ID: {self.cursor.lastrowid}")
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error saving tournament: {e}")
            return None

    def update_tournament_status(self, tournament_id, status, end_date=None):
        """Updates the status of a tournament."""
        try:
            if end_date:
                self.cursor.execute("UPDATE tournaments SET status = ?, end_date = ? WHERE tournament_id = ?",
                                    (status, end_date, tournament_id))
            else:
                self.cursor.execute("UPDATE tournaments SET status = ? WHERE tournament_id = ?",
                                    (status, tournament_id))
            self.conn.commit()
            print(f"Tournament {tournament_id} status updated to {status}")
        except sqlite3.Error as e:
            print(f"Error updating tournament status: {e}")

    def save_tournament_game_result(self, tournament_id, game_id, round_number, white_engine_id, black_engine_id, result):
        """
        Records a game result specifically for a tournament, linking it to the main games table.
        """
        try:
            self.cursor.execute("""
                INSERT INTO tournament_games (tournament_id, game_id, round_number, white_engine_id, black_engine_id, result)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (tournament_id, game_id, round_number, white_engine_id, black_engine_id, result))
            self.conn.commit()
            print(f"Tournament game result saved for tournament {tournament_id}, game {game_id}")
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error saving tournament game result: {e}")
            return None
            
    def get_tournament_games(self, tournament_id):
        """Retrieves all games played within a specific tournament."""
        self.cursor.execute("""
            SELECT tg.*, g.pgn, g.winner, g.reason,
                   ew.name AS white_engine_name, bw.name AS black_engine_name
            FROM tournament_games tg
            JOIN games g ON tg.game_id = g.game_id
            LEFT JOIN engines ew ON tg.white_engine_id = ew.engine_id
            LEFT JOIN engines bw ON tg.black_engine_id = bw.engine_id
            WHERE tg.tournament_id = ? ORDER BY tg.round_number
        """, (tournament_id,))
        columns = [description[0] for description in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

    def close(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()
            print("Database connection closed.")

# Example Usage (for testing purposes, remove in final app)
if __name__ == "__main__":
    db = DBManager()

    # Add some engines
    db.add_engine("Stockfish 15", "15", "/path/to/stockfish", {"Skill Level": 20})
    db.add_engine("Custom AI v1", "1.0", None, {"Depth": 3})
    stockfish_id = db.get_engine_id("Stockfish 15")
    custom_ai_id = db.get_engine_id("Custom AI v1")
    print(f"Stockfish ID: {stockfish_id}, Custom AI ID: {custom_ai_id}")

    # Add a human player
    db.add_player("Alice")
    db.add_player("Bob")
    alice_id = db.get_player_id("Alice")
    print(f"Alice ID: {alice_id}")

    # Save a human vs human game
    game1_data = {
        'start_time': datetime.now().isoformat(),
        'end_time': datetime.now().isoformat(),
        'winner': 'white',
        'reason': 'checkmate',
        'pgn': '1. e4 e5 2. Qh5 Nc6 3. Bc4 Nf6 4. Qxf7#',
        'white_player_type': 'human',
        'black_player_type': 'human',
        'white_player_name': 'Alice',
        'black_player_name': 'Bob'
    }
    game1_id = db.save_game(game1_data)

    # Save a human vs engine game
    game2_data = {
        'start_time': datetime.now().isoformat(),
        'end_time': datetime.now().isoformat(),
        'winner': 'black',
        'reason': 'resignation',
        'pgn': '1. d4 Nf6 2. c4 g6 3. Nc3 d5 4. Nf3 Bg7 5. Qb3 dxc4 6. Qxc4 O-O',
        'white_player_type': 'human',
        'black_player_type': 'engine',
        'white_player_name': 'Bob',
        'black_player_name': 'Stockfish 15',
        'engine_black_id': stockfish_id
    }
    game2_id = db.save_game(game2_data)

    # Create a tournament
    tournament_config = {'engines': ["Stockfish 15", "Custom AI v1"], 'time_control': '1+0'}
    tournament_data = {
        'name': 'Summer Engine Battle',
        'start_date': datetime.now().isoformat(),
        'end_date': None,
        'rounds': 3,
        'status': 'ongoing',
        'config': tournament_config
    }
    tournament_id = db.save_tournament(tournament_data)
    
    # Simulate a game in the tournament
    game3_data = {
        'start_time': datetime.now().isoformat(),
        'end_time': datetime.now().isoformat(),
        'winner': 'white', # Stockfish wins
        'reason': 'checkmate',
        'pgn': '1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7',
        'white_player_type': 'engine',
        'black_player_type': 'engine',
        'white_player_name': 'Stockfish 15',
        'black_player_name': 'Custom AI v1',
        'engine_white_id': stockfish_id,
        'engine_black_id': custom_ai_id,
        'tournament_id': tournament_id
    }
    game3_id = db.save_game(game3_data)
    db.save_tournament_game_result(tournament_id, game3_id, 1, stockfish_id, custom_ai_id, 'white_win')


    # Get game history
    print("\n--- All Games ---")
    games = db.get_games_history()
    for game in games:
        print(game)

    print("\n--- Games with Alice ---")
    alice_games = db.get_games_history(player_name="Alice")
    for game in alice_games:
        print(game)
        
    print("\n--- Games in Tournament ---")
    t_games = db.get_tournament_games(tournament_id)
    for game in t_games:
        print(game)

    db.close()
