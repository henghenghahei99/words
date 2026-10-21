#!/usr/bin/env python3
"""Prepare TrueType CJK fonts for ReportLab.

ReportLab cannot embed CFF/OTF fonts, so the CJK faces must be plain TTF.
This script produces static Regular/Bold TTFs in a cache directory
(default: <temp>/words_fonts, override with WORDS_FONT_DIR):

  * Linux: extract the Simplified-Chinese faces from NotoSerifCJK-*.ttc
    and convert them with otf2ttf.
  * Windows: instantiate the variable font NotoSerifSC-VF.ttf at
    wght=400 / 700.

Output: NotoSerifSC-Regular.ttf, NotoSerifSC-Bold.ttf
Requires: pip install fonttools (plus otf2ttf on Linux)
"""
import os
import subprocess
import sys
import tempfile

from fontTools.ttLib import TTCollection, TTFont
from fontTools.varLib.instancer import instantiateVariableFont

FONT_CACHE = os.environ.get("WORDS_FONT_DIR") or os.path.join(
    tempfile.gettempdir(), "words_fonts")

# Linux CFF collections (need otf2ttf to become TrueType).
PAIRS = [
    ("/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc", "Regular"),
    ("/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc", "Bold"),
]

# Windows variable fonts (instantiated at fixed weights).
VFS = [
    ("C:/Windows/Fonts/NotoSerifSC-VF.ttf", {"Regular": 400, "Bold": 700}),
]


def from_ttc(src, weight, out):
    otf = os.path.join(FONT_CACHE, "NotoSerifSC-%s.otf" % weight)
    col = TTCollection(src)
    idx = next((i for i, f in enumerate(col.fonts)
                if "SC" in (f["name"].getDebugName(1) or "")), 2)
    col.fonts[idx].save(otf)
    print("extracted:", otf)
    subprocess.run(["otf2ttf", otf], check=True)
    print("converted:", out)


def from_vf(src, weight, wght, out):
    font = TTFont(src)
    instantiateVariableFont(font, {"wght": wght}, inplace=True,
                            updateFontNames=False)
    font.save(out)
    print("instanced:", out, os.path.getsize(out))


def main():
    os.makedirs(FONT_CACHE, exist_ok=True)
    for src, weight in PAIRS:
        out = os.path.join(FONT_CACHE, "NotoSerifSC-%s.ttf" % weight)
        if os.path.exists(out):
            print("exists:", out)
            continue
        if os.path.exists(src):
            from_ttc(src, weight, out)
            continue
        for vf, weights in VFS:
            if os.path.exists(vf):
                from_vf(vf, weight, weights[weight], out)
                break
        else:
            sys.exit("missing font source for %s (looked for %s and %s)"
                     % (weight, src, ", ".join(v for v, _ in VFS)))
    print("font dir:", FONT_CACHE)


if __name__ == "__main__":
    main()
