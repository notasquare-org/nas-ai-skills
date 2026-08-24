---
name: nas-slides
description: Creates, revises, and reviews editable NaS sales decks in native Google Slides using the approved Not a Square tone, Google Sans typography, reference layouts, pattern catalog, Drive-hosted logo assets, and validation rules. Use whenever the user asks for an NaS-branded slide, sales deck, proposal, company introduction, service explanation, presentation pattern, slide catalog, or says「NaSのトンマナで」「いつものスライド形式で」.
---

# NaS Slides

## Trigger and source of truth

Apply this skill automatically to every NaS-branded presentation task in this project. The user does not need to name the skill explicitly.

Before creating or editing slides, read these files completely:

1. [CLAUDE.md](references/CLAUDE.md) — approved tone and non-negotiable rules
2. [PATTERN_CATALOG.md](references/PATTERN_CATALOG.md) — approved slide patterns and selection logic
3. [nas_slides_lib.py](scripts/nas_slides_lib.py) — editable slide primitives and current typography values

Treat those files as the source of truth. Do not copy their full contents into a prompt or create a competing style definition.

## Intake

Proceed without unnecessary questions when the user provides enough context. Otherwise ask only for missing items that materially affect the deck:

- purpose and desired action after reading
- audience
- source material or claims that must appear
- expected length or presentation time
- whether to create a new deck or edit an existing Google Slides file

Default audience is Japanese SME owners and business leaders. Default output is an editable native Google Slides deck.

## Workflow

1. Read [CLAUDE.md](references/CLAUDE.md) completely.
2. Read [PATTERN_CATALOG.md](references/PATTERN_CATALOG.md) and choose one approved pattern for every slide.
3. Use the native reference deck `Not a Square Pitch Deck v2` as the visual source of truth.
4. Write the narrative first. Except for covers, agendas, and section dividers, every title must state the conclusion.
5. Build editable slides from the approved patterns and `nas_slides_lib.py`; do not rasterize narrative text.
6. Use the official Drive logo asset. Never redraw, recolor, crop, stretch, or extract it from another slide.
7. Run `python3 scripts/validate_catalog.py <pptx>` for locally generated PPTX artifacts.
8. Import the verified PPTX as native Google Slides, then inspect every delivered slide visually.

## Pattern selection

Assign one catalog pattern to every slide before drawing it. Use the smallest pattern that communicates the message:

- cover or major divider: P01 or P02
- memorable key sentence: P03
- ordinary explanation: P04
- conclusion, contrast, or summary: P05 or P08
- process or roadmap: P06 or P07
- two-axis prioritization: P09
- detail that must stand alone: P10
- real-world evidence: P11
- final conclusion or next action: P12

Except for covers, agendas, and section dividers, write a conclusion-led one-sentence title. Reading the titles alone must reveal the argument of the deck.

## Delivery checklist

Before presenting the result to the user:

1. Confirm every narrative text box and shape remains editable.
2. Confirm Google Sans, approved colors, and approved font sizes.
3. Confirm navy headers have no logo and white-background brand slides use the official logo only where prescribed.
4. Confirm diagonal bands use the exact P01/P02 construction: one oversized, unskewed rectangle rotated clockwise about 24.3 degrees. Compare the rendered upper edge with the reference cover; it should run approximately from the lower-left corner to the right edge below the logo, while fully covering the lower canvas edge.
5. Confirm no rounded corners, decorative icons, charts, native tables, page numbers, footers, or animations.
6. Confirm arrows carry meaning and external images have a source name plus direct URL.
7. Check every slide visually for overflow, clipping, accidental overlaps, and weak hierarchy.
8. Run the local validator when a PPTX is generated. Deliver only after errors are resolved.

## Non-negotiable rules

- Audience: Japanese SME owners and business leaders.
- Canvas: 16:9.
- Font: Google Sans only.
- Core colors: NaS navy `#053259` and white `#FFFFFF`.
- Orange `#FB9F43` is exceptional and only allowed in a dense, important diagram where navy alone cannot create sufficient hierarchy.
- Use right angles. No rounded cards, shadows, gradients, decorative icons, charts, native tables, page numbers, footers, or animations.
- Use arrows only for meaningful process, causality, or information flow.
- Prefer shapes, lines, text, and numeric step labels over imagery.
- Use photos only when real-world identity or evidence matters.
- Use illustrations only for necessary concept explanation; external assets require a readable source name and direct URL at the bottom.
- Keep the NaS logo at the upper right on white-background brand slides whenever feasible.
- Do not place the NaS logo in the navy top header. A slide with the standard navy header has no logo by default.
- On diagonal cover and section patterns, use a single ordinary rectangle rotated clockwise `24.3°` (PowerPoint/python-pptx rotation `-24.3`; Google Slides affine rotation `-24.3°`). Oversize it beyond the canvas so it fully covers the bottom edge.
- Never substitute a parallelogram, trapezoid, freeform polygon, horizontal band, or skewed shape for the rotated rectangle. Those shapes can imitate one diagonal edge but do not match the native reference construction.
- For a native Google Slides 720×405 pt canvas, the canonical band is an 800×350 pt rectangle with affine rotation `-24.3°`, translated to approximately `x=-8`, `y=405`. Its visible upper edge should be approximately `(0, 405) → (720, 80)`. Render the slide and reject it if the left edge becomes vertical/slanted instead of the whole rectangle being rotated, or if any white gap remains along the bottom.
- Do not introduce a visual technique that is absent from the approved reference deck or catalog.

## References

- Full design contract: [CLAUDE.md](references/CLAUDE.md)
- Pattern selection: [PATTERN_CATALOG.md](references/PATTERN_CATALOG.md)
- Editable slide primitives: [nas_slides_lib.py](scripts/nas_slides_lib.py)

## Usage examples

The following requests should activate this skill:

- 「この企画書をNaSのトンマナで10枚の営業資料にして」
- 「いつものスライド形式で、経営者向けに提案資料を作って」
- 「このGoogleスライドをNaSの型に直して」
- 「P05の左右要約を使って、この内容を1枚に整理して」
- 「NaSスライドとしてトンマナ違反がないかレビューして」

When the user only supplies raw content, first propose a title-only storyline and pattern assignment, then create the deck unless the user asks to approve the outline first.
