#!/usr/bin/env python3
"""Prepare TrueType CJK fonts for ReportLab.

ReportLab cannot embed CFF/OTF fonts, and the system Noto CJK files are
CFF collections. This script extracts the Simplified-Chinese faces and
converts them to TrueType with otf2ttf.

Output: /tmp/NotoSerifSC-Regular.ttf, /tmp/NotoSerifSC-Bold.ttf
Requires: pip install fonttools otf2ttf
"""
import os
import subprocess
import sys

from fontTools.ttLib import TTCollection

PAIRS = [
    ("/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc", "Regular"),
    ("/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc", "Bold"),
]


def main():
    for src, weight in PAIRS:
        otf = "/tmp/NotoSerifSC-%s.otf" % weight
        ttf = "/tmp/NotoSerifSC-%s.ttf" % weight
        if os.path.exists(ttf):
            print("exists:", ttf)
            continue
        if not os.path.exists(src):
            sys.exit("missing font: " + src)
        col = TTCollection(src)
        idx = next((i for i, f in enumerate(col.fonts)
                    if "SC" in (f["name"].getDebugName(1) or "")), 2)
        col.fonts[idx].save(otf)
        print("extracted:", otf)
        subprocess.run(["otf2ttf", otf], check=True)
        print("converted:", ttf)


if __name__ == "__main__":
    main()
