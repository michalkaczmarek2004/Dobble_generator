# Dobble Library

Generates a full Dobble card deck from a set of symbol images.

---

## Running scripts

All scripts must be run as Python modules from the **project root** (the directory containing `dobble_library/`), not from inside `dobble_library/`. Use `-m` syntax:

```bash
# Correct — from project root
python -m dobble_library.scripts.generate_templates

# Wrong — causes ModuleNotFoundError
python dobble_library/scripts/generate_templates.py
```

---

## Full workflow (step by step)

### Step 1 — Generate layout templates

Creates a JSON file with symbol slot positions for each card.

```bash
python -m dobble_library.scripts.generate_templates
```

Default output: `models_55.json` (55 cards, 8 symbols each).

Change the number of cards:

```bash
python -m dobble_library.scripts.generate_templates --num-cards 30
```

Output will be named `models_30.json` automatically.

Change the number of symbols per card:

```bash
python -m dobble_library.scripts.generate_templates --symbols-per-card 6
```

> **Note:** For the Dobble algorithm to work, `symbols_per_card - 1` must be a prime number.
> Valid values: **3, 4, 6, 8, 14, 20** (i.e. n+1 where n is prime: 2, 3, 5, 7, 13, 19…).

> This step takes 2–3 minutes. Skip it if you already have a template file.

---

### Step 2 — Generate placeholder symbols

Creates numbered PNG images in `symbols/`. Skip if you have your own images.

```bash
python -m dobble_library.scripts.generate_symbols --templates models_55.json
```

Choose shape with `--shape circle`, `--shape square`, or `--shape mixed`:

```bash
python -m dobble_library.scripts.generate_symbols --templates models_55.json --shape circle
```

To regenerate existing symbols:

```bash
python -m dobble_library.scripts.generate_symbols --templates models_55.json --overwrite
```

---

### Step 3 — Render cards

Reads the template JSON and symbol images, outputs PNG cards to `output_cards/`.

```bash
python -m dobble_library.scripts.render_cards
```

By default uses `models_55_v2.json`. To use a different template:

```bash
python -m dobble_library.scripts.render_cards --templates models_55.json
```

---

### Step 4 — Generate A4 PDF for printing

Takes the rendered PNGs and places one card per A4 page into a single PDF.

```bash
python -m dobble_library.scripts.a4_generator
```

Output: `Final_cards/cards_a4.pdf`

---

## Key variables to customize

### Template generation (`scripts/generate_templates.py`)

| Argument | Default | Description |
|---|---|---|
| `--num-cards` | `55` | Number of card layouts to generate |
| `--symbols-per-card` | `8` | Symbol slots per card |
| `--margin` | `0.03` | Circle margin (fraction 0–1) — shrinks usable area |
| `--output` | `models_{N}.json` | Output JSON path |

```bash
python -m dobble_library.scripts.generate_templates --num-cards 55 --symbols-per-card 8 --margin 0.03
```

---

### Card rendering (`scripts/render_cards.py`)

| Argument | Default | Description |
|---|---|---|
| `--templates` | `models_55_v2.json` | Template JSON file |
| `--symbols-dir` | `symbols/` | Folder with symbol images |
| `--output-dir` | `output_cards/` | Output folder |
| `--card-size-px` | `1024` | Card size in pixels (width = height) |
| `--fit-scale` | `0.88` | Symbol scale inside each slot (0.75–0.95) |
| `--circle-margin` | `0.02` | Outside circle margin as fraction of card size |
| `--seed` | `1234` | Random seed for reproducibility |
| `--rotation-sign` | `-1` | Rotation direction (`-1` or `1`) |

```bash
python -m dobble_library.scripts.render_cards --card-size-px 2048 --circle-margin 0.03
```

> Tip: match `--circle-margin` to `--margin` used in template generation so the circle aligns with symbol slots.

---

### A4 PDF generation (`scripts/a4_generator.py`)

Edit the config block at the top of the file for permanent defaults:

```python
DPI               = 300        # print resolution
CARD_DIAMETER_MM  = 80.0       # printed card size in mm
INPUT_DIR         = "output_cards"
OUTPUT_DIR        = "Final_cards"
OUTPUT_PDF_NAME   = "cards_a4.pdf"
```

Or pass arguments at runtime:

| Argument | Default | Description |
|---|---|---|
| `--input-dir` | `output_cards/` | Folder with rendered card PNGs |
| `--output-dir` | `Final_cards/` | Output folder |
| `--output-name` | `cards_a4.pdf` | PDF filename |
| `--dpi` | `300` | Print resolution |
| `--card-diameter-mm` | `80.0` | Card diameter on the printed page |

```bash
python -m dobble_library.scripts.a4_generator --card-diameter-mm 90 --dpi 300
```

---

## Project structure

```text
dobble_library/
├── deck_generator/          # core rendering engine
├── json_template_generator/ # layout packing algorithm
├── scripts/
│   ├── generate_templates.py  # Step 1 — layout JSON
│   ├── generate_symbols.py    # Step 2 — placeholder images
│   ├── render_cards.py        # Step 3 — card PNGs
│   └── a4_generator.py        # Step 4 — A4 PDF
├── symbols/                 # symbol images (input)
├── output_cards/            # rendered cards (output)
├── Final_cards/             # print-ready PDFs (output)
└── models_55.json           # template file (example)
```

## Own symbols

Put your images in `symbols/`. Supported formats: `.png`, `.webp`, `.jpg`, `.jpeg`.

The number of symbol images must cover all unique symbols in the deck. The Dobble algorithm produces `p² + p + 1` unique symbols, where `p = symbols_per_card - 1`:

| `symbols_per_card` | unique symbols needed |
|---|---|
| 4 | 13 |
| 6 | 31 |
| 8 | 57 |
| 14 | 183 |
