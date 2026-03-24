import numpy as np


def evaluate(board, lines, piece=None):
    heights = []
    holes = 0

    for c in range(10):
        col_height = 0
        block_found = False

        for r in range(20):
            if board[r][c]:
                if not block_found:
                    col_height = 20 - r
                    block_found = True
            elif block_found:
                holes += 1

        heights.append(col_height)

    agg_height = sum(heights)
    bumpiness = sum(abs(heights[i] - heights[i + 1]) for i in range(9))
    max_height = max(heights)

    row_transitions = 0
    for r in range(20):
        for c in range(9):
            if board[r][c] != board[r][c + 1]:
                row_transitions += 1

    col_transitions = 0
    for c in range(10):
        for r in range(19):
            if board[r][c] != board[r + 1][c]:
                col_transitions += 1

    well_depth = _best_well(heights)

    if   lines == 4: line_bonus = 12.0
    elif lines == 3: line_bonus =  5.0
    elif lines == 2: line_bonus =  2.5
    elif lines == 1: line_bonus =  0.8
    else:            line_bonus =  0.0

    well_bonus = 0.0
    if piece == "I":
        well_bonus = 0.5 * well_depth
    elif well_depth >= 3:
        well_bonus = 0.3 * well_depth

    return (
        -0.51  * agg_height
        + line_bonus
        - 3.5  * holes
        - 0.18 * bumpiness
        - 0.35 * max_height
        - 0.10 * row_transitions
        - 0.08 * col_transitions
        + well_bonus
    )


def _best_well(heights):
    best = 0
    for i in range(10):
        left  = heights[i - 1] if i > 0 else 20
        right = heights[i + 1] if i < 9 else 20
        depth = min(left, right) - heights[i]
        if depth > best:
            best = depth
    return best