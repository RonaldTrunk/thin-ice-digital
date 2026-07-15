#!/usr/bin/env python3
"""RUNNR product advert — Horizon-style kinetic + UI demo video."""

from __future__ import annotations

import math
import os
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
FRAMES = ROOT / "frames"
OUTPUT = ROOT / "output"

W, H = 1920, 1080
FPS = 30
DURATION = 51.0  # matches narration
TOTAL = int(DURATION * FPS)

BG = (10, 10, 10)
SURFACE = (26, 26, 26)
SURFACE2 = (34, 34, 34)
LIME = (193, 255, 51)
LIME_DIM = (168, 230, 41)
WHITE = (255, 255, 255)
MUTED = (180, 180, 180)
GRAY = (90, 90, 90)

FONT_DIR = "/usr/share/fonts/truetype"


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    paths = {
        "display": f"{FONT_DIR}/noto/NotoSansDisplay-Bold.ttf",
        "bold": f"{FONT_DIR}/macos/Inter-Bold.ttf",
        "semi": f"{FONT_DIR}/macos/Inter-SemiBold.ttf",
        "med": f"{FONT_DIR}/macos/Inter-Medium.ttf",
        "reg": f"{FONT_DIR}/macos/Inter-Regular.ttf",
    }
    return ImageFont.truetype(paths[name], size)


def ease_out_cubic(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def ease_in_out(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 3 * t * t - 2 * t * t * t


def lerp(a, b, t):
    return a + (b - a) * t


def clamp01(t: float) -> float:
    return max(0.0, min(1.0, t))


def vignette(img: Image.Image, strength: float = 0.45) -> Image.Image:
    arr = np.asarray(img).astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    cx, cy = W / 2, H / 2
    r = np.sqrt(((xx - cx) / (W * 0.72)) ** 2 + ((yy - cy) / (H * 0.72)) ** 2)
    factor = 1 - strength * np.clip(r - 0.35, 0, 1) ** 1.4
    arr[..., :3] *= factor[..., None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def radial_glow(base: Image.Image, color=LIME, y: float = 0.78, alpha: float = 0.12) -> Image.Image:
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g = ImageDraw.Draw(glow)
    cx, cy = W // 2, int(H * y)
    for i, r in enumerate(range(900, 40, -40)):
        a = int(255 * alpha * (1 - i / 22) ** 2)
        g.ellipse((cx - r, cy - r // 2, cx + r, cy + r // 2), fill=(*color, a))
    glow = glow.filter(ImageFilter.GaussianBlur(80))
    out = base.convert("RGBA")
    out = Image.alpha_composite(out, glow)
    return out.convert("RGB")


def draw_centered_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    y: int,
    fnt: ImageFont.FreeTypeFont,
    fill=WHITE,
    max_width: int | None = None,
):
    if max_width:
        # simple wrap
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
        lines = [text]
    line_h = fnt.size + 12
    total_h = len(lines) * line_h
    start_y = y - total_h // 2
    for i, line in enumerate(lines):
        tw = draw.textlength(line, font=fnt)
        draw.text(((W - tw) / 2, start_y + i * line_h), line, font=fnt, fill=fill)


def rounded_rect(draw, box, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def phone_frame(base: Image.Image, content: Image.Image, scale: float = 1.0, y_offset: int = 0) -> Image.Image:
    """Composite a phone mockup centered on base."""
    pw, ph = int(420 * scale), int(860 * scale)
    phone = Image.new("RGBA", (pw + 24, ph + 24), (0, 0, 0, 0))
    d = ImageDraw.Draw(phone)
    # outer glow
    d.rounded_rectangle((0, 0, pw + 23, ph + 23), radius=56, fill=(*LIME, 35))
    phone = phone.filter(ImageFilter.GaussianBlur(18))
    shell = Image.new("RGBA", (pw + 24, ph + 24), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shell)
    sd.rounded_rectangle((8, 8, pw + 15, ph + 15), radius=48, fill=(20, 20, 20, 255), outline=(*LIME, 90), width=2)
    # screen
    content = content.resize((pw - 16, ph - 16), Image.Resampling.LANCZOS)
    mask = Image.new("L", content.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, content.size[0] - 1, content.size[1] - 1), radius=40, fill=255)
    screen = Image.new("RGBA", content.size)
    screen.paste(content.convert("RGBA"), (0, 0))
    screen.putalpha(mask)
    shell.paste(screen, (16, 16), screen)
    # notch
    ImageDraw.Draw(shell).rounded_rectangle(
        (pw // 2 - 40, 22, pw // 2 + 56, 38), radius=8, fill=(10, 10, 10, 255)
    )
    composed = base.convert("RGBA")
    x = (W - shell.width) // 2
    y = (H - shell.height) // 2 + y_offset
    composed.alpha_composite(phone, (x - 4, y - 4))
    composed.alpha_composite(shell, (x, y))
    return composed.convert("RGB")


def make_chat_screen(
    messages: list[tuple[str, str]],
    progress: float,
    plan_card: dict | None = None,
) -> Image.Image:
    """Build phone chat UI. messages: (role, text) role in user|coach."""
    screen = Image.new("RGB", (404, 844), BG)
    d = ImageDraw.Draw(screen)
    # header
    d.rectangle((0, 0, 404, 96), fill=SURFACE)
    logo = Image.open(ASSETS / "runnr-logo.png").convert("RGBA").resize((28, 28))
    screen.paste(logo, (20, 34), logo)
    d.text((58, 30), "RUNNR", font=font("bold", 22), fill=WHITE)
    d.text((58, 56), "Your AI Coach", font=font("med", 14), fill=LIME)

    visible = max(1, int(len(messages) * clamp01(progress) + 0.01))
    y = 120
    f_body = font("reg", 16)
    for i, (role, text) in enumerate(messages[:visible]):
        # type-on for last message
        show = text
        if i == visible - 1 and progress < 1:
            frac = (progress * len(messages)) % 1
            show = text[: max(1, int(len(text) * ease_out_cubic(frac)))]

        # wrap
        words = show.split(" ")
        lines, cur = [], ""
        max_w = 240
        for w in words:
            trial = f"{cur} {w}".strip()
            if d.textlength(trial, font=f_body) <= max_w:
                cur = trial
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        bh = 20 + len(lines) * 22
        if role == "user":
            x0 = 404 - 28 - 260
            rounded_rect(d, (x0, y, x0 + 260, y + bh), 16, (40, 55, 18))
            d.rounded_rectangle((x0, y, x0 + 260, y + bh), radius=16, outline=(*LIME, ), width=1)
            for li, line in enumerate(lines):
                d.text((x0 + 14, y + 10 + li * 22), line, font=f_body, fill=WHITE)
        else:
            x0 = 20
            # avatar
            d.ellipse((x0, y, x0 + 28, y + 28), fill=LIME)
            d.text((x0 + 8, y + 4), "R", font=font("bold", 14), fill=BG)
            rounded_rect(d, (x0 + 36, y, x0 + 36 + 260, y + bh), 16, SURFACE2)
            for li, line in enumerate(lines):
                d.text((x0 + 50, y + 10 + li * 22), line, font=f_body, fill=WHITE)
        y += bh + 16

    if plan_card and progress > 0.55:
        alpha_t = ease_out_cubic((progress - 0.55) / 0.45)
        cy = y + 8
        rounded_rect(d, (20, cy, 384, cy + 78), 16, (30, 40, 12))
        d.rounded_rectangle((20, cy, 384, cy + 78), radius=16, outline=LIME, width=1)
        d.ellipse((36, cy + 20, 68, cy + 52), fill=LIME)
        d.text((78, cy + 18), plan_card["title"], font=font("semi", 16), fill=WHITE)
        d.text((78, cy + 44), plan_card["sub"], font=font("reg", 13), fill=MUTED)
        d.text((320, cy + 30), "View", font=font("semi", 14), fill=LIME)
        # fade-in via overlay
        if alpha_t < 1:
            overlay = Image.new("RGB", screen.size, BG)
            screen = Image.blend(overlay, screen, 0.55 + 0.45 * alpha_t)

    # bottom nav
    d.rectangle((0, 780, 404, 844), fill=SURFACE)
    for i, label in enumerate(["Today", "Coach", "Stats", "You"]):
        cx = 50 + i * 90
        col = LIME if i == 1 else GRAY
        d.ellipse((cx, 798, cx + 10, 808), fill=col)
        d.text((cx - 10, 814), label, font=font("reg", 11), fill=col)

    return screen


def make_week_plan_screen(progress: float) -> Image.Image:
    screen = Image.new("RGB", (404, 844), BG)
    d = ImageDraw.Draw(screen)
    d.rectangle((0, 0, 404, 88), fill=SURFACE)
    d.text((24, 28), "This week", font=font("bold", 24), fill=WHITE)
    d.text((24, 58), "Built for your 10K · 3 days", font=font("reg", 13), fill=LIME)

    days = [
        ("Mon", "Easy 4 mi", "Recovery pace", True),
        ("Wed", "Intervals 5x400", "Build speed", True),
        ("Fri", "Rest / walk", "Travel day", False),
        ("Sat", "Long 6 mi", "Hotel treadmill OK", True),
        ("Sun", "Rest", "Recover", False),
    ]
    y = 110
    n = max(1, int(math.ceil(len(days) * clamp01(0.15 + 0.85 * progress))))
    for i, (day, title, sub, run) in enumerate(days[:n]):
        rounded_rect(d, (20, y, 384, y + 78), 16, SURFACE2)
        d.ellipse((34, y + 20, 66, y + 52), fill=LIME if run else (60, 60, 60))
        d.text((42, y + 26), day[:1], font=font("bold", 15), fill=BG if run else MUTED)
        d.text((84, y + 18), title, font=font("semi", 16), fill=WHITE)
        d.text((84, y + 44), sub, font=font("reg", 12), fill=MUTED)
        if run:
            d.text((300, y + 30), "Ready", font=font("semi", 12), fill=LIME)
        y += 90

    return screen


def scene_bg(t: float, glow_y: float = 0.85) -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    img = radial_glow(img, LIME, y=glow_y, alpha=0.10 + 0.02 * math.sin(t * 1.4))
    return vignette(img, 0.5)


def word_blasts(draw, words: list[str], t_local: float, color=LIME):
    """Kinetic single/few word overlays like Horizon."""
    fnt = font("display", 96)
    # cycle words
    if not words:
        return
    idx = min(len(words) - 1, int(t_local * len(words)))
    word = words[idx]
    frag = (t_local * len(words)) % 1
    alpha = ease_out_cubic(min(1, frag * 3)) if frag < 0.85 else ease_out_cubic((1 - frag) / 0.15)
    # can't easily do alpha on text with RGB; approximate by blending color
    col = tuple(int(c * (0.35 + 0.65 * alpha)) for c in color)
    tw = draw.textlength(word, font=fnt)
    draw.text(((W - tw) / 2, H // 2 - 60), word, font=fnt, fill=col)


def render_frame(i: int) -> Image.Image:
    t = i / FPS
    img = scene_bg(t)
    draw = ImageDraw.Draw(img)

    # --- SCENE TIMELINE ---
    if t < 3.4:
        #hasn't changed
        words = ["HASN'T", "CHANGED", "20 YEARS"]
        word_blasts(draw, words, t / 3.4, LIME)
        draw_centered_text(draw, "The running app workflow", H // 2 + 80, font("med", 28), MUTED)

    elif t < 5.1:
        local = (t - 3.4) / 1.7
        s = ease_out_cubic(local)
        fnt = font("display", int(lerp(72, 120, s)))
        draw_centered_text(draw, "Today", H // 2 - 20, fnt, WHITE)
        draw_centered_text(draw, "we're changing that", H // 2 + 70, font("med", 32), MUTED)

    elif t < 7.0:
        local = (t - 5.1) / 1.9
        s = ease_out_cubic(local)
        logo = Image.open(ASSETS / "runnr-logo.png").convert("RGBA")
        size = int(lerp(80, 160, s))
        logo = logo.resize((size, size))
        # glow behind logo
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        cx, cy = W // 2, H // 2 - 40
        gd.ellipse((cx - 120, cy - 120, cx + 120, cy + 120), fill=(*LIME, int(60 * s)))
        glow = glow.filter(ImageFilter.GaussianBlur(40))
        img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
        draw = ImageDraw.Draw(img)
        img.paste(logo, (cx - size // 2, cy - size // 2), logo)
        draw = ImageDraw.Draw(img)
        fnt = font("display", int(72 * s + 1))
        tw = draw.textlength("RUNNR", font=fnt)
        draw.text(((W - tw) / 2, cy + size // 2 + 20), "RUNNR", font=fnt, fill=WHITE)

    elif t < 10.7:
        local = (t - 7.0) / 3.7
        draw_centered_text(draw, "Your personal AI running coach.", H // 2 - 40, font("display", 52), WHITE, max_width=1400)
        c = LIME if local > 0.35 else MUTED
        draw_centered_text(draw, "Built for real life.", H // 2 + 50, font("semi", 36), c)

    elif t < 12.3:
        draw_centered_text(draw, "Let me show you how it works.", H // 2, font("display", 48), WHITE, max_width=1400)

    elif t < 14.57:
        # empty chat intro
        screen = make_chat_screen([], 0)
        # input prompt overlay on dark
        img = phone_frame(img, screen, scale=1.0, y_offset=20)
        draw = ImageDraw.Draw(img)
        draw_centered_text(draw, "telling your coach", H - 90, font("semi", 36), WHITE)

    elif t < 17.62:
        local = (t - 14.57) / 3.05
        msgs = [
            ("coach", "Hey! How's your knee feeling today?"),
            ("user", "A bit sore from yesterday, but manageable!"),
            ("coach", "Got it. I've adjusted today's run to an easy 3 miles with walking breaks."),
        ]
        screen = make_chat_screen(
            msgs,
            local,
            plan_card={"title": "Today's Run Updated", "sub": "Easy 3mi · Recovery pace"},
        )
        img = phone_frame(scene_bg(t, 0.9), screen, 1.0, 10)
        draw = ImageDraw.Draw(img)
        draw_centered_text(draw, "my knee's a bit sore", H - 80, font("semi", 32), WHITE)

    elif t < 22.07:
        local = (t - 17.62) / 4.45
        msgs = [
            ("user", "I have a 10K in 8 weeks and can only run 3 days."),
            ("coach", "Perfect. Building a 3-day plan around your race — no filler miles."),
        ]
        screen = make_chat_screen(msgs, min(1, local * 1.4))
        if local > 0.45:
            plan = make_week_plan_screen((local - 0.45) / 0.55)
            # crossfade-ish: show plan
            screen = plan
        img = phone_frame(scene_bg(t, 0.9), screen, 1.0, 10)
        draw = ImageDraw.Draw(img)
        draw_centered_text(draw, "10K in eight weeks", H - 80, font("semi", 32), WHITE)

    elif t < 25.83:
        local = (t - 22.07) / 3.76
        msgs = [
            ("user", "Traveling this weekend — hotel gym only."),
            ("coach", "Swapped your long run for a treadmill session. Same stimulus, flexible."),
        ]
        screen = make_chat_screen(
            msgs,
            local,
            plan_card={"title": "Weekend Adjusted", "sub": "Treadmill long · 45 min"},
        )
        img = phone_frame(scene_bg(t, 0.9), screen, 1.0, 10)
        draw = ImageDraw.Draw(img)
        draw_centered_text(draw, "hotel gym only", H - 80, font("semi", 32), WHITE)

    elif t < 31.38:
        local = (t - 25.83) / 5.55
        # agent working montage — steps
        img = scene_bg(t, 0.75)
        draw = ImageDraw.Draw(img)
        draw_centered_text(draw, "RUNNR goes to work", 180, font("display", 48), WHITE)
        steps = [
            "Syncs your runs automatically",
            "Adapts the plan to how you feel",
            "Explains the next session in plain language",
        ]
        for i, step in enumerate(steps):
            appear = ease_out_cubic(clamp01((local - i * 0.22) / 0.25))
            if appear <= 0:
                continue
            y = 320 + i * 110
            box = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            bd = ImageDraw.Draw(box)
            x0 = int(lerp(W // 2 - 100, W // 2 - 420, appear))
            bd.rounded_rectangle((x0, y, x0 + 840, y + 84), radius=20, fill=(*SURFACE2, int(230 * appear)))
            bd.ellipse((x0 + 28, y + 26, x0 + 60, y + 58), fill=(*LIME, int(255 * appear)))
            bd.text((x0 + 80, y + 26), step, font=font("semi", 28), fill=(*WHITE, int(255 * appear)))
            img = Image.alpha_composite(img.convert("RGBA"), box).convert("RGB")
        draw = ImageDraw.Draw(img)
        draw_centered_text(draw, "exactly what to do next", H - 90, font("semi", 28), MUTED)

    elif t < 35.44:
        local = (t - 31.38) / 4.06
        phrases = [
            (0.0, "No metrics to track."),
            (0.35, "No data to analyze."),
            (0.70, "Just run."),
        ]
        current = phrases[0][1]
        for start, text in phrases:
            if local >= start:
                current = text
        big = current == "Just run."
        fnt = font("display", 92 if big else 56)
        col = LIME if big else WHITE
        draw_centered_text(draw, current, H // 2, fnt, col)

    elif t < 40.86:
        local = (t - 35.44) / 5.42
        draw_centered_text(draw, "Imagine", int(H * 0.38), font("display", 100), WHITE)
        sub = "a coach that flexes around your life"
        alpha = ease_out_cubic(clamp01((local - 0.25) / 0.4))
        col = tuple(int(c * alpha) for c in LIME) if alpha > 0 else (0, 0, 0)
        if alpha > 0:
            draw_centered_text(draw, sub, int(H * 0.55), font("semi", 36), col if alpha > 0.5 else MUTED, max_width=1200)

    elif t < 43.63:
        local = (t - 40.86) / 2.77
        draw_centered_text(draw, "Version one.", H // 2 - 40, font("display", 64), WHITE)
        if local > 0.4:
            draw_centered_text(draw, "It's just the beginning.", H // 2 + 50, font("semi", 36), LIME)

    elif t < 48.35:
        draw_centered_text(
            draw,
            "Early access for runners who want a coach —\nnot another spreadsheet.",
            H // 2,
            font("display", 44),
            WHITE,
            max_width=1500,
        )

    else:
        # CTA
        local = (t - 48.35) / (DURATION - 48.35)
        s = ease_out_cubic(local)
        logo = Image.open(ASSETS / "runnr-logo.png").convert("RGBA").resize((96, 96))
        img.paste(logo, (W // 2 - 48, H // 2 - 180), logo)
        draw = ImageDraw.Draw(img)
        draw_centered_text(draw, "Get notified", H // 2 - 40, font("display", 56), WHITE)
        # CTA pill
        label = "runnrapp.com"
        fnt = font("bold", 28)
        tw = draw.textlength(label, font=fnt)
        pw, ph = tw + 64, 64
        x0 = (W - pw) / 2
        y0 = H // 2 + 40
        rounded_rect(draw, (x0, y0, x0 + pw, y0 + ph), 18, LIME)
        draw.text((x0 + 32, y0 + 16), label, font=fnt, fill=BG)
        draw_centered_text(draw, "Coming soon to iOS", H // 2 + 150, font("med", 24), MUTED)

    return img


def main():
    FRAMES.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)

    print(f"Rendering {TOTAL} frames @ {FPS}fps ({DURATION}s)…")
    for i in range(TOTAL):
        frame = render_frame(i)
        frame.save(FRAMES / f"frame_{i:05d}.jpg", quality=92, optimize=True)
        if i % 60 == 0:
            print(f"  {i}/{TOTAL} ({100 * i / TOTAL:.0f}%)")

    print("Encoding video…")
    silent = OUTPUT / "runnr-advert-silent.mp4"
    final = OUTPUT / "runnr-advert.mp4"
    subprocess.check_call(
        [
            "ffmpeg",
            "-y",
            "-framerate",
            str(FPS),
            "-i",
            str(FRAMES / "frame_%05d.jpg"),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-crf",
            "18",
            "-preset",
            "medium",
            str(silent),
        ]
    )
    subprocess.check_call(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(silent),
            "-i",
            str(ASSETS / "narration.mp3"),
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            str(final),
        ]
    )
    # artifacts copy
    artifacts = Path("/opt/cursor/artifacts")
    artifacts.mkdir(parents=True, exist_ok=True)
    subprocess.check_call(["cp", str(final), str(artifacts / "runnr-advert.mp4")])
    # poster
    Image.open(FRAMES / "frame_00180.jpg").save(artifacts / "runnr-advert-poster.jpg", quality=90)
    print("Done →", final)


if __name__ == "__main__":
    main()
