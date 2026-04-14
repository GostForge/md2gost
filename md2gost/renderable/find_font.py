from sys import platform, exit
import subprocess
import logging
import importlib
from functools import cache


TIMES_NEW_ROMAN = "Times New Roman"
CALIBRI = "Calibri"
ARIAL = "Arial"
COURIER_NEW = "Courier New"
CONSOLAS = "Consolas"


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
    candidate_words = candidate.lower().split()
    return any(word in resolved_family.lower() for word in candidate_words)


def __find_font_linux(name: str, bold: bool, italic: bool):
    """
    Use fc-match to resolve a font path for the given family/style.
    fc-match handles all the fontconfig alias/fallback logic natively,
    so we don't need to parse fc-list output manually.
    """
    weight = "bold" if bold else "regular"
    slant  = "italic" if italic else "roman"

    # Try the exact requested family first, then fallback aliases.
    aliases = {
        TIMES_NEW_ROMAN: [TIMES_NEW_ROMAN, "Liberation Serif"],
        CALIBRI: [CALIBRI, "Carlito"],
        ARIAL: [ARIAL, "Liberation Sans"],
        COURIER_NEW: [COURIER_NEW, "Liberation Mono"],
        CONSOLAS: [CONSOLAS, "Liberation Mono", COURIER_NEW],
    }
    candidates = aliases.get(name, [name])

    for candidate in candidates:
        pattern = f"{candidate}:weight={weight}:slant={slant}"
        lines = _resolve_fc_match(pattern)
        if not lines:
            continue

        path = lines[0].strip()
        if not path:
            continue

        # Sanity-check: make sure fontconfig actually gave us the right
        # family (it may silently fall back to a totally different font).
        resolved_family = lines[1].strip() if len(lines) > 1 else ""
        # Accept if the resolved family matches the current candidate
        # (needed for fallback aliases like Calibri -> Carlito).
        if not _candidate_matches_family(candidate, resolved_family):
            logging.debug(
                "fc-match returned '%s' for '%s' — skipping (family mismatch)",
                resolved_family, candidate,
            )
            continue

        logging.debug("find_font('%s', bold=%s, italic=%s) → %s", name, bold, italic, path)
        return path

    # Hard fallback — pick any monospace or serif font
    fallback_pattern = "mono" if name in (COURIER_NEW, CONSOLAS) else "serif"
    try:
        result = subprocess.run(
            ["fc-match", "--format=%{file}", fallback_pattern],
            check=True, capture_output=True, text=True,
        )
        path = result.stdout.strip()
        if path:
            logging.warning("Font '%s' not found, using system fallback: %s", name, path)
            return path
    except subprocess.CalledProcessError:
        pass

    raise ValueError(f"Font '{name}' not found on this system")


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
