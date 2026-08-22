# Runnr.fyi video advert

Horizon-style product launch advert for [Runnr](https://runnr.fyi/) — the discipline coach for traders.

## Deliverable

| File | Description |
|------|-------------|
| `output/runnr-advert.mp4` | English (~62s) · punchier Ryan + rising bed + pulse CTA |
| `output/runnr-advert-de.mp4` | German (~89s) · calm de-DE Conrad (−8% rate) |
| `output/runnr-advert-*-9x16.mp4` | Vertical crops |
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
# English
edge-tts --voice en-GB-RyanNeural --rate=+0% \
  --file runnr-advert/scripts/narration.txt \
  --write-media runnr-advert/assets/narration.mp3 \
  --write-subtitles runnr-advert/assets/narration.vtt
python3 runnr-advert/scripts/render_advert.py --lang en

# German (calm male)
edge-tts --voice de-DE-ConradNeural --rate=-8% \
  --file runnr-advert/scripts/narration-de.txt \
  --write-media runnr-advert/assets/narration-de.mp3 \
  --write-subtitles runnr-advert/assets/narration-de.vtt
python3 runnr-advert/scripts/render_advert.py --lang de
```


## Tune notes (EN v2)
- VO: `en-GB-RyanNeural` at +10% rate / +3Hz pitch / +5% volume
- Overlays shortened for punch
- Subtle rising pad bed under VO (`assets/bed-rising.mp3`)
- End CTA button larger with pulse glow
