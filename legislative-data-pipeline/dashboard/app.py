"""Streamlit dashboard for Mexican legislative data analytics.

Provides three views:
  1. Legislative Overview — session activity, approval rates, participation trends
  2. Party Analysis — cohesion scores, voting alignment heatmap, coalition detection
  3. Legislator Profiles — attendance, voting record, party loyalty

Consumes data from DuckDB (local dev) or Snowflake (production).
"""

from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# -- Configuration --

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "legislative.duckdb"


@st.cache_resource
def get_connection() -> duckdb.DuckDBPyConnection:
    """Create a read-only DuckDB connection."""
    return duckdb.connect(str(DB_PATH), read_only=True)


def query(sql: str) -> pd.DataFrame:
    """Execute a query and return as DataFrame."""
    conn = get_connection()
    return conn.sql(sql).df()


# =============================================================================
# Page config
# =============================================================================

st.set_page_config(
    page_title="Legislativo MX — Dashboard",
    page_icon="🏛️",
    layout="wide",
)

st.title("🏛️ Mexican Legislative Analytics")
st.caption("Pipeline de datos legislativos — Portafolio de Mario Casanova")

# =============================================================================
# Sidebar — Filters
# =============================================================================

st.sidebar.header("Filters")

# Try to load data; show instructions if database is empty.
try:
    legislatures = query(
        "SELECT DISTINCT legislature FROM analytics.fact_vote ORDER BY legislature"
    )["legislature"].tolist()
except Exception:
    legislatures = [64, 65, 66]

selected_legislature = st.sidebar.selectbox(
    "Legislature",
    options=legislatures,
    index=len(legislatures) - 1 if legislatures else 0,
)

# =============================================================================
# Tab 1: Legislative Overview
# =============================================================================

tab1, tab2, tab3 = st.tabs([
    "📊 Legislative Overview",
    "🏛️ Party Analysis",
    "👤 Legislator Profiles",
])

with tab1:
    st.header("Legislative Overview")

    col1, col2, col3, col4 = st.columns(4)

    try:
        summary = query(f"""
            SELECT
                COUNT(*) AS total_votes,
                SUM(CASE WHEN is_approved THEN 1 ELSE 0 END) AS approved,
                AVG(approval_rate) AS avg_approval,
                AVG(total_present) AS avg_attendance
            FROM analytics.fact_vote_summary
            WHERE legislature = {selected_legislature}
        """)

        col1.metric("Total Votes", f"{summary['total_votes'].iloc[0]:,}")
        col2.metric("Approved", f"{summary['approved'].iloc[0]:,}")
        col3.metric("Avg Approval Rate", f"{summary['avg_approval'].iloc[0]:.1%}")
        col4.metric("Avg Attendance", f"{summary['avg_attendance'].iloc[0]:,.0f}")

        # Approval rate over time
        timeline = query(f"""
            SELECT
                date_key,
                approval_rate,
                is_approved
            FROM analytics.fact_vote_summary
            WHERE legislature = {selected_legislature}
                AND date_key IS NOT NULL
            ORDER BY date_key
        """)

        if not timeline.empty:
            fig = px.scatter(
                timeline,
                x="date_key",
                y="approval_rate",
                color="is_approved",
                title="Vote Approval Rates Over Time",
                labels={"date_key": "Date", "approval_rate": "Approval Rate"},
                color_discrete_map={True: "#2ecc71", False: "#e74c3c"},
            )
            fig.add_hline(y=0.5, line_dash="dash", line_color="gray", annotation_text="Simple majority")
            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.info(
            "No data available yet. Run the pipeline first:\n\n"
            "```bash\n"
            "cd legislative-data-pipeline\n"
            "python -m flows.legislative_pipeline\n"
            "```"
        )
        st.exception(e)

with tab2:
    st.header("Party Analysis")

    try:
        party_votes = query(f"""
            SELECT
                dl.party,
                fv.vote_cast,
                COUNT(*) AS cnt
            FROM analytics.fact_vote fv
            JOIN analytics.dim_legislator dl ON fv.legislator_key = dl.legislator_key
            WHERE fv.legislature = {selected_legislature}
            GROUP BY dl.party, fv.vote_cast
        """)

        if not party_votes.empty:
            fig = px.bar(
                party_votes,
                x="party",
                y="cnt",
                color="vote_cast",
                title="Voting Distribution by Party",
                barmode="group",
                color_discrete_map={
                    "FOR": "#2ecc71",
                    "AGAINST": "#e74c3c",
                    "ABSTAIN": "#f39c12",
                    "ABSENT": "#95a5a6",
                },
            )
            st.plotly_chart(fig, use_container_width=True)

        # Party cohesion
        cohesion = query(f"""
            SELECT
                dl.party,
                fv.vote_event_id,
                COUNT(*) AS n,
                SUM(CASE WHEN fv.vote_cast = 'FOR' THEN 1 ELSE 0 END)::FLOAT / COUNT(*) AS for_pct,
                GREATEST(
                    SUM(CASE WHEN fv.vote_cast = 'FOR' THEN 1 ELSE 0 END)::FLOAT / COUNT(*),
                    SUM(CASE WHEN fv.vote_cast = 'AGAINST' THEN 1 ELSE 0 END)::FLOAT / COUNT(*)
                ) AS cohesion
            FROM analytics.fact_vote fv
            JOIN analytics.dim_legislator dl ON fv.legislator_key = dl.legislator_key
            WHERE fv.legislature = {selected_legislature}
                AND fv.vote_cast != 'ABSENT'
            GROUP BY dl.party, fv.vote_event_id
            HAVING COUNT(*) >= 5
        """)

        if not cohesion.empty:
            avg_cohesion = cohesion.groupby("party")["cohesion"].mean().reset_index()
            avg_cohesion = avg_cohesion.sort_values("cohesion", ascending=True)

            fig = px.bar(
                avg_cohesion,
                x="cohesion",
                y="party",
                orientation="h",
                title="Average Party Cohesion (1.0 = perfectly unified)",
                labels={"cohesion": "Cohesion Score", "party": "Party"},
            )
            st.plotly_chart(fig, use_container_width=True)

    except Exception:
        st.info("Run the pipeline to populate party analysis data.")

with tab3:
    st.header("Legislator Profiles")

    try:
        legislators = query(f"""
            SELECT
                dl.full_name,
                dl.party,
                dl.state,
                COUNT(*) AS total_events,
                SUM(CASE WHEN fv.is_present THEN 1 ELSE 0 END) AS present,
                SUM(CASE WHEN fv.is_present THEN 1 ELSE 0 END)::FLOAT / COUNT(*) AS attendance_rate,
                SUM(CASE WHEN fv.vote_cast = 'FOR' THEN 1 ELSE 0 END)::FLOAT /
                    NULLIF(SUM(CASE WHEN fv.is_present THEN 1 ELSE 0 END), 0) AS affirmative_rate
            FROM analytics.fact_vote fv
            JOIN analytics.dim_legislator dl ON fv.legislator_key = dl.legislator_key
            WHERE fv.legislature = {selected_legislature}
            GROUP BY dl.full_name, dl.party, dl.state
            ORDER BY attendance_rate DESC
        """)

        if not legislators.empty:
            # Search filter
            search = st.text_input("Search legislator", "")
            if search:
                legislators = legislators[
                    legislators["full_name"].str.contains(search, case=False, na=False)
                ]

            st.dataframe(
                legislators.style.format({
                    "attendance_rate": "{:.1%}",
                    "affirmative_rate": "{:.1%}",
                }),
                use_container_width=True,
                height=500,
            )

            # Attendance distribution
            fig = px.histogram(
                legislators,
                x="attendance_rate",
                nbins=20,
                title="Distribution of Legislator Attendance Rates",
                labels={"attendance_rate": "Attendance Rate"},
            )
            st.plotly_chart(fig, use_container_width=True)

    except Exception:
        st.info("Run the pipeline to populate legislator data.")

# =============================================================================
# Footer
# =============================================================================

st.divider()
st.caption(
    "Data sources: dipMex (github.com/emagar/dipMex), "
    "diputados.gob.mx, INE datos abiertos. "
    "Built with Prefect, dbt, DuckDB, and Streamlit."
)
