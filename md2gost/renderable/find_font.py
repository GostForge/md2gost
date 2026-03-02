from sys import platform, exit
import subprocess
import logging
from functools import cache


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
        "Times New Roman": ["Times New Roman", "Liberation Serif"],
        "Calibri":         ["Calibri", "Carlito"],
        "Arial":           ["Arial", "Liberation Sans"],
        "Courier New":     ["Courier New", "Liberation Mono"],
        "Consolas":        ["Consolas", "Liberation Mono", "Courier New"],
    }
    candidates = aliases.get(name, [name])

    for candidate in candidates:
        pattern = f"{candidate}:weight={weight}:slant={slant}"
        try:
            result = subprocess.run(
                ["fc-match", "--format=%{file}\\n%{family}\\n%{weight}\\n%{slant}", pattern],
                check=True, capture_output=True, text=True,
            )
            lines = result.stdout.strip().splitlines()
            if not lines:
                continue
            path = lines[0].strip()
            if not path:
                continue

            # Sanity-check: make sure fontconfig actually gave us the right
            # family (it may silently fall back to a totally different font).
            resolved_family = lines[1].strip() if len(lines) > 1 else ""
            # Accept if any word of the requested name appears in the resolved family
            name_words = name.lower().split()
            if not any(w in resolved_family.lower() for w in name_words):
                logging.debug(
                    "fc-match returned '%s' for '%s' — skipping (family mismatch)",
                    resolved_family, candidate,
                )
                continue

            logging.debug("find_font('%s', bold=%s, italic=%s) → %s", name, bold, italic, path)
            return path

        except subprocess.CalledProcessError as exc:
            logging.warning("fc-match failed for '%s': %s", pattern, exc)
            continue

    # Hard fallback — pick any monospace or serif font
    fallback_pattern = "mono" if name in ("Courier New", "Consolas") else "serif"
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
        from matplotlib.font_manager import findfont, FontProperties
        return findfont(FontProperties(
            family=name,
            weight="bold" if bold else "normal",
            style="italic" if italic else "normal"), fallback_to_default=False)


if __name__ == "__main__":
    print(find_font("Courier New", False, False))
