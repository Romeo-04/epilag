# Final-round deck: source

The 20-slide deck for the PJDSC 2026 final round. The files people open are
[`docs/deck/EpiLag-PH_deck.pdf`](../docs/deck/EpiLag-PH_deck.pdf) and the editable
[`docs/deck/EpiLag-PH_deck.pptx`](../docs/deck/EpiLag-PH_deck.pptx). The PDF is the reference: the PowerPoint is
made from it, one full-slide picture per PDF page, so it always looks exactly like the PDF whatever fonts a computer
has. Slides 15 to 17 (the System, the demo video and the Quezon City epidemiologists' validation) are not in
`build_deck.py`, which still has the older two System slides.

This folder rebuilds the first draft of the deck from the repository's own results, so every number on a slide comes
from a file in the repo (`reports/`, `research/results/`, `docs/data/`, `site/public/web/data/`).

| File | What it does |
|---|---|
| `build_deck.py` | Builds the first-draft slides as one HTML page, `docs/deck/final/index.html` (a build output, not committed) |
| `annotations.py` | The red hand-drawn notes and arrows, in slide coordinates |
| `art.py`, `outro_art.py` | Pixel-art maps, icons and the frog-and-mosquito closing scene, drawn from the app's sprites and map data |
| `deck.css`, `deck_v2.css`, `deck_v4.css` | Styles, applied in that order |
| `references.html` | The APA 7 reference list |
| `render.py` | Renders the HTML to one PNG per slide, and to a PDF with `--pdf` |
| `extract_layers.py`, `build_pptx.py` | Split each slide into a picture of the visuals plus real text boxes, and write the PowerPoint |
| `shoot_app.py`, `shoot_drill.py`, `shoot_mobile.py`, `measure_unit.py` | Take the app and game screenshots from the live site |
| `assets/` | The screenshots and images the slides use |

```bash
pip install python-pptx segno pymupdf playwright pandas
python deck_build/build_deck.py      # slides as HTML
python deck_build/render.py --pdf    # PNGs and a PDF
python deck_build/extract_layers.py && python deck_build/build_pptx.py   # the PowerPoint
```

The rendering uses Microsoft Edge through Playwright (`channel="msedge"`). The fonts are Plus Jakarta Sans, Caveat and
IBM Plex Mono (free, Google Fonts); install them before rendering or opening the PowerPoint to edit it.

Image credits: bottle-cap photo, Public Health Image Library, CDC (#26033, public domain). The three photographs on
slides 3, 4 and 17 are AI-generated illustrations.
