#!/usr/bin/env python3
"""Patch the live glacifraga.com HTML into the v5 / Ltd drop-in.

The Railway homepage is a single HTML file (inline CSS + inline Ķemeri hero).
This workspace cannot write to 6tbwmzr522-crypto/glacifraga-trading, so this
script is the production cutover: run it against that repo's index.html (or
against a fetch of https://glacifraga.com) and commit the result.

Only the document body is rewritten so the base64 hero is left untouched.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BODY_MARK = "<body>"

STATS_OLD = """<section class="stats-section">
  <p class="section-label">Backtested Performance · 2022–2026</p>
  <h2 class="section-title">The numbers speak clearly</h2>
  <div class="stats-grid">
    <div class="stat-card"><div class="stat-value">2.19</div><div class="stat-label">Profit Factor</div><div class="stat-sub">Target ≥ 2.0</div></div>
    <div class="stat-card"><div class="stat-value">6.01</div><div class="stat-label">Sharpe Ratio</div><div class="stat-sub">Risk-adjusted</div></div>
    <div class="stat-card"><div class="stat-value">52%</div><div class="stat-label">Win Rate</div><div class="stat-sub">99 trades</div></div>
    <div class="stat-card"><div class="stat-value">−2.7%</div><div class="stat-label">Max Drawdown</div><div class="stat-sub">Portfolio level</div></div>
    <div class="stat-card"><div class="stat-value">7k</div><div class="stat-label">Net P&amp;L</div><div class="stat-sub">On 00k capital</div></div>
  </div>
</section>"""

STATS_NEW = """<section class="stats-section">
  <p class="section-label">Backtested Performance · 2017–2026</p>
  <h2 class="section-title">The numbers speak clearly</h2>
  <div class="stats-grid">
    <div class="stat-card"><div class="stat-value">+22.0%</div><div class="stat-label">CAGR</div><div class="stat-sub">Obsidian · 9.6 years</div></div>
    <div class="stat-card"><div class="stat-value">2.65</div><div class="stat-label">Sharpe Ratio</div><div class="stat-sub">Annualised, 252-day</div></div>
    <div class="stat-card"><div class="stat-value">~61%</div><div class="stat-label">Win Rate</div><div class="stat-sub">~174 trades / year</div></div>
    <div class="stat-card"><div class="stat-value">−7.1%</div><div class="stat-label">Max Drawdown</div><div class="stat-sub">Peak-to-trough</div></div>
    <div class="stat-card"><div class="stat-value">$618,591</div><div class="stat-label">Net P&amp;L</div><div class="stat-sub">On $100k capital</div></div>
  </div>
  <p style="max-width:640px;margin:2rem auto 0;text-align:center;font-size:11px;color:rgba(245,242,236,0.28);letter-spacing:0.04em;line-height:1.6">Confidential — backtested Obsidian 48 through 24 Jul 2026. Profit factor 1.95 · Sortino 4.20. Not indicative of future results.</p>
</section>"""

QUOTE_OLD = "&ldquo;Lielā Ķemeru tīreļa laipa &mdash; patience, clarity, and the right moment.&rdquo;"
QUOTE_NEW = "&ldquo;Patience, clarity, and the right moment.&rdquo;"

BODY_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    (STATS_OLD, STATS_NEW),
    (QUOTE_OLD, QUOTE_NEW),
    ("Thin Ice Digital UG", "Thin Ice Digital Ltd"),
    ("<span>Price</span><span>6.09</span>", "<span>Price</span><span>$156.09</span>"),
    ("<span>20d Breakout</span><span>3.55 ✓</span>", "<span>20d Breakout</span><span>$153.55 ✓</span>"),
    ("<span>Stop Loss</span><span>0.42</span>", "<span>Stop Loss</span><span>$150.42</span>"),
    ("<span>Take Profit</span><span>7.44</span>", "<span>Take Profit</span><span>$167.44</span>"),
    ("<span>Risk ,000</span>", "<span>Risk $1,000</span>"),
)

OPTIONAL_BODY_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    (
        "Duke adds BTC (Aurora).",
        "DUKE / AURORA adds Bitcoin (fractional qty; daily bars settle 00:00 UTC).",
    ),
)


class PatchError(ValueError):
    pass


def split_head_body(html: str) -> tuple[str, str]:
    idx = html.find(BODY_MARK)
    if idx < 0:
        raise PatchError("HTML has no <body> tag")
    return html[:idx], html[idx:]


def patch_homepage(html: str) -> str:
    head, body = split_head_body(html)
    missing: list[str] = []
    for old, new in BODY_REPLACEMENTS:
        if old not in body:
            missing.append(old[:80].replace("\n", " "))
            continue
        body = body.replace(old, new, 1)
    if missing:
        raise PatchError("Live HTML did not contain expected fragments:\n- " + "\n- ".join(missing))
    for old, new in OPTIONAL_BODY_REPLACEMENTS:
        if old in body:
            body = body.replace(old, new, 1)
    return head + body


def load_source(path: Path | None) -> str:
    if path is not None:
        return path.read_text(encoding="utf-8")
    import urllib.request

    with urllib.request.urlopen("https://glacifraga.com/", timeout=30) as response:
        return response.read().decode("utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        help="Existing homepage HTML (default: fetch https://glacifraga.com/)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Write the patched homepage here (overwrite the Railway index.html)",
    )
    args = parser.parse_args(argv)
    try:
        patched = patch_homepage(load_source(args.input))
    except PatchError as exc:
        print(exc, file=sys.stderr)
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(patched, encoding="utf-8")
    print(f"Wrote {args.output} ({len(patched):,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
