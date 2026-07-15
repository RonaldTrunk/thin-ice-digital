# Runnr.fyi video advert

Horizon-style product launch advert for [Runnr](https://runnr.fyi/) — the discipline coach for traders.

## Deliverable

| File | Description |
|------|-------------|
| `output/runnr-advert.mp4` | Final ~82s · 1920×1080 · narration + motion graphics |
| `output/runnr-advert-9x16.mp4` | Vertical crop for Stories / Reels |
| `assets/narration.mp3` | Voiceover (Edge TTS · en-GB-RyanNeural) |
| `assets/narration.vtt` | Timed captions |
| `scripts/narration.txt` | Script |
| `scripts/render_advert.py` | Regenerator |

## Structure (mirrors Horizon)

Same arc as [Horizon’s launch ad](https://x.com/horizon_trade_x/status/2077432988887822536):

1. **Hook** — trading workflow hasn’t changed  
2. **Intro** — runnr logo + “discipline coach”  
3. **Product demo** — sizer → broker sync → watchlist → discipline score → coach → P&L impact → equity/heatmap  
4. **Payoff** — your edge works · your discipline doesn’t — until it does  
5. **CTA** — runnr.fyi  

## Suggested X / social copy

> If you’re trading without discipline, you’re someone else’s liquidity.
>
> Runnr is the coach that scores your process — not just your P&L. Size to rules, journal the trade, see what leaks cost you.
>
> Get started → https://runnr.fyi
>
> Here’s how it works:

## Brand

- Background `#080c12`
- Gold `#C9A96E`
- Accent `#00e5a0`
- Type: Cormorant Garamond + Jost (from runnr.fyi)

## Regenerate

```bash
edge-tts --voice en-US-AndrewNeural --rate=+2% \
  --file runnr-advert/scripts/narration.txt \
  --write-media runnr-advert/assets/narration.mp3 \
  --write-subtitles runnr-advert/assets/narration.vtt

python3 runnr-advert/scripts/render_advert.py
```
