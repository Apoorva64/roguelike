from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder


def get_path(multiprocessing_dict, pathfinding_matrix, start, end):
    end_pos = end
    grid = Grid(matrix=pathfinding_matrix[0])

    start = grid.node(int(start[0]), int(start[1]))
    end = grid.node(end[0], end[1])

    finder = AStarFinder(diagonal_movement=DiagonalMovement.never)
    path, runs = finder.find_path(start, end, grid)

    # print('operations:', runs, 'path length:', len(path))
    # print(grid.grid_str(path=path, start=start, end=end))
    multiprocessing_dict['path'] = tuple(path)
    # print(multiprocessing_dict)
