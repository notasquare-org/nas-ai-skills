"""NaS slide primitives and pattern renderers.

This module intentionally stays in one file so an AI can read the complete API
and brand contract at once. It generates editable PPTX slides that can be
imported into native Google Slides.
"""

from pathlib import Path
from typing import Iterable, Sequence

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE, MSO_CONNECTOR
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt


FONT = "Google Sans"
C = {
    "navy": "053259",
    "white": "FFFFFF",
    "textGray": "575B61",
    "darkGray": "2C2C2C",
    "lineGray": "D8D8D6",
    "orangeException": "FB9F43",
}
TEXT_STYLES = {
    "cover": {"size": 28, "bold": False, "color": "navy"},
    "title": {"size": 25.5, "bold": False, "color": "white"},
    "splitTitle": {"size": 23, "bold": False, "color": "white"},
    "key": {"size": 26, "bold": True, "color": "navy"},
    "diagramHeading": {"size": 17, "bold": True, "color": "navy"},
    "heading": {"size": 15, "bold": True, "color": "navy"},
    "body": {"size": 13, "bold": False, "color": "navy"},
    "bodyLarge": {"size": 15, "bold": False, "color": "navy"},
    "step": {"size": 12, "bold": False, "color": "white"},
    "caption": {"size": 11.5, "bold": False, "color": "textGray"},
    "source": {"size": 9, "bold": False, "color": "textGray"},
    # Venue / webinar projection mode. Prefer shortening or splitting content
    # over reducing these sizes.
    "presentationTitle": {"size": 28, "bold": True, "color": "white"},
    "presentationBody": {"size": 18, "bold": False, "color": "navy"},
    "presentationDenseBody": {"size": 17, "bold": False, "color": "navy"},
}

SLIDE_W = 13.333333
SLIDE_H = 7.5
LEFT = 0.8
RIGHT = 12.53
TOP_HEADER_H = 1.98
DIAGONAL_BAND_ROTATION_DEG = -24.3
DIAGONAL_BAND_GEOMETRY = (-1.0, 4.72, 15.5, 5.0)


def rgb(name_or_hex: str) -> RGBColor:
    value = C.get(name_or_hex, name_or_hex).lstrip("#")
    return RGBColor.from_string(value)


class SlideBuilder:
    def __init__(self, logo_path: str | None = None):
        self.prs = Presentation()
        self.prs.slide_width = Inches(SLIDE_W)
        self.prs.slide_height = Inches(SLIDE_H)
        self.blank = self.prs.slide_layouts[6]
        self.logo_path = Path(logo_path) if logo_path else None

    def new_slide(self, background: str = "white"):
        slide = self.prs.slides.add_slide(self.blank)
        slide.background.fill.solid()
        slide.background.fill.fore_color.rgb = rgb(background)
        return slide

    def add_rect(self, slide, x, y, w, h, fill="white", line=None, line_width=1):
        shape = slide.shapes.add_shape(
            MSO_AUTO_SHAPE_TYPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h)
        )
        shape.fill.solid()
        shape.fill.fore_color.rgb = rgb(fill)
        if line:
            shape.line.color.rgb = rgb(line)
            shape.line.width = Pt(line_width)
        else:
            shape.line.fill.background()
        shape.shadow.inherit = False
        return shape

    def add_text(self, slide, text, x, y, w, h, style="body", *,
                 color=None, size=None, bold=None, align=PP_ALIGN.LEFT,
                 valign=MSO_ANCHOR.TOP):
        spec = TEXT_STYLES[style]
        box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        frame = box.text_frame
        frame.clear()
        frame.word_wrap = True
        frame.margin_left = frame.margin_right = 0
        frame.margin_top = frame.margin_bottom = 0
        frame.vertical_anchor = valign
        p = frame.paragraphs[0]
        p.text = text
        p.alignment = align
        p.space_after = Pt(0)
        p.line_spacing = 1.15
        for run in p.runs:
            run.font.name = FONT
            run.font.size = Pt(size if size is not None else spec["size"])
            run.font.bold = spec["bold"] if bold is None else bold
            run.font.color.rgb = rgb(color or spec["color"])
        return box

    def add_line(self, slide, x1, y1, x2, y2, color="navy", width=1):
        line = slide.shapes.add_connector(
            MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2)
        )
        line.line.color.rgb = rgb(color)
        line.line.width = Pt(width)
        return line

    def add_arrow(self, slide, x1, y1, x2, y2, color="textGray", width=1.5):
        line = self.add_line(slide, x1, y1, x2, y2, color, width)
        head = slide.shapes.add_shape(
            MSO_AUTO_SHAPE_TYPE.ISOSCELES_TRIANGLE,
            Inches(x2 - 0.07), Inches(y2 - 0.06), Inches(0.14), Inches(0.12)
        )
        head.rotation = 90
        head.fill.solid()
        head.fill.fore_color.rgb = rgb(color)
        head.line.fill.background()
        head.shadow.inherit = False
        return line

    def add_logo(self, slide, x=10.75, y=0.22, w=1.78):
        if self.logo_path and self.logo_path.exists():
            slide.shapes.add_picture(str(self.logo_path), Inches(x), Inches(y), width=Inches(w))

    def add_header(self, slide, title):
        self.add_rect(slide, 0, 0, SLIDE_W, TOP_HEADER_H, "navy")
        self.add_text(slide, title, LEFT, 0.55, 10.9, 0.75, "title")

    def add_source(self, slide, source_name, direct_url):
        self.add_text(slide, f"出典：{source_name} — {direct_url}", LEFT, 7.12, 11.6, 0.18, "source")

    def add_diagonal_cover(self, title, subtitle=None):
        slide = self.new_slide()
        # P01/P02 invariant: this is one ordinary, unskewed rectangle rotated
        # clockwise. Never replace it with a parallelogram, trapezoid, freeform,
        # or horizontal band. The oversize geometry keeps the lower edge covered
        # after conversion to native Google Slides and matches the reference deck.
        band = self.add_rect(slide, *DIAGONAL_BAND_GEOMETRY, "navy")
        band.name = "NaS Diagonal Band"
        band.rotation = DIAGONAL_BAND_ROTATION_DEG
        self.add_text(slide, title, 0.58, 2.7, 7.8, 0.7, "cover")
        if subtitle:
            self.add_text(slide, subtitle, 0.6, 3.45, 7.4, 0.45, "body", color="textGray")
        self.add_logo(slide)
        return slide

    def add_key_message(self, japanese, english=None):
        slide = self.new_slide()
        if english:
            self.add_text(slide, english, 1.55, 2.62, 10.3, 0.55, "key", align=PP_ALIGN.CENTER)
            self.add_text(slide, japanese, 1.35, 4.05, 10.65, 0.65, "key", align=PP_ALIGN.CENTER)
        else:
            self.add_text(slide, japanese, 1.15, 3.25, 11.05, 0.75, "key", align=PP_ALIGN.CENTER)
        self.add_logo(slide)
        return slide

    def add_header_body(self, title, sections: Sequence[tuple[str, str]]):
        slide = self.new_slide()
        self.add_header(slide, title)
        n = max(1, len(sections))
        col_w = 11.9 / n
        for i, (heading, body) in enumerate(sections):
            x = 0.58 + i * col_w
            if i:
                self.add_line(slide, x - 0.22, 2.42, x - 0.22, 6.75, "lineGray")
            self.add_text(slide, heading, x, 2.4, col_w - 0.42, 0.42, "heading")
            self.add_text(slide, body, x, 2.96, col_w - 0.42, 3.25, "bodyLarge")
        return slide

    def add_split_summary(self, left_title, left_body, right_title, right_body, conclusion=None):
        slide = self.new_slide()
        self.add_rect(slide, 0, 0, 6.4, SLIDE_H, "navy")
        self.add_text(slide, left_title, 0.78, 0.72, 4.9, 0.65, "splitTitle")
        self.add_text(slide, left_body, 0.78, 2.0, 4.95, 3.6, "bodyLarge", color="white")
        self.add_text(slide, right_title, 6.92, 0.62, 5.35, 0.82, "key", bold=False)
        self.add_text(slide, right_body, 6.92, 1.83, 5.28, 3.85, "bodyLarge")
        if conclusion:
            self.add_rect(slide, 6.9, 5.93, 5.25, 0.74, "white", "navy", 1)
            self.add_text(slide, conclusion, 7.12, 6.13, 4.82, 0.3, "heading")
        self.add_logo(slide)
        return slide

    def add_steps(self, title, steps: Sequence[tuple[str, str]], outcomes: Sequence[str] | None = None):
        slide = self.new_slide()
        self.add_header(slide, title)
        n = len(steps)
        gap = 0.32
        total = 11.85
        w = (total - gap * (n - 1)) / n
        for i, (heading, body) in enumerate(steps):
            x = 0.58 + i * (w + gap)
            self.add_rect(slide, x, 2.38, w, 0.58, "navy")
            self.add_text(slide, f"{i + 1:02d}", x + 0.16, 2.54, 0.42, 0.22, "step")
            self.add_text(slide, heading, x + 0.62, 2.49, w - 0.75, 0.3, "heading", color="white")
            self.add_rect(slide, x, 2.96, w, 2.54, "white", "navy", 1)
            self.add_text(slide, body, x + 0.18, 3.28, w - 0.36, 1.65, "body")
            if i < n - 1:
                self.add_arrow(slide, x + w + 0.04, 4.18, x + w + gap - 0.04, 4.18)
            if outcomes:
                self.add_text(slide, outcomes[i], x + 0.18, 5.77, w - 0.36, 0.62, "caption")
        return slide

    def add_before_after(self, title, before: Sequence[str], after: Sequence[str]):
        slide = self.new_slide()
        self.add_header(slide, title)
        for x, label, items, fill in [(0.68, "現状", before, "white"), (6.86, "導入後", after, "white")]:
            self.add_text(slide, label, x, 2.35, 5.2, 0.4, "heading")
            self.add_rect(slide, x, 2.88, 5.15, 3.35, fill, "navy", 1)
            for i, item in enumerate(items[:4]):
                self.add_text(slide, item, x + 0.28, 3.2 + i * 0.68, 4.55, 0.42, "body")
                if i < min(len(items), 4) - 1:
                    self.add_line(slide, x + 0.28, 3.75 + i * 0.68, x + 4.84, 3.75 + i * 0.68, "lineGray")
        self.add_arrow(slide, 6.06, 4.55, 6.62, 4.55, "navy", 2)
        return slide

    def add_matrix(self, title, quadrants: Sequence[tuple[str, str]], x_axis, y_axis):
        slide = self.new_slide()
        self.add_header(slide, title)
        x0, y0, w, h = 2.05, 2.5, 9.6, 3.62
        self.add_rect(slide, x0, y0, w, h, "white", "navy", 1)
        self.add_line(slide, x0 + w / 2, y0, x0 + w / 2, y0 + h, "lineGray")
        self.add_line(slide, x0, y0 + h / 2, x0 + w, y0 + h / 2, "lineGray")
        for i, (head, body) in enumerate(quadrants[:4]):
            col, row = i % 2, i // 2
            x = x0 + col * w / 2 + 0.22
            y = y0 + row * h / 2 + 0.22
            self.add_text(slide, head, x, y, 4.25, 0.34, "heading")
            self.add_text(slide, body, x, y + 0.48, 4.25, 0.72, "body")
        self.add_text(slide, y_axis, 0.72, 3.6, 1.05, 0.55, "caption", align=PP_ALIGN.CENTER)
        self.add_text(slide, x_axis, 5.2, 6.42, 3.35, 0.25, "caption", align=PP_ALIGN.CENTER)
        return slide

    def add_detail(self, title, blocks: Sequence[tuple[str, str]]):
        return self.add_header_body(title, blocks)

    def add_evidence(self, title, headline, description, photo_path=None, source=None):
        slide = self.new_slide()
        self.add_header(slide, title)
        self.add_rect(slide, 0.72, 2.52, 5.0, 3.68, "navy")
        if photo_path and Path(photo_path).exists():
            slide.shapes.add_picture(str(photo_path), Inches(0.72), Inches(2.52), width=Inches(5.0), height=Inches(3.68))
        self.add_text(slide, headline, 6.25, 2.62, 5.75, 0.72, "key", bold=False)
        self.add_text(slide, description, 6.25, 3.62, 5.65, 2.05, "bodyLarge")
        if source:
            self.add_source(slide, source[0], source[1])
        return slide

    def add_closing(self, message, action=None):
        slide = self.new_slide()
        self.add_text(slide, message, 1.05, 2.75, 11.0, 0.72, "key", align=PP_ALIGN.CENTER)
        if action:
            self.add_text(slide, action, 1.75, 4.08, 9.6, 0.45, "bodyLarge", align=PP_ALIGN.CENTER)
        self.add_logo(slide)
        return slide

    def save(self, output_path: str):
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.prs.save(path)
        return path


def sample_sections() -> list[tuple[str, str]]:
    return [
        ("NaSの専門性", "AI開発、デジタル戦略、業務設計の知見を組み合わせ、貴社の課題を実行可能な計画へ落とし込みます。"),
        ("課題解決へのアプローチ", "業務とデータを確認し、効果と実現性の高いテーマから小さく実装します。"),
    ]
