"""
NILytics — Output Score (Percentile Ranking) (Phase 2.3)

Ranks each player's core_grade within their position group for that season.
Converts to 0-100 percentile score. This is the ONLY input for tiering.
"""

from scipy import stats


def compute_output_scores(player_grades: list[dict]) -> list[dict]:
    """
    Given a list of dicts with keys: player_id, season, position, core_grade
    Returns the same list with 'output_score' (0-100 percentile) added.

    Players are ranked within their position group PER SEASON.
    """
    # Group by (position, season)
    groups = {}
    for pg in player_grades:
        key = (pg['position'], pg['season'])
        groups.setdefault(key, []).append(pg)

    results = []
    for key, group in groups.items():
        grades = [p['core_grade'] for p in group]
        n = len(grades)

        if n == 1:
            # Only one player — assign 50th percentile
            group[0]['output_score'] = 50.0
            results.append(group[0])
            continue

        # Compute percentile rank for each player
        # percentileofscore gives the % of values <= the given score
        for p in group:
            pct = stats.percentileofscore(grades, p['core_grade'], kind='rank')
            p['output_score'] = round(pct, 2)
            results.append(p)

    return results
