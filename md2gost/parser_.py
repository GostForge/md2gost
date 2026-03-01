import logging
import os
from collections.abc import Generator

from docx import Document
from marko.block import BlankLine, Paragraph, CodeBlock, FencedCode, \
    BlockElement
from marko.inline import Image

from .extended_markdown import markdown, Caption
from .renderable.caption import CaptionInfo
from .renderable.renderable import Renderable
from .renderable_factory import RenderableFactory

logger = logging.getLogger(__name__)


class Parser:
    """Parses given markdown string and returns Renderable elements"""

    def __init__(self, document: Document):
        self._document = document
        self._renderables = []
        self._factory = RenderableFactory(self._document._body)
        self._caption_info: CaptionInfo | None = None

    @staticmethod
    def _safe_resolve(base_dir: str, relative_path: str) -> str | None:
        """Resolve *relative_path* inside *base_dir*.

        Returns the resolved absolute path if it stays within *base_dir*,
        or ``None`` if the path attempts to escape (path-traversal).
        ``~`` (home-dir expansion) is intentionally NOT applied.
        """
        # Strip leading slashes so os.path.join cannot ignore base_dir
        cleaned = relative_path.lstrip("/").lstrip("\\")
        resolved = os.path.normpath(os.path.join(base_dir, cleaned))
        base = os.path.normpath(base_dir)
        if not (resolved == base or resolved.startswith(base + os.sep)):
            logger.warning(
                "Path traversal blocked: '%s' resolved to '%s' (base: %s)",
                relative_path, resolved, base,
            )
            return None
        return resolved

    @staticmethod
    def resolve_paths(marko_element: BlockElement, relative_dir_path: str):
        """Resolves relative paths in Marko elements (with traversal protection)."""
        if isinstance(marko_element, Paragraph):
            for child in marko_element.children:
                if isinstance(child, Image) and not child.dest.startswith("http"):
                    safe = Parser._safe_resolve(relative_dir_path, child.dest)
                    if safe is not None:
                        child.dest = safe
                    else:
                        # Replace with obviously-invalid path so FileNotFoundError is raised later
                        child.dest = "__blocked_path_traversal__"
        if isinstance(marko_element, (CodeBlock, FencedCode)) and marko_element.extra:
            safe = Parser._safe_resolve(relative_dir_path, marko_element.extra)
            if safe is not None:
                marko_element.extra = safe
            else:
                marko_element.extra = "__blocked_path_traversal__"

    def parse(self, text, relative_dir_path: str) -> None:
        marko_parsed = markdown.parse(text)
        for marko_element in marko_parsed.children:
            self.resolve_paths(marko_element, relative_dir_path)

            if isinstance(marko_element, BlankLine):
                continue

            if isinstance(marko_element, Caption):
                self._caption_info =\
                    CaptionInfo(marko_element.unique_name, marko_element.text)
                continue

            for renderable in self._factory.create(marko_element, self._caption_info):
                self._renderables.append(renderable)
            self._caption_info = None

    def get_rendered(self) -> list[Renderable]:
        return self._renderables
