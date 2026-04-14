from sys import platform, exit
import subprocess
import logging
import importlib
from functools import cache


def _resolve_fc_match(pattern: str):
    """Return fc-match output lines for pattern or None on command failure."""
    try:
        result = subprocess.run(
            ["fc-match", "--format=%{file}\\n%{family}\\n%{weight}\\n%{slant}", pattern],
            check=True, capture_output=True, text=True,
        )
        return result.stdout.strip().splitlines()
    except subprocess.CalledProcessError as exc:
        logging.warning("fc-match failed for '%s': %s", pattern, exc)
        return None


def _candidate_matches_family(candidate: str, resolved_family: str) -> bool:
    requested = candidate.strip().lower()
    resolved_names = [name.strip().lower() for name in resolved_family.split(",") if name.strip()]
    return requested in resolved_names


def __find_font_linux(name: str, bold: bool, italic: bool):
    """
    Resolve a font path for the given family/style with strict family matching.
    If fontconfig resolves to a different family, treat it as missing.
    """
    weight = "bold" if bold else "regular"
    slant  = "italic" if italic else "roman"

    pattern = f"{name}:weight={weight}:slant={slant}"
    lines = _resolve_fc_match(pattern)
    if not lines:
        raise ValueError(f"Font '{name}' is not available on this system")

    path = lines[0].strip()
    if not path:
        raise ValueError(f"Font '{name}' resolved to empty path")

    resolved_family = lines[1].strip() if len(lines) > 1 else ""
    if not _candidate_matches_family(name, resolved_family):
        raise ValueError(
            f"Font '{name}' is not installed exactly. Resolved family: '{resolved_family}'"
        )

    logging.debug("find_font('%s', bold=%s, italic=%s) → %s", name, bold, italic, path)
    return path


@cache
def find_font(name: str, bold: bool, italic: bool):
    if not name:
        raise ValueError("Invalid font")
    if platform == "linux":
        return __find_font_linux(name, bold, italic)
    else:
        font_manager = importlib.import_module("matplotlib.font_manager")
        return font_manager.findfont(font_manager.FontProperties(
            family=name,
            weight="bold" if bold else "normal",
            style="italic" if italic else "normal"), fallback_to_default=False)


if __name__ == "__main__":
    print(find_font("Courier New", False, False))
