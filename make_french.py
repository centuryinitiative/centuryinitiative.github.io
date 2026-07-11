"""
Render French (_fr) versions of a plotting script's figures/videos WITHOUT
modifying the script. Monkeypatches matplotlib so that:
  * every rendered string is routed through french_i18n.translate()
  * every saved file (PNG via Figure.savefig, MP4 via Animation.save) gets a
    `_fr` suffix inserted before the extension.

Usage:
    python3 make_french.py <script.py>

After the script runs, any prose strings that were NOT translated are printed
to stderr as "[i18n-miss]" lines so translation gaps can be filled.
"""
import os
import sys
import runpy

import matplotlib
matplotlib.use("Agg")
import matplotlib.text as mtext
import matplotlib.figure as mfigure
import matplotlib.animation as manimation

import french_i18n as i18n


def _fr_path(path):
    if not isinstance(path, (str, os.PathLike)):
        return path
    path = os.fspath(path)
    d, b = os.path.split(path)
    root, ext = os.path.splitext(b)
    if root.endswith("_fr"):
        return path
    return os.path.join(d, root + "_fr" + ext)


def install():
    # -- text translation ---------------------------------------------------
    # Text.__init__ funnels through set_text, so patching set_text alone covers
    # titles, axis labels, legend entries, annotations and tick labels — one
    # translation pass per string (no double-translation).
    _orig_set_text = mtext.Text.set_text
    def set_text(self, s):
        return _orig_set_text(self, i18n.translate(s))
    mtext.Text.set_text = set_text

    # -- figure saving ------------------------------------------------------
    _orig_savefig = mfigure.Figure.savefig
    def savefig(self, fname, *a, **k):
        return _orig_savefig(self, _fr_path(fname), *a, **k)
    mfigure.Figure.savefig = savefig

    # -- animation saving ---------------------------------------------------
    _orig_anim_save = manimation.Animation.save
    def anim_save(self, filename, *a, **k):
        return _orig_anim_save(self, _fr_path(filename), *a, **k)
    manimation.Animation.save = anim_save


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: python3 make_french.py <script.py>")
    script = sys.argv[1]
    # present argv to the target script as if invoked directly
    sys.argv = [script]
    install()
    print(f"[fr] rendering French version of {script} ...")
    runpy.run_path(script, run_name="__main__")
    if i18n.MISSES:
        print(f"\n[fr] {len(i18n.MISSES)} untranslated prose string(s):", file=sys.stderr)
        for s in sorted(i18n.MISSES):
            print(f"[i18n-miss] {s!r}", file=sys.stderr)


if __name__ == "__main__":
    main()
