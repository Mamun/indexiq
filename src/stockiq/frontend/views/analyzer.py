"""Stock Analyzer page — thin orchestrator that composes panels."""

import pandas as pd
import streamlit as st

from stockiq.backend.services.analyzer_service import (
    get_company_display_name,
    get_stock_crosses,
    get_stock_df,
    get_stock_fibonacci,
    get_stock_gaps,
    get_stock_signal,
    get_ticker_fundamentals,
    search_stocks,
)
from stockiq.frontend.theme import BG, DN, MUT, NEU, SEP, UP, VAL
from stockiq.frontend.views.components.charts import build_chart
from stockiq.frontend.views.components.gap_table import render_gap_table
from stockiq.frontend.views.panels.analyzer_fundamentals import render_fundamentals_panel
from stockiq.frontend.views.panels.analyzer_signals import (
    render_buying_pressure,
    render_signal_analysis,
)

_PERIODS = {"1M": 30, "3M": 90, "6M": 180, "1Y": 365, "2Y": 730, "5Y": 1825}
_DEFAULT_PERIOD = "1Y"


def render_analyzer_tab() -> None:
    st.title("🔬 Stock Analyzer")

    params     = st.query_params
    url_ticker = params.get("tic", "").upper().strip()
    url_period = params.get("period", _DEFAULT_PERIOD)
    url_rsi    = params.get("rsi", "1") != "0"

    if url_ticker and st.session_state.ticker_val != url_ticker:
        st.session_state.ticker_val = url_ticker

    # ── Search + Ticker + Actions (single row) ───────────────────────────────
    col_q, col_t, col_srch, col_analyze = st.columns([3, 2, 1, 1], vertical_alignment="bottom")
    search_query = col_q.text_input(
        "company_search",
        placeholder="Company name, e.g. Microsoft…",
        label_visibility="collapsed",
    )
    ticker = col_t.text_input(
        "Ticker Symbol", value=st.session_state.ticker_val, max_chars=10,
        placeholder="Ticker, e.g. MSFT",
    ).upper().strip()
    search_clicked = col_srch.button("Search", width="stretch")
    analyze_btn = col_analyze.button("Analyze", width="stretch", type="primary")

    if search_clicked:
        if search_query.strip():
            with st.spinner("Searching…"):
                st.session_state.search_results = search_stocks(search_query.strip())
        else:
            st.session_state.search_results = []

    if st.session_state.search_results:
        labels = [
            f"{r['symbol']}  —  {r['name']}  ({r['exchange']})"
            for r in st.session_state.search_results
        ]
        choice_idx = st.selectbox(
            "Select a company", range(len(labels)), format_func=lambda i: labels[i]
        )
        st.session_state.ticker_val = st.session_state.search_results[choice_idx]["symbol"]
        ticker = st.session_state.ticker_val
    elif search_query and not st.session_state.search_results:
        st.caption("No matches found — try a different name.")

    auto_analyze = bool(url_ticker) and url_ticker != st.session_state.get("analyzer_ticker")

    if not (analyze_btn or auto_analyze or ticker):
        st.info("Enter a ticker symbol above and click **Analyze**.")
        return
    if not ticker:
        st.warning("Enter a ticker symbol above.")
        return

    # ── Fetch & cache data ────────────────────────────────────────────────────
    if analyze_btn or auto_analyze or st.session_state.get("analyzer_ticker") != ticker:
        with st.spinner(f"Fetching data for **{ticker}**…"):
            try:
                raw = get_stock_df(ticker)
            except Exception as e:
                st.error(f"Failed to download data: {e}")
                return
        if raw.empty:
            st.error(
                f"No data found for **{ticker}**. "
                "Use the Search box above to find the correct symbol."
            )
            return
        if len(raw) < 2:
            st.error(f"**{ticker}** returned insufficient price data.")
            return

        st.session_state.analyzer_df           = raw
        st.session_state.analyzer_ticker       = ticker
        st.session_state.analyzer_company      = get_company_display_name(ticker)
        st.session_state.analyzer_fundamentals = get_ticker_fundamentals(ticker)
        st.query_params["tic"] = ticker

    df           = st.session_state.analyzer_df
    company_name = st.session_state.analyzer_company
    sig          = get_stock_signal(df)
    latest, prev = sig["latest"], sig["prev"]
    score, signal_label, signal_color = sig["score"], sig["label"], sig["color"]

    price      = float(latest["Close"])
    prev_close = float(prev["Close"])
    chg        = price - prev_close
    chg_pct    = chg / prev_close * 100
    chg_clr    = UP if chg >= 0 else DN
    arrow      = "▲" if chg >= 0 else "▼"

    last_252 = df.tail(252)
    w52_high = float(last_252["High"].max())
    w52_low  = float(last_252["Low"].min())

    rsi_val = float(latest.get("RSI",   0) or 0)
    ma200   = float(latest.get("MA200", 0) or 0)
    vol_now = float(latest.get("Volume", 0) or 0)
    vol_avg = (
        float(df["Volume"].rolling(20).mean().iloc[-1])
        if "Volume" in df.columns else 0.0
    )

    # ── Section 1: Header ────────────────────────────────────────────────────
    h_name, h_price, h_signal = st.columns([4, 2, 2])
    with h_name:
        st.markdown(
            f'<div style="padding-top:6px">'
            f'<div style="font-size:1.4rem;font-weight:700;color:{VAL}">{company_name}</div>'
            f'<div style="font-size:0.9rem;color:{MUT};margin-top:2px">{ticker}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with h_price:
        st.markdown(
            f'<div style="padding-top:4px">'
            f'<div style="font-size:2rem;font-weight:800;color:{VAL}">${price:,.2f}</div>'
            f'<div style="font-size:0.95rem;color:{chg_clr};margin-top:2px">'
            f'{arrow} {abs(chg):.2f} &nbsp;({chg_pct:+.2f}%)'
            f'</div></div>',
            unsafe_allow_html=True,
        )
    with h_signal:
        st.markdown(
            f'<div style="background:{signal_color};border-radius:8px;padding:12px 8px;'
            f'text-align:center">'
            f'<div style="font-size:0.85rem;font-weight:800;color:#fff;'
            f'letter-spacing:.03em">{signal_label}</div>'
            f'<div style="font-size:0.78rem;color:rgba(255,255,255,.8);margin-top:2px">'
            f'Score {score:+d}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    st.markdown("<div style='margin-top:12px'></div>", unsafe_allow_html=True)

    # ── Section 2: Quick stats ────────────────────────────────────────────────
    qs1, qs2, qs3, qs4 = st.columns(4)
    _stat = _stat_card   # local alias for brevity

    with qs1:
        if w52_high > w52_low:
            pos_pct   = (price - w52_low) / (w52_high - w52_low) * 100
            range_clr = UP if pos_pct >= 50 else DN
            qs1.markdown(
                _stat("52W Range", f"{pos_pct:.1f}% of range",
                      f"${w52_low:,.2f} — ${w52_high:,.2f}", range_clr),
                unsafe_allow_html=True,
            )
    with qs2:
        if rsi_val:
            rsi_clr = DN if rsi_val >= 70 else UP if rsi_val <= 30 else NEU
            rsi_lbl = "Overbought" if rsi_val >= 70 else "Oversold" if rsi_val <= 30 else "Neutral"
            qs2.markdown(_stat("RSI (14)", f"{rsi_val:.1f}", rsi_lbl, rsi_clr), unsafe_allow_html=True)
    with qs3:
        if ma200:
            diff200   = (price - ma200) / ma200 * 100
            ma200_clr = UP if diff200 >= 0 else DN
            qs3.markdown(
                _stat("vs MA 200", f"{diff200:+.1f}%", f"MA200 at ${ma200:,.2f}", ma200_clr),
                unsafe_allow_html=True,
            )
    with qs4:
        if vol_now and vol_avg:
            vol_vs  = (vol_now / vol_avg - 1) * 100
            vol_clr = UP if vol_vs >= 20 else DN if vol_vs <= -20 else MUT
            qs4.markdown(
                _stat("Volume", f"{vol_now/1e6:.1f}M", f"{vol_vs:+.0f}% vs 20D avg", vol_clr),
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # ── Section 3: Fundamentals ───────────────────────────────────────────────
    render_fundamentals_panel(st.session_state.analyzer_fundamentals, price)
    st.markdown("---")

    # ── Section 4: Chart ──────────────────────────────────────────────────────
    valid_period = url_period if url_period in _PERIODS else _DEFAULT_PERIOD
    period_col, rsi_col = st.columns([6, 1])
    with period_col:
        selected_period = st.radio(
            "period_selector", list(_PERIODS), horizontal=True,
            index=list(_PERIODS).index(valid_period), label_visibility="collapsed",
        )
    show_rsi = rsi_col.checkbox("RSI", value=url_rsi)

    st.query_params["tic"]    = ticker
    st.query_params["period"] = selected_period
    st.query_params["rsi"]    = "1" if show_rsi else "0"

    cutoff     = pd.Timestamp.today() - pd.Timedelta(days=_PERIODS[selected_period])
    display_df = df[df.index >= cutoff].copy()
    if len(display_df) < 2:
        st.warning(f"Not enough data for the **{selected_period}** window. Try a longer period.")
        return

    fib = get_stock_fibonacci(display_df)
    golden, death = get_stock_crosses(display_df)
    fig = build_chart(display_df, fib, ticker,
                      show_vol=True, show_fib=False,
                      show_patterns=True, show_rsi=show_rsi,
                      golden_dates=golden, death_dates=death)
    st.plotly_chart(fig, width="stretch")
    st.markdown("---")

    # ── Section 5+6: Signals + BX + Key Levels ───────────────────────────────
    sig_col, bx_col, lvl_col = st.columns([3, 2, 2])
    with sig_col:
        render_signal_analysis(sig)
    with bx_col:
        render_buying_pressure(df)
    with lvl_col:
        _render_key_levels(latest, fib, price)

    st.markdown("---")

    # ── Section 7: Gap history ────────────────────────────────────────────────
    st.markdown("#### Gap History")
    last    = display_df.iloc[-1]
    gaps_df = get_stock_gaps(
        display_df, {"day_high": float(last["High"]), "day_low": float(last["Low"])}
    )
    if "RSI" in display_df.columns:
        gaps_df = gaps_df.copy()
        rsi_dedup         = display_df["RSI"][~display_df.index.duplicated(keep="last")]
        gaps_df["RSI"]    = rsi_dedup.reindex(gaps_df.index)
    render_gap_table(gaps_df, show_rsi=True)


# ── Key levels panel (always-visible right column below chart) ────────────────

def _render_key_levels(latest, fib: dict, price: float) -> None:
    st.markdown("**Key Price Levels**")
    st.markdown(
        f'<div style="font-size:11px;color:{MUT};text-transform:uppercase;'
        f'letter-spacing:.05em;margin-bottom:4px">Moving Averages</div>',
        unsafe_allow_html=True,
    )
    for name, key in [("MA 5", "MA5"), ("MA 20", "MA20"), ("MA 50", "MA50"),
                      ("MA 100", "MA100"), ("MA 200", "MA200"), ("MA 200W", "MA200W")]:
        val = float(latest.get(key, 0) or 0)
        if val:
            diff = (price - val) / val * 100
            clr  = UP if diff >= 0 else DN
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;'
                f'padding:3px 0;border-bottom:1px solid {SEP}">'
                f'<span style="color:{MUT};font-size:0.85rem">{name}</span>'
                f'<span style="font-size:0.85rem">${val:,.2f}&nbsp;'
                f'<span style="color:{clr}">{diff:+.1f}%</span></span></div>',
                unsafe_allow_html=True,
            )
    st.markdown(
        f'<div style="font-size:11px;color:{MUT};text-transform:uppercase;'
        f'letter-spacing:.05em;margin:10px 0 4px">Fibonacci</div>',
        unsafe_allow_html=True,
    )
    for name, val in sorted(fib.items(), key=lambda x: x[1], reverse=True):
        above = price >= val
        clr   = UP if above else DN
        mark  = "▲" if above else "▼"
        st.markdown(
            f'<div style="display:flex;justify-content:space-between;'
            f'padding:3px 0;border-bottom:1px solid {SEP}">'
            f'<span style="color:{MUT};font-size:0.85rem">Fib {name}</span>'
            f'<span style="font-size:0.85rem">${val:,.2f}&nbsp;'
            f'<span style="color:{clr}">{mark}</span></span></div>',
            unsafe_allow_html=True,
        )


# ── HTML helper (local, identical pattern to analyzer_fundamentals._stat_card) ─

def _stat_card(label: str, value: str, sub: str = "", sub_color: str | None = None) -> str:
    sub_html = (
        f'<div style="font-size:11px;color:{sub_color or MUT};margin-top:3px">{sub}</div>'
        if sub else ""
    )
    return (
        f'<div style="background:{BG};border:1px solid {SEP};border-radius:8px;padding:14px 16px">'
        f'<div style="font-size:11px;color:{MUT};text-transform:uppercase;'
        f'letter-spacing:.05em;margin-bottom:4px">{label}</div>'
        f'<div style="font-size:19px;font-weight:700;color:{VAL}">{value}</div>'
        f'{sub_html}'
        f'</div>'
    )


# ── Session state init & entry point ──────────────────────────────────────────
for _k, _v in [
    ("search_results", []),
    ("ticker_val", "MSFT"),
    ("analyzer_df", None),
    ("analyzer_ticker", None),
    ("analyzer_company", None),
    ("analyzer_fundamentals", {}),
]:
    if _k not in st.session_state:
        st.session_state[_k] = _v

render_analyzer_tab()
