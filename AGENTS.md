# Repository instructions

- `cv.md` is the single source of truth. Do not edit generated DOCX, PDF, or HTML directly.
- `README.md` is a symlink to `cv.md`, so GitHub renders the CV on the repository front page.
- Keep the Markdown readable as a standalone document.
- Keep web and print styling together in `style.css`.
- `reference/` contains the editable, decomposed DOCX reference package. The build deterministically creates `.build/reference.docx`; do not track a binary reference DOCX.
- Keep the bundled Carlito and Caladea files and their SIL Open Font Licenses under `fonts/`; they are metric-compatible alternatives to Calibri and Cambria, make local and CI PDF typography deterministic, and are embedded in the generated DOCX.

## Build

Install [mise](https://mise.jdx.dev/) and the native Pango library on macOS, then build:

```sh
brew install pango
mise install
mise run build
```

Mise supplies Pandoc, Python, and WeasyPrint 69.0 through its `pipx:` backend. `mise.macos.toml` supplies the Homebrew dynamic-library path on macOS. The build writes the website to `site/`, including auto-download routes at `site/pdf/` and `site/docx/` with full-name copies of both documents. It writes the generated reference DOCX to `.build/`, writes the final DOCX/PDF files to `dist/`, and fails unless the PDF is exactly one A4 page and the DOCX declares A4 page dimensions.

After DOCX layout or reference-style changes, render the generated DOCX through Microsoft Word and confirm it is one page. Preserve the 11 pt body font and the 2.75 cm/2 cm top/bottom margins; recover space through paragraph or line spacing instead of shrinking text or margins.

Generated directories (`.build/`, `dist/`, and `site/`) stay git-ignored.

## CSS unit conversion

The shared layout uses `rem` values derived from physical print measurements so the 16 pt website can scale proportionally from the 11 pt PDF and retain similar line wrapping. At the print root size, `1rem = 11pt = 11 × 25.4 ÷ 72 = 3.8806mm`. Convert millimetres with:

```text
rem = mm ÷ (11 × 25.4 ÷ 72)
    = mm ÷ 3.8806
```

Keep the source millimetre value in an inline CSS comment next to every `rem` value derived from millimetres.

## GitHub Actions

The workflow installs Pandoc, Python, and WeasyPrint 69.0 with mise. `mise.linux.toml` declares Ubuntu’s native Pango libraries, which mise bootstrap packages install into standard loader paths. The workflow then builds all formats and deploys the website to GitHub Pages.
