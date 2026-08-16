from pathlib import Path

import pytest

from scripts.patch_live_homepage import PatchError, patch_homepage

LIVE_SNIPPET = """<!DOCTYPE html>
<html><head><style>/* UG in css is fine */</style></head>
<body>
<section class="stats-section">
  <p class="section-label">Backtested Performance · 2022–2026</p>
  <h2 class="section-title">The numbers speak clearly</h2>
  <div class="stats-grid">
    <div class="stat-card"><div class="stat-value">2.19</div><div class="stat-label">Profit Factor</div><div class="stat-sub">Target ≥ 2.0</div></div>
    <div class="stat-card"><div class="stat-value">6.01</div><div class="stat-label">Sharpe Ratio</div><div class="stat-sub">Risk-adjusted</div></div>
    <div class="stat-card"><div class="stat-value">52%</div><div class="stat-label">Win Rate</div><div class="stat-sub">99 trades</div></div>
    <div class="stat-card"><div class="stat-value">−2.7%</div><div class="stat-label">Max Drawdown</div><div class="stat-sub">Portfolio level</div></div>
    <div class="stat-card"><div class="stat-value">7k</div><div class="stat-label">Net P&amp;L</div><div class="stat-sub">On 00k capital</div></div>
  </div>
</section>
<div class="signal-row"><span>Price</span><span>6.09</span></div>
<div class="signal-row"><span>20d Breakout</span><span>3.55 ✓</span></div>
<div class="signal-row"><span>Stop Loss</span><span>0.42</span></div>
<div class="signal-row"><span>Take Profit</span><span>7.44</span></div>
<div class="signal-row hl"><span>Position · 176 shares</span><span>Risk ,000</span></div>
<blockquote>&ldquo;Lielā Ķemeru tīreļa laipa &mdash; patience, clarity, and the right moment.&rdquo;</blockquote>
<p>Same Alpaca account as the Railway worker. BOT_MODE=BARON runs the Obsidian 48 universe; Duke adds BTC (Aurora).</p>
<footer><span>Thin Ice Digital UG</span></footer>
</body></html>
"""


def test_patch_rewrites_v5_copy_and_legal():
    patched = patch_homepage(LIVE_SNIPPET)
    assert "2017–2026" in patched
    assert "+22.0%" in patched
    assert "2.65" in patched
    assert "~61%" in patched
    assert "−7.1%" in patched
    assert "$618,591" in patched
    assert "On $100k capital" in patched
    assert "Profit factor 1.95" in patched
    assert "Sortino 4.20" in patched
    assert "Patience, clarity, and the right moment." in patched
    assert "Lielā" not in patched
    assert "Thin Ice Digital Ltd" in patched
    assert "Thin Ice Digital UG" not in patched
    assert "$156.09" in patched
    assert "$153.55" in patched
    assert "$150.42" in patched
    assert "$167.44" in patched
    assert "Risk $1,000" in patched
    assert "DUKE / AURORA adds Bitcoin" in patched
    assert "00:00 UTC" in patched


def test_patch_does_not_touch_head():
    html = "<head>Thin Ice Digital UG</head>\n" + LIVE_SNIPPET[LIVE_SNIPPET.find("<body>") :]
    patched = patch_homepage(html)
    head, _, _ = patched.partition("<body>")
    assert "Thin Ice Digital UG" in head
    assert "Thin Ice Digital Ltd" in patched


def test_patch_rejects_unknown_markup():
    with pytest.raises(PatchError):
        patch_homepage("<body>unrelated</body>")


def test_served_homepage_is_v5():
    html = Path("web/index.html").read_text(encoding="utf-8")
    assert "Thin Ice Digital Ltd" in html
    assert "Thin Ice Digital UG" not in html
    assert "Patience, clarity, and the right moment." in html
    assert "Lielā" not in html
    assert "$618,591" in html
    assert "+22.0%" in html
    assert "/assets/kemeru-hero.png" in html
    assert Path("web/assets/kemeru-hero.png").is_file()
