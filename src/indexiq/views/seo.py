"""
SEO helpers — config driven from config/seo.yml.

Streamlit controls the <head> tag, so tags injected via st.markdown() land in
<body>. The JS snippet below upserts every tag directly into <head> at page-load,
where crawlers and social parsers expect them.
"""
import json
from pathlib import Path

import streamlit as st
import yaml

# ── Load config ────────────────────────────────────────────────────────────────
_seo_path = Path(__file__).parent.parent.parent.parent / "config" / "seo.yml"
with open(_seo_path) as _f:
    _s: dict = yaml.safe_load(_f)

_site        = _s["site"]
_TITLE       = _site["title"]
_URL         = _site["url"]
_IMAGE       = _site["image"]
_DESCRIPTION = _s["description"].strip().replace("\n", " ")
_KEYWORDS    = ", ".join(_s["keywords"])

# ── JSON-LD ────────────────────────────────────────────────────────────────────
_json_ld = {
    "@context": "https://schema.org",
    "@graph": [
        {
            "@type": "WebApplication",
            "name": _site["name"],
            "url": _URL,
            "description": _DESCRIPTION,
            "applicationCategory": "FinanceApplication",
            "operatingSystem": "Any (Web Browser)",
            "inLanguage": _site["locale"][:2],
            "isAccessibleForFree": True,
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
            "image": _IMAGE,
            "featureList": [
                "Moving averages MA5, MA20, MA50, MA100, MA200",
                "200-week moving average overlay",
                "RSI-14 overbought and oversold indicator",
                "Fibonacci retracement levels",
                "Candlestick reversal pattern detection",
                "S&P 500 weekly and monthly candle screener",
                "Short squeeze scanner with squeeze score",
                "Bounce radar for stocks near 200-day MA",
                "Charlie Munger quality stock watchlist",
                "AI-powered SPY 5-day price forecast",
                "Golden Cross and Death Cross detection",
            ],
        },
        {
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": item["q"],
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": item["a"].strip().replace("\n", " "),
                    },
                }
                for item in _s["faq"]
            ],
        },
    ],
}


def inject_seo() -> None:
    """
    Call once at the top of app.py.
    Injects meta tags into <head> via JS and emits JSON-LD structured data.
    """
    _gverify = _site.get("google_verification", "")
    meta_rows = [
        # Standard
        ("name",     "description",        _DESCRIPTION),
        ("name",     "keywords",           _KEYWORDS),
        ("name",     "author",             _site["name"]),
        ("name",     "application-name",   _site["name"]),
        ("name",     "robots",             "index, follow, max-snippet:-1, max-image-preview:large"),
        ("name",     "theme-color",        "#0F172A"),
        # Open Graph
        ("property", "og:type",            "website"),
        ("property", "og:url",             _URL),
        ("property", "og:title",           _TITLE),
        ("property", "og:description",     _DESCRIPTION),
        ("property", "og:site_name",       _site["name"]),
        ("property", "og:locale",          _site["locale"]),
        ("property", "og:image",           _IMAGE),
        ("property", "og:image:width",     str(_site["image_width"])),
        ("property", "og:image:height",    str(_site["image_height"])),
        ("property", "og:image:alt",       f"{_site['name']} — {_TITLE}"),
        # Google Search Console ownership verification
        *([("name", "google-site-verification", _gverify)] if _gverify else []),
        # Twitter Card
        ("name",     "twitter:card",       "summary_large_image"),
        ("name",     "twitter:title",      _TITLE),
        ("name",     "twitter:description", _DESCRIPTION),
        ("name",     "twitter:image",      _IMAGE),
    ]

    js_calls = []
    for attr, key, val in meta_rows:
        safe = val.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")
        js_calls.append(f'    upsertMeta("{attr}", "{key}", "{safe}");')

    json_ld_str = json.dumps(_json_ld, ensure_ascii=False).replace("\\", "\\\\").replace("`", "\\`")

    # Inject via st.components so the script runs in an iframe and uses
    # window.parent.document (same-origin) — more reliable than st.markdown()
    # because React does not re-execute <script> tags set via innerHTML.
    # The script also fires an extra time on DOMContentLoaded / readystatechange
    # so Googlebot's deferred rendering pass also sees the tags.
    import streamlit.components.v1 as components

    components.html(
        f"""<!DOCTYPE html>
<html><head></head><body>
<script>
(function inject() {{
  var d = (window.parent || window).document;

  function upsertMeta(attr, key, content) {{
    var sel = 'meta[' + attr + '="' + key + '"]';
    var el  = d.querySelector(sel);
    if (!el) {{
      el = d.createElement('meta');
      el.setAttribute(attr, key);
      d.head.appendChild(el);
    }}
    el.setAttribute('content', content);
  }}

  function upsertCanonical(url) {{
    var el = d.querySelector('link[rel="canonical"]');
    if (!el) {{
      el = d.createElement('link');
      el.rel = 'canonical';
      d.head.appendChild(el);
    }}
    el.href = url;
  }}

  function upsertJsonLd(json) {{
    var el = d.querySelector('script[data-indexiq-ld]');
    if (!el) {{
      el = d.createElement('script');
      el.type = 'application/ld+json';
      el.setAttribute('data-indexiq-ld', '1');
      d.head.appendChild(el);
    }}
    el.textContent = json;
  }}

  function run() {{
{chr(10).join(js_calls)}
    upsertCanonical("{_URL}");
    d.title = "{_TITLE}";
    upsertJsonLd(`{json_ld_str}`);
  }}

  run();
  // Re-run after Streamlit finishes loading so Googlebot's second-pass renderer
  // also captures the tags when window.prerenderReady becomes true.
  if (window.parent && window.parent.document.readyState !== 'complete') {{
    window.parent.addEventListener('load', run);
  }}
}})();
</script>
</body></html>""",
        height=0,
        scrolling=False,
    )
