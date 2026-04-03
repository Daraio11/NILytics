"""
NILytics — Snap Proxy Computation (Phase 2.1)

Computes the snap proxy for each player-season based on position.
This is the volume metric used for eligibility checks and penalties.

Rules:
  QB:      passing_stats.passing_snaps
  RB/WR:   receiving(wide_snaps + slot_snaps + inline_snaps) + blocking(snap_counts_run_block) + rushing(attempts)
  TE:      receiving(wide_snaps + slot_snaps + inline_snaps) + blocking(snap_counts_run_block + snap_counts_pass_block)
  OT/IOL:  blocking(snap_counts_block)
  Defense:  defense(snap_counts_run_defense + snap_counts_pass_rush + snap_counts_coverage)
"""


def compute_snap_proxy(position: str, passing: dict | None, receiving: dict | None,
                       rushing: dict | None, blocking: dict | None, defense: dict | None) -> int:
    """
    Compute snap proxy for a player based on position and available stat rows.
    All inputs are dicts of column_name -> value (or None if no row exists for that stat type).
    Returns integer snap count.
    """

    def safe(d, key):
        if d is None:
            return 0
        v = d.get(key)
        if v is None:
            return 0
        try:
            return int(float(v))
        except (ValueError, TypeError):
            return 0

    if position == 'QB':
        return safe(passing, 'passing_snaps')

    elif position in ('RB', 'WR'):
        rec_snaps = (safe(receiving, 'wide_snaps') +
                     safe(receiving, 'slot_snaps') +
                     safe(receiving, 'inline_snaps'))
        blk_snaps = safe(blocking, 'snap_counts_run_block')
        rush_att = safe(rushing, 'attempts')
        return rec_snaps + blk_snaps + rush_att

    elif position == 'TE':
        rec_snaps = (safe(receiving, 'wide_snaps') +
                     safe(receiving, 'slot_snaps') +
                     safe(receiving, 'inline_snaps'))
        blk_snaps = (safe(blocking, 'snap_counts_run_block') +
                     safe(blocking, 'snap_counts_pass_block'))
        return rec_snaps + blk_snaps

    elif position in ('OT', 'IOL'):
        return safe(blocking, 'snap_counts_block')

    elif position in ('EDGE', 'IDL', 'LB', 'CB', 'S'):
        return (safe(defense, 'snap_counts_run_defense') +
                safe(defense, 'snap_counts_pass_rush') +
                safe(defense, 'snap_counts_coverage'))

    else:
        return 0
