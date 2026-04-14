"""Regression tests for Equation -> Heading rendering flow."""

from pathlib import Path

import docx

from md2gost.layout_tracker import LayoutTracker
from md2gost.renderable.caption import CaptionInfo
from md2gost.renderable.equation import Equation
from md2gost.renderable.heading import Heading


def _create_layout_tracker(document: docx.Document) -> LayoutTracker:
    section = document.sections[-1]
    max_height = section.page_height - section.top_margin - section.bottom_margin
    max_width = section.page_width - section.left_margin - section.right_margin
    return LayoutTracker(max_height, max_width)


def test_equation_followed_by_heading_does_not_crash():
    template_path = Path(__file__).resolve().parents[1] / "md2gost" / "Template.docx"
    document = docx.Document(str(template_path))

    tracker = _create_layout_tracker(document)
    equation = Equation(document._body, r"x^2 + 1", CaptionInfo("eq-regression", "Формула"))

    previous = None
    for info in equation.render(None, tracker.current_state):
        tracker.add_height(info.height)
        previous = info

    heading = Heading(document._body, 2, True)
    heading.add_run("Раздел после формулы")

    rendered = list(heading.render(previous, tracker.current_state))
    assert rendered
