import logging
import os
from collections.abc import Generator
from urllib.parse import urlparse

from docx import Document
from marko.block import BlankLine, Paragraph, CodeBlock, FencedCode, \
    BlockElement
from marko.inline import Image

from .extended_markdown import markdown, Caption
from .config import Md2GostConfig, get_default_config
from .renderable.caption import CaptionInfo
from .renderable.renderable import Renderable
from .renderable_factory import RenderableFactory

logger = logging.getLogger(__name__)


_BLOCKED_PATH_TRAVERSAL = "__blocked_path_traversal__"
_BLOCKED_EXTERNAL_REFERENCE = "__blocked_external_reference__"


class Parser:
    """Parses given markdown string and returns Renderable elements"""

    def __init__(self, document: Document, config: Md2GostConfig | None = None):
        self._document = document
        self._renderables = []
        self._config = config or get_default_config()
        self._factory = RenderableFactory(self._document._body, config=self._config)
        self._caption_info: CaptionInfo | None = None

    @staticmethod
    def _is_external_reference(path: str) -> bool:
        if not isinstance(path, str):
            return False
        parsed = urlparse(path)
        return bool(parsed.scheme) or path.startswith("//")

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
    def _resolve_image_paths(marko_paragraph: Paragraph, relative_dir_path: str):
        for child in marko_paragraph.children:
            if not isinstance(child, Image):
                continue

            if not isinstance(child.dest, str) or not child.dest.strip():
                setattr(child, "source_dest", str(child.dest))
                child.dest = _BLOCKED_PATH_TRAVERSAL
                continue

            setattr(child, "source_dest", child.dest)
            if Parser._is_external_reference(child.dest):
                child.dest = _BLOCKED_EXTERNAL_REFERENCE
                continue

            safe = Parser._safe_resolve(relative_dir_path, child.dest)
            child.dest = safe if safe is not None else _BLOCKED_PATH_TRAVERSAL

    @staticmethod
    def _resolve_code_extra(marko_code: CodeBlock | FencedCode, relative_dir_path: str):
        if not marko_code.extra:
            return

        if not isinstance(marko_code.extra, str):
            setattr(marko_code, "source_extra", str(marko_code.extra))
            marko_code.extra = _BLOCKED_PATH_TRAVERSAL
            return

        setattr(marko_code, "source_extra", marko_code.extra)

        if Parser._is_external_reference(marko_code.extra):
            marko_code.extra = _BLOCKED_EXTERNAL_REFERENCE
            return

        safe = Parser._safe_resolve(relative_dir_path, marko_code.extra)
        marko_code.extra = safe if safe is not None else _BLOCKED_PATH_TRAVERSAL

    @staticmethod
    def resolve_paths(marko_element: BlockElement, relative_dir_path: str):
        """Resolves relative paths in Marko elements (with traversal protection)."""
        if isinstance(marko_element, Paragraph):
            Parser._resolve_image_paths(marko_element, relative_dir_path)

        if isinstance(marko_element, (CodeBlock, FencedCode)):
            Parser._resolve_code_extra(marko_element, relative_dir_path)

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
