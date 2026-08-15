# Thin Ice Digital

Company site for [thinicedigital.com](https://thinicedigital.com) — Oxford software for traders and institutions.

Two products:

- **Runnr** — retail discipline system → [runnr.fyi](https://runnr.fyi)
- **Glacifraga** — institutional signals API

## Local preview

```bash
python3 -m http.server 4173
```

Open `http://localhost:4173`.

## Deploy

This repo is a static GitHub Pages site (no build step).

1. Settings → Pages → Deploy from branch `main`, folder `/` (root).
2. Custom domain: `thinicedigital.com` (the `CNAME` file is already in the repo).

Fonts are self-hosted (no Google Fonts request). Fill in street address, Geschäftsführer, and HRB on `impressum.html` once the commercial-register filing is public.
