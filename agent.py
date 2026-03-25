import numpy as np
import pyautogui
import time
from pieces import PIECES
from heuristics import evaluate, get_line_bonus

class Agent:

    def __init__(self, env):
        self.env = env
        self._well_col = None
        self._last_played = None   # (piece, rot, col) de la ultima jugada
        self._last_play_time = 0.0

    def collision(self, board, piece, row, col):
        for r in range(len(piece)):
            for c in range(len(piece[0])):
                if piece[r][c]:
                    nr, nc = row + r, col + c
                    if nr < 0 or nr >= 20: return True
                    if nc < 0 or nc >= 10: return True
                    if board[nr][nc]:      return True
        return False

    def drop(self, board, piece, col):
        if self.collision(board, piece, 0, col):
            return None
        row = 0
        while not self.collision(board, piece, row + 1, col):
            row += 1
        return row

    def place(self, board, piece, row, col):
        new = board.copy()
        for r in range(len(piece)):
            for c in range(len(piece[0])):
                if piece[r][c]:
                    new[row + r][col + c] = 1
        return new

    def clear(self, board):
        lines = 0
        new = []
        for row in board:
            if all(row):
                lines += 1
            else:
                new.append(list(row))
        while len(new) < 20:
            new.insert(0, [0] * 10)
        return np.array(new), lines

    def _get_heights(self, board):
        heights = []
        for c in range(10):
            h = 0
            for r in range(20):
                if board[r][c]:
                    h = 20 - r
                    break
            heights.append(h)
        return heights

    def count_deep_holes(self, board):
        holes = 0
        for c in range(10):
            block_found = False
            for r in range(20):
                if board[r][c]:
                    block_found = True
                elif block_found:
                    holes += 1
        return holes

    def _detect_well_column(self, board):
        heights = self._get_heights(board)
        best_col = 9
        best_depth = 0
        for i in range(10):
            left  = heights[i - 1] if i > 0 else 20
            right = heights[i + 1] if i < 9 else 20
            depth = min(left, right) - heights[i]
            if depth > best_depth:
                best_depth = depth
                best_col = i
        self._well_col = best_col if best_depth >= 2 else None

    def lookahead(self, board, next_piece):
        best = -999999
        for piece in PIECES[next_piece]:
            width = len(piece[0])
            for col in range(10 - width + 1):
                row = self.drop(board, piece, col)
                if row is None:
                    continue
                new, lines = self.clear(self.place(board, piece, row, col))
                score = evaluate(new, lines, next_piece)
                best = max(best, score)
        return best

    def best_move(self, board, piece_type, next_type):
        self._detect_well_column(board)
        best = None

        for rot, p in enumerate(PIECES[piece_type]):
            width = len(p[0])

            for col in range(10 - width + 1):
                row = self.drop(board, p, col)
                if row is None:
                    continue

                new, lines = self.clear(self.place(board, p, row, col))

                # Usamos la ecuación de Bellman correcta: recompensa inmediata + valor futuro
                # El valor futuro (lookahead) ya evalúa el tablero resultante.
                score = (
                    get_line_bonus(lines)
                    + 0.9 * self.lookahead(new, next_type)
                )

                max_height = max(self._get_heights(new))
                if max_height > 15:
                    score -= (max_height - 15) * 15

                if piece_type == "I" and self._well_col is not None:
                    if col == self._well_col:
                        score += 3.0
                    else:
                        score -= 1.0

                if best is None or score > best[0]:
                    best = (score, rot, col)

        return best

    def play(self, rotation, col):
        """
        Movimiento absoluto y determinista:
          1. Rotar
          2. Pulsar izquierda 12 veces (llega siempre al borde)
          3. Pulsar derecha `col` veces
          4. Hard drop

        Se usan pulsaciones individuales en lugar de keyDown/keyUp
        para garantizar que cada tecla se registre correctamente.
        """
        for _ in range(rotation):
            pyautogui.press("x")
            time.sleep(0.05)

        for _ in range(12):
            pyautogui.press("left")
            time.sleep(0.03)

        for _ in range(col):
            pyautogui.press("right")
            time.sleep(0.03)

        pyautogui.press("space")
        time.sleep(0.4)

    def run(self):
        """
        Bucle principal con timeout por pieza.

        Si detect_piece devuelve la misma pieza que la última jugada
        por más de MAX_SAME_PIECE_TIME segundos sin que aparezca una nueva,
        significa que la siguiente pieza aun no spawneó — esperar.

        Si pasan más de PIECE_TIMEOUT segundos desde la última jugada
        sin detectar una pieza diferente, actuar de todas formas con
        lo que haya para no dejar caer piezas sin moverlas.
        """
        PIECE_TIMEOUT    = 1.5   # segundos máximos esperando detección
        MIN_WAIT         = 0.08  # pausa mínima entre intentos de detección

        self._last_play_time = time.time()
        start_time = time.time()
        last_acted_piece = None

        while True:
            now = time.time()
            if now - start_time >= 125:
                print("Han pasado 2 minutos. Tomando captura de pantalla y deteniendo la ejecución.")
                pyautogui.screenshot("screenshot.png")
                break

            board      = self.env.get_board()
            piece      = self.env.detect_piece()
            next_piece = self.env.next_piece()

            now = time.time()

            # Si la pieza detectada es la misma con la que ya jugamos,
            # significa que todavía no ha spawneado la siguiente → esperar.
            if piece == last_acted_piece:
                if now - self._last_play_time < PIECE_TIMEOUT:
                    time.sleep(MIN_WAIT)
                    continue
                # Timeout: forzar con lo que hay para no dejar caer sin mover
                print(f"  [timeout] forzando jugada con {piece}")

            move = self.best_move(board, piece, next_piece)

            if move is None:
                print("Game Over")
                break

            _, rot, col = move
            well = self._well_col if self._well_col is not None else "-"
            print(f"  {piece}->{next_piece}  rot={rot}  col={col}  pozo={well}")

            self.play(rot, col)

            last_acted_piece     = piece
            self._last_play_time = time.time()