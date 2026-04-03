"""
NILytics — Trajectory Analysis (Phase 3.5)

Compare output_score across seasons for the same player.
  UP       — improving (>5pt gain)
  DOWN     — declining (>5pt drop)
  STABLE   — within ±5pt
  BREAKOUT — >15pt jump from prior season
"""


def compute_trajectory(scores_by_season: list[dict]) -> str:
    """
    Given a list of {'season': int, 'output_score': float} sorted by season,
    return a trajectory flag.

    If only one season, returns 'STABLE'.
    Compares the two most recent seasons.
    """
    if len(scores_by_season) < 2:
        return 'STABLE'

    # Sort by season ascending
    sorted_scores = sorted(scores_by_season, key=lambda x: x['season'])
    prev = sorted_scores[-2]['output_score']
    curr = sorted_scores[-1]['output_score']

    delta = curr - prev

    if delta > 15:
        return 'BREAKOUT'
    elif delta > 5:
        return 'UP'
    elif delta < -5:
        return 'DOWN'
    else:
        return 'STABLE'
