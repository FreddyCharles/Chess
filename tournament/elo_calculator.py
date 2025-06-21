# tournament/elo_calculator.py
import math

DEFAULT_K_FACTOR = 32

def calculate_expected_score(player_elo: float, opponent_elo: float) -> float:
    """
    Calculates the expected score for a player based on their Elo rating
    and their opponent's Elo rating.
    E_a = 1 / (1 + 10^((elo_b - elo_a) / 400))
    """
    return 1 / (1 + math.pow(10, (opponent_elo - player_elo) / 400))

def calculate_new_elo(current_elo: float, actual_score: float, expected_score: float, k_factor: int = DEFAULT_K_FACTOR) -> float:
    """
    Calculates the new Elo rating for a player.
    elo_new = elo_old + K * (actual_score - expected_score)

    Args:
        current_elo: The player's current Elo rating.
        actual_score: The actual score achieved by the player (1 for win, 0.5 for draw, 0 for loss).
        expected_score: The expected score for the player against the opponent.
        k_factor: The K-factor, determining the sensitivity of Elo changes.
                  Defaults to 32.

    Returns:
        The new Elo rating, rounded to the nearest integer.
    """
    new_elo = current_elo + k_factor * (actual_score - expected_score)
    return round(new_elo)

def update_elos(elo_player1: float, elo_player2: float, score_player1: float, k_factor: int = DEFAULT_K_FACTOR) -> tuple[float, float]:
    """
    Calculates and returns the new Elo ratings for two players after a game.

    Args:
        elo_player1: Current Elo of player 1.
        elo_player2: Current Elo of player 2.
        score_player1: Score of player 1 (1 for win, 0.5 for draw, 0 for loss).
        k_factor: The K-factor to use for both players.

    Returns:
        A tuple containing (new_elo_player1, new_elo_player2).
    """
    expected_score_player1 = calculate_expected_score(elo_player1, elo_player2)
    expected_score_player2 = calculate_expected_score(elo_player2, elo_player1) # Or 1 - expected_score_player1

    # Score for player 2 is inverse of player 1's score (e.g., if P1 wins (1), P2 loses (0))
    score_player2 = 1 - score_player1

    new_elo_player1 = calculate_new_elo(elo_player1, score_player1, expected_score_player1, k_factor)
    new_elo_player2 = calculate_new_elo(elo_player2, score_player2, expected_score_player2, k_factor)

    return new_elo_player1, new_elo_player2

if __name__ == '__main__':
    # Example Usage:
    p1_elo = 1500
    p2_elo = 1500

    print(f"Initial Elos: Player 1 = {p1_elo}, Player 2 = {p2_elo}")

    # Scenario 1: Player 1 (1500) wins against Player 2 (1500)
    new_p1_elo, new_p2_elo = update_elos(p1_elo, p2_elo, 1.0) # P1 wins
    print(f"P1 (1500) wins vs P2 (1500): New P1 Elo = {new_p1_elo}, New P2 Elo = {new_p2_elo}")
    # Expected: P1 gains 16, P2 loses 16 (for K=32) -> P1=1516, P2=1484

    # Scenario 2: Player 1 (1600) draws with Player 2 (1400)
    p1_elo_stronger = 1600
    p2_elo_weaker = 1400
    new_p1_elo, new_p2_elo = update_elos(p1_elo_stronger, p2_elo_weaker, 0.5) # Draw
    print(f"P1 (1600) draws vs P2 (1400): New P1 Elo = {new_p1_elo}, New P2 Elo = {new_p2_elo}")
    # Expected for K=32: P1 (stronger) loses Elo, P2 (weaker) gains Elo.
    # Exp P1 = 1 / (1 + 10^((1400-1600)/400)) = 1 / (1 + 10^(-0.5)) = 1 / (1 + 0.316) = 0.76
    # P1 change = 32 * (0.5 - 0.76) = 32 * (-0.26) = -8.32 -> P1 = 1592
    # Exp P2 = 1 - 0.76 = 0.24
    # P2 change = 32 * (0.5 - 0.24) = 32 * (0.26) = 8.32 -> P2 = 1408

    # Scenario 3: Player 1 (1400) loses to Player 2 (1600)
    new_p1_elo, new_p2_elo = update_elos(p2_elo_weaker, p1_elo_stronger, 0.0) # P1 (1400) loses
    print(f"P1 (1400) loses vs P2 (1600): New P1 Elo = {new_p1_elo}, New P2 Elo = {new_p2_elo}")
    # Expected for K=32: P1 (1400) loses less, P2 (1600) gains less.
    # Exp P1 (1400 vs 1600) = 0.24
    # P1 change = 32 * (0.0 - 0.24) = 32 * (-0.24) = -7.68 -> P1 = 1392
    # Exp P2 (1600 vs 1400) = 0.76
    # P2 change = 32 * (1.0 - 0.76) = 32 * (0.24) = 7.68 -> P2 = 1608

    # Test with a different K-factor
    p1_elo_ktest = 2000
    p2_elo_ktest = 2000
    new_p1_elo_k, new_p2_elo_k = update_elos(p1_elo_ktest, p2_elo_ktest, 1.0, k_factor=16)
    print(f"P1 (2000) wins vs P2 (2000) with K=16: New P1 Elo = {new_p1_elo_k}, New P2 Elo = {new_p2_elo_k}")
    # Expected: P1 gains 8, P2 loses 8 -> P1=2008, P2=1992

    # Test expected score calculation directly
    exp_score = calculate_expected_score(1500, 1500)
    print(f"Expected score for 1500 vs 1500: {exp_score} (Should be 0.5)")
    exp_score_diff = calculate_expected_score(1600, 1400)
    print(f"Expected score for 1600 vs 1400: {exp_score_diff} (Should be ~0.76)")
