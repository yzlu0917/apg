# NeurIPS LaTeX Draft

This directory contains the current anonymous NeurIPS-style manuscript draft.

Current template basis:

- official NeurIPS 2025 LaTeX style downloaded from the official NeurIPS site
- used as the latest official public template available at the time of writing
- as of `2026-03-15`, the NeurIPS 2026 style was not yet publicly posted, so the manuscript uses the current official public style as the submission base

Main entry point:

- `paper/main.tex`

Compile:

```bash
cd paper
pdflatex -interaction=nonstopmode main.tex
bibtex main
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
```

Notes:

- This is a submission-style anonymous draft, not a camera-ready version.
- The manuscript now includes a BibTeX-based reference list in `paper/references.bib`.
- The manuscript now also includes an appendix skeleton for calibration, benchmark acceptance, reproduction, and negative-result details.
- References and final figure assets still need venue-specific polish.
- The benchmark story is intentionally dual-regime:
  - naturalized full-hybrid is the main deployment benchmark
  - benchmark-v3 is the secondary cleaner audit benchmark
