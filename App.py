import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import norm

st.set_page_config(page_title="NBL Quant Edge Model", page_icon="🏀", layout="wide")

# ---------------------------------------------------------
# 1. TEAM BASELINES (Initial Anchors)
# ---------------------------------------------------------
DEFAULT_TEAMS = {
    "Sydney Kings": {"pace": 78.8, "ortg": 115.4, "drtg": 110.2},
    "Perth Wildcats": {"pace": 77.5, "ortg": 114.8, "drtg": 112.0},
    "Melbourne United": {"pace": 74.6, "ortg": 113.2, "drtg": 107.5},
    "Tasmania JackJumpers": {"pace": 71.2, "ortg": 109.8, "drtg": 106.8},
    "Illawarra Hawks": {"pace": 78.2, "ortg": 114.5, "drtg": 112.8},
    "Adelaide 36ers": {"pace": 77.0, "ortg": 113.0, "drtg": 115.5},
    "Brisbane Bullets": {"pace": 75.1, "ortg": 109.5, "drtg": 113.2},
    "Cairns Taipans": {"pace": 79.2, "ortg": 108.6, "drtg": 114.8},
    "South East Melbourne Phoenix": {"pace": 76.8, "ortg": 111.4, "drtg": 116.2},
    "New Zealand Breakers": {"pace": 73.5, "ortg": 110.5, "drtg": 109.8},
}

teams_list = sorted(list(DEFAULT_TEAMS.keys()))

st.title("🏀 NBL Quantitative Edge Terminal")
st.caption("Custom Pace & Possession Engine | 1% Flat Staking Rule")

# ---------------------------------------------------------
# 2. MATCHUP SELECTION
# ---------------------------------------------------------
col_m1, col_m2 = st.columns(2)
with col_m1:
    home_team = st.selectbox("🏠 Home Team", teams_list, index=4)  # Illawarra
with col_m2:
    away_team = st.selectbox("✈️ Away Team", [t for t in teams_list if t != home_team], index=3)  # Tasmania

# ---------------------------------------------------------
# 3. SIDEBAR: LIVE TEAM-SPECIFIC OVERRIDES & CONSTANTS
# ---------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Bankroll Settings")
    bankroll = st.number_input("Total Bankroll ($AUD)", min_value=100.0, value=2000.0, step=100.0)
    flat_pct = st.slider("Flat Stake Percentage", 0.5, 2.0, 1.0, 0.1) / 100.0
    unit_stake = bankroll * flat_pct
    st.metric("1-Unit Stake", f"${unit_stake:.2f}")

    st.divider()
    st.header("🎯 Team Calibration (Current Season)")
    st.caption("Adjust these if teams are playing faster/slower this season")
    
    st.subheader(f"🏠 {home_team}")
    h_pace_input = st.number_input(f"{home_team} Pace (Poss/40m)", value=DEFAULT_TEAMS[home_team]["pace"], step=0.5)
    h_ortg_input = st.number_input(f"{home_team} Off Rating (Pts/100)", value=DEFAULT_TEAMS[home_team]["ortg"], step=0.5)
    h_drtg_input = st.number_input(f"{home_team} Def Rating (Pts/100)", value=DEFAULT_TEAMS[home_team]["drtg"], step=0.5)

    st.subheader(f"✈️ {away_team}")
    a_pace_input = st.number_input(f"{away_team} Pace (Poss/40m)", value=DEFAULT_TEAMS[away_team]["pace"], step=0.5)
    a_ortg_input = st.number_input(f"{away_team} Off Rating (Pts/100)", value=DEFAULT_TEAMS[away_team]["ortg"], step=0.5)
    a_drtg_input = st.number_input(f"{away_team} Def Rating (Pts/100)", value=DEFAULT_TEAMS[away_team]["drtg"], step=0.5)

    st.divider()
    st.header("🌐 League Benchmarks")
    league_pace = st.number_input("League Avg Pace", value=76.2, step=0.1)
    league_ortg = st.number_input("League Avg Efficiency", value=112.5, step=0.1)
    hca_margin = st.number_input("Home Court Advantage (Pts)", value=2.4, step=0.1)
    totals_sigma = st.number_input("Totals Standard Dev (σ)", value=12.2, step=0.1)
    spread_sigma = st.number_input("Spread Standard Dev (σ)", value=10.5, step=0.1)
    min_edge_pct = st.slider("Min Edge Required (EV %)", 1.0, 10.0, 3.5, 0.5) / 100.0

# ---------------------------------------------------------
# 4. CALCULATION ENGINE
# ---------------------------------------------------------
# Expected Matchup Pace
exp_pace = league_pace * (h_pace_input / league_pace) * (a_pace_input / league_pace)

# Efficiency Adjustments
hca_eff_boost = (hca_margin * 100) / exp_pace
exp_home_eff = ((h_ortg_input * a_drtg_input) / league_ortg) + hca_eff_boost
exp_away_eff = ((a_ortg_input * h_drtg_input) / league_ortg) - hca_eff_boost

proj_home_score = exp_pace * (exp_home_eff / 100.0)
proj_away_score = exp_pace * (exp_away_eff / 100.0)
proj_total = proj_home_score + proj_away_score
proj_margin = proj_home_score - proj_away_score

st.info(f"📊 **Calculated Matchup Pace:** **{exp_pace:.1f} possessions** | "
        f"**Projected Score:** {home_team} **{proj_home_score:.1f}** — **{proj_away_score:.1f}** {away_team} | "
        f"**Projected Total:** **{proj_total:.1f} pts**")

# ---------------------------------------------------------
# 5. MARKET INPUTS
# ---------------------------------------------------------
st.subheader("📥 Enter Bookmaker Lines")
tab1, tab2, tab3 = st.tabs(["1. Over / Under", "2. Point Spread", "3. Head to Head"])

with tab1:
    c1, c2, c3 = st.columns(3)
    book_total = c1.number_input("Bookie Total Line", value=188.5, step=0.5)
    odds_over = c2.number_input("Over Odds", value=1.90, step=0.01)
    odds_under = c3.number_input("Under Odds", value=1.90, step=0.01)

with tab2:
    c4, c5, c6 = st.columns(3)
    book_spread = c4.number_input(f"{home_team} Line", value=-3.5, step=0.5)
    odds_home_spread = c5.number_input(f"{home_team} Spread Odds", value=1.91, step=0.01)
    odds_away_spread = c6.number_input(f"{away_team} Spread Odds", value=1.91, step=0.01)

with tab3:
    c7, c8 = st.columns(2)
    odds_home_ml = c7.number_input(f"{home_team} Win Odds", value=1.65, step=0.01)
    odds_away_ml = c8.number_input(f"{away_team} Win Odds", value=2.25, step=0.01)

# ---------------------------------------------------------
# 6. SIGNALS & EXPECTED VALUE
# ---------------------------------------------------------
st.divider()
st.subheader("🎯 Edge Verdict")

r1, r2, r3 = st.columns(3)

with r1:
    st.write("#### 🏀 Total Points")
    prob_over = 1.0 - norm.cdf(book_total + 0.5, loc=proj_total, scale=totals_sigma)
    prob_under = norm.cdf(book_total - 0.5, loc=proj_total, scale=totals_sigma)
    ev_over = (prob_over * odds_over) - 1.0
    ev_under = (prob_under * odds_under) - 1.0

    st.write(f"Fair Total: **{proj_total:.1f}**")
    st.write(f"Prob: Over `{prob_over*100:.1f}%` | Under `{prob_under*100:.1f}%`")
    st.write(f"EV: Over `{ev_over*100:+.1f}%` | Under `{ev_under*100:+.1f}%`")

    if ev_over > min_edge_pct and ev_over > ev_under:
        st.success(f"**BET: OVER {book_total}**\n\nStake: **${unit_stake:.2f}** | Edge: **+{ev_over*100:.1f}%**")
    elif ev_under > min_edge_pct and ev_under > ev_over:
        st.success(f"**BET: UNDER {book_total}**\n\nStake: **${unit_stake:.2f}** | Edge: **+{ev_under*100:.1f}%**")
    else:
        st.warning("**PASS (NO BET)**\n\nNo edge above threshold.")

with r2:
    st.write("#### 🛡️ Point Spread")
    z_spread = (proj_margin - (-book_spread)) / spread_sigma
    prob_home_cover = norm.cdf(z_spread)
    prob_away_cover = 1.0 - prob_home_cover
    ev_home_spread = (prob_home_cover * odds_home_spread) - 1.0
    ev_away_spread = (prob_away_cover * odds_away_spread) - 1.0

    st.write(f"Fair Margin: **{proj_margin:+.1f}**")
    st.write(f"Prob: Home `{prob_home_cover*100:.1f}%` | Away `{prob_away_cover*100:.1f}%`")
    st.write(f"EV: Home `{ev_home_spread*100:+.1f}%` | Away `{ev_away_spread*100:.1f}%`")

    if ev_home_spread > min_edge_pct and ev_home_spread > ev_away_spread:
        st.success(f"**BET: {home_team} ({book_spread:+.1f})**\n\nStake: **${unit_stake:.2f}** | Edge: **+{ev_home_spread*100:.1f}%**")
    elif ev_away_spread > min_edge_pct and ev_away_spread > ev_home_spread:
        st.success(f"**BET: {away_team} ({-book_spread:+.1f})**\n\nStake: **${unit_stake:.2f}** | Edge: **+{ev_away_spread*100:.1f}%**")
    else:
        st.warning("**PASS (NO BET)**\n\nNo edge above threshold.")

with r3:
    st.write("#### 🏆 Moneyline (H2H)")
    prob_home_win = norm.cdf(proj_margin / spread_sigma)
    prob_away_win = 1.0 - prob_home_win
    ev_home_ml = (prob_home_win * odds_home_ml) - 1.0
    ev_away_ml = (prob_away_win * odds_away_ml) - 1.0

    st.write(f"Win Prob: Home `{prob_home_win*100:.1f}%` | Away `{prob_away_win*100:.1f}%`")
    st.write(f"EV: Home `{ev_home_ml*100:+.1f}%` | Away `{ev_away_ml*100:+.1f}%`")

    if ev_home_ml > min_edge_pct and ev_home_ml > ev_away_ml:
        st.success(f"**BET: {home_team} H2H**\n\nStake: **${unit_stake:.2f}** | Edge: **+{ev_home_ml*100:.1f}%**")
    elif ev_away_ml > min_edge_pct and ev_away_ml > ev_home_ml:
        st.success(f"**BET: {away_team} H2H**\n\nStake: **${unit_stake:.2f}** | Edge: **+{ev_away_ml*100:.1f}%**")
    else:
        st.warning("**PASS (NO BET)**\n\nNo edge above threshold.")
