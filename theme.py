"""Light / Dark theme definitions for the A* Maze Solver.

Each theme is a plain dict. Keys that gui.py reads:
    bg          – root / frame background
    panel       – card / stat-panel background
    text        – primary text colour
    text_dim    – secondary / muted text colour
    wall        – wall cell fill
    empty       – empty (unvisited) cell fill
    canvas_bg   – canvas background outside the grid
    border      – subtle borders / separators
    btn_bg      – button background
    btn_fg      – button foreground text
"""

LIGHT = {
    "name":       "light",
    "bg":         "#f1f5f9",    # slate-100
    "panel":      "#ffffff",
    "text":       "#1e293b",    # slate-800
    "text_dim":   "#64748b",    # slate-500
    "wall":       "#1f2937",    # gray-800
    "empty":      "#ffffff",
    "canvas_bg":  "#f1f5f9",
    "border":     "#e2e8f0",    # slate-200
    "btn_bg":     "#e2e8f0",
    "btn_fg":     "#1e293b",
    "grid":       "#d1d5db",    # slate-300 — light grid lines
}

DARK = {
    "name":       "dark",
    "bg":         "#0b1120",    # deep navy, minimal blue tint
    "panel":      "#111827",    # gray-900
    "text":       "#f8fafc",    # slate-50 — bright text
    "text_dim":   "#94a3b8",    # slate-400
    "wall":       "#020617",    # near-black — clearly distinct from unvisited
    "empty":      "#263449",    # lighter dark slate — clearly distinct from wall
    "canvas_bg":  "#0b1120",
    "border":     "#1e293b",
    "btn_bg":     "#1e293b",
    "btn_fg":     "#f8fafc",
    "grid":       "#475569",    # slate-600 — visible grid lines in dark mode
}
