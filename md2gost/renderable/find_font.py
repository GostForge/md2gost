from sys import platform, exit
import subprocess
import logging
from functools import cache


def __find_font_linux(name: str, bold: bool, italic: bool):
    result = subprocess.run(
        "fc-list", shell=True, check=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True)

    if result.returncode == 0:
        fonts = \
            [line.split(":") for line in result.stdout.strip().split("\n")]
        fonts = [font for font in fonts if len(font) == 3]
    else:
        logging.log(logging.ERROR, "fc-list not found")
        exit(1)

    def match_font(target_names: list[str], strict_style: bool):
        for path, names, styles in fonts:
            if not any(target in names for target in target_names):
                continue
            if strict_style:
                if (("Bold" in styles) == bool(bold)
                        and ("Italic" in styles) == bool(italic)):
                    return path
            else:
                return path
        return None

    aliases = {
        "Times New Roman": ["Times New Roman", "Times", "Liberation Serif", "DejaVu Serif"],
        "Calibri": ["Calibri", "Carlito", "Liberation Sans", "DejaVu Sans"],
        "Arial": ["Arial", "Liberation Sans", "DejaVu Sans"],
        "Courier New": ["Courier New", "Liberation Mono", "DejaVu Sans Mono"],
    }

    candidates = aliases.get(name, [name, "DejaVu Serif", "DejaVu Sans"])

    # 1) strict by style
    path = match_font(candidates, strict_style=True)
    if path:
        return path

    # 2) relax style requirements
    path = match_font(candidates, strict_style=False)
    if path:
        logging.warning("Font '%s' style variant not found, using closest match", name)
        return path

    # 3) final fallback to any common default
    path = match_font(["DejaVu Serif", "DejaVu Sans", "Liberation Serif", "Liberation Sans"], strict_style=False)
    if path:
        logging.warning("Font '%s' not found, fallback font selected", name)
        return path

    raise ValueError(f"Font {name} not found")


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
