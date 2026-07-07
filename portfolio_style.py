"""
portfolio_style.py — Mario Casanova design tokens for matplotlib

Drop-in module for Jupyter notebooks in MarioCasanovacf/Portfolio. Importing
this file applies the brand palette and typography to all subsequent matplotlib
figures, so SVG exports for the website inherit the design system without
manual restyling.

Usage:
    import portfolio_style  # auto-applies on import
    # or, explicitly:
    from portfolio_style import apply, COLORS, SERIES

The palette mirrors colors_and_type.css. Series cycle: ink, oxblood, ochre,
dark-forest, warm-grey — the same five used across the site.

Fonts: IBM Plex Sans for axes/labels, IBM Plex Mono for tick labels and
annotations. If Plex is not installed, matplotlib falls back to its default
sans/mono — figures still read correctly, just slightly off-brand. Install with:
    pip install matplotlib  # then ensure IBM Plex is on the system
or download from https://www.ibm.com/plex/

Export:
    fig.savefig('fig.svg', format='svg', bbox_inches='tight', transparent=True)

`transparent=True` lets the page's --paper background show through, so the
figure inherits whatever paper tone the surrounding layout uses.
"""

from cycler import cycler
import matplotlib as mpl
import matplotlib.pyplot as plt


# ---------- Colors (mirror of colors_and_type.css) ----------

COLORS = {
    "paper":       "#F4EFE6",
    "paper_deep":  "#EBE4D6",
    "paper_hi":    "#FAF6EE",
    "ink":         "#1A1814",
    "ink_2":       "#3C3833",
    "ink_3":       "#6B655C",
    "ink_4":       "#948D82",
    "oxblood":     "#6E1F1F",
    "oxblood_2":   "#8A2B2B",
    "ochre":       "#A87333",
    "ochre_2":     "#C28A45",
    "forest":      "#2E4A3F",
    "warm_grey":   "#6B655C",
}

# Diagrammatic series — match --series-1..5 in CSS
SERIES = [
    COLORS["ink"],       # series-1
    COLORS["oxblood"],   # series-2 — the single chromatic accent
    COLORS["ochre"],     # series-3
    COLORS["forest"],    # series-4
    COLORS["warm_grey"], # series-5
]


# ---------- rcParams ----------

RC = {
    # Figure
    "figure.facecolor":   "none",          # transparent — page paper shows through
    "savefig.facecolor":  "none",
    "savefig.transparent": True,
    "savefig.bbox":       "tight",
    "savefig.pad_inches": 0.05,

    # Axes
    "axes.facecolor":     "none",
    "axes.edgecolor":     COLORS["ink"],
    "axes.linewidth":     1.0,
    "axes.labelcolor":    COLORS["ink"],
    "axes.titlecolor":    COLORS["ink"],
    "axes.titleweight":   "600",
    "axes.titlesize":     11,
    "axes.titlepad":      10,
    "axes.labelsize":     11,
    "axes.labelpad":      6,
    "axes.spines.top":    False,
    "axes.spines.right":  False,
    "axes.grid":          False,
    "axes.prop_cycle":    cycler(color=SERIES),

    # Ticks
    "xtick.color":        COLORS["ink"],
    "ytick.color":        COLORS["ink"],
    "xtick.labelcolor":   COLORS["ink_3"],
    "ytick.labelcolor":   COLORS["ink_3"],
    "xtick.labelsize":    9,
    "ytick.labelsize":    9,
    "xtick.direction":    "out",
    "ytick.direction":    "out",
    "xtick.major.size":   4,
    "ytick.major.size":   4,
    "xtick.minor.size":   2,
    "ytick.minor.size":   2,
    "xtick.major.width":  0.8,
    "ytick.major.width":  0.8,

    # Lines
    "lines.linewidth":    1.4,
    "lines.solid_capstyle": "round",
    "lines.markersize":   4,

    # Legend
    "legend.frameon":     False,
    "legend.fontsize":    10,
    "legend.labelcolor":  COLORS["ink_2"],
    "legend.loc":         "best",

    # Grid (off by default; if turned on, hairline)
    "grid.color":         COLORS["ink"],
    "grid.linewidth":     0.4,
    "grid.alpha":         0.18,

    # Fonts
    "font.family":        "sans-serif",
    "font.sans-serif":    ["IBM Plex Sans", "Helvetica Neue", "Arial", "DejaVu Sans"],
    "font.monospace":     ["IBM Plex Mono", "JetBrains Mono", "SF Mono", "DejaVu Sans Mono"],
    "font.size":          10,
    "mathtext.fontset":   "stix",  # cleaner serif math, closer to KaTeX feel

    # Output
    "svg.fonttype":       "none",  # keep text as <text>, not paths — searchable + light
    "pdf.fonttype":       42,      # TrueType fonts in PDF (also lighter, embedded)
    "ps.fonttype":        42,
}


def apply():
    """Apply Mario's design tokens to matplotlib's global rcParams."""
    mpl.rcParams.update(RC)


def palette(name):
    """Return a hex color by short name (e.g. 'oxblood', 'ink_2')."""
    return COLORS[name]


def series(n=None):
    """Return the diagrammatic series cycle, or its first n entries."""
    return SERIES[:n] if n is not None else list(SERIES)


# ---------- Auto-apply on import ----------
apply()


__all__ = ["apply", "palette", "series", "COLORS", "SERIES", "RC"]
