import numpy as np
import cv2

PIECE_COLORS_HSV = {
    "Z": (  0, 210, 200),
    "L": ( 30, 200, 200),
    "O": ( 60, 220, 240),
    "S": (120, 190, 160),
    "I": (180, 200, 180),
    "J": (240, 180, 180),
    "T": (280, 180, 160),
}

HUE_THRESHOLD = 22
SAT_THRESHOLD = 60
VAL_THRESHOLD = 80


def is_block(avg):
    return 1 if avg > 50 else 0


def bgr_to_hsv_single(bgr):
    pixel = np.uint8([[bgr]])
    hsv = cv2.cvtColor(pixel, cv2.COLOR_BGR2HSV)
    h, s, v = hsv[0][0]
    return float(h) * 2.0, float(s), float(v)


def classify_cell_color(sample_bgr):
    if sample_bgr.size == 0:
        return None

    mask = sample_bgr.max(axis=2) > VAL_THRESHOLD
    if mask.sum() < 5:
        return None

    avg_bgr = sample_bgr[mask].mean(axis=0).astype(np.uint8)
    hue, sat, val = bgr_to_hsv_single(avg_bgr)

    if sat < SAT_THRESHOLD or val < VAL_THRESHOLD:
        return None

    best = None
    best_d = float("inf")

    for piece, (ph, ps, pv) in PIECE_COLORS_HSV.items():
        hue_diff = min(abs(hue - ph), 360 - abs(hue - ph))
        if hue_diff < best_d:
            best_d = hue_diff
            best = piece

    return best if best_d < HUE_THRESHOLD else None


def vote_piece_from_region(region_bgr, cell_w, cell_h, rows, cols):
    votes = {}

    for r in range(rows):
        for c in range(cols):
            cx = int((c + 0.5) * cell_w)
            cy = int((r + 0.5) * cell_h)
            px = max(2, int(min(cell_w, cell_h) * 0.18))

            sample = region_bgr[
                max(0, cy - px): cy + px + 1,
                max(0, cx - px): cx + px + 1
            ]

            piece = classify_cell_color(sample)
            if piece:
                votes[piece] = votes.get(piece, 0) + 1

    if not votes:
        return None

    return max(votes, key=votes.get)