from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from lxml.etree import _Element
import os
import re
from urllib.parse import urlparse


_WINDOWS_ABS_RE = re.compile(r"^[A-Za-z]:/")


def _collapse_media_prefix(path: str) -> str:
    normalized = path
    while normalized.lower().startswith("media/media/"):
        normalized = normalized[len("media/"):]
    return normalized


def public_path_for_warning(path: object) -> str:
    """Convert internal/absolute paths to user-facing safe relative labels.

    Rules:
    - Preserve external URLs (http/https/ftp/data/ws/wss and protocol-relative //).
    - Normalize file:// and local absolute paths to safe labels.
    - Collapse duplicated media/media prefixes.
    """
    normalized = str(path).replace("\\", "/")

    if normalized.startswith("//"):
        return normalized

    parsed = urlparse(normalized)
    if parsed.scheme and parsed.scheme not in {"file"}:
        return normalized

    if parsed.scheme == "file":
        normalized = parsed.path or normalized

    is_abs = os.path.isabs(normalized) or bool(_WINDOWS_ABS_RE.match(normalized))
    if is_abs:
        media_index = normalized.lower().find("/media/")
        if media_index != -1:
            normalized = normalized[media_index + 1:]
        else:
            normalized = os.path.basename(normalized) or normalized

    normalized = normalized.lstrip("/").lstrip("./")
    normalized = _collapse_media_prefix(normalized)
    return normalized


def create_element(name: str, *args: dict[str, str] | list[_Element] | str)\
        -> _Element:
    """Creates an OxmlElement

    Variable arguments:
    * dict -- element's attributes
    * list -- element's children
    * string -- element's text
    """
    attrs = {}
    children = []
    text = None

    for arg in args:
        if isinstance(arg, dict):
            attrs.update(arg)
        elif isinstance(arg, list):
            children.extend(arg)
        elif isinstance(arg, str):
            text = arg

    element = OxmlElement(name, {
        (qn(name) if ":" in name else name): value for name, value in attrs.items()
    })
    for child in children:
        element.append(child)
    if text:
        element.text = text
    return element


def _safe_getmembers(obj):
    """Like inspect.getmembers but catches ValueError too.

    python-docx raises ValueError from some properties (e.g. ``.part``)
    when elements are not attached to a document part.  The stdlib
    ``inspect.getmembers`` only catches ``AttributeError``, so those
    ``ValueError``s propagate and crash.  This helper swallows both.
    """
    results = []
    for key in dir(obj):
        try:
            value = getattr(obj, key)
        except (AttributeError, ValueError, TypeError):
            continue
        results.append((key, value))
    results.sort(key=lambda pair: pair[0])
    return results


def merge_objects(*objects):
    from inspect import ismethod
    """
    Returns the new object containing attributes from objects, where the latest
    one has the highest priority.
    """

    class MergedObject:
        pass

    merged_object = MergedObject()
    for name, value in _safe_getmembers(objects[0]):
        if name.startswith("_") or ismethod(value):
            continue
        merged_object.__setattr__(name, value)

    for object_ in objects[1:]:
        for name, value in _safe_getmembers(object_):
            if name.startswith("_") or ismethod(value):
                continue
            if value is not None:
                merged_object.__setattr__(name, value)

    return merged_object
