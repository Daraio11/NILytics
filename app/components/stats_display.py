"""
NILytics — Player Stats Display Component
Shows key metrics by position with percentile highlighting.
"""
import streamlit as st
import pandas as pd
import numpy as np


# Define which stats to show per position, grouped logically
# (label, stat_key, table, format, higher_is_better)
POSITION_STATS = {
    'QB': [
        ('Passing', [
            ('Pass Grade', 'grades_pass', 'passing_stats', '.1f', True),
            ('Comp %', 'completion_percent', 'passing_stats', '.1f', True),
            ('Yards', 'yards', 'passing_stats', ',', True),
            ('TDs', 'touchdowns', 'passing_stats', ',', True),
            ('INTs', 'interceptions', 'passing_stats', ',', False),
            ('YPA', 'ypa', 'passing_stats', '.1f', True),
            ('Avg Depth', 'avg_depth_of_target', 'passing_stats', '.1f', True),
            ('TWP %', 'twp_rate', 'passing_stats', '.1f', False),
            ('QB Rating', 'qb_rating', 'passing_stats', '.1f', True),
            ('Attempts', 'attempts', 'passing_stats', ',', True),
        ]),
        ('Rushing', [
            ('Rush Grade', 'grades_run', 'rushing_stats', '.1f', True),
            ('Rush Yards', 'yards', 'rushing_stats', ',', True),
            ('Rush TDs', 'touchdowns', 'rushing_stats', ',', True),
            ('YPA', 'ypa', 'rushing_stats', '.1f', True),
        ]),
    ],
    'RB': [
        ('Rushing', [
            ('Rush Grade', 'grades_run', 'rushing_stats', '.1f', True),
            ('Yards', 'yards', 'rushing_stats', ',', True),
            ('TDs', 'touchdowns', 'rushing_stats', ',', True),
            ('Attempts', 'attempts', 'rushing_stats', ',', True),
            ('YPA', 'ypa', 'rushing_stats', '.1f', True),
            ('YAC/Att', 'yco_attempt', 'rushing_stats', '.2f', True),
            ('Elusive Rating', 'elusive_rating', 'rushing_stats', '.1f', True),
            ('Breakaway %', 'breakaway_percent', 'rushing_stats', '.1f', True),
            ('Avoided Tackles', 'avoided_tackles', 'rushing_stats', ',', True),
            ('Fumbles', 'fumbles', 'rushing_stats', ',', False),
        ]),
        ('Receiving', [
            ('Rec Grade', 'grades_pass_route', 'receiving_stats', '.1f', True),
            ('Receptions', 'receptions', 'receiving_stats', ',', True),
            ('Rec Yards', 'yards', 'receiving_stats', ',', True),
            ('Rec TDs', 'touchdowns', 'receiving_stats', ',', True),
            ('YPRR', 'yprr', 'receiving_stats', '.2f', True),
            ('Drop Rate', 'drop_rate', 'receiving_stats', '.1f', False),
        ]),
    ],
    'WR': [
        ('Receiving', [
            ('Route Grade', 'grades_pass_route', 'receiving_stats', '.1f', True),
            ('Receptions', 'receptions', 'receiving_stats', ',', True),
            ('Yards', 'yards', 'receiving_stats', ',', True),
            ('TDs', 'touchdowns', 'receiving_stats', ',', True),
            ('Targets', 'targets', 'receiving_stats', ',', True),
            ('Catch %', 'caught_percent', 'receiving_stats', '.1f', True),
            ('YPRR', 'yprr', 'receiving_stats', '.2f', True),
            ('YAC/Rec', 'yards_after_catch_per_reception', 'receiving_stats', '.1f', True),
            ('Avg Depth', 'avg_depth_of_target', 'receiving_stats', '.1f', True),
            ('Drop Rate', 'drop_rate', 'receiving_stats', '.1f', False),
            ('Contested Catch %', 'contested_catch_rate', 'receiving_stats', '.1f', True),
        ]),
    ],
    'TE': [
        ('Receiving', [
            ('Rec Grade', 'grades_pass_route', 'receiving_stats', '.1f', True),
            ('Receptions', 'receptions', 'receiving_stats', ',', True),
            ('Yards', 'yards', 'receiving_stats', ',', True),
            ('TDs', 'touchdowns', 'receiving_stats', ',', True),
            ('YPRR', 'yprr', 'receiving_stats', '.2f', True),
            ('Drop Rate', 'drop_rate', 'receiving_stats', '.1f', False),
        ]),
        ('Blocking', [
            ('Pass Block Grade', 'grades_pass_block', 'blocking_stats', '.1f', True),
            ('Run Block Grade', 'grades_run_block', 'blocking_stats', '.1f', True),
            ('PBE', 'pbe', 'blocking_stats', '.1f', True),
            ('Pressures Allowed', 'pressures_allowed', 'blocking_stats', ',', False),
            ('Sacks Allowed', 'sacks_allowed', 'blocking_stats', ',', False),
        ]),
    ],
    'OT': [
        ('Blocking', [
            ('Pass Block Grade', 'grades_pass_block', 'blocking_stats', '.1f', True),
            ('Run Block Grade', 'grades_run_block', 'blocking_stats', '.1f', True),
            ('Overall Grade', 'grades_offense', 'blocking_stats', '.1f', True),
            ('PBE', 'pbe', 'blocking_stats', '.1f', True),
            ('Pressures Allowed', 'pressures_allowed', 'blocking_stats', ',', False),
            ('Sacks Allowed', 'sacks_allowed', 'blocking_stats', ',', False),
            ('Hurries Allowed', 'hurries_allowed', 'blocking_stats', ',', False),
            ('Hits Allowed', 'hits_allowed', 'blocking_stats', ',', False),
            ('Penalties', 'penalties', 'blocking_stats', ',', False),
            ('Total Snaps', 'snap_counts_block', 'blocking_stats', ',', True),
        ]),
    ],
    'IOL': [
        ('Blocking', [
            ('Pass Block Grade', 'grades_pass_block', 'blocking_stats', '.1f', True),
            ('Run Block Grade', 'grades_run_block', 'blocking_stats', '.1f', True),
            ('Overall Grade', 'grades_offense', 'blocking_stats', '.1f', True),
            ('PBE', 'pbe', 'blocking_stats', '.1f', True),
            ('Pressures Allowed', 'pressures_allowed', 'blocking_stats', ',', False),
            ('Sacks Allowed', 'sacks_allowed', 'blocking_stats', ',', False),
            ('Hurries Allowed', 'hurries_allowed', 'blocking_stats', ',', False),
            ('Penalties', 'penalties', 'blocking_stats', ',', False),
            ('Total Snaps', 'snap_counts_block', 'blocking_stats', ',', True),
        ]),
    ],
    'EDGE': [
        ('Pass Rush', [
            ('Pass Rush Grade', 'grades_pass_rush_defense', 'defense_stats', '.1f', True),
            ('Sacks', 'sacks', 'defense_stats', ',', True),
            ('Total Pressures', 'total_pressures', 'defense_stats', ',', True),
            ('Hurries', 'hurries', 'defense_stats', ',', True),
            ('Hits', 'hits', 'defense_stats', ',', True),
            ('TFLs', 'tackles_for_loss', 'defense_stats', ',', True),
        ]),
        ('Run Defense', [
            ('Run Def Grade', 'grades_run_defense', 'defense_stats', '.1f', True),
            ('Tackles', 'tackles', 'defense_stats', ',', True),
            ('Stops', 'stops', 'defense_stats', ',', True),
            ('Missed Tackle %', 'missed_tackle_rate', 'defense_stats', '.1f', False),
        ]),
    ],
    'IDL': [
        ('Pass Rush', [
            ('Pass Rush Grade', 'grades_pass_rush_defense', 'defense_stats', '.1f', True),
            ('Sacks', 'sacks', 'defense_stats', ',', True),
            ('Total Pressures', 'total_pressures', 'defense_stats', ',', True),
            ('Hurries', 'hurries', 'defense_stats', ',', True),
            ('TFLs', 'tackles_for_loss', 'defense_stats', ',', True),
        ]),
        ('Run Defense', [
            ('Run Def Grade', 'grades_run_defense', 'defense_stats', '.1f', True),
            ('Tackles', 'tackles', 'defense_stats', ',', True),
            ('Stops', 'stops', 'defense_stats', ',', True),
            ('Missed Tackle %', 'missed_tackle_rate', 'defense_stats', '.1f', False),
            ('Penalties', 'grades_defense_penalty', 'defense_stats', '.1f', True),
        ]),
    ],
    'LB': [
        ('Coverage', [
            ('Coverage Grade', 'grades_coverage_defense', 'defense_stats', '.1f', True),
            ('Catch Rate Allowed', 'catch_rate', 'defense_stats', '.1f', False),
            ('INTs', 'interceptions', 'defense_stats', ',', True),
            ('PBUs', 'pass_break_ups', 'defense_stats', ',', True),
            ('QB Rating Against', 'qb_rating_against', 'defense_stats', '.1f', False),
        ]),
        ('Run Defense', [
            ('Run Def Grade', 'grades_run_defense', 'defense_stats', '.1f', True),
            ('Tackles', 'tackles', 'defense_stats', ',', True),
            ('Stops', 'stops', 'defense_stats', ',', True),
            ('TFLs', 'tackles_for_loss', 'defense_stats', ',', True),
            ('Missed Tackle %', 'missed_tackle_rate', 'defense_stats', '.1f', False),
        ]),
    ],
    'CB': [
        ('Coverage', [
            ('Coverage Grade', 'grades_coverage_defense', 'defense_stats', '.1f', True),
            ('Catch Rate Allowed', 'catch_rate', 'defense_stats', '.1f', False),
            ('INTs', 'interceptions', 'defense_stats', ',', True),
            ('PBUs', 'pass_break_ups', 'defense_stats', ',', True),
            ('Targets', 'targets', 'defense_stats', ',', False),
            ('Receptions Allowed', 'receptions', 'defense_stats', ',', False),
            ('Yards Allowed', 'yards', 'defense_stats', ',', False),
            ('QB Rating Against', 'qb_rating_against', 'defense_stats', '.1f', False),
            ('TDs Allowed', 'touchdowns', 'defense_stats', ',', False),
        ]),
        ('Tackling', [
            ('Tackle Grade', 'grades_tackle', 'defense_stats', '.1f', True),
            ('Tackles', 'tackles', 'defense_stats', ',', True),
            ('Missed Tackle %', 'missed_tackle_rate', 'defense_stats', '.1f', False),
        ]),
    ],
    'S': [
        ('Coverage', [
            ('Coverage Grade', 'grades_coverage_defense', 'defense_stats', '.1f', True),
            ('Catch Rate Allowed', 'catch_rate', 'defense_stats', '.1f', False),
            ('INTs', 'interceptions', 'defense_stats', ',', True),
            ('PBUs', 'pass_break_ups', 'defense_stats', ',', True),
            ('QB Rating Against', 'qb_rating_against', 'defense_stats', '.1f', False),
        ]),
        ('Tackling & Run Support', [
            ('Tackle Grade', 'grades_tackle', 'defense_stats', '.1f', True),
            ('Tackles', 'tackles', 'defense_stats', ',', True),
            ('Stops', 'stops', 'defense_stats', ',', True),
            ('TFLs', 'tackles_for_loss', 'defense_stats', ',', True),
            ('Missed Tackle %', 'missed_tackle_rate', 'defense_stats', '.1f', False),
            ('Run Def Grade', 'grades_run_defense', 'defense_stats', '.1f', True),
        ]),
    ],
}


def _compute_percentile(value, series, higher_is_better=True):
    """Compute percentile of a value within a series."""
    if value is None or pd.isna(value) or series.empty:
        return None
    clean = series.dropna()
    if len(clean) == 0:
        return None
    if higher_is_better:
        return (clean < value).sum() / len(clean) * 100
    else:
        return (clean > value).sum() / len(clean) * 100


def _percentile_color(pct):
    """Return color based on percentile tier."""
    if pct is None:
        return '#6B7280'
    if pct >= 90:
        return '#15803D'  # Elite — green
    elif pct >= 75:
        return '#0369A1'  # Great — blue
    elif pct >= 50:
        return '#B45309'  # Average — amber
    elif pct >= 25:
        return '#6B7280'  # Below avg — gray
    else:
        return '#DC2626'  # Poor — red


def _percentile_label(pct):
    """Return label for percentile."""
    if pct is None:
        return ''
    if pct >= 95:
        return 'ELITE'
    elif pct >= 90:
        return 'TOP 10%'
    elif pct >= 75:
        return 'TOP 25%'
    elif pct >= 50:
        return ''
    elif pct >= 25:
        return ''
    else:
        return '▼'


def _format_val(val, fmt):
    """Format a stat value."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return '--'
    try:
        if fmt == ',':
            return f"{int(float(val)):,}"
        elif fmt.startswith('.'):
            return f"{float(val):{fmt}}"
        return str(val)
    except (ValueError, TypeError):
        return str(val)


def render_player_stats(player_stats: dict, position: str, percentile_data: dict = None):
    """
    Render player stats with percentile highlighting.

    player_stats: dict from load_player_stats (table_name -> list of row dicts)
    position: player position
    percentile_data: dict from load_position_percentiles (table_name -> DataFrame)
    """
    stat_groups = POSITION_STATS.get(position)
    if not stat_groups:
        st.info(f"No stat template defined for position: {position}")
        return

    for group_name, stats in stat_groups:
        st.markdown(f'<p class="section-header">{group_name} Stats</p>', unsafe_allow_html=True)

        # Build stat rows
        rows_html = []
        for label, key, table, fmt, higher_is_better in stats:
            # Get value from player stats
            table_data = player_stats.get(table, [])
            value = None
            if table_data:
                # Use most recent if multiple rows (shouldn't happen with season filter)
                row = table_data[0] if len(table_data) == 1 else table_data[-1]
                value = row.get(key)

            formatted = _format_val(value, fmt)

            # Compute percentile if we have comparison data
            pct = None
            if percentile_data and table in percentile_data and value is not None:
                pctl_df = percentile_data[table]
                if key in pctl_df.columns:
                    pct = _compute_percentile(
                        float(value), pd.to_numeric(pctl_df[key], errors='coerce'),
                        higher_is_better
                    )

            pct_color = _percentile_color(pct)
            pct_label = _percentile_label(pct)
            pct_display = f"{pct:.0f}th" if pct is not None else ''

            # Build row
            badge = ''
            if pct_label and pct is not None and pct >= 75:
                badge = (f'<span style="background:{pct_color}; color:#fff; font-size:0.6rem; '
                         f'font-weight:700; padding:0.1rem 0.4rem; border-radius:3px; '
                         f'letter-spacing:0.04em;">{pct_label}</span>')
            elif pct_label and pct is not None and pct < 25:
                badge = (f'<span style="color:#DC2626; font-size:0.75rem; font-weight:700;">'
                         f'{pct_label}</span>')

            # Build tooltip text for the stat row
            tooltip_parts = [f"{label}: {formatted}"]
            if pct is not None:
                tooltip_parts.append(f"{pct:.0f}th percentile among position group")
            if pct_label:
                tooltip_parts.append(pct_label)
            tooltip = " — ".join(tooltip_parts)

            row_idx = len(rows_html)
            row_bg = '#ffffff' if row_idx % 2 == 0 else '#f9fafb'
            rows_html.append(
                f'<tr title="{tooltip}" style="background:{row_bg};">'
                f'<td style="padding:0.4rem 0.75rem; color:#6b7280; font-size:0.85rem; border-bottom:1px solid #e5e7eb;">{label}</td>'
                f'<td style="padding:0.4rem 0.75rem; font-weight:700; font-size:0.95rem; color:{pct_color}; border-bottom:1px solid #e5e7eb; text-align:right;">{formatted}</td>'
                f'<td style="padding:0.4rem 0.75rem; font-size:0.75rem; color:#6b7280; border-bottom:1px solid #e5e7eb; text-align:center;">{pct_display}</td>'
                f'<td style="padding:0.4rem 0.75rem; border-bottom:1px solid #e5e7eb; text-align:right;">{badge}</td>'
                f'</tr>'
            )

        # Build table HTML with NO leading whitespace (Streamlit treats indented HTML as code blocks)
        table_html = (
            '<table style="width:100%; border-collapse:collapse; margin-bottom:1.5rem; background:#ffffff; border-radius:8px; border:1px solid #e5e7eb;">'
            '<thead>'
            '<tr style="background:#3a4553; border-bottom:2px solid #E8390E;">'
            '<th style="padding:0.5rem 0.75rem; text-align:left; color:#ffffff; font-size:11px; text-transform:uppercase; letter-spacing:0.08em; font-weight:600;">Stat</th>'
            '<th style="padding:0.5rem 0.75rem; text-align:right; color:#ffffff; font-size:11px; text-transform:uppercase; letter-spacing:0.08em; font-weight:600;">Value</th>'
            '<th style="padding:0.5rem 0.75rem; text-align:center; color:#ffffff; font-size:11px; text-transform:uppercase; letter-spacing:0.08em; font-weight:600;" title="Percentile rank among all eligible players at this position">Pctl</th>'
            '<th style="padding:0.5rem 0.75rem; text-align:right; color:#ffffff; font-size:11px; text-transform:uppercase; letter-spacing:0.08em; font-weight:600;"></th>'
            '</tr>'
            '</thead>'
            '<tbody>'
            + ''.join(rows_html) +
            '</tbody>'
            '</table>'
        )

        st.markdown(table_html, unsafe_allow_html=True)
