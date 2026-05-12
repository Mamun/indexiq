"""
SPY Trade Idea card — strategy suggestion rendered from options data.

Public API:
  render_spy_trade_idea(suggestion, exp_label, exp_iso, show_why)
"""

from __future__ import annotations

import urllib.parse

import streamlit as st


def _share_url(exp_iso: str = "") -> str:
    try:
        parsed = urllib.parse.urlparse(st.context.url)
        url = f"{parsed.scheme}://{parsed.netloc}/spy-trade-idea"
        if exp_iso:
            url += f"?exp={exp_iso}"
        return url
    except Exception:
        return f"/spy-trade-idea?exp={exp_iso}" if exp_iso else "/spy-trade-idea"


def render_spy_trade_idea(
    suggestion: dict | None,
    exp_label: str = "",
    exp_iso: str = "",
    show_why: bool = True,
) -> None:
    """Render the SPY strategy suggestion card with optional rationale panel."""
    if not suggestion:
        return

    strat_clr = suggestion["strat_color"]
    dir_clr   = suggestion["dir_color"]
    conf_clr  = suggestion["conf_color"]
    vb_clr    = suggestion["vb_color"]
    em_range  = (
        f'${suggestion["em_low"]:,.2f} – ${suggestion["em_high"]:,.2f}'
        if suggestion["em_low"] and suggestion["em_high"] else "—"
    )
    strike_str = suggestion["strike_label"] or "—"

    # Context-aware title derived from DTE
    if exp_label:
        dte_part = exp_label.split("(")[-1].rstrip(")").strip() if "(" in exp_label else ""
        try:
            dte_num = int(dte_part.rstrip("d"))
        except (ValueError, AttributeError):
            dte_num = 7
        if dte_num == 0:
            setup_title = f"Today's Setup · {exp_label}"
        elif dte_num <= 2:
            setup_title = f"Near-Term Setup · {exp_label}"
        elif dte_num <= 9:
            setup_title = f"This Week's Setup · {exp_label}"
        elif dte_num <= 35:
            setup_title = f"This Month's Setup · {exp_label}"
        else:
            setup_title = f"Longer-Term Setup · {exp_label}"
    else:
        setup_title = "This Week's Setup"

    rationale_html = "".join(
        f'<div style="font-size:0.77rem;color:#94A3B8;margin-bottom:3px">◆ {r}</div>'
        for r in suggestion["rationale"]
    )

    # Reference levels
    ref_target  = suggestion.get("ref_target")
    ref_source  = suggestion.get("ref_source", "—")
    ref_pct     = suggestion.get("ref_pct")
    stop_level  = suggestion.get("stop_level")
    stop_source = suggestion.get("stop_source", "—")
    stop_pct    = suggestion.get("stop_pct")
    gap_fill      = suggestion.get("gap_fill")
    gap_fill_pct  = suggestion.get("gap_fill_pct")
    gap_fill_date = suggestion.get("gap_fill_date")
    gap_fill_type = suggestion.get("gap_fill_type", "")
    mp_headwind   = suggestion.get("mp_headwind", False)
    hold_note     = suggestion.get("hold_note", "")
    direction     = suggestion["direction"]

    tgt_clr  = "#22C55E" if direction == "Bullish" else "#EF4444" if direction == "Bearish" else "#A78BFA"
    stop_clr = "#EF4444" if direction == "Bullish" else "#22C55E" if direction == "Bearish" else "#F59E0B"

    def _level_html(price, pct, source, color):
        if price is None:
            return '<span style="font-size:0.82rem;font-weight:700;color:#475569">—</span>'
        sign  = "+" if (pct or 0) >= 0 else ""
        pct_s = f"{sign}{pct:.1f}%" if pct is not None else ""
        return (
            f'<span style="font-size:0.85rem;font-weight:700;color:{color}">${price:,.2f}</span>'
            f'<span style="font-size:0.7rem;color:#64748B;margin-left:4px">{pct_s} · {source}</span>'
        )

    ref_html  = _level_html(ref_target, ref_pct,  ref_source,  tgt_clr)
    stop_html = _level_html(stop_level, stop_pct, stop_source, stop_clr)

    show_gap = gap_fill is not None and (ref_target is None or abs(gap_fill - ref_target) > 0.50)
    _gap_parts = [p for p in [gap_fill_type, gap_fill_date] if p and p != "—"]
    _gap_src   = "Gap fill" + (" · " + " · ".join(_gap_parts) if _gap_parts else "")
    gap_html   = _level_html(gap_fill, gap_fill_pct, _gap_src, "#F59E0B") if show_gap else ""

    mp_warn   = (f'<div style="font-size:0.72rem;color:#F59E0B;margin-top:5px">⚠ Max pain may act as friction before target</div>' if mp_headwind else "")
    hold_html = (f'<div style="font-size:0.72rem;color:#94A3B8;margin-top:5px">⟳ {hold_note}</div>' if hold_note else "")
    gap_row   = (
        f'<div style="margin-top:6px">'
        f'<span style="font-size:9px;color:#64748B;text-transform:uppercase;letter-spacing:.06em">Gap Fill &nbsp;</span>'
        f'{gap_html}</div>'
        if show_gap else ""
    )

    ref_levels_html = (
        f'<div style="margin-top:12px;padding-top:10px;border-top:1px solid #1E293B">'
        f'<div style="font-size:9px;color:#64748B;text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px">Reference Levels</div>'
        f'<div style="display:flex;gap:32px;flex-wrap:wrap;align-items:flex-start">'
        f'<div><div style="font-size:9px;color:#64748B;text-transform:uppercase;letter-spacing:.06em;margin-bottom:2px">Target</div>'
        f'<div>{ref_html}</div></div>'
        f'<div><div style="font-size:9px;color:#64748B;text-transform:uppercase;letter-spacing:.06em;margin-bottom:2px">Stop / Invalidation</div>'
        f'<div>{stop_html}</div></div>'
        f'</div>{gap_row}{mp_warn}{hold_html}</div>'
    )

    c_main, c_why = st.columns([3, 2]) if show_why else (st.container(), None)
    with c_main:
        st.markdown(
            f'<div style="background:rgba(255,255,255,0.03);border:1px solid #1E293B;'
            f'border-left:4px solid {strat_clr};border-radius:10px;padding:16px 20px">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">'
            f'<span style="font-size:11px;font-weight:700;color:#64748B;letter-spacing:.08em;text-transform:uppercase">{setup_title}</span>'
            f'<div style="display:flex;align-items:center;gap:8px">'
            f'<a href="{_share_url(exp_iso)}" target="_blank" style="font-size:10px;color:#475569;'
            f'text-decoration:none;padding:2px 7px;border:1px solid #334155;border-radius:4px;white-space:nowrap">🔗 Share</a>'
            f'<span style="background:{conf_clr}22;color:{conf_clr};font-size:0.68rem;font-weight:700;'
            f'padding:2px 8px;border-radius:4px;letter-spacing:.06em">{suggestion["confidence"]} CONFIDENCE</span>'
            f'</div></div>'
            f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">'
            f'<span style="font-size:28px;font-weight:900;color:{strat_clr};line-height:1">{suggestion["strategy"]}</span>'
            f'<span style="background:{dir_clr}22;color:{dir_clr};font-size:0.7rem;font-weight:700;padding:2px 8px;border-radius:4px;letter-spacing:.05em">{suggestion["direction"].upper()}</span>'
            f'<span style="background:{vb_clr}22;color:{vb_clr};font-size:0.7rem;font-weight:700;padding:2px 8px;border-radius:4px;letter-spacing:.05em">{suggestion["vol_bias"]}</span>'
            f'</div>'
            f'<div style="font-size:0.8rem;color:#94A3B8;margin-bottom:12px">{suggestion["strat_note"]}</div>'
            f'<div style="display:flex;gap:28px;flex-wrap:wrap">'
            f'<div><div style="font-size:9px;color:#64748B;text-transform:uppercase;letter-spacing:.06em;margin-bottom:2px">Strike Hints</div>'
            f'<div style="font-size:0.82rem;font-weight:700;color:#F1F5F9">{strike_str}</div></div>'
            f'<div><div style="font-size:9px;color:#64748B;text-transform:uppercase;letter-spacing:.06em;margin-bottom:2px">EM Range</div>'
            f'<div style="font-size:0.82rem;font-weight:700;color:#A78BFA">{em_range}</div></div>'
            f'</div>'
            f'{ref_levels_html}'
            f'<div style="font-size:9px;color:#475569;margin-top:10px">'
            f'Not financial advice · Strike hints ≈ 30%/60% of expected move · Reference levels are price magnets, not guaranteed exits</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    if show_why and c_why is not None:
        with c_why:
            st.markdown(
                f'<div style="background:rgba(255,255,255,0.03);border:1px solid #1E293B;'
                f'border-radius:10px;padding:16px">'
                f'<div style="font-size:9px;color:#64748B;text-transform:uppercase;'
                f'letter-spacing:.06em;margin-bottom:8px">Why this strategy</div>'
                f'{rationale_html}</div>',
                unsafe_allow_html=True,
            )
