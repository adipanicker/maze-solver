from maze import Maze
from astar import astar

GRID = [
    [0, 1, 1, 0, 0],
    [0, 0, 0, 1, 0],
    [1, 1, 0, 0, 0],
    [0, 0, 0, 1, 0],
    [0, 1, 0, 0, 0],
]


def solve(maze):
    explored = 0
    for kind, data in astar(maze, maze.start, maze.goal):
        if kind == "explore":
            explored += 1
        else:
            return data, explored


def test_path_found():
    path, explored = solve(Maze(GRID, (0, 0), (4, 4)))
    assert path is not None
    assert path[0] == (0, 0) and path[-1] == (4, 4)
    assert len(path) == 9  # 8 moves, 9 cells
    print("path:", path, "| explored:", explored)


def test_no_path():
    blocked = [
        [0, 1, 0],
        [1, 1, 0],
        [0, 0, 0],
    ]
    path, _ = solve(Maze(blocked, (0, 0), (2, 2)))
    assert path is None


if __name__ == "__main__":
    test_path_found()
    test_no_path()
    print("All tests passed")