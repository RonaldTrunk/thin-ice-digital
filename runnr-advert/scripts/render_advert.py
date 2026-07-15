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
FRAMES = ROOT / "frames"
OUTPUT = ROOT / "output"

W, H = 1920, 1080
FPS = 30
DURATION = 52.0
TOTAL = int(DURATION * FPS)

BG = (8, 12, 18)
SURFACE = (12, 17, 24)
SURFACE2 = (16, 22, 32)
SURFACE3 = (22, 29, 40)
GOLD = (201, 169, 110)
GOLD_LIGHT = (232, 201, 122)
ACCENT = (0, 229, 160)
ACCENT2 = (0, 184, 122)
TEXT = (245, 242, 236)
TEXT2 = (160, 157, 150)
TEXT3 = (100, 98, 94)
RED = (232, 93, 111)


def font(kind: str, size: int) -> ImageFont.FreeTypeFont:
    # Mapped from Google CSS download order in assets/fonts
    paths = {
        "head": FONTS / "font_3.ttf",  # Cormorant 400
        "head_med": FONTS / "font_4.ttf",  # Cormorant 500
        "head_semi": FONTS / "font_5.ttf",  # Cormorant 600
        "head_light": FONTS / "font_2.ttf",  # Cormorant 300
        "head_italic": FONTS / "font_1.ttf",  # Cormorant italic 400
        "body": FONTS / "font_7.ttf",  # Jost 400
        "body_light": FONTS / "font_6.ttf",  # Jost 300
        "body_med": FONTS / "font_8.ttf",  # Jost 500
    }
    p = paths[kind]
    return ImageFont.truetype(str(p), size)


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
    # gold wash top (brand)
    cx, cy = W // 2, int(H * gold_y - 80)
    for i, r in enumerate(range(1100, 80, -50)):
        a = int(28 * (1 - i / 22) ** 2)
        g.ellipse((cx - r, cy - r // 2, cx + r, cy + r // 2), fill=(*GOLD, a))
    # accent wash bottom
    cx2, cy2 = W // 2, int(H * accent_y)
    for i, r in enumerate(range(800, 40, -40)):
        a = int(22 * (1 - i / 20) ** 2 * (0.85 + 0.15 * math.sin(t * 1.2)))
        g.ellipse((cx2 - r, cy2 - r // 2, cx2 + r, cy2 + r // 2), fill=(*ACCENT, a))
    glow = glow.filter(ImageFilter.GaussianBlur(90))
    out = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
    return vignette(out, 0.48)


def draw_centered(
    draw: ImageDraw.ImageDraw,
    text: str,
    y: int,
    fnt: ImageFont.FreeTypeFont,
    fill=TEXT,
    max_width: int | None = None,
    tracking: float = 0,
):
    if max_width:
        words = text.split()
        lines, cur = [], ""
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
    # soft gold rim glow
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
    # status bar
    ImageDraw.Draw(shell).text((36, 28), "9:41", font=font("body_med", 13), fill=TEXT)
    ImageDraw.Draw(shell).rounded_rectangle((pw // 2 - 36, 24, pw // 2 + 52, 36), radius=6, fill=(10, 10, 10, 255))

    composed = base.convert("RGBA")
    x = (W - shell.width) // 2
    y = (H - shell.height) // 2 + y_offset
    composed.alpha_composite(glow, (x - 2, y - 2))
    composed.alpha_composite(shell, (x, y))
    return composed.convert("RGB")


def app_header(d: ImageDraw.ImageDraw, w: int):
    d.rectangle((0, 0, w, 72), fill=(8, 12, 18))
    d.rectangle((18, 26, 20, 48), fill=GOLD)  # brand mark
    d.text((30, 22), "runnr", font=font("head_italic", 28), fill=TEXT)
    rounded(d, (w - 118, 22, w - 18, 46), 12, (40, 34, 24), outline=GOLD, width=1)
    d.text((w - 108, 26), "NOVICE", font=font("body_med", 11), fill=GOLD)


def app_nav(d: ImageDraw.ImageDraw, w: int, h: int, active: int = 0):
    d.rectangle((0, h - 70, w, h), fill=SURFACE)
    labels = ["Home", "Size", "Journal", "Coach", "Markets"]
    for i, lab in enumerate(labels):
        cx = 20 + i * (w // 5) + 18
        col = ACCENT if i == active else TEXT3
        d.ellipse((cx + 12, h - 54, cx + 22, h - 44), fill=col)
        d.text((cx, h - 36), lab, font=font("body_med", 9), fill=col)


def make_sizer_screen(progress: float) -> Image.Image:
    w, h = 410, 860
    screen = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(screen)
    app_header(d, w)

    d.text((18, 90), "SHARES POSITION SIZER", font=font("body_med", 10), fill=GOLD)
    # Baron preset pill
    rounded(d, (18, 118, 200, 148), 14, (40, 34, 24), outline=GOLD, width=1)
    d.text((30, 124), "Baron Preset  ·  1% risk", font=font("body", 12), fill=GOLD_LIGHT)

    fields = [
        ("TICKER", "NVDA"),
        ("ENTRY", "128.40"),
        ("STOP LOSS", "124.10"),
        ("TARGET", "136.90"),
    ]
    y = 168
    shown = max(1, int(len(fields) * clamp01(progress * 1.2) + 0.01))
    for label, val in fields[:shown]:
        d.text((22, y), label, font=font("body_med", 9), fill=GOLD)
        rounded(d, (18, y + 18, w - 18, y + 58), 6, SURFACE2, outline=(60, 50, 35), width=1)
        d.text((30, y + 28), val, font=font("head", 20), fill=TEXT)
        y += 72

    if progress > 0.55:
        a = ease_out((progress - 0.55) / 0.45)
        box_y = y + 8
        rounded(d, (18, box_y, w - 18, box_y + 150), 12, (28, 36, 28), outline=GOLD, width=1)
        d.text((w // 2 - 40, box_y + 18), "MAX SHARES", font=font("body_med", 10), fill=TEXT3)
        d.text((w // 2 - 70, box_y + 40), "232", font=font("head_med", 48), fill=ACCENT)
        # sub metrics
        for i, (lab, val) in enumerate([("RISK", "€100"), ("R:R", "2.0"), ("REWARD", "€200")]):
            x0 = 40 + i * 120
            d.text((x0, box_y + 100), lab, font=font("body_med", 9), fill=TEXT3)
            d.text((x0, box_y + 116), val, font=font("head", 18), fill=TEXT)

    app_nav(d, w, h, active=1)
    return screen


def make_discipline_screen(progress: float) -> Image.Image:
    w, h = 410, 860
    screen = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(screen)
    app_header(d, w)

    d.text((18, 90), "DISCIPLINE SCORE", font=font("body_med", 10), fill=GOLD)
    # ring
    cx, cy, r = w // 2, 240, 78
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=SURFACE3, width=10)
    # arc approx with chord segments based on progress
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

    # metric grid
    metrics = [
        ("Stop", "82%"),
        ("Size", "91%"),
        ("Profit Factor", "1.8"),
        ("Win Rate", "58%"),
    ]
    y = 360
    for i, (lab, val) in enumerate(metrics):
        if progress < 0.25 + i * 0.15:
            continue
        x0 = 18 if i % 2 == 0 else w // 2 + 4
        if i == 2:
            y = 460
        if i == 3:
            y = 460
        yy = 360 if i < 2 else 470
        xx = 18 if i % 2 == 0 else w // 2 + 4
        rounded(d, (xx, yy, xx + w // 2 - 22, yy + 90), 12, SURFACE, outline=(50, 42, 30), width=1)
        d.text((xx + 16, yy + 18), lab.upper(), font=font("body_med", 9), fill=GOLD)
        d.text((xx + 16, yy + 40), val, font=font("head_med", 32), fill=TEXT if i > 0 else ACCENT)

    app_nav(d, w, h, active=0)
    return screen


def make_coach_screen(progress: float, prompt: str, answer_lines: list[str]) -> Image.Image:
    w, h = 410, 860
    screen = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(screen)
    app_header(d, w)

    d.text((18, 90), "COACH INSIGHTS", font=font("body_med", 10), fill=GOLD)
    d.text((18, 118), "Ask about patterns in your own trade data", font=font("body_light", 13), fill=TEXT2)

    # user chip
    rounded(d, (60, 170, w - 18, 230), 14, SURFACE3)
    show = prompt[: max(1, int(len(prompt) * ease_out(min(1, progress * 2))))]
    # wrap
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

    if progress > 0.4:
        rounded(d, (18, 250, w - 18, 520), 12, SURFACE, outline=(50, 42, 30), width=1)
        d.text((32, 268), "WEEKLY · AI", font=font("body_med", 9), fill=ACCENT)
        ans_progress = ease_out((progress - 0.4) / 0.6)
        n = max(1, int(len(answer_lines) * ans_progress + 0.01))
        yy = 300
        for line in answer_lines[:n]:
            # simple wrap
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

    # projection strip
    if progress > 0.75:
        rounded(d, (18, 540, w - 18, 680), 12, (28, 22, 16), outline=GOLD, width=1)
        d.text((32, 556), "MONTHLY EQUITY PROJECTION", font=font("body_med", 9), fill=GOLD)
        d.text((40, 590), "-€180", font=font("head_med", 28), fill=RED)
        d.text((40, 628), "ACTUAL", font=font("body_med", 10), fill=TEXT3)
        d.text((210, 590), "+€1,240", font=font("head_med", 28), fill=ACCENT)
        d.text((210, 628), "WITH RUNNR RULES", font=font("body_med", 10), fill=TEXT3)

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
        if progress < 0.15 + i * 0.18:
            break
        rounded(d, (18, y, w - 18, y + 88), 12, SURFACE, outline=(50, 42, 30), width=1)
        d.text((34, y + 18), lab.upper(), font=font("body_med", 10), fill=GOLD)
        d.text((34, y + 42), val, font=font("head_med", 32), fill=col)
        y += 100

    app_nav(d, w, h, active=2)
    return screen


def caption(draw, text: str):
    draw_centered(draw, text, H - 78, font("body_med", 28), TEXT)


def render_frame(i: int) -> Image.Image:
    t = i / FPS
    img = scene_bg(t)
    draw = ImageDraw.Draw(img)

    if t < 3.4:
        words = ["HASN'T", "CHANGED", "20 YEARS"]
        idx = min(len(words) - 1, int((t / 3.4) * len(words)))
        word = words[idx]
        draw_centered(draw, word, H // 2 - 30, font("head_semi", 96), GOLD)
        draw_centered(draw, "The trading workflow", H // 2 + 70, font("body", 26), TEXT2)

    elif t < 5.04:
        draw_centered(draw, "Today", H // 2 - 30, font("head_italic", 110), TEXT)
        draw_centered(draw, "we're changing that", H // 2 + 70, font("body", 28), TEXT2)

    elif t < 6.4:
        local = ease_out((t - 5.04) / 1.36)
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

    elif t < 9.68:
        draw_centered(draw, "The discipline coach", H // 2 - 50, font("head", 56), TEXT, max_width=1400)
        draw_centered(draw, "for traders who already know their edge", H // 2 + 40, font("body", 28), GOLD_LIGHT, max_width=1200)

    elif t < 11.27:
        draw_centered(draw, "Let me show you how it works.", H // 2, font("head", 48), TEXT, max_width=1400)

    elif t < 16.86:
        local = (t - 11.27) / 5.59
        screen = make_sizer_screen(local)
        img = phone_frame(scene_bg(t, accent_y=0.92), screen, 10)
        draw = ImageDraw.Draw(img)
        caption(draw, "risk one percent · stop set · 2R")

    elif t < 20.75:
        local = (t - 16.86) / 3.89
        screen = make_discipline_screen(local)
        img = phone_frame(scene_bg(t, accent_y=0.92), screen, 10)
        draw = ImageDraw.Draw(img)
        caption(draw, "scores the discipline — not just P&L")

    elif t < 23.79:
        local = (t - 20.75) / 3.04
        screen = make_coach_screen(
            local,
            "Why do I cut winners early?",
            [
                "You exit at +0.8R on winning NVDA setups — your plan says 2R.",
                "Cutting winners early cost €640 this month.",
            ],
        )
        img = phone_frame(scene_bg(t, accent_y=0.92), screen, 10)
        draw = ImageDraw.Draw(img)
        caption(draw, "why do I cut winners early?")

    elif t < 27.89:
        local = (t - 23.79) / 4.1
        screen = make_coach_screen(
            local,
            "P&L if I followed rules 100%?",
            [
                "If every trade followed Runnr rules this month:",
            ],
        )
        img = phone_frame(scene_bg(t, accent_y=0.92), screen, 10)
        draw = ImageDraw.Draw(img)
        caption(draw, "rules on every trade")

    elif t < 33.37:
        local = (t - 27.89) / 5.48
        screen = make_journal_impact(local)
        img = phone_frame(scene_bg(t, accent_y=0.92), screen, 10)
        draw = ImageDraw.Draw(img)
        caption(draw, "money discipline would have saved")

    elif t < 38.38:
        local = (t - 33.37) / 5.01
        phrases = [
            (0.0, "Stop confirmation."),
            (0.28, "Size discipline."),
            (0.52, "Profit factor."),
            (0.76, "All in one place."),
        ]
        current = phrases[0][1]
        for start, text in phrases:
            if local >= start:
                current = text
        col = ACCENT if current.startswith("All") else TEXT
        draw_centered(draw, current, H // 2, font("head", 64 if not current.startswith("All") else 56), col)

    elif t < 42.11:
        local = (t - 38.38) / 3.73
        draw_centered(draw, "Your edge works.", H // 2 - 50, font("head", 56), TEXT)
        if local > 0.35:
            draw_centered(draw, "Your discipline doesn't —", H // 2 + 20, font("head", 40), TEXT2)
            draw_centered(draw, "until it does.", H // 2 + 80, font("head_italic", 44), ACCENT)

    elif t < 44.88:
        draw_centered(draw, "Version one.", H // 2 - 30, font("head", 64), TEXT)
        draw_centered(draw, "It's just the beginning.", H // 2 + 50, font("body", 28), GOLD_LIGHT)

    elif t < 49.47:
        draw_centered(
            draw,
            "Institutional habits.\nWithout the institutional stack.",
            H // 2,
            font("head", 48),
            TEXT,
            max_width=1500,
        )

    else:
        icon = Image.open(ASSETS / "runnr-icon.png").convert("RGBA").resize((88, 88))
        img.paste(icon, (W // 2 - 44, H // 2 - 200), icon)
        draw = ImageDraw.Draw(img)
        draw_centered(draw, "Get started", H // 2 - 60, font("head", 56), TEXT)
        label = "runnr.fyi"
        fnt = font("body_med", 26)
        tw = draw.textlength(label, font=fnt)
        pw, ph = tw + 64, 58
        x0 = (W - pw) / 2
        y0 = H // 2 + 20
        rounded(draw, (x0, y0, x0 + pw, y0 + ph), 8, ACCENT)
        draw.text((x0 + 32, y0 + 14), label, font=fnt, fill=BG)
        draw_centered(draw, "Discipline over dopamine", H // 2 + 130, font("body", 22), TEXT2)

    return img


def main():
    FRAMES.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    # clear old frames
    for p in FRAMES.glob("*.jpg"):
        p.unlink()

    print(f"Rendering {TOTAL} frames @ {FPS}fps ({DURATION}s)…")
    for i in range(TOTAL):
        render_frame(i).save(FRAMES / f"frame_{i:05d}.jpg", quality=92)
        if i % 90 == 0:
            print(f"  {i}/{TOTAL}")

    silent = OUTPUT / "runnr-advert-silent.mp4"
    final = OUTPUT / "runnr-advert.mp4"
    subprocess.check_call(
        [
            "ffmpeg", "-y", "-framerate", str(FPS),
            "-i", str(FRAMES / "frame_%05d.jpg"),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium",
            str(silent),
        ]
    )
    subprocess.check_call(
        [
            "ffmpeg", "-y",
            "-i", str(silent),
            "-i", str(ASSETS / "narration.mp3"),
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
            str(final),
        ]
    )
    vertical = OUTPUT / "runnr-advert-9x16.mp4"
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
    subprocess.check_call(["cp", str(final), str(artifacts / "runnr-advert.mp4")])
    subprocess.check_call(["cp", str(vertical), str(artifacts / "runnr-advert-9x16.mp4")])
    Image.open(FRAMES / f"frame_{int(6.1*FPS):05d}.jpg").save(artifacts / "runnr-advert-poster.jpg", quality=90)
    print("Done →", final)


if __name__ == "__main__":
    main()
