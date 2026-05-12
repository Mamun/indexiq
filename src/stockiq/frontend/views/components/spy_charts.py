"""
SPY price/candle Plotly figure builders.

These functions are pure data-in / figure-out — no Streamlit calls — so they
can be tested independently and reused across panels without coupling to any
particular page.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def spy_candle_chart(
    df: pd.DataFrame,
    prev_close: float | None = None,
    vwap: pd.Series | None = None,
    max_pain: float | None = None,
    call_wall: float | None = None,
    put_wall: float | None = None,
    em_upper: float | None = None,
    em_lower: float | None = None,
    or_high: float | None = None,
    or_low: float | None = None,
    pdh: float | None = None,
    pdl: float | None = None,
    pivot: float | None = None,
    r1: float | None = None,
    s1: float | None = None,
    vwap_u1: pd.Series | None = None,
    vwap_l1: pd.Series | None = None,
    vwap_u2: pd.Series | None = None,
    vwap_l2: pd.Series | None = None,
) -> go.Figure:
    """Intraday candlestick + volume + VWAP bands + options-derived key levels.

    Options levels (Max Pain, Call/Put Wall, Expected Move band) are the primary
    differentiator over TradingView — they are rendered more prominently than
    standard price levels.
    """
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        row_heights=[0.80, 0.20], vertical_spacing=0.03,
    )

    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
        increasing_line_color="#22C55E", decreasing_line_color="#EF4444",
        name="SPY", showlegend=False,
    ), row=1, col=1)

    if vwap is not None:
        _add_vwap_bands(fig, df, vwap, vwap_u1, vwap_l1, vwap_u2, vwap_l2)

    _add_hlines(fig, or_high, or_low, pdh, pdl, pivot, r1, s1,
                prev_close, max_pain, call_wall, put_wall, em_upper, em_lower)

    if "Volume" in df.columns:
        bar_colors = ["#22C55E" if c >= o else "#EF4444"
                      for c, o in zip(df["Close"], df["Open"])]
        fig.add_trace(go.Bar(
            x=df.index, y=df["Volume"],
            marker_color=bar_colors, opacity=0.5,
            name="Volume", showlegend=False,
        ), row=2, col=1)

    fig.update_layout(
        template="plotly_dark",
        height=480,
        margin=dict(l=60, r=90, t=10, b=40),
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", y=1.04, x=0),
        yaxis=dict(title="Price", gridcolor="#1E293B"),
        yaxis2=dict(title="Volume", gridcolor="#1E293B"),
        hovermode="x unified",
    )
    return fig


def spy_sparkline(
    df: pd.DataFrame,
    vwap: "pd.Series | None" = None,
) -> go.Figure:
    """Compact close-price sparkline with optional VWAP — trajectory context only."""
    close_vals = df["Close"].dropna()
    y_min = float(close_vals.min()) if not close_vals.empty else 0.0
    y_max = float(close_vals.max()) if not close_vals.empty else 1.0
    if vwap is not None:
        vwap_vals = vwap.dropna()
        if not vwap_vals.empty:
            y_min = min(y_min, float(vwap_vals.min()))
            y_max = max(y_max, float(vwap_vals.max()))
    pad = (y_max - y_min) * 0.15 or y_min * 0.001 or 1.0

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.index, y=df["Close"],
        mode="lines",
        line=dict(color="#3B82F6", width=1.5),
        hovertemplate="%{x|%H:%M} &nbsp;<b>$%{y:,.2f}</b><extra></extra>",
        showlegend=False,
    ))
    if vwap is not None:
        fig.add_trace(go.Scatter(
            x=df.index, y=vwap,
            mode="lines",
            line=dict(color="#E879F9", width=1, dash="dash"),
            hovertemplate="VWAP $%{y:,.2f}<extra></extra>",
            showlegend=False,
        ))
    fig.update_layout(
        template="plotly_dark",
        height=160,
        margin=dict(l=50, r=10, t=6, b=30),
        xaxis=dict(gridcolor="#1E293B", showgrid=True, tickformat="%H:%M"),
        yaxis=dict(gridcolor="#1E293B", showgrid=True, range=[y_min - pad, y_max + pad]),
        hovermode="x unified",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


# ── Private helpers ────────────────────────────────────────────────────────────

def _add_vwap_bands(
    fig: go.Figure,
    df: pd.DataFrame,
    vwap: pd.Series,
    u1: pd.Series | None,
    l1: pd.Series | None,
    u2: pd.Series | None,
    l2: pd.Series | None,
) -> None:
    if u2 is not None:
        fig.add_trace(go.Scatter(x=df.index, y=u2, name="VWAP+2σ", mode="lines",
                                 line=dict(color="#E879F9", width=0.8, dash="dot"), opacity=0.4,
                                 hovertemplate="VWAP+2σ: <b>%{y:,.2f}</b><extra></extra>"), row=1, col=1)
    if l2 is not None:
        fig.add_trace(go.Scatter(x=df.index, y=l2, name="VWAP-2σ", mode="lines",
                                 line=dict(color="#E879F9", width=0.8, dash="dot"), opacity=0.4,
                                 fill="tonexty", fillcolor="rgba(232,121,249,0.03)",
                                 hovertemplate="VWAP-2σ: <b>%{y:,.2f}</b><extra></extra>"), row=1, col=1)
    if u1 is not None:
        fig.add_trace(go.Scatter(x=df.index, y=u1, name="VWAP+1σ", mode="lines",
                                 line=dict(color="#E879F9", width=1, dash="dot"), opacity=0.6,
                                 hovertemplate="VWAP+1σ: <b>%{y:,.2f}</b><extra></extra>"), row=1, col=1)
    if l1 is not None:
        fig.add_trace(go.Scatter(x=df.index, y=l1, name="VWAP-1σ", mode="lines",
                                 line=dict(color="#E879F9", width=1, dash="dot"), opacity=0.6,
                                 fill="tonexty", fillcolor="rgba(232,121,249,0.05)",
                                 hovertemplate="VWAP-1σ: <b>%{y:,.2f}</b><extra></extra>"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=vwap, name="VWAP", mode="lines",
                             line=dict(color="#E879F9", width=1.5, dash="dash"),
                             hovertemplate="VWAP: <b>%{y:,.2f}</b><extra></extra>"), row=1, col=1)


def _add_hlines(
    fig: go.Figure,
    or_high, or_low, pdh, pdl, pivot, r1, s1, prev_close,
    max_pain, call_wall, put_wall, em_upper=None, em_lower=None,
) -> None:
    _hl = fig.add_hline

    # ── Standard price levels (dim, secondary) ─────────────────────────────────
    if prev_close is not None:
        _hl(y=prev_close, row=1, col=1, line_dash="dot", line_color="#475569", line_width=1,
            annotation_text=f"Prev {prev_close:,.2f}", annotation_font_size=9,
            annotation_font_color="#475569", annotation_position="top right")
    if pdh is not None:
        _hl(y=pdh, row=1, col=1, line_dash="dash", line_color="#64748B", line_width=1,
            annotation_text=f"PDH {pdh:,.2f}", annotation_font_size=9,
            annotation_font_color="#64748B", annotation_position="top right")
    if pdl is not None:
        _hl(y=pdl, row=1, col=1, line_dash="dash", line_color="#64748B", line_width=1,
            annotation_text=f"PDL {pdl:,.2f}", annotation_font_size=9,
            annotation_font_color="#64748B", annotation_position="bottom right")
    if pivot is not None:
        _hl(y=pivot, row=1, col=1, line_dash="dot", line_color="#38BDF8", line_width=1,
            annotation_text=f"P {pivot:,.2f}", annotation_font_size=9,
            annotation_font_color="#38BDF8", annotation_position="top left")
    if r1 is not None:
        _hl(y=r1, row=1, col=1, line_dash="dot", line_color="#86EFAC", line_width=1,
            annotation_text=f"R1 {r1:,.2f}", annotation_font_size=9,
            annotation_font_color="#86EFAC", annotation_position="top left")
    if s1 is not None:
        _hl(y=s1, row=1, col=1, line_dash="dot", line_color="#FDA4AF", line_width=1,
            annotation_text=f"S1 {s1:,.2f}", annotation_font_size=9,
            annotation_font_color="#FDA4AF", annotation_position="bottom left")
    if or_high is not None:
        _hl(y=or_high, row=1, col=1, line_dash="solid", line_color="#FBBF24", line_width=1.2,
            annotation_text=f"OR H {or_high:,.2f}", annotation_font_size=9,
            annotation_font_color="#FBBF24", annotation_position="top left")
    if or_low is not None:
        _hl(y=or_low, row=1, col=1, line_dash="solid", line_color="#FBBF24", line_width=1.2,
            annotation_text=f"OR L {or_low:,.2f}", annotation_font_size=9,
            annotation_font_color="#FBBF24", annotation_position="bottom left")

    # ── Options-derived levels (bold, primary — unique vs TradingView) ─────────
    if em_upper is not None and em_lower is not None:
        # Shaded expected-move band drawn first so level lines render on top
        fig.add_hrect(y0=em_lower, y1=em_upper,
                      fillcolor="rgba(99,102,241,0.07)", line_width=0, row=1, col=1)
        _hl(y=em_upper, row=1, col=1, line_dash="dot", line_color="#818CF8", line_width=1.5,
            annotation_text=f"EM+ {em_upper:,.2f}", annotation_font_size=10,
            annotation_font_color="#818CF8", annotation_position="top right")
        _hl(y=em_lower, row=1, col=1, line_dash="dot", line_color="#818CF8", line_width=1.5,
            annotation_text=f"EM− {em_lower:,.2f}", annotation_font_size=10,
            annotation_font_color="#818CF8", annotation_position="bottom right")
    if put_wall is not None:
        _hl(y=put_wall, row=1, col=1, line_dash="solid", line_color="#EF4444", line_width=2,
            annotation_text=f"Put Wall  {put_wall:,.0f}", annotation_font_size=10,
            annotation_font_color="#EF4444", annotation_position="bottom left")
    if call_wall is not None:
        _hl(y=call_wall, row=1, col=1, line_dash="solid", line_color="#22C55E", line_width=2,
            annotation_text=f"Call Wall  {call_wall:,.0f}", annotation_font_size=10,
            annotation_font_color="#22C55E", annotation_position="top left")
    if max_pain is not None:
        _hl(y=max_pain, row=1, col=1, line_dash="dash", line_color="#F59E0B", line_width=2,
            annotation_text=f"Max Pain  {max_pain:,.0f}", annotation_font_size=10,
            annotation_font_color="#F59E0B", annotation_position="top left")


def _add_rsi_subplot(fig: go.Figure, df: pd.DataFrame, rsi_row: int) -> None:
    fig.add_trace(go.Scatter(
        x=df.index, y=df["RSI"], name="RSI (14)",
        line=dict(color="#A78BFA", width=1.5),
        hovertemplate="RSI: %{y:.1f}<extra></extra>",
    ), row=rsi_row, col=1)
    fig.add_hrect(y0=70, y1=100, fillcolor="rgba(239,68,68,0.08)", line_width=0, row=rsi_row, col=1)
    fig.add_hrect(y0=0,  y1=30,  fillcolor="rgba(34,197,94,0.08)",  line_width=0, row=rsi_row, col=1)
    for level, label, color in [(70, "OB 70", "#EF4444"), (50, "50", "#64748B"), (30, "OS 30", "#22C55E")]:
        fig.add_hline(y=level, line_dash="dot", line_color=color, line_width=1,
                      annotation_text=label, annotation_position="right",
                      annotation_font_size=9, row=rsi_row, col=1)
    fig.update_yaxes(title_text="RSI", range=[0, 100], row=rsi_row, col=1)
