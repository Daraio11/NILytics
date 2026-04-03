"""
NILytics — CSV Export Functions
"""
import io
import streamlit as st
import pandas as pd
from app.components.card_front import fmt_money


def export_leaderboard_csv(df: pd.DataFrame, view_name: str, season: int):
    """Render a CSV download button for the leaderboard."""
    if df.empty:
        return

    export_df = df.copy()

    # Select and rename columns for export
    cols = ['name', 'position', 'school', 'conference', 'market', 'tier',
            'core_grade', 'output_score', 'adjusted_value']

    if 'market_value' in export_df.columns:
        cols.append('market_value')
    if 'opportunity_score' in export_df.columns:
        cols.append('opportunity_score')
    if 'trajectory_flag' in export_df.columns:
        cols.append('trajectory_flag')

    cols = [c for c in cols if c in export_df.columns]
    export_df = export_df[cols]

    rename_map = {
        'name': 'Player',
        'position': 'Position',
        'school': 'School',
        'conference': 'Conference',
        'market': 'Market',
        'tier': 'Tier',
        'core_grade': 'Core Grade',
        'output_score': 'Output Score',
        'adjusted_value': 'Player Value',
        'market_value': 'Market Value',
        'opportunity_score': 'Alpha (Opportunity)',
        'trajectory_flag': 'Trajectory',
    }
    export_df = export_df.rename(columns=rename_map)

    csv_buffer = io.StringIO()
    export_df.to_csv(csv_buffer, index=False)

    filename = f"nilytics_{view_name.lower().replace(' ', '_')}_{season}.csv"

    st.download_button(
        label="Export to CSV",
        data=csv_buffer.getvalue(),
        file_name=filename,
        mime="text/csv",
        use_container_width=True,
    )


def export_roster_csv(roster: dict, budget: int = 0):
    """Render a CSV download button for the GM Mode roster."""
    if not roster:
        return

    rows = []
    for pid, p in roster.items():
        rows.append({
            'Player': p.get('name', '?'),
            'Position': p.get('position', '?'),
            'School': p.get('school', '?'),
            'Conference': p.get('conference', ''),
            'Tier': p.get('tier', ''),
            'Core Grade': round(float(p.get('core_grade', 0)), 1) if pd.notna(p.get('core_grade')) else '',
            'Output Score': round(float(p.get('output_score', 0)), 1) if pd.notna(p.get('output_score')) else '',
            'Value': int(float(p.get('adjusted_value', 0))) if p.get('adjusted_value') else 0,
            'Market Value': int(float(p.get('market_value', 0))) if p.get('market_value') else 0,
            'Alpha': int(float(p.get('opportunity_score', 0))) if p.get('opportunity_score') else 0,
            'Trajectory': p.get('trajectory_flag', ''),
        })

    export_df = pd.DataFrame(rows).sort_values('Output Score', ascending=False)

    # Add summary row
    total_value = export_df['Value'].sum()
    total_mkt = export_df['Market Value'].sum()
    total_alpha = export_df['Alpha'].sum()
    summary = pd.DataFrame([{
        'Player': f'TOTAL ({len(export_df)} players)',
        'Position': '', 'School': '', 'Conference': '', 'Tier': '',
        'Core Grade': '', 'Output Score': '',
        'Value': total_value, 'Market Value': total_mkt, 'Alpha': total_alpha,
        'Trajectory': f'Budget: ${budget:,}' if budget else '',
    }])
    export_df = pd.concat([export_df, summary], ignore_index=True)

    csv_buffer = io.StringIO()
    export_df.to_csv(csv_buffer, index=False)

    st.download_button(
        label="Export Roster (CSV)",
        data=csv_buffer.getvalue(),
        file_name="nilytics_roster.csv",
        mime="text/csv",
        use_container_width=True,
    )


def export_player_card_csv(player: dict, scores_df: pd.DataFrame, signals_df: pd.DataFrame):
    """Render a CSV download button for a player's full history."""
    if scores_df.empty:
        return

    name = player.get('name', 'player')

    if not signals_df.empty:
        merged = scores_df.merge(
            signals_df[['season', 'market_value', 'opportunity_score', 'trajectory_flag']],
            on='season', how='left'
        )
    else:
        merged = scores_df.copy()

    export_cols = ['season', 'core_grade', 'output_score', 'tier', 'adjusted_value']
    if 'market_value' in merged.columns:
        export_cols.extend(['market_value', 'opportunity_score', 'trajectory_flag'])

    export_cols = [c for c in export_cols if c in merged.columns]
    export_df = merged[export_cols].sort_values('season', ascending=False)

    # Format season as int string
    export_df['season'] = export_df['season'].apply(lambda x: str(int(x)))

    rename_map = {
        'season': 'Season',
        'core_grade': 'Core Grade',
        'output_score': 'Output Score',
        'tier': 'Tier',
        'adjusted_value': 'Player Value',
        'market_value': 'Market Value',
        'opportunity_score': 'Alpha',
        'trajectory_flag': 'Trajectory',
    }
    export_df = export_df.rename(columns=rename_map)

    csv_buffer = io.StringIO()
    export_df.to_csv(csv_buffer, index=False)

    safe_name = name.replace(' ', '_').replace("'", "")
    filename = f"nilytics_{safe_name}_card.csv"

    st.download_button(
        label="Export Player Data (CSV)",
        data=csv_buffer.getvalue(),
        file_name=filename,
        mime="text/csv",
        use_container_width=True,
    )
