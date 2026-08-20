"""ELO rating system for checkers AI.

Standard ELO formula:
    Expected score: E_A = 1 / (1 + 10^((R_B - R_A) / 400))
    New rating:     R_A' = R_A + K * (S_A - E_A)

Where:
    R_A = current rating of player A
    R_B = current rating of opponent (AI)
    S_A = actual score (1=win, 0.5=draw, 0=loss)
    K   = K-factor (sensitivity to individual results)

AI base ratings by difficulty:
    Easy   = 800   (beatable by beginners)
    Medium = 1100  (solid opponent)
    Hard   = 1500  (very strong)
"""
from __future__ import annotations
from dataclasses import dataclass
import math

# AI base ELO for each difficulty level
AI_RATINGS = {
    "easy": 800,
    "medium": 1100,
    "hard": 1500,
}

# K-factor: how much each game matters
# Newer/lower-rated players change faster
BASE_K = 32
K_BY_GAMES_PLAYED = {
    # games_played_range_max: K_factor
    30: 40,     # first 30 games: high variance (learning phase)
    100: 24,    # 30-100 games: moderate
    999999: 16, # 100+ games: stable
}

# Rating floor and ceiling
MIN_RATING = 100
MAX_RATING = 3000


def _k_factor(games_played: int) -> int:
    """Return the K-factor based on number of games played."""
    for threshold, k in K_BY_GAMES_PLAYED.items():
        if games_played <= threshold:
            return k
    return 16


def expected_score(player_rating: int, opponent_rating: int) -> float:
    """Calculate expected score for player against opponent."""
    return 1.0 / (1.0 + math.pow(10, (opponent_rating - player_rating) / 400.0))


def calculate_elo(
    player_rating: int,
    opponent_rating: int,
    result: float,
    games_played: int = 0,
) -> int:
    """Calculate new ELO rating after a game.

    Args:
        player_rating: Current player rating
        opponent_rating: Opponent (AI) rating
        result: 1.0 = win, 0.5 = draw, 0.0 = loss
        games_played: Total games played so far (affects K-factor)

    Returns:
        New rating (clamped to MIN_RATING..MAX_RATING)
    """
    k = _k_factor(games_played)
    e = expected_score(player_rating, opponent_rating)
    new_rating = player_rating + k * (result - e)
    return max(MIN_RATING, min(MAX_RATING, round(new_rating)))


def rating_change(
    player_rating: int,
    opponent_rating: int,
    result: float,
    games_played: int = 0,
) -> int:
    """Calculate the delta (+/-) of the rating change."""
    new_rating = calculate_elo(player_rating, opponent_rating, result, games_played)
    return new_rating - player_rating


@dataclass
class GameResult:
    """Result of an ELO update to pass to the frontend."""
    old_rating: int
    new_rating: int
    change: int
    opponent_rating: int
    opponent_name: str
    k_factor: int
    result_label: str  # "win", "loss", "draw"


def process_game_result(
    player_rating: int,
    player_won: bool,
    player_draw: bool,
    difficulty: str,
    games_played: int = 0,
) -> GameResult:
    """Process a game result and return the ELO update info.

    Args:
        player_rating: Current player ELO rating
        player_won: True if the human player won
        player_draw: True if the game was a draw
        difficulty: AI difficulty level ("easy", "medium", "hard")
        games_played: Number of games played so far

    Returns:
        GameResult with all rating change details
    """
    ai_rating = AI_RATINGS.get(difficulty, 1100)
    ai_name = {"easy": "Fácil", "medium": "Médio", "hard": "Difícil"}.get(difficulty, difficulty)

    if player_draw:
        result = 0.5
        label = "draw"
    elif player_won:
        result = 1.0
        label = "win"
    else:
        result = 0.0
        label = "loss"

    k = _k_factor(games_played)
    new_rating = calculate_elo(player_rating, ai_rating, result, games_played)
    change = new_rating - player_rating

    return GameResult(
        old_rating=player_rating,
        new_rating=new_rating,
        change=change,
        opponent_rating=ai_rating,
        opponent_name=ai_name,
        k_factor=k,
        result_label=label,
    )
