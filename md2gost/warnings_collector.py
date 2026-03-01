"""Thread-local warnings collector for md2gost conversions.

Collect warnings during a conversion run so the HTTP response can relay
them back to the caller (and ultimately to the end-user).

Usage::

    clear_warnings()            # before conversion
    add_warning("Foo")          # inside renderable / factory / image / listing
    warnings = get_warnings()   # after conversion
"""

import threading

_thread_local = threading.local()


def get_warnings() -> list[str]:
    """Return the accumulated warnings list (creates one if absent)."""
    if not hasattr(_thread_local, "warnings"):
        _thread_local.warnings = []
    return _thread_local.warnings


def add_warning(msg: str) -> None:
    """Append a warning message to the current thread's collector."""
    get_warnings().append(msg)


def clear_warnings() -> None:
    """Reset the warnings list (call before each conversion)."""
    _thread_local.warnings = []
