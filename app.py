import streamlit as st

from seo import inject_seo

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="IndexIQ — Free S&P 500 Technical Analysis & Screener",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "Free stock technical analysis: moving averages, RSI, Fibonacci retracement, "
                 "short squeeze scanner, bounce radar, and Munger quality watchlist."
    },
)

# ── SEO metadata ──────────────────────────────────────────────────────────────
inject_seo()

# ── Navigation ────────────────────────────────────────────────────────────────
pages = [
    st.Page("views/spy_dashboard.py",   title="SPY Live",               icon="📈", url_path="spy",          default=True),
    st.Page("views/spy_gap_table.py",   title="SPY Gap Table",          icon="📋", url_path="spy-gaps"),
    st.Page("views/analyzer.py",        title="Stock Analyzer",         icon="🔬", url_path="analyzer"),
    st.Page("views/screener.py",        title="Weekly/Monthly Screener",icon="📊", url_path="screener"),
    st.Page("views/bounce_radar.py",    title="Bounce Radar",           icon="📡", url_path="bounce-radar"),
    st.Page("views/squeeze_scanner.py", title="Squeeze Scanner",        icon="🔥", url_path="squeeze"),
    st.Page("views/strong_buy.py",      title="Strong Buy",             icon="💎", url_path="strong-buy"),
    st.Page("views/strong_sell.py",     title="Strong Sell",            icon="🔻", url_path="strong-sell"),
    st.Page("views/munger_strategy.py", title="Munger Watchlist",       icon="🎩", url_path="munger"),
    st.Page("views/about.py",           title="About",                  icon="ℹ️",  url_path="about"),
]

pg = st.navigation(pages)

# Hide utility pages (shareable embeds) from the sidebar nav
st.markdown("""
<style>
[data-testid="stSidebarNav"] a[href$="/spy-gaps"],
[data-testid="stSidebarNavLink"] a[href$="/spy-gaps"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.caption("Data sourced from Yahoo Finance · Real-time")

pg.run()
