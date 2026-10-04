# 🧩 A* Maze Solver

A lightweight, pure-Python Tkinter application that visualises the **A\* path-finding algorithm** on a grid-based maze.  
Zero external dependencies — uses only the Python standard library.

## Quick Start

```bash
python main.py
```

The window opens at **1280 × 800**, centered, with a solvable 5 × 5 default maze.

## Features

| Category | Details |
|---|---|
| **Algorithm** | A\* with Manhattan heuristic (generator-based, yields per-node events) |
| **Visualisation** | Explored → yellow, Final path → blue, animated step-by-step |
| **Start / Goal** | Green **S** / Red **G** — always drawn on top of overlays |
| **Responsive canvas** | Grid centered with cell-size clamped 16–60 px; adapts to fullscreen |
| **Fullscreen** | **F11** toggles, **Escape** exits |
| **Light / Dark theme** | One-click toggle, semantic maze colours stay consistent |
| **Sound** | Optional search tick, success chime, path animation tones (toggle ON/OFF) |
| **Cell Inspector** | Click any cell after solving to see g(n), h(n), f(n), and state |
| **"How A\* Works"** | Collapsible educational panel explaining f = g + h and the Manhattan heuristic |
| **Difficulty** | Easy / Medium / Hard controls wall density; mazes are always solvable |
| **Size selector** | Small (5×5), Medium (10×10), Large (20×20) |
| **Click-to-toggle** | Click cells to add/remove walls before solving |
| **Stats** | Nodes explored, path length, execution time (algorithm-only, in ms) |
| **Status** | Ready (gray) · Searching (amber) · Path Found ✓ (green) · No Path Found ✗ (red) |

## Files

```
maze_solver/
├── main.py          # Entry point
├── astar.py         # A* generator (immutable)
├── maze.py          # Maze data structure + Maze.random factory
├── gui.py           # MazeApp Tkinter UI
├── config.py        # Shared constants
├── theme.py         # Light / Dark theme definitions
├── audio.py         # Sound system (winsound + generated WAVs)
├── test_astar.py    # Unit tests
├── requirements.txt # (empty — stdlib only)
├── assets/
│   └── sounds/      # Auto-generated WAV files
└── README.md
```

## Controls

| Action | How |
|---|---|
| Solve | Click **▶ Solve** |
| New maze | Click **🔀 New Maze** |
| Reset | Click **↺ Reset** (keeps walls, clears solve) |
| Toggle wall | Click a cell *before* solving |
| Inspect cell | Click a cell *during/after* solving |
| Fullscreen | **F11** |
| Exit fullscreen | **Escape** |
| Theme | Click **🌙 Dark** / **☀️ Light** |
| Sound | Click **🔊 Sound: ON/OFF** |

## Default Maze

```
0 1 1 0 0
0 0 0 1 0
1 1 0 0 0
0 0 0 1 0
0 1 0 0 0
```

Start `(0,0)` → Goal `(4,4)`.

## Screenshots

*(Add screenshots in a `screens/` folder and reference them here.)*

---

Built for demonstrating A\* search in an AI / Data Structures viva.
