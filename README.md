# Thin Ice Digital

Company site for [thinicedigital.com](https://thinicedigital.com). Software for traders and institutions, registered in England and Wales.

Two products:

- **Runnr** — retail discipline system → [runnr.fyi](https://runnr.fyi)
- **Glacifraga** — institutional signals API → [glacifraga.com](https://glacifraga.com)

## Local preview

```bash
python3 -m http.server 4173
```

Open `http://localhost:4173`.

## Deploy

The live domain [thinicedigital.com](https://thinicedigital.com) is GitHub Pages on `6tbwmzr522-crypto/thin-ice-digital` (Actions workflow, custom domain already attached).

This repo has the same workflow (`.github/workflows/pages.yml`). To publish:

1. Push these files to `6tbwmzr522-crypto/thin-ice-digital` on `main`, **or**
2. In that repo: Settings → Pages, then in **this** repo enable Pages (GitHub Actions) and move the `thinicedigital.com` custom domain across.

Fonts are self-hosted (no Google Fonts request). The registered office and Companies House number are on `impressum.html`.
