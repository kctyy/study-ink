# Handwriting engine

Typed text in, the student's own handwriting out. No image generation: the output is built from the
student's real pen strokes, so the words are always exactly the words you typed.

## Pipeline
1. `template`  makes a one-time sheet (labeled cells, baseline guide). The student fills it in with the Pencil.
2. `extract`   finds each character in the filled sheet, measures baseline, letter height and pen thickness,
               and saves a profile folder (PNG per glyph + meta.json).
3. `write`     composes words from random glyph variants with small size, tilt, spacing and baseline noise.

## Run the combined studio
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY="your-key"  # enables Claude slide analysis and optional ink reading
    python app.py      # then open http://localhost:8000

Slide and text workflows still run locally without an API key, except Claude slide analysis/refinement
and optional vision reading of handwritten study answers. Handwritten answers can always be checked by
typing the transcription. Image OCR for imported notes requires the Tesseract executable.

The **Slide → diagram** tab accepts PNG, JPEG, WebP, or GIF images up to 10 MB.
It sends the selected image to Claude when you click **Analyze slide**, then shows
editable JSON, extracted study notes, and a handwritten render. Add a correction
to the instructions and click **Refine diagram** to update that same scene in place.
The default redraw mode asks Claude for
diagram strokes and label positions, then draws the strokes with pen-like lines
and labels with glyphs from the handwriting profile. Dense structures such as
molecules may need manual correction in the JSON editor. Source-preserving mode
is available as a fallback, and vector rebuild mode supports simple node/edge
diagrams. Keep the API key in the terminal environment; it is never placed in
the page. Choose Claude Sonnet 4.6 or Haiku 4.5 from the model menu.

The diagram workflow uses structured reconstruction, not free-form image generation;
review dense scientific diagrams for missed labels or bonds. **Simplify automatically
if the diagram is too dense** lets Claude abstract low-level detail while keeping the
central components, key labels, and important relationships.

For template creation and profile extraction, use the CLI below:

    pip install -r requirements.txt
    python cli.py template --out template.png                 # writes template.png + template_rows.json
    # student fills it in (Notability / Procreate / print and photograph), export as PNG
    python cli.py extract --image filled.png --rows template_rows.json --out profiles/me --debug debug.png --sheet contact.png
    # open contact.png: every extracted glyph is labeled char:index. Re-run with --drop "i:1,u:1,→" to remove bad cells
    # (a char:index drops one variant, a bare char drops all of them; dropped chars fall back to stand-ins)
    python cli.py write --profile profiles/me --text "R3 to A: cost 3 (next-hop is R2)" --paper lined --ink "#0a5a28"

Python:
    from handwriting import HandwritingFont, Writer
    font = HandwritingFont.load("profiles/me")
    img = Writer(font, ink=(10, 90, 40), neatness=0.5).write("Hello", width=1400, size=56, paper="lined")

Diagram labels and shapes can use the same profile:

    from handwriting import DiagramWriter, HandwritingFont
    font = HandwritingFont.load("profiles/me")
    diagram = {
        "nodes": [
            {"id": "a", "kind": "box", "text": "Start", "x": 0.18, "y": 0.5, "w": 0.2, "h": 0.14},
            {"id": "b", "kind": "diamond", "text": "Ready?", "x": 0.5, "y": 0.5, "w": 0.22, "h": 0.18},
            {"id": "c", "kind": "circle", "text": "Done", "x": 0.82, "y": 0.5, "w": 0.18, "h": 0.14},
        ],
        "edges": [
            {"from": "a", "to": "b", "directed": True},
            {"from": "b", "to": "c", "label": "yes", "directed": True},
        ],
    }
    img = DiagramWriter(font, seed=7, neatness=0.5).render(diagram, width=1200, height=600)
    img.save("diagram.png")

Diagram coordinates and dimensions are normalized to 0..1. The renderer draws
boxes, circles/ellipses, diamonds, arrows, and edge labels. A vision model can
produce this node/edge data from a slide; the diagram renderer handles the
handwritten visual style after extraction.

## Notes
- `neatness` 0..1 is the loose-to-neat slider. More template repetitions give more visible variety.
- Characters missing from a sample get single-stroke stand-in glyphs (`handwriting/fallback.py`) matched to the
  student's letter size and pen thickness. The full template removes the need for them.
- `profiles/trisha_full` is from the completed template (dropped: i:1, u:1, and the crossed-out • → ← cells).
- Letters that belong on the line (most lowercase, capitals, digits) are snapped to sit on it; the renderer adds wobble back.
- Check `--debug` output after extraction: red boxes should surround exactly one character each.
- Limits: print-style handwriting works best. Cursive that connects letters needs a different method.

The **Text → handwriting** tab can import TXT/PDF notes and run local OCR on PNG/JPEG files before
rendering them with a handwriting profile. **Smart Quick Mode** hides about 25% of key terms for
fill-in-the-blank practice; re-roll to generate a different worksheet. This follows Sneha's local
active-recall behavior and does not call an AI model for text masking. PDF extraction uses PyMuPDF. Image OCR also requires the
Tesseract executable to be installed on the computer.

Slide analysis also extracts the title, lecture notes, and a source-grounded study guide. Use
**Print study sheet / PDF** to print or save a Notability-ready page with the handwritten diagram and
searchable study text. Enable **Add active-recall blanks** to mask selected key terms and include an
answer key.

The **Study Along** tab adds the interactive practice loop from `study-loop-clean`: handwriting-style
lesson pages with blanks across text, graphs, flowcharts, comparison cards, tables, and concept maps;
mouse/touch/Pencil ink capture; single-answer and reveal-all controls; answer checking; graph path and
forwarding-table calculations using NetworkX; redraw practice with a handwritten reference; and PDF plus
`studyalong.v1` JSON export. The included Dijkstra/R3 lesson is a ready-to-run example. Vision ink reading
is optional; the recognized text is checked against answers computed from the lesson data and graph solver.
