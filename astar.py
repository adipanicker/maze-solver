import heapq


def astar(maze, start, goal):
    """Generator. Yields ('explore', cell) per expanded node,
    then finally ('done', path) or ('done', None) if no path."""

    def h(cell):
        return abs(cell[0] - goal[0]) + abs(cell[1] - goal[1])  # Manhattan

    open_heap = [(h(start), 0, start)]  # (f, g, cell)
    g_score = {start: 0}
    parent = {start: None}
    closed = set()

    while open_heap:
        f, g, cur = heapq.heappop(open_heap)
        if cur in closed:
            continue
        closed.add(cur)
        yield ("explore", cur)

        if cur == goal:
            path = []
            while cur is not None:
                path.append(cur)
                cur = parent[cur]
            yield ("done", path[::-1])
            return

        for nb in maze.neighbours(cur):
            new_g = g + 1
            if new_g < g_score.get(nb, float("inf")):
                g_score[nb] = new_g
                parent[nb] = cur
                heapq.heappush(open_heap, (new_g + h(nb), new_g, nb))

    yield ("done", None)