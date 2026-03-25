import numpy as np
import mss
import time
from pynput import mouse as mouse_lib
from vision import is_block, classify_cell_color, vote_piece_from_region

ROWS = 20
COLS = 10


class Environment:

    def __init__(self):
        self.sct = mss.mss()
        self.board_region = None
        self.cell_w = 0.0
        self.cell_h = 0.0
        self._last_piece = "T"

    def screenshot(self):
        monitor = self.sct.monitors[1]
        img = np.array(self.sct.grab(monitor))
        return img[:, :, :3]

    def detect_board(self):
        print("\nHaz clic en la ESQUINA SUPERIOR-IZQUIERDA del tablero...")

        points = []

        def on_click(x, y, button, pressed):
            if pressed and button == mouse_lib.Button.left:
                points.append((int(x), int(y)))
                if len(points) == 1:
                    print(f"  Superior-izq: ({x}, {y})")
                    print("Haz clic en la ESQUINA INFERIOR-DERECHA del tablero...")
                elif len(points) == 2:
                    print(f"  Inferior-der: ({x}, {y})")
                    return False

        with mouse_lib.Listener(on_click=on_click) as listener:
            listener.join()

        x1, y1 = points[0]
        x2, y2 = points[1]

        x = min(x1, x2)
        y = min(y1, y2)
        w = abs(x2 - x1)
        h = abs(y2 - y1)

        self.board_region = (x, y, w, h)
        self.cell_w = w / COLS
        self.cell_h = h / ROWS

        print(f"  Region: x={x} y={y} w={w} h={h}")
        print(f"  Celda:  {self.cell_w:.1f} x {self.cell_h:.1f} px")

    def get_board(self):
        x, y, w, h = self.board_region
        full = self.screenshot()
        img = full[y:y + h, x:x + w]

        board = np.zeros((ROWS, COLS), dtype=int)
        px = max(2, int(min(self.cell_w, self.cell_h) * 0.20))

        for row in range(ROWS):
            for col in range(COLS):
                cx = int((col + 0.5) * self.cell_w)
                cy = int((row + 0.5) * self.cell_h)

                sample = img[
                    max(0, cy - px): cy + px + 1,
                    max(0, cx - px): cx + px + 1
                ]

                if sample.size == 0:
                    continue

                board[row, col] = is_block(float(np.mean(sample)))

        for row in range(4):
            for col in range(COLS):
                board[row, col] = 0

        return board

    def detect_piece(self):

        x, y, w, h = self.board_region
        full = self.screenshot()

        spawn_h = int(self.cell_h * 4)
        region = full[y: y + spawn_h, x: x + w]

        piece = vote_piece_from_region(
            region, self.cell_w, self.cell_h,
            rows=4, cols=COLS
        )

        if piece is not None:
            self._last_piece = piece
            return piece

        return self._last_piece

    def next_piece(self):
        x, y, w, h = self.board_region
        full = self.screenshot()
        screen_h, screen_w = full.shape[:2]

        nx1 = x + w + int(w * 0.08)
        nx2 = min(screen_w, nx1 + int(w * 0.50))
        ny1 = y
        ny2 = y + int(h * 0.22)

        region = full[ny1:ny2, nx1:nx2]

        nw = nx2 - nx1
        nh = ny2 - ny1
        cw = nw / 4
        ch = nh / 4

        piece = vote_piece_from_region(region, cw, ch, rows=4, cols=4)
        return piece if piece else "T"