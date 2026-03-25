import numpy as np


def get_line_bonus(lines, danger=False):
    if danger:
        # Modo supervivencia: premiar fuertemente limpiar cualquier línea para bajar la torre
        if   lines == 4: return 40.0
        elif lines == 3: return 20.0
        elif lines == 2: return 10.0
        elif lines == 1: return  5.0
        else:            return  0.0
    else:
        # Modo ataque B2B Tetris
        if   lines == 4: return 50.0  # Massive score for Tetris
        elif lines == 3: return  3.0
        elif lines == 2: return  1.0
        elif lines == 1: return  0.0  # Disincentivize burning single lines
        else:            return  0.0

def evaluate_structure(board, piece=None):
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
    # Evaluamos 'bumpiness' solo en las columnas 0 a 8
    # Ignoramos el paso de la col 8 a la 9 para no arruinar el hueco del Tetris
    bumpiness = sum(abs(heights[i] - heights[i + 1]) for i in range(8))
    max_height = max(heights)
    danger = max_height >= 14  # Si la torre llega al bloque 14 de altura, pánico.

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

    # Si estamos a salvo, prohibido usar el hueco. Si estamos en peligro, usarlo es aceptable para sobrevivir.
    col_9_penalty = -8.0 * heights[9] if not danger else -0.5 * heights[9]

    score = (
        -0.51  * agg_height
        - 12.0 * holes
        - 1.5  * bumpiness
        - 0.50 * max_height
        - 0.50 * row_transitions
        - 0.50 * col_transitions
        + col_9_penalty
    )
    return score, danger

def evaluate(board, lines, piece=None):
    struct_score, danger = evaluate_structure(board, piece)
    return get_line_bonus(lines, danger) + struct_score

