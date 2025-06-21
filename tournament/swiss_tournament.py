# tournament/swiss_tournament.py
import chess
from game.chess_game_manager import ChessGameManager
from database.db_manager import DBManager
from datetime import datetime
import random

class SwissTournament:
    """
    Manages a Swiss-style chess tournament for AI engines.
    Handles pairings, game execution, and scoring.
    """
    def __init__(self, tournament_name: str, engines: list, num_rounds: int, db_manager: DBManager):
        self.tournament_name = tournament_name
        self.engines = engines # List of engine objects (instances of BaseChessEngine subclasses)
        self.num_rounds = num_rounds
        self.db_manager = db_manager
        self.engine_scores = {engine.name: {"points": 0.0, "opponents": [], "games_played": 0} for engine in engines}
        self.tournament_id = None
        self.current_round = 0
        self.games_in_round = [] # Stores (white_engine, black_engine) for current round
        self.ongoing_game_state = None # To hold the state of an individual game being played if run step-by-step
        self.is_tournament_running = False

    def start_tournament(self):
        """Initializes and starts the tournament, saving its details to the database."""
        tournament_config = {
            "engines": [e.name for e in self.engines],
            "rounds": self.num_rounds
        }
        self.tournament_id = self.db_manager.save_tournament({
            'name': self.tournament_name,
            'start_date': datetime.now().isoformat(),
            'end_date': None,
            'rounds': self.num_rounds,
            'status': 'ongoing',
            'config': tournament_config
        })
        if self.tournament_id:
            self.is_tournament_running = True
            print(f"Tournament '{self.tournament_name}' started with ID: {self.tournament_id}")
            self.run_next_round() # Start the first round

    def run_next_round(self):
        """
        Generates pairings for the next round based on Swiss system rules
        and starts playing games for that round.
        """
        if not self.is_tournament_running or self.current_round >= self.num_rounds:
            print("Tournament is not running or all rounds completed.")
            self._end_tournament()
            return False

        self.current_round += 1
        print(f"\n--- Starting Round {self.current_round} ---")
        self.games_in_round = [] # Reset games for the new round

        # Simple pairing: Sort by score, then pair adjacent.
        # In a real Swiss system, you'd avoid pairing same opponents twice,
        # balance colors, and handle bye if odd number of players.
        sorted_engines = sorted(self.engines, key=lambda e: self.engine_scores[e.name]["points"], reverse=True)
        
        # Ensure engines play each other as white and black equally over rounds
        # Simple alternating color assignment for pairings:
        pairings = []
        # Create a list of available engines for pairing
        available_engines = list(sorted_engines)
        random.shuffle(available_engines) # Randomize within score groups

        while len(available_engines) >= 2:
            e1 = available_engines.pop(0)
            e2 = available_engines.pop(0)

            # Basic color balancing: if e1 played white last, e2 plays white this time.
            # This is a very simplified heuristic.
            if self.engine_scores[e1.name]["games_played"] <= self.engine_scores[e2.name]["games_played"]:
                white_engine, black_engine = e1, e2
            else:
                white_engine, black_engine = e2, e1
            
            pairings.append((white_engine, black_engine))

        if len(available_engines) == 1:
            # Handle bye (if odd number of engines) - this engine gets a "win" without playing
            # For simplicity, we'll just ignore it for now or give a half point bye.
            # A true Swiss system gives a bye to the lowest score available that hasn't had one.
            print(f"Engine {available_engines[0].name} has a bye this round (odd number of engines).")
            self.engine_scores[available_engines[0].name]["points"] += 1.0 # Full point bye
            self.engine_scores[available_engines[0].name]["games_played"] += 1


        for white_engine, black_engine in pairings:
            print(f"Pairing: {white_engine.name} (White) vs. {black_engine.name} (Black)")
            self.games_in_round.append((white_engine, black_engine))
            # In a real UI, you'd run these games one by one or in parallel
            self._play_single_game(white_engine, black_engine)
        
        # After all games in the round are played (or simulated)
        self.db_manager.update_tournament_status(self.tournament_id, "ongoing")
        self.get_standings() # Print standings after each round

        if self.current_round >= self.num_rounds:
            self._end_tournament()
            return False # Tournament completed
        return True # More rounds to play


    def _play_single_game(self, white_engine, black_engine):
        """Plays a single game between two engines."""
        game_manager = ChessGameManager()
        game_manager.reset_game() # Ensure fresh board for each game
        
        white_engine.set_board(game_manager.get_board_object())
        black_engine.set_board(game_manager.get_board_object())

        start_time = datetime.now()
        game_result = "unknown" # For internal tracking before saving

        print(f"  Game: {white_engine.name} (W) vs. {black_engine.name} (B)")
        move_count = 0
        max_moves = 200 # Prevent infinite games for simple AIs
        
        while not game_manager.is_game_over() and move_count < max_moves:
            current_turn = game_manager.get_board_object().turn
            if current_turn == chess.WHITE:
                engine_to_move = white_engine
            else:
                engine_to_move = black_engine
            
            # Sync engine's internal board before asking for move
            engine_to_move.set_board(game_manager.get_board_object())
            move = engine_to_move.make_move()

            if move:
                if game_manager.make_move(move.uci()):
                    move_count += 1
                else:
                    print(f"  Error: {engine_to_move.name} made illegal move {move.uci()}")
                    # Forfeit or error handling
                    if engine_to_move == white_engine: game_result = "black_win"
                    else: game_result = "white_win"
                    break
            else:
                print(f"  {engine_to_move.name} failed to make a move (no legal moves?).")
                # This might indicate game over, or a bug in engine
                break

        end_time = datetime.now()
        winner, reason = game_manager.get_game_result()

        if winner == 'white':
            self.engine_scores[white_engine.name]["points"] += 1.0
            game_result = "white_win"
        elif winner == 'black':
            self.engine_scores[black_engine.name]["points"] += 1.0
            game_result = "black_win"
        elif winner == 'draw':
            self.engine_scores[white_engine.name]["points"] += 0.5
            self.engine_scores[black_engine.name]["points"] += 0.5
            game_result = "draw"
        else: # Game might not be truly over according to chess.Board.is_game_over() if max_moves hit
            print(f"  Game ended due to max moves ({max_moves}). Declaring a draw.")
            self.engine_scores[white_engine.name]["points"] += 0.5
            self.engine_scores[black_engine.name]["points"] += 0.5
            game_result = "draw"
            reason = "max moves reached"

        self.engine_scores[white_engine.name]["games_played"] += 1
        self.engine_scores[black_engine.name]["games_played"] += 1

        print(f"  Result: {winner if winner else 'Draw'} by {reason if reason else 'timeout/max moves'}")

        # Save game to main games table
        game_data = {
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'winner': winner if winner else 'draw',
            'reason': reason if reason else 'max moves reached',
            'pgn': game_manager.get_pgn(),
            'white_player_type': 'engine',
            'black_player_type': 'engine',
            'white_player_name': white_engine.name,
            'black_player_name': black_engine.name,
            'engine_white_id': self.db_manager.get_engine_id(white_engine.name),
            'engine_black_id': self.db_manager.get_engine_id(black_engine.name),
            'tournament_id': self.tournament_id
        }
        game_id = self.db_manager.save_game(game_data)
        
        # Save game to tournament_games table
        if game_id:
            self.db_manager.save_tournament_game_result(
                self.tournament_id,
                game_id,
                self.current_round,
                self.db_manager.get_engine_id(white_engine.name),
                self.db_manager.get_engine_id(black_engine.name),
                game_result
            )

    def _end_tournament(self):
        """Finalizes the tournament, updates status in DB, and prints final standings."""
        self.is_tournament_running = False
        self.db_manager.update_tournament_status(self.tournament_id, "completed", datetime.now().isoformat())
        print("\n--- Tournament Completed! ---")
        self.get_standings()
        print("Tournament results saved to database.")
        
        # Clean up engines if they manage processes
        for engine in self.engines:
            if hasattr(engine, 'quit') and callable(engine.quit):
                engine.quit()

    def get_standings(self):
        """Prints the current standings of the tournament."""
        print("\n--- Current Standings ---")
        sorted_standings = sorted(self.engine_scores.items(), key=lambda item: item[1]["points"], reverse=True)
        for i, (engine_name, data) in enumerate(sorted_standings):
            print(f"{i+1}. {engine_name}: {data['points']} points ({data['games_played']} games)")
        print("-------------------------\n")

    def get_current_round(self):
        return self.current_round

    def get_num_rounds(self):
        return self.num_rounds

    def get_engine_scores(self):
        return self.engine_scores

# Example Usage (for testing purposes)
if __name__ == "__main__":
    from database.db_manager import DBManager
    from engine.simple_ai_engine import SimpleAIEngine
    from engine.stockfish_engine import StockfishEngine

    db_test = DBManager()
    
    # Ensure some engines are in DB or define paths for Stockfish
    stockfish_path = "/usr/local/bin/stockfish" # Adjust as needed
    
    # Add dummy engines to DB for demonstration
    db_test.add_engine("SimpleAI1", "1.0")
    db_test.add_engine("SimpleAI2", "1.0")
    # Uncomment and adjust path if you have Stockfish
    # db_test.add_engine("StockfishEngine", "15", stockfish_path)

    # Fetch engines from DB and create instances
    engine_data = db_test.get_all_engines()
    
    actual_engines = []
    for data in engine_data:
        if data['name'] == "StockfishEngine": # Adjust name if you add other Stockfish versions
            try:
                # Only add if path exists and engine connects
                stock_engine = StockfishEngine(data['path'], name=data['name'], version=data['version'])
                if stock_engine.engine:
                    actual_engines.append(stock_engine)
                else:
                    print(f"Skipping {data['name']} due to connection issue.")
            except Exception as e:
                print(f"Could not initialize StockfishEngine: {e}")
        elif data['name'].startswith("SimpleAI"): # Example for simple AI
            actual_engines.append(SimpleAIEngine(name=data['name'], version=data['version']))
        # Add other engine types here if you have them

    if len(actual_engines) < 2:
        print("Need at least two working engine instances to run a tournament.")
        print("Please configure Stockfish path or ensure SimpleAIEngine is available.")
        # Fallback to creating simple engines if not enough
        actual_engines = [SimpleAIEngine("FallbackAI1"), SimpleAIEngine("FallbackAI2", delay_seconds=0.1)]
        print("Using fallback SimpleAIEngines for testing.")


    if len(actual_engines) >= 2:
        tournament = SwissTournament("Test Tournament", actual_engines, num_rounds=3, db_manager=db_test)
        tournament.start_tournament()
        # In a real UI, you'd manage rounds through button clicks/updates,
        # here we're simulating sequential execution.
        # While tournament.run_next_round() returns True:
        #    tournament.run_next_round()
    else:
        print("Not enough engines to start a tournament.")

    db_test.close()
