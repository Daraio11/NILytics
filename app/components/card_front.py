"""
NILytics — Baseball Card Front Component
"""
import json


TIER_COLORS = {'T1': '#E8390E', 'T2': '#F97316', 'T3': '#3B82F6', 'T4': '#6B7280'}
TIER_TEXT   = {'T1': '#fff',    'T2': '#fff',    'T3': '#fff',    'T4': '#fff'}
TIER_LABELS = {'T1': 'TIER 1',  'T2': 'TIER 2',  'T3': 'TIER 3',  'T4': 'TIER 4'}

FLAG_STYLES = {
    'BREAKOUT_CANDIDATE': ('flag-breakout', 'BREAKOUT'),
    'HIDDEN_GEM': ('flag-hidden', 'HIDDEN GEM'),
    'REGRESSION_RISK': ('flag-regression', 'REGRESSION RISK'),
    'PORTAL_VALUE': ('flag-portal', 'PORTAL VALUE'),
    'EXPERIENCE_PREMIUM': ('flag-experience', 'EXPERIENCE'),
}

TRAJ_ICONS = {
    'BREAKOUT': ('&#9650;&#9650;', 'traj-breakout'),
    'UP': ('&#9650;', 'traj-up'),
    'DOWN': ('&#9660;', 'traj-down'),
    'STABLE': ('&#9654;', 'traj-stable'),
}

TRAJ_LABELS = {
    'BREAKOUT': 'Breakout',
    'UP': 'Trending Up',
    'DOWN': 'Trending Down',
    'STABLE': 'Stable',
}


def fmt_money(val):
    """Format as currency."""
    if val is None:
        return '--'
    try:
        v = int(float(val))
    except (ValueError, TypeError):
        return '--'
    if v >= 1_000_000:
        return f"${v / 1_000_000:.1f}M"
    elif v >= 1_000:
        return f"${v / 1_000:.0f}K"
    return f"${v:,}"


def render_card_front_st(player, scores, signals, st_module, skip_header=False, season=None, most_recent_season=None):
    """
    Render the front of a baseball card using native Streamlit components.

    player: dict with name, position, school, conference, market, class_year
    scores: dict with core_grade, output_score, tier, adjusted_value
    signals: dict with market_value, opportunity_score, trajectory_flag, flags
    st_module: the streamlit module (passed in to avoid import issues)
    skip_header: if True, skip rendering the name/tier/meta header (caller renders it)
    """
    st = st_module

    name = player.get('name', 'Unknown')
    pos = player.get('position', '?')
    school = player.get('school', '?')
    conference = player.get('conference', '')
    market = player.get('market', '')
    class_year = player.get('class_year', '')

    tier = scores.get('tier', 'T4')
    core_grade = scores.get('core_grade', 0)
    output_score = scores.get('output_score', 0)
    raw_adjusted = scores.get('adjusted_value', 0)

    raw_market = signals.get('market_value', 0)
    raw_opp = signals.get('opportunity_score', 0)

    # DB semantics (use directly — do NOT swap):
    #   adjusted_value = production worth (valuation.py)  → "Value"
    #   market_value   = market rate      (market_estimate.py) → "Mkt Value"
    #   opportunity_score = adjusted - market (positive = undervalued)
    has_signals = raw_market is not None and raw_market != 0
    if has_signals:
        adjusted_value = raw_adjusted   # "Value" = production worth
        market_value = raw_market       # "Mkt Value" = market rate
        opp_score = raw_opp             # positive = undervalued
    else:
        adjusted_value = raw_adjusted   # fallback: show what we have
        market_value = 0
        opp_score = 0
    trajectory = signals.get('trajectory_flag', 'STABLE')

    # Parse flags
    flags_raw = signals.get('flags', '[]')
    if isinstance(flags_raw, str):
        try:
            flag_list = json.loads(flags_raw)
        except (json.JSONDecodeError, TypeError):
            flag_list = []
    else:
        flag_list = flags_raw if flags_raw else []

    tier_color = TIER_COLORS.get(tier, '#d0d0d0')
    tier_text = TIER_TEXT.get(tier, '#666')
    tier_label = TIER_LABELS.get(tier, tier)
    traj_label = TRAJ_LABELS.get(trajectory, 'Stable')

    opp_val = int(float(opp_score)) if opp_score else 0

    # Meta line
    meta_parts = [pos, school]
    if conference:
        meta_parts.append(conference)
    if market:
        meta_parts.append(market)
    if class_year:
        meta_parts.append(str(class_year))

    # Flag chips as HTML (simple, inline)
    flag_html = ''
    for f in flag_list:
        css_class, label = FLAG_STYLES.get(f, ('flag-hidden', f))
        flag_html += f'<span class="flag-chip {css_class}">{label}</span> '

    # Trajectory color mapping
    traj_color_map = {'UP': '#16A34A', 'BREAKOUT': '#16A34A', 'DOWN': '#DC2626', 'STABLE': '#6B7280'}
    traj_color = traj_color_map.get(trajectory, '#6B7280')

    # Build card using container (native Streamlit)
    with st.container():
        # Top: Name + Tier badge inline, meta line, trajectory
        if not skip_header:
            st.markdown(
                f'<div style="display:flex; align-items:center; gap:12px; margin-bottom:4px;">'
                f'<span style="font-size:28px; font-weight:800; color:#1f2937;">{name}</span>'
                f'<span style="background:{tier_color};color:{tier_text};padding:3px 10px;font-size:12px;font-weight:700;border-radius:999px;">{tier_label}</span>'
                f'</div>'
                f'<p style="font-size:14px; color:#6b7280; margin:0 0 4px 0;">{" · ".join(meta_parts)}</p>'
                f'<span style="font-size:12px; color:{traj_color}; font-weight:600;">{traj_label}</span>',
                unsafe_allow_html=True
            )

        # Score badges row
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            st.metric("Core Grade", f"{float(core_grade):.1f}", help="Weighted composite of PFF position grades. See Methodology page for details.")
        with c2:
            st.metric("Output Score", f"{float(output_score):.1f}", help="Percentile rank (0-100) among eligible players at this position. See Methodology page for details.")
        with c3:
            st.metric("Value", fmt_money(adjusted_value), help="What the player's production justifies — based on output, visibility, and conference premium. See Methodology page for details.")
        with c4:
            st.metric("Mkt Value", fmt_money(market_value), help="What the NIL market actually pays — based on position, tier, and market. See Methodology page for details.")
        with c5:
            if opp_val > 50000:
                st.metric("Alpha", f"+{fmt_money(abs(opp_val))}", delta="Undervalued", help="Value minus Market — positive means undervalued (Moneyball pick). See Methodology page for details.")
            elif opp_val < -50000:
                st.metric("Alpha", f"-{fmt_money(abs(opp_val))}", delta="Overvalued", delta_color="inverse", help="Value minus Market — negative means overvalued. See Methodology page for details.")
            else:
                st.metric("Alpha", fmt_money(opp_val), delta="Fair Value", delta_color="off", help="Value minus Market — gap between production worth and market cost. See Methodology page for details.")

        # Alpha visual emphasis — softer styling with season context
        _season_label = f" ({int(season)})" if season else ""
        _is_historical = season and most_recent_season and int(season) < int(most_recent_season)
        _see_latest = (f' · <a href="#" style="color:#fbbf24;text-decoration:underline;font-size:12px;" '
                       f'title="Switch to {int(most_recent_season)}">See {int(most_recent_season)} →</a>'
                       if _is_historical else '')

        # Build inline flag badges for the valuation banner
        _flag_inline = ''
        if flag_html.strip():
            _flag_inline = f'<span style="margin-left:12px;">{flag_html.strip()}</span>'

        if opp_val > 50000:
            st.markdown(
                f'<div style="background:#f0fdf4; border-left:4px solid #16a34a; border-radius:0 6px 6px 0; '
                f'padding:8px 16px; margin-top:8px; display:flex; align-items:center; flex-wrap:wrap;">'
                f'<span style="color:#15803d; font-weight:700; font-size:13px;">Significantly Undervalued{_season_label}</span>'
                f'{_flag_inline}'
                f'</div>',
                unsafe_allow_html=True
            )
        elif opp_val < -50000:
            if _is_historical:
                st.markdown(
                    f'<div style="background:#fef9c3; border-left:4px solid #eab308; border-radius:0 6px 6px 0; '
                    f'padding:8px 16px; margin-top:8px; display:flex; align-items:center; flex-wrap:wrap;">'
                    f'<span style="color:#92400e; font-weight:700; font-size:13px;">Overvalued{_season_label}</span>'
                    f'{_see_latest}{_flag_inline}'
                    f'</div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f'<div style="background:#fef2f2; border-left:4px solid #dc2626; border-radius:0 6px 6px 0; '
                    f'padding:8px 16px; margin-top:8px; display:flex; align-items:center; flex-wrap:wrap;">'
                    f'<span style="color:#991b1b; font-weight:700; font-size:13px;">Overvalued{_season_label}</span>'
                    f'{_flag_inline}'
                    f'</div>',
                    unsafe_allow_html=True
                )
        elif flag_html.strip():
            # Neither significantly over/under valued but has flags — show them standalone
            st.markdown(flag_html, unsafe_allow_html=True)


# Keep the old function name as alias for backward compat
def render_card_front(player, scores, signals):
    """Legacy HTML version — deprecated, use render_card_front_st instead."""
    return ""
