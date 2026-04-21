"""AI forecast service — assembles context and delegates to the LLM layer."""

import pandas as pd

from stockiq.backend.llm import PROVIDERS, fetch_ai_prediction, get_secret
from stockiq.backend.models.spy_context import (
    build_forecast_context,
    is_market_open,
    next_market_open_str,
)
from stockiq.backend.services.market_service import get_vix_chart_df
from stockiq.backend.services.spy_service import (
    get_put_call_ratio, get_spy_chart_df, get_spy_options_analysis, get_spy_quote,
)


def get_providers() -> dict[str, dict]:
    """Return provider metadata (label, model, env_var, free flag)."""
    return PROVIDERS


def has_app_key(provider: str) -> bool:
    """Return True if the app-level API key for this provider is configured."""
    env_var = PROVIDERS[provider]["env_var"]
    return bool(get_secret(env_var))


def get_app_key(provider: str) -> str:
    """Return the app-level API key for the given provider (empty string if absent)."""
    return get_secret(PROVIDERS[provider]["env_var"])


def get_market_status() -> dict:
    """Return market open/closed status and next-open string."""
    open_ = is_market_open()
    return {
        "is_open":        open_,
        "next_open_str":  next_market_open_str() if not open_ else "",
    }


def get_ai_forecast(
    gaps_df: pd.DataFrame,
    provider: str = "groq",
    user_key: str = "",
    cache_key: str = "",
) -> list[dict]:
    """
    Assemble all context data and return a 10-day SPY forecast from the AI model.

    Returns a list of 10 prediction dicts (date, direction, est_close, …).
    Raises on provider errors so the caller can handle UX.
    """
    quote         = get_spy_quote()
    current_price = float(quote.get("price", 0.0))
    daily_df      = get_spy_chart_df("1y", "1d")
    vix_df        = get_vix_chart_df("1y")
    pc_data       = get_put_call_ratio()
    options       = get_spy_options_analysis(current_price=current_price)

    options_flow: dict | None = None
    if options and not options["oi_df"].empty:
        oi_df        = options["oi_df"]
        max_pain     = options["max_pain"]
        call_wall    = float(oi_df.loc[oi_df["call_oi"].idxmax(), "strike"])
        put_wall     = float(oi_df.loc[oi_df["put_oi"].idxmax(), "strike"])
        dist_pct     = round((current_price - max_pain) / max_pain * 100, 2) if max_pain else 0.0
        options_flow = {
            "expiration": options["expiration"],
            "max_pain":   max_pain,
            "dist_pct":   dist_pct,
            "call_wall":  call_wall,
            "put_wall":   put_wall,
        }

    context_json = build_forecast_context(
        gaps_df, quote,
        daily_df=daily_df,
        vix_df=vix_df,
        pc_data=pc_data,
        options_flow=options_flow,
    )

    return fetch_ai_prediction(
        cache_key,
        context_json,
        provider=provider,
        _user_key=user_key,
    )
