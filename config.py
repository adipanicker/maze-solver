"""Shared constants and configuration for the A* Maze Solver."""


# ── Window ────────────────────────────────────────────────────────────
WINDOW_TITLE = "A* Maze Solver"
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 800

# ── Cell rendering ────────────────────────────────────────────────────
MIN_CELL_SIZE = 16
MAX_CELL_SIZE = 60

# ── Animation ─────────────────────────────────────────────────────────
DEFAULT_DELAY_MS = 30
MIN_DELAY_MS = 1
MAX_DELAY_MS = 100
SOUND_TICK_EVERY_N = 7   # play a tick sound every N explored nodes

# ── Maze sizes ────────────────────────────────────────────────────────
SIZE_MAP = {"Small": 5, "Medium": 10, "Large": 20}

# ── Difficulty → wall probability ─────────────────────────────────────
DIFFICULTY_MAP = {
    "Easy":   0.15,
    "Medium": 0.25,
    "Hard":   0.35,
}

# ── Semantic cell colours (shared by both themes) ─────────────────────
CELL_COLORS = {
    "start":    "#22c55e",
    "goal":     "#ef4444",
    "explored": "#facc15",
    "path":     "#3b82f6",
    "grid":     "#d1d5db",
}

# ── Status label colours ──────────────────────────────────────────────
STATUS_COLORS = {
    "Ready":            "#6b7280",
    "Searching...":     "#f59e0b",
    "Path Found ✓":     "#22c55e",
    "No Path Found ✗":  "#ef4444",
}
