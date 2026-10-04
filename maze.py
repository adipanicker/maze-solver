class Maze:
    def __init__(self, grid, start, goal):
        self.grid = grid
        self.start = start
        self.goal = goal
        self.rows = len(grid)
        self.cols = len(grid[0])

    def neighbours(self, cell):
        r, c = cell
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):  # UP, DOWN, LEFT, RIGHT
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.rows and 0 <= nc < self.cols and self.grid[nr][nc] == 0:
                yield (nr, nc)

    @classmethod
    def random(cls, rows, cols, wall_prob=0.25):
        """
        Generate a random maze. Guarantees a solvable path.
        * 0 – empty cell, 1 – wall.
        * The start cell (0,0) and the goal cell (rows‑1, cols‑1) are never walls.
        * Attempts up to 100 times; if none solvable, falls back to an open grid.
        """
        import random
        from astar import astar

        for _ in range(100):
            grid = []
            for r in range(rows):
                row = []
                for c in range(cols):
                    if (r, c) in ((0, 0), (rows - 1, cols - 1)):
                        row.append(0)
                    else:
                        row.append(1 if random.random() < wall_prob else 0)
                grid.append(row)
            maze = cls(grid, (0, 0), (rows - 1, cols - 1))
            # Check solvability using astar generator
            gen = astar(maze, maze.start, maze.goal)
            for ev, payload in gen:
                if ev == "done" and payload is not None:
                    return maze
        # Fallback: completely open grid
        open_grid = [[0 for _ in range(cols)] for _ in range(rows)]
        return cls(open_grid, (0, 0), (rows - 1, cols - 1))