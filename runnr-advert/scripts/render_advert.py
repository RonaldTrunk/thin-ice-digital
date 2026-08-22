#!/usr/bin/env python3
"""Runnr.fyi product advert — Horizon-style kinetic + product UI demo."""

from __future__ import annotations

import math
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
FONTS = ASSETS / "fonts"
OUTPUT = ROOT / "output"

W, H = 1920, 1080
FPS = 30

# Per-language duration / audio / output naming
LANG_CFG = {
    "en": {
        "duration": 62.0,
        "audio": "narration.mp3",
        "bed": "bed-rising.mp3",
        "out": "runnr-advert",
        "frames": "frames",
    },
    "de": {
        "duration": 90.0,
        "audio": "narration-de.mp3",
        "bed": "bed-rising.mp3",
        "out": "runnr-advert-de",
        "frames": "frames-de",
    },
}

BG = (8, 12, 18)
SURFACE = (12, 17, 24)
SURFACE2 = (16, 22, 32)
SURFACE3 = (22, 29, 40)
GOLD = (201, 169, 110)
GOLD_LIGHT = (232, 201, 122)
ACCENT = (0, 229, 160)
TEXT = (245, 242, 236)
TEXT2 = (160, 157, 150)
TEXT3 = (100, 98, 94)
RED = (232, 93, 111)
AMBER = (232, 201, 122)
BLUE = (126, 184, 232)


def font(kind: str, size: int) -> ImageFont.FreeTypeFont:
    paths = {
        "head": FONTS / "font_3.ttf",
        "head_med": FONTS / "font_4.ttf",
        "head_semi": FONTS / "font_5.ttf",
        "head_light": FONTS / "font_2.ttf",
        "head_italic": FONTS / "font_1.ttf",
        "body": FONTS / "font_7.ttf",
        "body_light": FONTS / "font_6.ttf",
        "body_med": FONTS / "font_8.ttf",
    }
    return ImageFont.truetype(str(paths[kind]), size)


def ease_out(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def clamp01(t: float) -> float:
    return max(0.0, min(1.0, t))


def vignette(img: Image.Image, strength: float = 0.55) -> Image.Image:
    arr = np.asarray(img).astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    cx, cy = W / 2, H / 2
    r = np.sqrt(((xx - cx) / (W * 0.75)) ** 2 + ((yy - cy) / (H * 0.75)) ** 2)
    factor = 1 - strength * np.clip(r - 0.3, 0, 1) ** 1.3
    arr[..., :3] *= factor[..., None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def scene_bg(t: float, gold_y: float = 0.0, accent_y: float = 0.85) -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g = ImageDraw.Draw(glow)
    cx, cy = W // 2, int(H * gold_y - 80)
    for i, r in enumerate(range(1100, 80, -50)):
        a = int(28 * (1 - i / 22) ** 2)
        g.ellipse((cx - r, cy - r // 2, cx + r, cy + r // 2), fill=(*GOLD, a))
    cx2, cy2 = W // 2, int(H * accent_y)
    for i, r in enumerate(range(800, 40, -40)):
        a = int(22 * (1 - i / 20) ** 2 * (0.85 + 0.15 * math.sin(t * 1.2)))
        g.ellipse((cx2 - r, cy2 - r // 2, cx2 + r, cy2 + r // 2), fill=(*ACCENT, a))
    glow = glow.filter(ImageFilter.GaussianBlur(90))
    out = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
    return vignette(out, 0.48)


def draw_centered(draw, text, y, fnt, fill=TEXT, max_width=None):
    if max_width:
        lines = []
        for paragraph in text.split("\n"):
            words = paragraph.split()
            if not words:
                continue
            cur = ""
            for w in words:
                trial = f"{cur} {w}".strip()
                if draw.textlength(trial, font=fnt) <= max_width:
                    cur = trial
                else:
                    if cur:
                        lines.append(cur)
                    cur = w
            if cur:
                lines.append(cur)
    else:
        lines = text.split("\n")
    line_h = int(fnt.size * 1.2)
    total = len(lines) * line_h
    start = y - total // 2
    for i, line in enumerate(lines):
        tw = draw.textlength(line, font=fnt)
        draw.text(((W - tw) / 2, start + i * line_h), line, font=fnt, fill=fill)


def rounded(draw, box, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def phone_frame(base: Image.Image, content: Image.Image, y_offset: int = 0) -> Image.Image:
    pw, ph = 430, 880
    shell = Image.new("RGBA", (pw + 20, ph + 20), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shell)
    glow = Image.new("RGBA", shell.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.rounded_rectangle((0, 0, pw + 19, ph + 19), radius=48, fill=(*GOLD, 40))
    glow = glow.filter(ImageFilter.GaussianBlur(16))
    sd.rounded_rectangle((6, 6, pw + 13, ph + 13), radius=42, fill=(8, 12, 18, 255), outline=(*GOLD, 90), width=2)

    content = content.resize((pw - 20, ph - 20), Image.Resampling.LANCZOS)
    mask = Image.new("L", content.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, content.size[0] - 1, content.size[1] - 1), radius=34, fill=255)
    screen = Image.new("RGBA", content.size)
    screen.paste(content.convert("RGBA"), (0, 0))
    screen.putalpha(mask)
    shell.paste(screen, (16, 16), screen)
    ImageDraw.Draw(shell).text((36, 28), "9:41", font=font("body_med", 13), fill=TEXT)
    ImageDraw.Draw(shell).rounded_rectangle((pw // 2 - 36, 24, pw // 2 + 52, 36), radius=6, fill=(10, 10, 10, 255))

    composed = base.convert("RGBA")
    x = (W - shell.width) // 2
    y = (H - shell.height) // 2 + y_offset
    composed.alpha_composite(glow, (x - 2, y - 2))
    composed.alpha_composite(shell, (x, y))
    return composed.convert("RGB")


def app_header(d, w):
    d.rectangle((0, 0, w, 72), fill=(8, 12, 18))
    d.rectangle((18, 26, 20, 48), fill=GOLD)
    d.text((30, 22), "runnr", font=font("head_italic", 28), fill=TEXT)
    rounded(d, (w - 118, 22, w - 18, 46), 12, (40, 34, 24), outline=GOLD, width=1)
    d.text((w - 108, 26), "NOVICE", font=font("body_med", 11), fill=GOLD)


def app_nav(d, w, h, active: int = 0):
    d.rectangle((0, h - 70, w, h), fill=SURFACE)
    labels = ["Home", "Size", "Journal", "Coach", "Markets"]
    for i, lab in enumerate(labels):
        cx = 20 + i * (w // 5) + 18
        col = ACCENT if i == active else TEXT3
        d.ellipse((cx + 12, h - 54, cx + 22, h - 44), fill=col)
        d.text((cx, h - 36), lab, font=font("body_med", 9), fill=col)


def caption(draw, text: str):
    draw_centered(draw, text, H - 78, font("body_med", 26), TEXT)


def make_sizer_screen(progress: float) -> Image.Image:
    w, h = 410, 860
    screen = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(screen)
    app_header(d, w)

    d.text((18, 90), "SHARES POSITION SIZER", font=font("body_med", 10), fill=GOLD)
    rounded(d, (18, 118, 220, 148), 14, (40, 34, 24), outline=GOLD, width=1)
    d.text((30, 124), "Baron Preset  ·  1% risk", font=font("body", 12), fill=GOLD_LIGHT)

    fields = [
        ("TICKER", "NVDA"),
        ("ENTRY", "128.40"),
        ("STOP LOSS", "124.10"),
        ("TARGET", "136.90"),
    ]
    y = 168
    shown = max(1, int(len(fields) * clamp01(0.2 + progress * 1.0) + 0.01))
    for label, val in fields[:shown]:
        d.text((22, y), label, font=font("body_med", 9), fill=GOLD)
        rounded(d, (18, y + 18, w - 18, y + 58), 6, SURFACE2, outline=(60, 50, 35), width=1)
        d.text((30, y + 28), val, font=font("head", 20), fill=TEXT)
        y += 72

    if progress > 0.45:
        box_y = y + 4
        rounded(d, (18, box_y, w - 18, box_y + 150), 12, (28, 36, 28), outline=GOLD, width=1)
        d.text((w // 2 - 40, box_y + 18), "MAX SHARES", font=font("body_med", 10), fill=TEXT3)
        d.text((w // 2 - 70, box_y + 40), "232", font=font("head_med", 48), fill=ACCENT)
        for i, (lab, val) in enumerate([("RISK", "€100"), ("R:R", "2.0"), ("REWARD", "€200")]):
            x0 = 40 + i * 120
            d.text((x0, box_y + 100), lab, font=font("body_med", 9), fill=TEXT3)
            d.text((x0, box_y + 116), val, font=font("head", 18), fill=TEXT)

    app_nav(d, w, h, active=1)
    return screen


def make_broker_screen(progress: float) -> Image.Image:
    w, h = 410, 860
    screen = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(screen)
    app_header(d, w)

    d.text((18, 90), "CONNECTED BROKERS", font=font("body_med", 10), fill=GOLD)
    d.text((18, 118), "Connect once. Pull real trades\ninto your journal.", font=font("body_light", 15), fill=TEXT2)

    brokers = [
        ("Alpa", "Alpaca", "Connected · paper keys", True, ACCENT),
        ("CSV", "CSV Import", "Any broker · upload history", False, GOLD),
        ("T212", "Trading 212", "Coming soon", False, TEXT3),
        ("IBKR", "Interactive Brokers", "Coming soon", False, TEXT3),
    ]
    y = 180
    n = max(1, int(len(brokers) * clamp01(0.15 + progress) + 0.01))
    for i, (code, name, status, synced, badge_col) in enumerate(brokers[:n]):
        rounded(d, (18, y, w - 18, y + 78), 10, SURFACE, outline=(50, 42, 30), width=1)
        # logo tile
        rounded(d, (30, y + 18, 66, y + 54), 6, SURFACE3)
        d.text((36, y + 26), code[:3], font=font("body_med", 11), fill=GOLD_LIGHT if not synced else ACCENT)
        d.text((80, y + 20), name, font=font("body", 16), fill=TEXT)
        d.text((80, y + 44), status, font=font("body_light", 12), fill=TEXT3)
        badge = "SYNCED" if synced else ("IMPORT" if code == "CSV" else "SOON")
        bw = 62 if synced else 58
        rounded(d, (w - 28 - bw, y + 28, w - 28, y + 50), 10, (20, 40, 32) if synced else (40, 34, 24))
        d.text((w - 24 - bw + 8, y + 32), badge, font=font("body_med", 9), fill=badge_col)
        y += 90

    if progress > 0.7:
        rounded(d, (18, y + 4, w - 18, y + 64), 10, (20, 40, 32), outline=ACCENT, width=1)
        d.text((36, y + 24), "↻  Synced 14 trades · just now", font=font("body", 14), fill=ACCENT)

    app_nav(d, w, h, active=0)
    return screen


def make_watchlist_screen(progress: float) -> Image.Image:
    w, h = 410, 860
    screen = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(screen)
    app_header(d, w)

    d.text((18, 90), "WATCHLIST", font=font("body_med", 10), fill=GOLD)
    # Baron + add
    rounded(d, (18, 114, 130, 142), 12, (40, 34, 24), outline=GOLD, width=1)
    d.text((28, 120), "🎩  Baron", font=font("body", 13), fill=GOLD_LIGHT)
    rounded(d, (140, 114, 250, 142), 12, SURFACE2, outline=(50, 42, 30), width=1)
    d.text((152, 120), "+ Add Setup", font=font("body", 13), fill=TEXT2)

    setups = [
        ("NVDA", "LONG", "128.40", "+1.2%", "Break of 127 · 1% risk", True, ACCENT),
        ("RACE", "LONG", "412.80", "-0.4%", "Price entering entry zone", True, AMBER),
        ("BTC", "LONG", "67,420", "+2.8%", "Funding calm · swing long", False, ACCENT),
        ("GOLD", "SHORT", "2,348", "+0.1%", "Rejection at weekly high", False, RED),
    ]
    y = 160
    n = max(1, int(len(setups) * clamp01(0.2 + progress * 0.95) + 0.01))
    for i, (sym, direc, price, chg, thesis, alert, dcol) in enumerate(setups[:n]):
        # gold left rail like live app
        d.rectangle((18, y, 20, y + 118), fill=AMBER if alert and sym == "RACE" else GOLD)
        rounded(d, (20, y, w - 18, y + 118), 0, SURFACE)
        # redraw as rounded card overlapping rail
        rounded(d, (20, y, w - 18, y + 118), 8, SURFACE, outline=(50, 42, 30), width=1)
        d.rectangle((18, y + 8, 20, y + 110), fill=AMBER if alert and sym == "RACE" else GOLD)

        d.text((34, y + 14), sym, font=font("head_italic", 22), fill=TEXT)
        # direction chip
        chip_w = 52
        rounded(d, (120, y + 18, 120 + chip_w, y + 38), 10, (20, 40, 32) if direc == "LONG" else (45, 22, 28))
        d.text((128, y + 20), direc, font=font("body_med", 10), fill=dcol)

        d.text((w - 110, y + 14), price, font=font("head", 18), fill=TEXT)
        chg_col = ACCENT if chg.startswith("+") else RED
        d.text((w - 110, y + 40), chg, font=font("body", 13), fill=chg_col)

        # levels row
        d.text((34, y + 56), "ENT 128.40   STOP 124.10   TGT 136.90", font=font("body_light", 11), fill=TEXT3)
        d.text((34, y + 82), thesis, font=font("head_italic", 14), fill=TEXT2)

        if alert and progress > 0.55 and i == 1:
            rounded(d, (w - 100, y + 78, w - 28, y + 100), 8, (45, 38, 20))
            d.text((w - 92, y + 82), "ALERT", font=font("body_med", 10), fill=AMBER)
        y += 128

    app_nav(d, w, h, active=4)
    return screen


def make_discipline_screen(progress: float) -> Image.Image:
    w, h = 410, 860
    screen = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(screen)
    app_header(d, w)

    d.text((18, 90), "DISCIPLINE SCORE", font=font("body_med", 10), fill=GOLD)
    cx, cy, r = w // 2, 230, 78
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=SURFACE3, width=10)
    score = int(82 * clamp01(progress))
    for ang in range(-90, int(-90 + 360 * score / 100), 4):
        rad1 = math.radians(ang)
        rad2 = math.radians(ang + 5)
        x1 = cx + int((r - 2) * math.cos(rad1))
        y1 = cy + int((r - 2) * math.sin(rad1))
        x2 = cx + int((r - 2) * math.cos(rad2))
        y2 = cy + int((r - 2) * math.sin(rad2))
        d.line([(x1, y1), (x2, y2)], fill=ACCENT, width=10)
    d.text((cx - 36, cy - 28), f"{score}%", font=font("head_med", 42), fill=TEXT)
    d.text((cx - 48, cy + 22), "Stop Discipline", font=font("body", 13), fill=TEXT2)

    metrics = [("Stop", "82%"), ("Size", "91%"), ("Profit Factor", "1.8"), ("Win Rate", "58%")]
    for i, (lab, val) in enumerate(metrics):
        if progress < 0.2 + i * 0.15:
            continue
        yy = 360 if i < 2 else 470
        xx = 18 if i % 2 == 0 else w // 2 + 4
        rounded(d, (xx, yy, xx + w // 2 - 22, yy + 90), 12, SURFACE, outline=(50, 42, 30), width=1)
        d.text((xx + 16, yy + 18), lab.upper(), font=font("body_med", 9), fill=GOLD)
        d.text((xx + 16, yy + 40), val, font=font("head_med", 32), fill=ACCENT if i == 0 else TEXT)

    app_nav(d, w, h, active=0)
    return screen


def make_coach_screen(progress: float, prompt: str, answer_lines: list[str], show_projection: bool = False) -> Image.Image:
    w, h = 410, 860
    screen = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(screen)
    app_header(d, w)

    d.text((18, 90), "COACH INSIGHTS", font=font("body_med", 10), fill=GOLD)
    d.text((18, 118), "Ask about patterns in your own trade data", font=font("body_light", 13), fill=TEXT2)

    rounded(d, (60, 170, w - 18, 230), 14, SURFACE3)
    show = prompt[: max(1, int(len(prompt) * ease_out(min(1, progress * 2))))]
    words = show.split()
    lines, cur = [], ""
    for word in words:
        trial = f"{cur} {word}".strip()
        if d.textlength(trial, font=font("body", 14)) <= 280:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    for i, line in enumerate(lines[:2]):
        d.text((76, 182 + i * 20), line, font=font("body", 14), fill=TEXT)

    if progress > 0.35:
        rounded(d, (18, 250, w - 18, 500 if not show_projection else 480), 12, SURFACE, outline=(50, 42, 30), width=1)
        d.text((32, 268), "WEEKLY · AI", font=font("body_med", 9), fill=ACCENT)
        ans_progress = ease_out((progress - 0.35) / 0.55)
        n = max(1, int(len(answer_lines) * ans_progress + 0.01))
        yy = 300
        for line in answer_lines[:n]:
            words = line.split()
            cur = ""
            for word in words:
                trial = f"{cur} {word}".strip()
                if d.textlength(trial, font=font("body_light", 15)) <= 340:
                    cur = trial
                else:
                    d.text((32, yy), cur, font=font("body_light", 15), fill=TEXT2)
                    yy += 24
                    cur = word
            if cur:
                d.text((32, yy), cur, font=font("body_light", 15), fill=TEXT2)
                yy += 28

    if show_projection and progress > 0.65:
        rounded(d, (18, 500, w - 18, 640), 12, (28, 22, 16), outline=GOLD, width=1)
        d.text((32, 516), "MONTHLY EQUITY PROJECTION", font=font("body_med", 9), fill=GOLD)
        d.text((40, 550), "-€180", font=font("head_med", 28), fill=RED)
        d.text((40, 588), "ACTUAL", font=font("body_med", 10), fill=TEXT3)
        d.text((210, 550), "+€1,240", font=font("head_med", 28), fill=ACCENT)
        d.text((210, 588), "WITH RUNNR RULES", font=font("body_med", 10), fill=TEXT3)

    app_nav(d, w, h, active=3)
    return screen


def make_journal_impact(progress: float) -> Image.Image:
    w, h = 410, 860
    screen = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(screen)
    app_header(d, w)

    d.text((18, 90), "DISCIPLINE IMPACT", font=font("body_med", 10), fill=GOLD)
    d.text((18, 120), "What leaks cost you", font=font("head_italic", 28), fill=TEXT)

    cards = [
        ("+€2,503", "Disciplined P&L", ACCENT),
        ("-€190", "Undisciplined P&L", RED),
        ("82%", "Stop Confirmed", GOLD_LIGHT),
        ("91%", "Correctly Sized", GOLD_LIGHT),
    ]
    y = 180
    for i, (val, lab, col) in enumerate(cards):
        if progress < 0.12 + i * 0.16:
            break
        rounded(d, (18, y, w - 18, y + 88), 12, SURFACE, outline=(50, 42, 30), width=1)
        d.text((34, y + 18), lab.upper(), font=font("body_med", 10), fill=GOLD)
        d.text((34, y + 42), val, font=font("head_med", 32), fill=col)
        y += 100

    app_nav(d, w, h, active=2)
    return screen


def make_analytics_screen(progress: float) -> Image.Image:
    """Equity curve + heatmap + institutional metrics."""
    w, h = 410, 860
    screen = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(screen)
    app_header(d, w)

    d.text((18, 90), "EQUITY CURVE", font=font("body_med", 10), fill=GOLD)
    rounded(d, (18, 118, w - 18, 300), 12, SURFACE, outline=(50, 42, 30), width=1)

    # faux equity curve
    pts = []
    for x in range(40, w - 40):
        t = (x - 40) / (w - 80)
        yv = 260 - int(110 * (t ** 1.15) * clamp01(progress * 1.2)) + int(8 * math.sin(t * 14))
        pts.append((x, yv))
    if len(pts) > 1:
        d.line(pts, fill=ACCENT, width=2)
        # fill under
        poly = pts + [(pts[-1][0], 288), (pts[0][0], 288)]
        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(overlay).polygon(poly, fill=(*ACCENT, 28))
        screen = Image.alpha_composite(screen.convert("RGBA"), overlay).convert("RGB")
        d = ImageDraw.Draw(screen)

    d.text((30, 270), "+€2,313  ·  +23.1%", font=font("head", 16), fill=ACCENT)

    # institutional stats
    if progress > 0.35:
        d.text((18, 320), "INSTITUTIONAL GRADE", font=font("body_med", 10), fill=GOLD)
        stats = [("Sortino", "2.4"), ("Recovery", "3.1"), ("PF", "1.8")]
        for i, (lab, val) in enumerate(stats):
            xx = 18 + i * 128
            rounded(d, (xx, 348, xx + 118, 430), 10, SURFACE, outline=(50, 42, 30), width=1)
            d.text((xx + 14, 362), lab.upper(), font=font("body_med", 9), fill=GOLD)
            d.text((xx + 14, 386), val, font=font("head_med", 28), fill=TEXT)

    # heatmap
    if progress > 0.55:
        d.text((18, 450), "ACTIVITY HEATMAP", font=font("body_med", 10), fill=GOLD)
        d.text((18, 472), "Last 28 days", font=font("body_light", 12), fill=TEXT3)
        rng = np.random.default_rng(7)
        y0 = 500
        for row in range(4):
            for col in range(7):
                intens = float(rng.random())
                if intens < 0.25:
                    c = SURFACE3
                elif intens < 0.5:
                    c = (20, 55, 42)
                elif intens < 0.75:
                    c = (0, 120, 85)
                else:
                    c = ACCENT
                x0 = 22 + col * 52
                yy = y0 + row * 40
                rounded(d, (x0, yy, x0 + 44, yy + 32), 4, c)

    app_nav(d, w, h, active=2)
    return screen


def _copy(d: dict) -> dict:
    return dict(d)


EN = {
    "hook_words": ["HASN'T", "CHANGED"],
    "hook_sub": "20 years",
    "today": "Until now.",
    "today_sub": "",
    "tagline1": "Discipline coach.",
    "tagline2": "For traders who already know their edge.",
    "show": "Here's how it works.",
    "cap_sizer": "1% risk · stop · 2R",
    "cap_broker": "Broker sync.",
    "cap_watch": "Levels. Thesis. Alerts.",
    "cap_disc": "Discipline — not P&L.",
    "coach_q1": "Why do I cut winners early?",
    "coach_a1": [
        "You exit at +0.8R — your plan says 2R.",
        "That leak: €640 this month.",
    ],
    "cap_coach1": "Cut winners early?",
    "coach_q2": "P&L if I followed rules 100%?",
    "coach_a2": ["If every trade followed the rules:"],
    "cap_coach2": "Rules win.",
    "cap_impact": "What leaks cost you.",
    "cap_analytics": "Equity. Heatmap. Stats.",
    "edge1": "Your edge works.",
    "edge2": "Your discipline doesn't —",
    "edge3": "until it does.",
    "inst": "Institutional habits.\nWithout the stack.",
    "cta": "Get started",
    "tag": "Discipline over dopamine",
    # scene end times — punchy EN VTT (~61s)
    "t": [2.9, 4.5, 6.3, 9.7, 11.6, 17.1, 22.0, 26.7, 31.5, 34.5, 38.1, 42.7, 49.4, 54.0, 58.5],
}

DE = {
    "hook_words": ["HAT SICH", "NICHT", "GEÄNDERT"],
    "hook_sub": "Der Handelsablauf",
    "today": "Heute",
    "today_sub": "ändern wir das",
    "tagline1": "Der Disziplin-Coach",
    "tagline2": "für Trader, die ihren Edge bereits kennen",
    "show": "Ich zeige dir, wie es funktioniert.",
    "cap_sizer": "ein Prozent Risiko · Stop · 2R",
    "cap_broker": "Alpaca heute · CSV von überall",
    "cap_watch": "Levels · Thesis · Kursalarme",
    "cap_disc": "bewertet die Disziplin — nicht nur P&L",
    "coach_q1": "Warum schließe ich Gewinner zu früh?",
    "coach_a1": [
        "Du steigst bei +0,8R aus NVDA-Setups aus — dein Plan sagt 2R.",
        "Frühe Gewinne kosten dich diesen Monat €640.",
    ],
    "cap_coach1": "Gewinner zu früh geschlossen?",
    "coach_q2": "P&L bei 100% Regeldisziplin?",
    "coach_a2": ["Wenn jeder Trade den Runnr-Regeln gefolgt wäre:"],
    "cap_coach2": "Regeln bei jedem Trade",
    "cap_impact": "Geld, das Disziplin gerettet hätte",
    "cap_analytics": "Equity · Heatmap · Kennzahlen",
    "edge1": "Dein Edge funktioniert.",
    "edge2": "Deine Disziplin nicht —",
    "edge3": "bis sie es tut.",
    "inst": "Institutionelle Gewohnheiten.\nOhne den Stack.",
    "cta": "Jetzt starten",
    "tag": "Disziplin statt Dopamin",
    # scene end times — calm DE Conrad VTT (~89s)
    "t": [4.5, 6.7, 8.9, 13.5, 16.7, 24.7, 34.1, 42.2, 51.9, 55.9, 62.3, 68.6, 74.5, 80.0, 86.2],
}


def render_frame(i: int, lang: str = "en") -> Image.Image:
    S = DE if lang == "de" else EN
    ends = S["t"]
    t = i / FPS
    img = scene_bg(t)
    draw = ImageDraw.Draw(img)

    if t < ends[0]:
        words = S["hook_words"]
        idx = min(len(words) - 1, int((t / ends[0]) * len(words)))
        draw_centered(draw, words[idx], H // 2 - 30, font("head_semi", 90 if lang == "de" else 96), GOLD)
        draw_centered(draw, S["hook_sub"], H // 2 + 70, font("body", 26), TEXT2)

    elif t < ends[1]:
        draw_centered(draw, S["today"], H // 2 - 10, font("head_italic", 110), TEXT)
        if S.get("today_sub"):
            draw_centered(draw, S["today_sub"], H // 2 + 70, font("body", 28), TEXT2)

    elif t < ends[2]:
        local = ease_out((t - ends[1]) / max(0.01, ends[2] - ends[1]))
        icon = Image.open(ASSETS / "runnr-icon.png").convert("RGBA").resize((140, 140))
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        cx, cy = W // 2, H // 2 - 50
        gd.ellipse((cx - 100, cy - 100, cx + 100, cy + 100), fill=(*ACCENT, int(50 * local)))
        glow = glow.filter(ImageFilter.GaussianBlur(36))
        img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
        img.paste(icon, (cx - 70, cy - 70), icon)
        draw = ImageDraw.Draw(img)
        draw_centered(draw, "runnr", H // 2 + 90, font("head_italic", 72), TEXT)

    elif t < ends[3]:
        draw_centered(draw, S["tagline1"], H // 2 - 50, font("head", 56), TEXT, max_width=1400)
        draw_centered(draw, S["tagline2"], H // 2 + 40, font("body", 28), GOLD_LIGHT, max_width=1200)

    elif t < ends[4]:
        draw_centered(draw, S["show"], H // 2, font("head", 48), TEXT, max_width=1400)

    elif t < ends[5]:
        local = (t - ends[4]) / max(0.01, ends[5] - ends[4])
        screen = make_sizer_screen(local)
        img = phone_frame(scene_bg(t, accent_y=0.92), screen, 10)
        draw = ImageDraw.Draw(img)
        caption(draw, S["cap_sizer"])

    elif t < ends[6]:
        local = (t - ends[5]) / max(0.01, ends[6] - ends[5])
        screen = make_broker_screen(local)
        img = phone_frame(scene_bg(t, accent_y=0.92), screen, 10)
        draw = ImageDraw.Draw(img)
        caption(draw, S["cap_broker"])

    elif t < ends[7]:
        local = (t - ends[6]) / max(0.01, ends[7] - ends[6])
        screen = make_watchlist_screen(local)
        img = phone_frame(scene_bg(t, accent_y=0.92), screen, 10)
        draw = ImageDraw.Draw(img)
        caption(draw, S["cap_watch"])

    elif t < ends[8]:
        local = (t - ends[7]) / max(0.01, ends[8] - ends[7])
        screen = make_discipline_screen(local)
        img = phone_frame(scene_bg(t, accent_y=0.92), screen, 10)
        draw = ImageDraw.Draw(img)
        caption(draw, S["cap_disc"])

    elif t < ends[9]:
        local = (t - ends[8]) / max(0.01, ends[9] - ends[8])
        screen = make_coach_screen(local, S["coach_q1"], S["coach_a1"])
        img = phone_frame(scene_bg(t, accent_y=0.92), screen, 10)
        draw = ImageDraw.Draw(img)
        caption(draw, S["cap_coach1"])

    elif t < ends[10]:
        local = (t - ends[9]) / max(0.01, ends[10] - ends[9])
        screen = make_coach_screen(local, S["coach_q2"], S["coach_a2"], show_projection=True)
        img = phone_frame(scene_bg(t, accent_y=0.92), screen, 10)
        draw = ImageDraw.Draw(img)
        caption(draw, S["cap_coach2"])

    elif t < ends[11]:
        local = (t - ends[10]) / max(0.01, ends[11] - ends[10])
        screen = make_journal_impact(local)
        img = phone_frame(scene_bg(t, accent_y=0.92), screen, 10)
        draw = ImageDraw.Draw(img)
        caption(draw, S["cap_impact"])

    elif t < ends[12]:
        local = (t - ends[11]) / max(0.01, ends[12] - ends[11])
        screen = make_analytics_screen(local)
        img = phone_frame(scene_bg(t, accent_y=0.92), screen, 10)
        draw = ImageDraw.Draw(img)
        caption(draw, S["cap_analytics"])

    elif t < ends[13]:
        local = (t - ends[12]) / max(0.01, ends[13] - ends[12])
        draw_centered(draw, S["edge1"], H // 2 - 50, font("head", 52 if lang == "de" else 56), TEXT)
        if local > 0.3:
            draw_centered(draw, S["edge2"], H // 2 + 20, font("head", 36 if lang == "de" else 40), TEXT2)
            draw_centered(draw, S["edge3"], H // 2 + 80, font("head_italic", 44), ACCENT)

    elif t < ends[14]:
        # Keep lines within ~580px so 9:16 center-crop does not clip text.
        draw_centered(draw, S["inst"], H // 2, font("head", 40 if lang == "de" else 44), TEXT)

    else:
        # Big pulsing CTA
        pulse = 0.5 + 0.5 * math.sin(t * 7.0)
        scale = 1.0 + 0.08 * pulse
        glow_a = int(40 + 70 * pulse)
        icon = Image.open(ASSETS / "runnr-icon.png").convert("RGBA").resize((96, 96))
        img.paste(icon, (W // 2 - 48, H // 2 - 230), icon)
        draw = ImageDraw.Draw(img)
        draw_centered(draw, S["cta"], H // 2 - 90, font("head", 64), TEXT)

        label = "runnr.fyi"
        fnt = font("body_med", 34)
        tw = draw.textlength(label, font=fnt)
        pw = (tw + 96) * scale
        ph = 78 * scale
        x0 = (W - pw) / 2
        y0 = H // 2 + 10
        # outer glow pulse
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        pad = 18 + 10 * pulse
        gd.rounded_rectangle(
            (x0 - pad, y0 - pad, x0 + pw + pad, y0 + ph + pad),
            radius=int(22 + 4 * pulse),
            fill=(*ACCENT, glow_a),
        )
        glow = glow.filter(ImageFilter.GaussianBlur(18))
        img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
        draw = ImageDraw.Draw(img)
        rounded(draw, (x0, y0, x0 + pw, y0 + ph), 14, ACCENT)
        # center label in scaled button
        lx = x0 + (pw - tw) / 2
        ly = y0 + (ph - fnt.size) / 2 - 2
        draw.text((lx, ly), label, font=fnt, fill=BG)
        draw_centered(draw, S["tag"], H // 2 + 160, font("body", 24), TEXT2)

    return img


def main():
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", choices=["en", "de"], default="en")
    args = ap.parse_args()
    lang = args.lang
    cfg = LANG_CFG[lang]
    duration = cfg["duration"]
    total = int(duration * FPS)
    frames_dir = ROOT / cfg["frames"]
    out_stem = cfg["out"]
    audio = ASSETS / cfg["audio"]

    frames_dir.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for p in frames_dir.glob("*.jpg"):
        p.unlink()

    print(f"Rendering {lang.upper()} · {total} frames @ {FPS}fps ({duration}s)…")
    for i in range(total):
        render_frame(i, lang=lang).save(frames_dir / f"frame_{i:05d}.jpg", quality=92)
        if i % 150 == 0:
            print(f"  {i}/{total}")

    silent = OUTPUT / f"{out_stem}-silent.mp4"
    final = OUTPUT / f"{out_stem}.mp4"
    subprocess.check_call(
        [
            "ffmpeg", "-y", "-framerate", str(FPS),
            "-i", str(frames_dir / "frame_%05d.jpg"),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium",
            str(silent),
        ]
    )
    # Mix VO + subtle rising bed (bed duck under speech)
    bed = ASSETS / cfg.get("bed", "bed-rising.mp3")
    mixed_audio = OUTPUT / f"{out_stem}-mix.m4a"
    if bed.exists():
        subprocess.check_call(
            [
                "ffmpeg", "-y",
                "-i", str(audio),
                "-stream_loop", "-1", "-i", str(bed),
                "-filter_complex",
                "[0:a]volume=1.0,aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo[vo];"
                "[1:a]volume=0.16,highpass=f=80,lowpass=f=4000,"
                "afade=t=in:st=0:d=2,aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo[bed];"
                "[vo][bed]amix=inputs=2:duration=first:dropout_transition=2,loudnorm=I=-14:TP=-1.5:LRA=9[a]",
                "-map", "[a]", "-c:a", "aac", "-b:a", "192k", str(mixed_audio),
            ]
        )
        audio_for_mux = mixed_audio
    else:
        audio_for_mux = audio
    subprocess.check_call(
        [
            "ffmpeg", "-y",
            "-i", str(silent),
            "-i", str(audio_for_mux),
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
            str(final),
        ]
    )
    vertical = OUTPUT / f"{out_stem}-9x16.mp4"
    subprocess.check_call(
        [
            "ffmpeg", "-y", "-i", str(final),
            "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
            "-c:v", "libx264", "-crf", "20", "-c:a", "aac", "-b:a", "160k",
            str(vertical),
        ]
    )
    artifacts = Path("/opt/cursor/artifacts")
    artifacts.mkdir(parents=True, exist_ok=True)
    subprocess.check_call(["cp", str(final), str(artifacts / f"{out_stem}.mp4")])
    subprocess.check_call(["cp", str(vertical), str(artifacts / f"{out_stem}-9x16.mp4")])
    Image.open(frames_dir / f"frame_{int(7.5 * FPS):05d}.jpg").save(
        artifacts / f"{out_stem}-poster.jpg", quality=90
    )
    print("Done →", final)


if __name__ == "__main__":
    main()
