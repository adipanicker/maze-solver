"""MazeApp – Tkinter GUI for the A* Maze Solver.

Features
--------
- Responsive, centered grid with min/max cell-size clamping
- Start (green "S") and Goal (red "G") always rendered on top
- Light / Dark theme toggle
- Sound ON / OFF with throttled search ticks
- Cell inspection panel showing g / h / f values
- "How A* Works" collapsible educational panel
- Difficulty selector (Easy / Medium / Hard → wall density)
- F11 fullscreen toggle, Escape exits fullscreen
- Fixed 1280×800 window, non-resizable, centered on launch
"""

import time
import tkinter as tk
from tkinter import ttk, font as tkfont

from astar import astar
from maze import Maze
from config import (
    WINDOW_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT,
    MIN_CELL_SIZE, MAX_CELL_SIZE,
    DEFAULT_DELAY_MS, MIN_DELAY_MS, MAX_DELAY_MS,
    SIZE_MAP, DIFFICULTY_MAP, CELL_COLORS, STATUS_COLORS,
    SOUND_TICK_EVERY_N,
)
from theme import LIGHT, DARK
from audio import SoundPlayer


class MazeApp:
    """Tkinter front-end for the A* maze solver."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(WINDOW_TITLE)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Theme & sound
        self.theme = LIGHT
        self.sound = SoundPlayer()

        self._setup_state()
        self._setup_fonts()
        self._configure_window()
        self._build_ui()
        self._apply_theme()
        self._reset_ui_state()

        # Key bindings
        self.root.bind("<F11>", self._toggle_fullscreen)
        self.root.bind("<Escape>", self._exit_fullscreen)

    # ==================================================================
    # 1.  STATE
    # ==================================================================
    def _setup_state(self):
        self.maze: Maze | None = None
        self.delay = tk.IntVar(value=DEFAULT_DELAY_MS)
        self.nodes_explored = tk.IntVar(value=0)
        self.path_len = tk.IntVar(value=0)
        self.exec_time_str = tk.StringVar(value="0.00 ms")
        self.status = tk.StringVar(value="Ready")
        self._anim_id = None
        self._solving = False
        self._gen = None
        self._algo_time = 0.0       # cumulative algorithm-only time (s)
        self._start_time = 0.0
        # geometry
        self.cell_sz = MIN_CELL_SIZE
        self.offset_x = 0
        self.offset_y = 0
        self._fullscreen = False
        # cell inspection data (populated during/after solve)
        self._explored_set: set = set()
        self._path_set: set = set()
        self._path_list: list = []
        # selection
        self._selected_cell = None

    def _setup_fonts(self):
        families = tkfont.families()
        body = "Segoe UI" if "Segoe UI" in families else "Helvetica"
        self.font_title  = (body, 18, "bold")
        self.font_heading = (body, 11, "bold")
        self.font_body   = (body, 10)
        self.font_small  = (body, 9)
        self.font_mono   = ("Consolas" if "Consolas" in families else "Courier", 10)

    # ==================================================================
    # 2.  WINDOW
    # ==================================================================
    def _configure_window(self):
        w, h = WINDOW_WIDTH, WINDOW_HEIGHT
        sx = self.root.winfo_screenwidth()
        sy = self.root.winfo_screenheight()
        x = (sx - w) // 2
        y = (sy - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.resizable(False, False)
        self.root.minsize(w, h)

    def _toggle_fullscreen(self, event=None):
        self._fullscreen = not self._fullscreen
        self.root.attributes("-fullscreen", self._fullscreen)
        if self._fullscreen:
            self.root.resizable(False, False)
        else:
            self.root.resizable(False, False)
        if self.maze:
            self.root.after(100, self._draw_grid)

    def _exit_fullscreen(self, event=None):
        if self._fullscreen:
            self._fullscreen = False
            self.root.attributes("-fullscreen", False)
            self.root.resizable(False, False)
            if self.maze:
                self.root.after(100, self._draw_grid)

    def _on_close(self):
        if self._anim_id:
            self.root.after_cancel(self._anim_id)
        self.root.destroy()

    # ==================================================================
    # 3.  UI CONSTRUCTION
    # ==================================================================
    def _build_ui(self):
        # ── Top bar: title + theme/sound toggles ──
        top = tk.Frame(self.root)
        top.pack(fill="x", padx=20, pady=(12, 0))

        self.lbl_title = tk.Label(top, text="🧩 A* Maze Solver", font=self.font_title, anchor="w")
        self.lbl_title.pack(side="left")

        toggles = tk.Frame(top)
        toggles.pack(side="right")

        self.btn_theme = tk.Button(toggles, text="🌙 Dark", font=self.font_small,
                                   relief="flat", bd=0, cursor="hand2",
                                   command=self._toggle_theme)
        self.btn_theme.pack(side="left", padx=6)

        self.sound_var = tk.StringVar(value="🔊 Sound: ON")
        self.btn_sound = tk.Button(toggles, textvariable=self.sound_var, font=self.font_small,
                                   relief="flat", bd=0, cursor="hand2",
                                   command=self._toggle_sound)
        self.btn_sound.pack(side="left", padx=6)

        # ── Main area: canvas + sidebar ──
        main = tk.Frame(self.root)
        main.pack(fill="both", expand=True, padx=20, pady=8)
        main.columnconfigure(0, weight=3)
        main.columnconfigure(1, weight=0)
        main.rowconfigure(0, weight=1)

        # Canvas
        self.canvas = tk.Canvas(main, highlightthickness=0, cursor="crosshair")
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<Configure>", self._on_resize)

        # Sidebar
        self.sidebar = tk.Frame(main, width=240)
        self.sidebar.grid(row=0, column=1, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self._build_sidebar()

        # ── Bottom area: controls + legend + education ──
        bottom = tk.Frame(self.root)
        bottom.pack(fill="x", padx=20, pady=(0, 8))
        self._build_controls(bottom)
        self._build_legend(bottom)
        self._build_education(bottom)

    # -- Sidebar ---
    def _build_sidebar(self):
        sb = self.sidebar

        # Stats card
        self.stats_frame = tk.LabelFrame(sb, text=" Statistics ", font=self.font_heading,
                                         labelanchor="nw", padx=12, pady=8)
        self.stats_frame.pack(fill="x", pady=(0, 10))

        stat_defs = [
            ("Algorithm", "A*"),
            ("Heuristic", "Manhattan"),
        ]
        self._stat_labels = {}
        for label, value in stat_defs:
            row = tk.Frame(self.stats_frame)
            row.pack(fill="x", pady=2)
            lk = tk.Label(row, text=label, font=self.font_small, anchor="w")
            lk.pack(side="left")
            lv = tk.Label(row, text=value, font=(self.font_small[0], self.font_small[1], "bold"), anchor="e")
            lv.pack(side="right")
            self._stat_labels[label] = (lk, lv)

        # Dynamic stats
        dynamic = [
            ("Nodes Explored", self.nodes_explored),
            ("Path Length",    self.path_len),
        ]
        for label, var in dynamic:
            row = tk.Frame(self.stats_frame)
            row.pack(fill="x", pady=2)
            lk = tk.Label(row, text=label, font=self.font_small, anchor="w")
            lk.pack(side="left")
            lv = tk.Label(row, textvariable=var, font=(self.font_small[0], self.font_small[1], "bold"), anchor="e")
            lv.pack(side="right")
            self._stat_labels[label] = (lk, lv)

        # Execution time
        row = tk.Frame(self.stats_frame)
        row.pack(fill="x", pady=2)
        lk = tk.Label(row, text="Exec Time", font=self.font_small, anchor="w")
        lk.pack(side="left")
        self.lbl_exec_time = tk.Label(row, textvariable=self.exec_time_str,
                                      font=(self.font_small[0], self.font_small[1], "bold"), anchor="e")
        self.lbl_exec_time.pack(side="right")
        self._stat_labels["Exec Time"] = (lk, self.lbl_exec_time)

        # Status
        row = tk.Frame(self.stats_frame)
        row.pack(fill="x", pady=(6, 2))
        lk = tk.Label(row, text="Status", font=self.font_small, anchor="w")
        lk.pack(side="left")
        self.lbl_status = tk.Label(row, textvariable=self.status,
                                   font=(self.font_small[0], self.font_small[1], "bold"), anchor="e")
        self.lbl_status.pack(side="right")
        self._stat_labels["Status"] = (lk, self.lbl_status)

        # ── Cell Inspection card ──
        self.inspect_frame = tk.LabelFrame(sb, text=" Cell Inspector ", font=self.font_heading,
                                           labelanchor="nw", padx=12, pady=8)
        self.inspect_frame.pack(fill="x", pady=(0, 10))

        self.inspect_labels = {}
        for field in ("Row", "Column", "g(n)", "h(n)", "f(n)", "State"):
            row = tk.Frame(self.inspect_frame)
            row.pack(fill="x", pady=1)
            lk = tk.Label(row, text=field, font=self.font_small, anchor="w")
            lk.pack(side="left")
            lv = tk.Label(row, text="—", font=self.font_mono, anchor="e")
            lv.pack(side="right")
            self.inspect_labels[field] = (lk, lv)

    # -- Controls bar ---
    def _build_controls(self, parent):
        ctrl = tk.Frame(parent)
        ctrl.pack(fill="x", pady=(0, 6))

        # Buttons
        btn_frame = tk.Frame(ctrl)
        btn_frame.pack(side="left")
        self.btn_solve = tk.Button(btn_frame, text="▶  Solve", font=self.font_body,
                                   relief="flat", padx=14, pady=4, cursor="hand2",
                                   command=self.solve)
        self.btn_solve.pack(side="left", padx=(0, 6))
        self.btn_new = tk.Button(btn_frame, text="🔀  New Maze", font=self.font_body,
                                 relief="flat", padx=14, pady=4, cursor="hand2",
                                 command=self.new_maze)
        self.btn_new.pack(side="left", padx=(0, 6))
        self.btn_reset = tk.Button(btn_frame, text="↺  Reset", font=self.font_body,
                                   relief="flat", padx=14, pady=4, cursor="hand2",
                                   command=self.reset)
        self.btn_reset.pack(side="left", padx=(0, 6))

        # Right side: dropdowns + slider
        right = tk.Frame(ctrl)
        right.pack(side="right")

        # Size
        tk.Label(right, text="Size:", font=self.font_small).pack(side="left", padx=(0, 2))
        self.size_var = tk.StringVar(value="Small")
        self.opt_size = ttk.OptionMenu(right, self.size_var, "Small", *SIZE_MAP.keys())
        self.opt_size.pack(side="left", padx=(0, 10))

        # Difficulty
        tk.Label(right, text="Difficulty:", font=self.font_small).pack(side="left", padx=(0, 2))
        self.diff_var = tk.StringVar(value="Medium")
        self.opt_diff = ttk.OptionMenu(right, self.diff_var, "Medium", *DIFFICULTY_MAP.keys())
        self.opt_diff.pack(side="left", padx=(0, 10))

        # Speed
        tk.Label(right, text="Speed:", font=self.font_small).pack(side="left", padx=(0, 2))
        self.speed_scale = ttk.Scale(right, from_=MIN_DELAY_MS, to=MAX_DELAY_MS,
                                     orient="horizontal", variable=self.delay, length=100)
        self.speed_scale.pack(side="left")

    # -- Legend ---
    def _build_legend(self, parent):
        self.legend_frame = tk.Frame(parent)
        self.legend_frame.pack(fill="x", pady=(0, 4))

        items = [
            ("Start (S)", CELL_COLORS["start"]),
            ("Goal (G)",  CELL_COLORS["goal"]),
            ("Wall",      None),   # filled at theme-apply time
            ("Unvisited", None),
            ("Explored",  CELL_COLORS["explored"]),
            ("Path",      CELL_COLORS["path"]),
        ]
        self._legend_swatches = {}
        for text, colour in items:
            fr = tk.Frame(self.legend_frame)
            fr.pack(side="left", padx=8)
            sw = tk.Canvas(fr, width=14, height=14, highlightthickness=0, bd=0)
            if colour:
                sw.create_rectangle(1, 1, 13, 13, fill=colour, outline="#888")
            else:
                sw.create_rectangle(1, 1, 13, 13, fill="#ccc", outline="#888", tags="swatch")
            sw.pack(side="left")
            lbl = tk.Label(fr, text=text, font=self.font_small)
            lbl.pack(side="left", padx=2)
            self._legend_swatches[text] = (sw, lbl)

    # -- Education panel ---
    def _build_education(self, parent):
        self._edu_expanded = False

        self.edu_toggle = tk.Button(parent, text="▶  How A* Works", font=self.font_heading,
                                    relief="flat", bd=0, cursor="hand2",
                                    anchor="w", command=self._toggle_education)
        self.edu_toggle.pack(fill="x", pady=(2, 0))

        self.edu_frame = tk.Frame(parent)
        # starts collapsed

        edu_text = (
            "f(n)  =  g(n)  +  h(n)\n"
            "\n"
            "g(n)   Actual cost from Start to the current cell.\n"
            "h(n)   Estimated cost from the current cell to Goal.\n"
            "f(n)   Total estimated cost — A* always expands the\n"
            "       node with the lowest f(n) first.\n"
            "\n"
            "Heuristic:  Manhattan Distance\n"
            "\n"
            "  h(n) = |current_row − goal_row|\n"
            "       + |current_col − goal_col|\n"
        )
        self.edu_label = tk.Label(self.edu_frame, text=edu_text, font=self.font_mono,
                                  justify="left", anchor="nw", padx=12, pady=6)
        self.edu_label.pack(fill="x")

    def _toggle_education(self):
        self._edu_expanded = not self._edu_expanded
        if self._edu_expanded:
            self.edu_toggle.config(text="▼  How A* Works")
            self.edu_frame.pack(fill="x", pady=(0, 4))
        else:
            self.edu_toggle.config(text="▶  How A* Works")
            self.edu_frame.pack_forget()

    # ==================================================================
    # 4.  THEME
    # ==================================================================
    def _toggle_theme(self):
        self.theme = DARK if self.theme["name"] == "light" else LIGHT
        self._apply_theme()
        if self.maze:
            self._draw_grid()

    def _toggle_sound(self):
        on = self.sound.toggle()
        self.sound_var.set("🔊 Sound: ON" if on else "🔇 Sound: OFF")

    def _apply_theme(self):
        t = self.theme
        is_dark = t["name"] == "dark"
        self.btn_theme.config(text="☀️ Light" if is_dark else "🌙 Dark")

        # Root
        self.root.configure(bg=t["bg"])

        # Recursively style plain tk widgets
        self._style_children(self.root, t)

        # Canvas
        self.canvas.configure(bg=t["canvas_bg"])

        # Buttons
        for btn in (self.btn_solve, self.btn_new, self.btn_reset,
                     self.btn_theme, self.btn_sound, self.edu_toggle):
            btn.configure(bg=t["btn_bg"], fg=t["btn_fg"], activebackground=t["border"],
                          activeforeground=t["text"])

        # Legend swatches – update Wall/Unvisited colours
        wall_sw = self._legend_swatches.get("Wall", (None, None))[0]
        if wall_sw:
            wall_sw.delete("swatch")
            wall_sw.create_rectangle(1, 1, 13, 13, fill=t["wall"], outline="#888", tags="swatch")
        unvis_sw = self._legend_swatches.get("Unvisited", (None, None))[0]
        if unvis_sw:
            unvis_sw.delete("swatch")
            unvis_sw.create_rectangle(1, 1, 13, 13, fill=t["empty"], outline="#888", tags="swatch")

        # Status colour
        self._update_status_colour()

        # LabelFrame borders
        for lf in (self.stats_frame, self.inspect_frame):
            lf.configure(bg=t["panel"], fg=t["text"])

    def _style_children(self, widget, t):
        """Recursively apply bg/fg to plain tk.Frame / tk.Label widgets."""
        wtype = widget.winfo_class()
        try:
            if wtype == "Frame":
                widget.configure(bg=t["bg"])
            elif wtype == "Label":
                widget.configure(bg=t["bg"], fg=t["text"])
            elif wtype == "Labelframe":
                widget.configure(bg=t["panel"], fg=t["text"])
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            self._style_children(child, t)

    # ==================================================================
    # 5.  MAZE HELPERS
    # ==================================================================
    def _default_maze(self) -> Maze:
        """Hard-coded solvable 5×5 maze shown on launch."""
        grid = [
            [0, 1, 1, 0, 0],
            [0, 0, 0, 1, 0],
            [1, 1, 0, 0, 0],
            [0, 0, 0, 1, 0],
            [0, 1, 0, 0, 0],
        ]
        return Maze(grid, (0, 0), (4, 4))

    def _make_maze_from_size(self) -> Maze:
        n = SIZE_MAP.get(self.size_var.get(), 5)
        wall_prob = DIFFICULTY_MAP.get(self.diff_var.get(), 0.25)
        return Maze.random(n, n, wall_prob=wall_prob)

    def start_with_default(self):
        """Called once from main.py after mainloop is ready."""
        self.maze = self._default_maze()
        # schedule draw after the window has been mapped
        self.root.after(50, self._draw_grid)

    def new_maze(self):
        if self._solving:
            return
        self.maze = self._make_maze_from_size()
        self._reset_ui_state()
        self._draw_grid()

    def reset(self):
        """Clear exploration / path colours; keep walls."""
        if self._solving:
            self.root.after_cancel(self._anim_id)
            self._anim_id = None
            self._solving = False
        self._reset_ui_state()
        self._draw_grid()

    def _reset_ui_state(self):
        self.nodes_explored.set(0)
        self.path_len.set(0)
        self.exec_time_str.set("0.00 ms")
        self.status.set("Ready")
        self._update_status_colour()
        self._gen = None
        self._algo_time = 0.0
        self._start_time = 0.0
        self._explored_set = set()
        self._path_set = set()
        self._path_list = []
        self._selected_cell = None
        self._clear_inspection()

    # ==================================================================
    # 6.  DRAWING — CORRECT PAINT ORDER
    # ==================================================================
    def _on_resize(self, event):
        if self.maze:
            self._draw_grid()

    def _draw_grid(self):
        """Full redraw.  Paint order per spec:
        1. base cell  2. explored/path overlay  3. grid border
        4. start fill + "S"   5. goal fill + "G"
        """
        c = self.canvas
        c.delete("all")
        if not self.maze:
            return
        rows, cols = self.maze.rows, self.maze.cols
        cw = c.winfo_width()
        ch = c.winfo_height()
        if cw <= 1 or ch <= 1:
            self.root.after(100, self._draw_grid)
            return

        t = self.theme
        self.cell_sz = max(MIN_CELL_SIZE,
                           min(MAX_CELL_SIZE, min(cw, ch) // max(rows, cols)))
        grid_w = cols * self.cell_sz
        grid_h = rows * self.cell_sz
        self.offset_x = (cw - grid_w) // 2
        self.offset_y = (ch - grid_h) // 2

        for r in range(rows):
            for c_idx in range(cols):
                x1 = self.offset_x + c_idx * self.cell_sz
                y1 = self.offset_y + r * self.cell_sz
                x2 = x1 + self.cell_sz
                y2 = y1 + self.cell_sz

                cell = (r, c_idx)
                # 1. base colour
                if self.maze.grid[r][c_idx] == 1:
                    fill = t["wall"]
                else:
                    fill = t["empty"]

                # 2. explored / path overlay (only for non-start/goal)
                if cell not in (self.maze.start, self.maze.goal):
                    if cell in self._path_set:
                        fill = CELL_COLORS["path"]
                    elif cell in self._explored_set:
                        fill = CELL_COLORS["explored"]

                # 3. start / goal ALWAYS override
                if cell == self.maze.start:
                    fill = CELL_COLORS["start"]
                elif cell == self.maze.goal:
                    fill = CELL_COLORS["goal"]

                c.create_rectangle(x1, y1, x2, y2, fill=fill,
                                   outline=CELL_COLORS["grid"], tags=f"cell_{r}_{c_idx}")

        # 4-5. letters on top
        self._draw_letter(self.maze.start, "S")
        self._draw_letter(self.maze.goal, "G")

        # re-highlight selected cell if any
        if self._selected_cell:
            self._highlight_selected(self._selected_cell)

    def _draw_letter(self, pos, char):
        r, c_idx = pos
        x = self.offset_x + c_idx * self.cell_sz + self.cell_sz // 2
        y = self.offset_y + r * self.cell_sz + self.cell_sz // 2
        self.canvas.create_text(
            x, y, text=char, fill="white",
            font=(self.font_body[0], max(8, int(self.cell_sz * 0.45)), "bold"),
            tags=f"letter_{r}_{c_idx}",
        )

    def _paint_cell(self, cell, colour):
        """Repaint a single cell and ensure start/goal stay on top."""
        r, c_idx = cell
        tag = f"cell_{r}_{c_idx}"
        # if this is start or goal, force their colour
        if cell == self.maze.start:
            self.canvas.itemconfigure(tag, fill=CELL_COLORS["start"])
            self.canvas.delete(f"letter_{r}_{c_idx}")
            self._draw_letter(cell, "S")
        elif cell == self.maze.goal:
            self.canvas.itemconfigure(tag, fill=CELL_COLORS["goal"])
            self.canvas.delete(f"letter_{r}_{c_idx}")
            self._draw_letter(cell, "G")
        else:
            self.canvas.itemconfigure(tag, fill=colour)

    # ==================================================================
    # 7.  CLICK HANDLING (wall toggle + cell inspection)
    # ==================================================================
    def _on_canvas_click(self, event):
        if not self.maze:
            return
        col = (event.x - self.offset_x) // self.cell_sz
        row = (event.y - self.offset_y) // self.cell_sz
        if not (0 <= row < self.maze.rows and 0 <= col < self.maze.cols):
            return

        cell = (row, col)

        # If NOT solving and NOT solved → wall toggle mode
        if not self._solving and not self._explored_set:
            if cell in (self.maze.start, self.maze.goal):
                return
            self.maze.grid[row][col] = 0 if self.maze.grid[row][col] == 1 else 1
            new_fill = self.theme["wall"] if self.maze.grid[row][col] == 1 else self.theme["empty"]
            self._paint_cell(cell, new_fill)
            return

        # Otherwise → inspection mode
        self._inspect_cell(cell)

    def _inspect_cell(self, cell):
        r, c_idx = cell
        self._selected_cell = cell
        # Clear old highlight, draw new
        self.canvas.delete("sel_highlight")
        self._highlight_selected(cell)

        # Determine state
        if cell == self.maze.start:
            state = "Start"
        elif cell == self.maze.goal:
            state = "Goal"
        elif self.maze.grid[r][c_idx] == 1:
            state = "Wall"
        elif cell in self._path_set:
            state = "Path"
        elif cell in self._explored_set:
            state = "Explored"
        else:
            state = "Unvisited"

        # Compute h (always Manhattan to goal)
        gr, gc = self.maze.goal
        h_val = abs(r - gr) + abs(c_idx - gc)

        # Compute g: if on path, use index; otherwise "—"
        if cell in self._path_set and self._path_list:
            try:
                g_val = self._path_list.index(cell)
            except ValueError:
                g_val = None
        elif cell == self.maze.start:
            g_val = 0
        else:
            g_val = None

        f_val = (g_val + h_val) if g_val is not None else None

        self.inspect_labels["Row"][1].config(text=str(r))
        self.inspect_labels["Column"][1].config(text=str(c_idx))
        self.inspect_labels["g(n)"][1].config(text=str(g_val) if g_val is not None else "—")
        self.inspect_labels["h(n)"][1].config(text=str(h_val))
        self.inspect_labels["f(n)"][1].config(text=str(f_val) if f_val is not None else "—")
        self.inspect_labels["State"][1].config(text=state)

    def _highlight_selected(self, cell):
        r, c_idx = cell
        x1 = self.offset_x + c_idx * self.cell_sz
        y1 = self.offset_y + r * self.cell_sz
        x2 = x1 + self.cell_sz
        y2 = y1 + self.cell_sz
        self.canvas.create_rectangle(x1, y1, x2, y2, outline="#f97316", width=3,
                                     fill="", tags="sel_highlight")

    def _clear_inspection(self):
        for field in self.inspect_labels:
            self.inspect_labels[field][1].config(text="—")
        self.canvas.delete("sel_highlight")

    # ==================================================================
    # 8.  SOLVING & ANIMATION
    # ==================================================================
    def solve(self):
        if self._solving:
            return
        if not self.maze:
            return
        self._solving = True
        self._explored_set = set()
        self._path_set = set()
        self._path_list = []
        self._selected_cell = None
        self._clear_inspection()
        # redraw clean grid before solving
        self._draw_grid()

        self.status.set("Searching...")
        self._update_status_colour()
        self.nodes_explored.set(0)
        self.path_len.set(0)
        self._algo_time = 0.0
        self.exec_time_str.set("0.00 ms")

        self._gen = astar(self.maze, self.maze.start, self.maze.goal)
        self._start_time = time.perf_counter()
        self._step()

    def _step(self):
        try:
            t0 = time.perf_counter()
            event, payload = next(self._gen)
            self._algo_time += time.perf_counter() - t0
            self.exec_time_str.set(f"{self._algo_time * 1000:.2f} ms")
        except StopIteration:
            self._finish(None)
            return

        if event == "explore":
            cell = payload
            self._explored_set.add(cell)
            n = self.nodes_explored.get() + 1
            self.nodes_explored.set(n)
            # paint (start/goal stay green/red thanks to _paint_cell)
            self._paint_cell(cell, CELL_COLORS["explored"])
            # throttled sound
            if self.sound.enabled and n % SOUND_TICK_EVERY_N == 0:
                self.sound.play_search_tick()
            self._anim_id = self.root.after(self.delay.get(), self._step)
        elif event == "done":
            self._finish(payload)

    def _finish(self, path):
        self._solving = False
        self._anim_id = None
        self.exec_time_str.set(f"{self._algo_time * 1000:.2f} ms")
        if path is None:
            self.status.set("No Path Found ✗")
            self._update_status_colour()
            return
        self.status.set("Path Found ✓")
        self._update_status_colour()
        self.path_len.set(len(path) - 1)
        self._path_list = list(path)
        self.sound.play_success()
        self._animate_path(path, 0)

    def _animate_path(self, path, idx):
        if idx >= len(path):
            return
        cell = path[idx]
        self._path_set.add(cell)
        self._paint_cell(cell, CELL_COLORS["path"])
        # soft ascending tone for path animation
        if idx % 2 == 0:
            self.sound.play_path_step()
        self._anim_id = self.root.after(self.delay.get(),
                                        lambda: self._animate_path(path, idx + 1))

    # ==================================================================
    # 9.  STATUS COLOUR
    # ==================================================================
    def _update_status_colour(self):
        colour = STATUS_COLORS.get(self.status.get(), "#6b7280")
        self.lbl_status.configure(fg=colour)


# ── Standalone entry point ────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app = MazeApp(root)
    app.start_with_default()
    root.mainloop()
