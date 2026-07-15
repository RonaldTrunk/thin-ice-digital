# RUNNR video advert

Horizon-style product launch advert for [RUNNR](https://www.runnrapp.com/) — the AI running coach.

## Deliverable

| File | Description |
|------|-------------|
| `output/runnr-advert.mp4` | Final 51s · 1920×1080 · narration + motion graphics |
| `assets/narration.mp3` | Voiceover (Edge TTS · AndrewNeural) |
| `assets/narration.vtt` | Timed captions |
| `scripts/narration.txt` | Script |
| `scripts/render_advert.py` | Regenerator |

Also copied to `/opt/cursor/artifacts/runnr-advert.mp4`.

## Structure (mirrors Horizon)

Same arc as [Horizon’s launch ad](https://x.com/horizon_trade_x/status/2077432988887822536):

1. **Hook** — “HASN’T CHANGED” kinetic type  
2. **Intro** — logo reveal + positioning  
3. **Product demo** — plain-language chat → plan adapts (knee / 10K / travel)  
4. **Payoff** — “No metrics. Just run.”  
5. **CTA** — runnrapp.com early access  

## Suggested X / social copy

> If you’re training without a coach, you’re someone else’s template.
>
> RUNNR is the AI running coach that turns plain-English updates into a plan that flexes around real life.
>
> Early access → https://runnrapp.com
>
> Here’s how it works:

## Regenerate

```bash
# voiceover
edge-tts --voice en-US-AndrewNeural --rate=+2% \
  --file runnr-advert/scripts/narration.txt \
  --write-media runnr-advert/assets/narration.mp3 \
  --write-subtitles runnr-advert/assets/narration.vtt

# video
python3 runnr-advert/scripts/render_advert.py
```

## Brand

- Background `#0a0a0a`
- Accent `#C1FF33`
- Logo from runnrapp.com
