"""Tests for the ELO rating system."""
import pytest
from app.elo import (
    calculate_elo,
    expected_score,
    rating_change,
    process_game_result,
    AI_RATINGS,
    MIN_RATING,
    MAX_RATING,
)


class TestExpectedScore:
    def test_equal_ratings(self):
        """Two players with equal rating should have ~0.5 expected score."""
        e = expected_score(1000, 1000)
        assert abs(e - 0.5) < 0.001

    def test_higher_vs_lower(self):
        """Higher-rated player should have expected score > 0.5."""
        e = expected_score(1200, 1000)
        assert e > 0.5

    def test_lower_vs_higher(self):
        """Lower-rated player should have expected score < 0.5."""
        e = expected_score(800, 1200)
        assert e < 0.5

    def test_symmetry(self):
        """E(A vs B) + E(B vs A) should equal 1."""
        e1 = expected_score(1000, 1400)
        e2 = expected_score(1400, 1000)
        assert abs(e1 + e2 - 1.0) < 0.001


class TestCalculateElo:
    def test_win_increases_rating(self):
        """Winning should increase rating."""
        new = calculate_elo(1000, 1000, 1.0, 0)
        assert new > 1000

    def test_loss_decreases_rating(self):
        """Losing should decrease rating."""
        new = calculate_elo(1000, 1000, 0.0, 0)
        assert new < 1000

    def test_draw_stays_similar(self):
        """Drawing against equal opponent should keep rating nearly the same."""
        new = calculate_elo(1000, 1000, 0.5, 0)
        assert abs(new - 1000) <= 1

    def test_beating_weak_gives_fewer_points(self):
        """Beating a much weaker opponent gives fewer points."""
        win_vs_weak = calculate_elo(1200, 800, 1.0, 0) - 1200
        win_vs_equal = calculate_elo(1200, 1200, 1.0, 0) - 1200
        assert win_vs_weak < win_vs_equal

    def test_losing_to_weak_gives_bigger_drop(self):
        """Losing to a much weaker opponent drops more."""
        loss_vs_weak = 1200 - calculate_elo(1200, 800, 0.0, 0)
        loss_vs_equal = 1200 - calculate_elo(1200, 1200, 0.0, 0)
        assert loss_vs_weak > loss_vs_equal

    def test_clamped_to_min(self):
        """Rating should not go below MIN_RATING."""
        r = MIN_RATING
        for _ in range(100):
            r = calculate_elo(r, 2000, 0.0, 100)
        assert r >= MIN_RATING

    def test_clamped_to_max(self):
        """Rating should not exceed MAX_RATING."""
        r = MAX_RATING - 5
        r = calculate_elo(r, 100, 1.0, 0)
        assert r <= MAX_RATING


class TestKFactor:
    def test_high_k_for_new_players(self):
        """New players should have higher K-factor."""
        new = calculate_elo(1000, 1000, 1.0, 0) - 1000
        veteran = calculate_elo(1000, 1000, 1.0, 200) - 1000
        assert new > veteran

    def test_k_decreases_with_games(self):
        """K-factor should decrease as games_played increases."""
        k_new = abs(calculate_elo(1000, 1000, 1.0, 5) - 1000)
        k_mid = abs(calculate_elo(1000, 1000, 1.0, 50) - 1000)
        k_old = abs(calculate_elo(1000, 1000, 1.0, 150) - 1000)
        assert k_new >= k_mid >= k_old


class TestRatingChange:
    def test_positive_on_win(self):
        """Win should return positive change."""
        change = rating_change(1000, 1000, 1.0)
        assert change > 0

    def test_negative_on_loss(self):
        """Loss should return negative change."""
        change = rating_change(1000, 1000, 0.0)
        assert change < 0


class TestProcessGameResult:
    def test_win_vs_easy(self):
        """Win against Easy AI."""
        r = process_game_result(1000, True, False, "easy", 0)
        assert r.result_label == "win"
        assert r.new_rating > r.old_rating
        assert r.opponent_name == "Fácil"

    def test_loss_vs_hard(self):
        """Loss against Hard AI."""
        r = process_game_result(1000, False, False, "hard", 0)
        assert r.result_label == "loss"
        assert r.new_rating < r.old_rating
        assert r.opponent_name == "Difícil"

    def test_draw(self):
        """Draw result."""
        r = process_game_result(1000, False, True, "medium", 0)
        assert r.result_label == "draw"

    def test_beating_easier_opponent_gives_less(self):
        """Beating Easy AI should give fewer points than beating Hard AI."""
        easy_win = process_game_result(1000, True, False, "easy", 0)
        hard_win = process_game_result(1000, True, False, "hard", 0)
        assert easy_win.change < hard_win.change

    def test_losing_to_easier_opponent_costs_more(self):
        """Losing to Easy AI should cost more than losing to Hard AI."""
        easy_loss = process_game_result(1000, False, False, "easy", 0)
        hard_loss = process_game_result(1000, False, False, "hard", 0)
        assert easy_loss.change < hard_loss.change  # more negative


class TestAIRatings:
    def test_easy_is_weakest(self):
        assert AI_RATINGS["easy"] < AI_RATINGS["medium"]

    def test_hard_is_strongest(self):
        assert AI_RATINGS["hard"] > AI_RATINGS["medium"]

    def test_all_difficulties_present(self):
        assert "easy" in AI_RATINGS
        assert "medium" in AI_RATINGS
        assert "hard" in AI_RATINGS
