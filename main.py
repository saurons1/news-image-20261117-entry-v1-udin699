#!/usr/bin/env python3
"""THE WORLD IN ONE DAY -- Tuesday 17 November 2026 (v2).

A denser one-page newspaper front page for the same day: 47 stories
across 6 regions, three big illustrated hero scenes, four small
illustrated panels, a world map with the day's hotspots, and the day
in numbers. Drawn entirely with the Python standard library: a
hand-written PNG encoder (zlib + struct), a hand-built 6x8 bitmap
font, and every shape plotted pixel by pixel.

Writes entry.png to $MAKEFUN_OUTPUT_DIR (default /output).
Deterministic: the same bytes on every run.
"""

import os
import struct
import zlib

# ------------------------------------------------------------------ font
# 6x8 bitmap font, written from scratch for this page. Each glyph is
# 8 rows; every row is one byte holding 6 bits, bit 5 (0x20) is the
# leftmost pixel, bit 0 the rightmost. All page text is set in capitals.
GLYPHS = {
    "A": (0x1C, 0x22, 0x22, 0x3E, 0x22, 0x22, 0x22, 0x00),
    "B": (0x3E, 0x22, 0x22, 0x3E, 0x22, 0x22, 0x3E, 0x00),
    "C": (0x1C, 0x22, 0x20, 0x20, 0x20, 0x22, 0x1C, 0x00),
    "D": (0x3E, 0x22, 0x22, 0x22, 0x22, 0x22, 0x3E, 0x00),
    "E": (0x3E, 0x20, 0x20, 0x3C, 0x20, 0x20, 0x3E, 0x00),
    "F": (0x3E, 0x20, 0x20, 0x3C, 0x20, 0x20, 0x20, 0x00),
    "G": (0x1C, 0x22, 0x20, 0x2E, 0x22, 0x22, 0x1E, 0x00),
    "H": (0x22, 0x22, 0x22, 0x3E, 0x22, 0x22, 0x22, 0x00),
    "I": (0x1C, 0x08, 0x08, 0x08, 0x08, 0x08, 0x1C, 0x00),
    "J": (0x0E, 0x04, 0x04, 0x04, 0x04, 0x24, 0x18, 0x00),
    "K": (0x22, 0x24, 0x28, 0x30, 0x28, 0x24, 0x22, 0x00),
    "L": (0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x3E, 0x00),
    "M": (0x22, 0x36, 0x2A, 0x2A, 0x22, 0x22, 0x22, 0x00),
    "N": (0x22, 0x32, 0x2A, 0x26, 0x22, 0x22, 0x22, 0x00),
    "O": (0x1C, 0x22, 0x22, 0x22, 0x22, 0x22, 0x1C, 0x00),
    "P": (0x3E, 0x22, 0x22, 0x3E, 0x20, 0x20, 0x20, 0x00),
    "Q": (0x1C, 0x22, 0x22, 0x22, 0x2A, 0x24, 0x1A, 0x00),
    "R": (0x3E, 0x22, 0x22, 0x3E, 0x28, 0x24, 0x22, 0x00),
    "S": (0x1E, 0x20, 0x20, 0x1C, 0x02, 0x02, 0x3C, 0x00),
    "T": (0x3E, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x00),
    "U": (0x22, 0x22, 0x22, 0x22, 0x22, 0x22, 0x1C, 0x00),
    "V": (0x22, 0x22, 0x22, 0x22, 0x22, 0x14, 0x08, 0x00),
    "W": (0x22, 0x22, 0x22, 0x2A, 0x2A, 0x36, 0x22, 0x00),
    "X": (0x22, 0x22, 0x14, 0x08, 0x14, 0x22, 0x22, 0x00),
    "Y": (0x22, 0x22, 0x14, 0x08, 0x08, 0x08, 0x08, 0x00),
    "Z": (0x3E, 0x02, 0x04, 0x08, 0x10, 0x20, 0x3E, 0x00),
    "0": (0x1C, 0x22, 0x26, 0x2A, 0x32, 0x22, 0x1C, 0x00),
    "1": (0x08, 0x18, 0x08, 0x08, 0x08, 0x08, 0x1C, 0x00),
    "2": (0x1C, 0x22, 0x02, 0x0C, 0x10, 0x20, 0x3E, 0x00),
    "3": (0x3C, 0x02, 0x02, 0x1C, 0x02, 0x02, 0x3C, 0x00),
    "4": (0x04, 0x0C, 0x14, 0x24, 0x3E, 0x04, 0x04, 0x00),
    "5": (0x3E, 0x20, 0x3C, 0x02, 0x02, 0x22, 0x1C, 0x00),
    "6": (0x1C, 0x20, 0x20, 0x3C, 0x22, 0x22, 0x1C, 0x00),
    "7": (0x3E, 0x02, 0x04, 0x08, 0x10, 0x10, 0x10, 0x00),
    "8": (0x1C, 0x22, 0x22, 0x1C, 0x22, 0x22, 0x1C, 0x00),
    "9": (0x1C, 0x22, 0x22, 0x1E, 0x02, 0x02, 0x1C, 0x00),
    " ": (0, 0, 0, 0, 0, 0, 0, 0),
    ".": (0, 0, 0, 0, 0, 0x0C, 0x0C, 0),
    ",": (0, 0, 0, 0, 0x0C, 0x04, 0x08, 0),
    ":": (0, 0x0C, 0x0C, 0, 0x0C, 0x0C, 0, 0),
    ";": (0, 0x0C, 0x0C, 0, 0x0C, 0x04, 0x08, 0),
    "'": (0x08, 0x08, 0x10, 0, 0, 0, 0, 0),
    "-": (0, 0, 0, 0x3E, 0, 0, 0, 0),
    "/": (0x02, 0x04, 0x04, 0x08, 0x08, 0x10, 0x10, 0x20),
    "(": (0x04, 0x08, 0x10, 0x10, 0x10, 0x08, 0x04, 0),
    ")": (0x10, 0x08, 0x04, 0x04, 0x04, 0x08, 0x10, 0),
    "&": (0x0C, 0x12, 0x14, 0x08, 0x15, 0x12, 0x0D, 0),
    "%": (0x32, 0x25, 0x04, 0x08, 0x10, 0x29, 0x26, 0),
    "+": (0, 0x08, 0x08, 0x3E, 0x08, 0x08, 0, 0),
    "=": (0, 0, 0x3E, 0, 0x3E, 0, 0, 0),
    "?": (0x1C, 0x22, 0x02, 0x0C, 0x08, 0, 0x08, 0),
    "!": (0x08, 0x08, 0x08, 0x08, 0x08, 0, 0x08, 0),
    "$": (0x08, 0x1E, 0x28, 0x1C, 0x0A, 0x3C, 0x08, 0),
    '"': (0x14, 0x14, 0, 0, 0, 0, 0, 0),
    "\u2022": (0, 0, 0x0C, 0x1E, 0x1E, 0x0C, 0, 0),
}
EMPTY_GLYPH = (0, 0, 0, 0, 0, 0, 0, 0)
ADVANCE = 7  # pixels per character at scale 1 (6 px glyph + 1 px gap)


def measure(text, scale):
    """Pixel width of text at the given scale."""
    if not text:
        return 0
    return len(text) * ADVANCE * scale - scale


def fold(text, scale, max_w):
    """Greedy word wrap; returns lines that fit max_w pixels."""
    out = []
    cur = ""
    for word in text.split(" "):
        cand = word if not cur else cur + " " + word
        if measure(cand, scale) <= max_w or not cur:
            cur = cand
        else:
            out.append(cur)
            cur = word
    if cur:
        out.append(cur)
    return out


# ------------------------------------------------------------------ palette
PAPER = (247, 242, 230)   # newsprint off-white
INK = (18, 18, 18)        # near-black
RULE = (90, 86, 78)       # thin rules and secondary marks
FAINT = (128, 124, 114)   # captions and footers
CRIMSON = (164, 22, 34)   # masthead accents, Middle East
OCEAN = (28, 76, 136)     # Europe
FOREST = (13, 104, 72)    # Asia-Pacific
OCHRE = (120, 72, 16)     # Americas
PLUM = (106, 56, 120)     # Africa
SLATE = (48, 50, 56)      # Global / Tech
LAND = (156, 170, 142)    # map land
LAND2 = (132, 148, 118)   # map land, shaded side
SEA = (214, 228, 232)     # map sea
SEA2 = (190, 210, 218)    # map sea, deep side
WHITE = (255, 255, 255)
SKY1 = (168, 198, 224)    # hero sky, top
SKY2 = (226, 236, 240)    # hero sky, horizon
FIRE = (238, 118, 28)     # explosion orange
EMBER = (214, 42, 20)     # explosion red core
GOLD = (232, 178, 52)     # explosion yellow
SMOKE = (96, 96, 96)


# ------------------------------------------------------------------ canvas
class Sheet:
    """An RGB canvas backed by one flat bytearray, 3 bytes per pixel."""

    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg) * (w * h)

    def put(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def bar(self, x, y, w, h, color):
        """Filled rectangle, clipped to the sheet."""
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def frame(self, x, y, w, h, color, t=1):
        self.bar(x, y, w, t, color)
        self.bar(x, y + h - t, w, t, color)
        self.bar(x, y, t, h, color)
        self.bar(x + w - t, y, t, h, color)

    def rule(self, x, y, w, color, t=1):
        self.bar(x, y, w, t, color)

    def disc(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) * (xx - cx) + (yy - cy) * (yy - cy) <= r * r:
                    self.put(xx, yy, color)

    def ring(self, cx, cy, r, color, t=2):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d2 = (xx - cx) * (xx - cx) + (yy - cy) * (yy - cy)
                if (r - t) * (r - t) <= d2 <= r * r:
                    self.put(xx, yy, color)

    def line(self, x0, y0, x1, y1, color, t=1):
        """Bresenham line, t pixels thick."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.bar(x0 - t // 2, y0 - t // 2, t, t, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def poly(self, pts, color):
        """Scanline-filled polygon from a list of (x, y) points."""
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        for y in range(max(0, min(ys)), min(self.h, max(ys) + 1)):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if y0 == y1:
                    continue
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                self.bar(int(xs[k]), y, max(1, int(xs[k + 1]) - int(xs[k])), 1, color)

    def ellipse(self, cx, cy, rx, ry, color):
        for yy in range(cy - ry, cy + ry + 1):
            dy = (yy - cy) / ry
            half = int(rx * (1 - dy * dy) ** 0.5)
            self.bar(cx - half, yy, 2 * half, 1, color)

    def vgrad(self, x, y, w, h, top, bottom):
        """Vertical gradient band, one fill_rect per row."""
        for i in range(h):
            f = i / max(1, h - 1)
            c = tuple(int(top[k] + (bottom[k] - top[k]) * f) for k in range(3))
            self.bar(x, y + i, w, 1, c)

    def speckle(self, x, y, w, h, color, step, seed):
        """Deterministic paper grain: sparse 1px dots on a fixed lattice."""
        s = seed
        for yy in range(y, y + h, step):
            for xx in range(x, x + w, step):
                s = (s * 1103515245 + 12345) & 0x7FFFFFFF
                if s % 3 == 0:
                    self.put(xx + (s >> 9) % step, yy + (s >> 17) % step, color)

    # -- text -------------------------------------------------------
    def glyph(self, x, y, ch, scale, color, heavy=False):
        rows = GLYPHS.get(ch, EMPTY_GLYPH)
        for r in range(8):
            bits = rows[r]
            if not bits:
                continue
            for c in range(6):
                if bits & (0x20 >> c):
                    self.bar(x + c * scale, y + r * scale, scale, scale, color)
                    if heavy:
                        self.bar(x + c * scale + 1, y + r * scale, scale, scale, color)

    def write(self, x, y, s, scale, color, heavy=False):
        s = s.upper()
        cx = x
        for ch in s:
            self.glyph(cx, y, ch, scale, color, heavy)
            cx += ADVANCE * scale
        return cx

    def write_mid(self, cx, y, s, scale, color, heavy=False):
        w = measure(s.upper(), scale)
        return self.write(cx - w // 2, y, s, scale, color, heavy)

    def write_tight(self, x, y, s, color, heavy=False):
        """Scale-2 text with a 13 px advance (glyphs 12 px + 1 px gap),
        so 12-character headers fit a 156 px column."""
        s = s.upper()
        cx = x
        for ch in s:
            rows = GLYPHS.get(ch, EMPTY_GLYPH)
            for r in range(8):
                bits = rows[r]
                if not bits:
                    continue
                for c in range(6):
                    if bits & (0x20 >> c):
                        self.bar(cx + c * 2, y + r * 2, 2, 2, color)
                        if heavy:
                            self.bar(cx + c * 2 + 1, y + r * 2, 2, 2, color)
            cx += 13
        return cx

    def write_tight_mid(self, cx, y, s, color, heavy=False):
        w = len(s.upper()) * 13 - 1
        return self.write_tight(cx - w // 2, y, s, color, heavy)

    def block(self, x, y, s, scale, color, max_w, max_lines, heavy=False,
              gap=None):
        """Wrapped paragraph; returns the y just below the last line."""
        lh = gap if gap is not None else 8 * scale + 2
        lines = fold(s, scale, max_w)[:max_lines]
        for ln in lines:
            self.write(x, y, ln, scale, color, heavy)
            y += lh
        return y


# ------------------------------------------------------------------ png
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def encode_png(sheet):
    """Encode the sheet as a deterministic RGB PNG (no time chunks)."""
    raw = bytearray()
    stride = sheet.w * 3
    for y in range(sheet.h):
        raw.append(0)  # filter: none
        raw += sheet.px[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", sheet.w, sheet.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + _chunk(b"IHDR", ihdr)
            + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + _chunk(b"IEND", b""))


# ------------------------------------------------------------------ art
def scene_bridge(sh, x, y, w, h):
    """Kerch bridge at dusk: sky, sea, deck, towers, cables, blast."""
    sh.vgrad(x, y, w, h * 55 // 100, SKY1, SKY2)
    sh.vgrad(x, y + h * 55 // 100, w, h - h * 55 // 100,
             (52, 96, 128), (28, 62, 92))
    # low sun + haze band
    sh.disc(x + w * 78 // 100, y + h * 30 // 100, 11, GOLD)
    sh.disc(x + w * 78 // 100, y + h * 30 // 100, 7, (244, 214, 120))
    # bridge deck and towers
    deck = y + h * 62 // 100
    sh.bar(x, deck, w, 5, (52, 48, 44))
    sh.bar(x, deck + 5, w, 2, (90, 86, 80))
    for tx in (w * 22 // 100, w * 58 // 100):
        sh.bar(x + tx, y + h * 18 // 100, 5, deck - y - h * 18 // 100 + 5,
               (64, 60, 54))
        sh.line(x + tx + 2, y + h * 18 // 100, x + w * 8 // 100, deck,
                (120, 114, 104), 1)
        sh.line(x + tx + 2, y + h * 18 // 100, x + w * 40 // 100, deck,
                (120, 114, 104), 1)
    # broken span: the middle deck sags and is gone
    sh.bar(x + w * 40 // 100, deck, w * 18 // 100, 5, (28, 62, 92))
    sh.line(x + w * 40 // 100, deck, x + w * 49 // 100, deck + 14,
            (52, 48, 44), 2)
    sh.line(x + w * 58 // 100, deck, x + w * 49 // 100, deck + 14,
            (52, 48, 44), 2)
    # blast: fireball, sparks, smoke
    bx, by = x + w * 49 // 100, deck - 16
    sh.disc(bx, by, 15, FIRE)
    sh.disc(bx, by, 10, GOLD)
    sh.disc(bx, by, 5, EMBER)
    for sx, sy in ((-18, -10), (16, -14), (20, 4), (-14, 8), (2, -22)):
        sh.disc(bx + sx, by + sy, 3, GOLD)
    sh.disc(bx - 8, by - 26, 7, SMOKE)
    sh.disc(bx + 6, by - 32, 9, (120, 120, 120))
    sh.disc(bx + 16, by - 24, 6, SMOKE)
    # sea glints
    for gx in range(6, w, 26):
        sh.bar(x + gx, y + h - 12, 14, 2, (120, 170, 200))


def scene_hormuz(sh, x, y, w, h):
    """Two tankers in a strait, one burning, mines in the water."""
    sh.vgrad(x, y, w, h * 48 // 100, SKY1, SKY2)
    sh.vgrad(x, y + h * 48 // 100, w, h - h * 48 // 100,
             (46, 92, 126), (22, 58, 90))
    sh.disc(x + w * 15 // 100, y + h * 20 // 100, 9, GOLD)
    # far tanker, upright
    tx, ty = x + w * 8 // 100, y + h * 58 // 100
    sh.bar(tx, ty, w * 34 // 100, 10, (150, 40, 30))
    sh.bar(tx + w * 4 // 100, ty - 12, 14, 12, (210, 210, 205))
    sh.bar(tx + w * 4 // 100, ty - 18, 3, 6, (210, 210, 205))
    # near tanker, burning amidships
    nx, ny = x + w * 52 // 100, y + h * 62 // 100
    sh.bar(nx, ny, w * 40 // 100, 11, (120, 32, 24))
    sh.bar(nx + w * 28 // 100, ny - 13, 16, 13, (225, 222, 214))
    sh.bar(nx + w * 28 // 100, ny - 19, 3, 6, (225, 222, 214))
    fx, fy = nx + w * 12 // 100, ny - 6
    sh.disc(fx, fy, 12, FIRE)
    sh.disc(fx, fy, 8, GOLD)
    sh.disc(fx, fy, 4, EMBER)
    sh.disc(fx - 6, fy - 14, 6, SMOKE)
    sh.disc(fx + 5, fy - 18, 8, (130, 130, 130))
    # mines: spiked black spheres on the water
    for mx, my in ((w * 30 // 100, h * 82 // 100),
                   (w * 72 // 100, h * 86 // 100),
                   (w * 88 // 100, h * 76 // 100)):
        sh.disc(x + mx, y + my, 5, INK)
        for dx, dy in ((-6, 0), (6, 0), (0, -6), (0, 6), (-4, -4), (4, 4)):
            sh.line(x + mx + dx, y + my + dy, x + mx, y + my, INK, 1)
    # wave lines
    for wy in (h * 72 // 100, h * 90 // 100):
        for wx in range(8, w - 20, 34):
            sh.bar(x + wx, y + wy, 18, 2, (140, 185, 210))


def scene_summit(sh, x, y, w, h):
    """Three flags over a Shenzhen skyline: US, China, Russia."""
    sh.vgrad(x, y, w, h, (188, 206, 226), (238, 240, 236))
    # skyline
    base = y + h * 72 // 100
    for bx, bw, bh in ((4, 18, 34), (26, 14, 52), (44, 20, 40),
                       (68, 12, 62), (84, 16, 30), (104, 18, 48),
                       (126, 12, 70), (142, 16, 36), (162, 20, 55),
                       (186, 14, 42), (204, 18, 60), (226, 16, 34),
                       (246, 18, 50), (266, 16, 38)):
        sh.bar(x + bx, base - bh, bw, bh, (96, 108, 128))
        for wy in range(base - bh + 5, base - 4, 9):
            for wx in range(bx + 3, bx + bw - 3, 6):
                sh.bar(x + wx, wy, 2, 3, (214, 220, 128))
    sh.bar(x, base, w, h - (base - y), (70, 82, 100))
    # three flagpoles with flags
    def flag(fx, fy, cols):
        sh.bar(fx, fy - 44, 3, 44, (70, 66, 60))
        for i, c in enumerate(cols):
            sh.bar(fx + 3, fy - 44 + i * 9, 34, 9, c)
    flag(x + w * 12 // 100, y + h * 46 // 100,
         [(178, 34, 52), (255, 255, 255), (178, 34, 52)])
    sh.disc(x + w * 12 // 100 + 12, y + h * 46 // 100 - 40, 3, (28, 52, 120))
    flag(x + w * 44 // 100, y + h * 46 // 100,
         [(222, 40, 34), (222, 40, 34), (222, 40, 34)])
    sh.disc(x + w * 44 // 100 + 10, y + h * 46 // 100 - 40, 2, GOLD)
    sh.disc(x + w * 44 // 100 + 20, y + h * 46 // 100 - 36, 1, GOLD)
    flag(x + w * 76 // 100, y + h * 46 // 100,
         [(255, 255, 255), (28, 68, 160), (214, 40, 30)])


def scene_geneva(sh, x, y, w, h):
    """UN hall in Geneva: blue flag, columns, pediment."""
    sh.vgrad(x, y, w, h, (200, 214, 228), (238, 240, 238))
    base = y + h - 6
    apex = y + h * 48 // 100
    sh.poly([(x + 8, base), (x + w - 8, base),
             (x + w // 2, apex)], (200, 196, 184))
    for cx in range(x + 16, x + w - 16, 26):
        sh.bar(cx, apex + 6, 6, base - apex - 6, (232, 228, 216))
    sh.bar(x + 8, base, w - 16, 4, (120, 116, 106))
    # flag on the roof
    fx = x + w // 2
    sh.bar(fx - 1, apex - 16, 2, 16, (70, 66, 60))
    sh.bar(fx + 1, apex - 16, 22, 12, (28, 76, 150))
    sh.disc(fx + 12, apex - 10, 4, WHITE)


def scene_rwanda(sh, x, y, w, h):
    """Green hills of Rwanda with a new hub building and a plane."""
    sh.vgrad(x, y, w, h * 60 // 100, SKY1, SKY2)
    # low hills: shallow arcs that stay inside the art area
    sh.ellipse(x + w * 28 // 100, y + h * 80 // 100, w * 45 // 100,
               h * 20 // 100, (96, 148, 88))
    sh.ellipse(x + w * 76 // 100, y + h * 84 // 100, w * 45 // 100,
               h * 20 // 100, (70, 122, 66))
    # hub building, standing on the hill line
    bx, by = x + w * 40 // 100, y + h * 52 // 100
    sh.bar(bx, by, 34, h - (by - y) - 4, (232, 226, 210))
    sh.bar(bx - 4, by - 6, 42, 6, CRIMSON)
    for wx in (bx + 5, bx + 15, bx + 25):
        sh.bar(wx, by + 4, 5, 5, (52, 96, 128))
    # plane
    px, py = x + w * 74 // 100, y + h * 20 // 100
    sh.line(px - 14, py, px + 16, py, INK, 2)
    sh.line(px + 2, py - 8, px + 8, py, INK, 2)
    sh.line(px + 2, py + 6, px + 8, py, INK, 2)


def scene_pentagon(sh, x, y, w, h):
    """The Pentagon, ringed, with a red audit stamp."""
    sh.vgrad(x, y, w, h, (214, 220, 226), (240, 240, 238))
    cx, cy = x + w // 2 - 18, y + h * 48 // 100
    r = max(10, h * 30 // 100)
    import math
    pts = []
    for k in range(5):
        a = -math.pi / 2 + k * 2 * math.pi / 5
        pts.append((cx + int(r * math.cos(a)), cy + int(r * math.sin(a))))
    sh.poly(pts, (150, 156, 164))
    inner = []
    for k in range(5):
        a = -math.pi / 2 + k * 2 * math.pi / 5
        inner.append((cx + int(r * 0.45 * math.cos(a)),
                      cy + int(r * 0.45 * math.sin(a))))
    sh.poly(inner, (110, 116, 124))
    # audit stamp
    sx, sy = x + w * 62 // 100, y + h * 58 // 100
    sh.frame(sx, sy, 52, 16, EMBER, 2)
    sh.write(sx + 5, sy + 4, "FAIL", 1, EMBER, heavy=True)


def scene_nvidia(sh, x, y, w, h):
    """A chip on a board, with a rising chart."""
    sh.vgrad(x, y, w, h, (226, 232, 226), (244, 244, 240))
    # circuit board traces
    for ty in (h * 20 // 100, h * 82 // 100):
        sh.bar(x + 8, y + ty, w - 16, 2, (140, 160, 140))
    # chip, sized to the panel
    half = max(10, h * 26 // 100)
    cx, cy = x + w * 28 // 100, y + h * 52 // 100
    for px in range(-half, half + 1, 7):
        sh.bar(cx + px, cy - half - 5, 2, 5, GOLD)
        sh.bar(cx + px, cy + half, 2, 5, GOLD)
    for py in range(-half, half + 1, 7):
        sh.bar(cx - half - 5, cy + py, 5, 2, GOLD)
        sh.bar(cx + half, cy + py, 5, 2, GOLD)
    sh.bar(cx - half, cy - half, 2 * half, 2 * half, (26, 60, 40))
    sh.bar(cx - half // 2, cy - half // 2, half, half, (46, 110, 70))
    sh.disc(cx, cy, 4, GOLD)
    # rising chart
    pts = [(x + w * 56 // 100, y + h * 74 // 100),
           (x + w * 65 // 100, y + h * 60 // 100),
           (x + w * 74 // 100, y + h * 64 // 100),
           (x + w * 84 // 100, y + h * 40 // 100),
           (x + w * 94 // 100, y + h * 22 // 100)]
    for a, b in zip(pts, pts[1:]):
        sh.line(a[0], a[1], b[0], b[1], FOREST, 3)
    sh.disc(pts[-1][0], pts[-1][1], 4, FOREST)


# ------------------------------------------------------------------ map
# Continent outlines as polygons in map-local coordinates (640 x 182).
# Rough but recognisable: Americas left, Europe/Africa centre, Asia
# right, Australia low. Labels are drawn on top so the map reads at
# a glance, even shrunk.
CONTINENTS = [
    ("N. AMERICA", (95, 48), [(46, 34), (64, 18), (110, 10), (160, 8),
                               (196, 16), (214, 30), (200, 44), (186, 50),
                               (172, 56), (158, 66), (148, 82), (136, 100),
                               (124, 108), (114, 94), (104, 76), (88, 68),
                               (66, 64), (48, 50)]),
    ("GREENLAND", (210, 10), [(200, 4), (226, 2), (234, 12), (214, 20),
                              (196, 14)]),
    ("S. AMERICA", (168, 142), [(148, 108), (172, 102), (196, 112),
                                 (208, 132), (200, 160), (182, 180),
                                 (162, 172), (146, 142), (140, 122)]),
    ("EUROPE", (312, 22), [(296, 34), (318, 20), (344, 18), (362, 30),
                            (356, 46), (340, 58), (318, 60), (300, 50),
                            (290, 42)]),
    ("AFRICA", (318, 132), [(298, 66), (322, 60), (348, 64), (366, 78),
                             (362, 102), (348, 132), (330, 152), (308, 146),
                             (296, 116), (290, 88)]),
    ("ASIA", (470, 45), [(364, 28), (410, 12), (470, 8), (530, 14),
                          (566, 26), (584, 44), (570, 62), (540, 70),
                          (516, 82), (492, 88), (470, 76), (446, 80),
                          (420, 72), (396, 78), (378, 60), (364, 44)]),
    ("AUSTRALIA", (512, 150), [(478, 138), (516, 130), (548, 140),
                                (556, 156), (524, 166), (488, 160),
                                (474, 148)]),
]

# (map x, map y, colour, number) hotspots for the day's big stories.
SPOTS = [
    (354, 42, CRIMSON, "1"),   # Crimea / Kyiv
    (392, 66, CRIMSON, "2"),   # Strait of Hormuz
    (384, 78, CRIMSON, "3"),   # Bahrain
    (520, 62, FOREST, "4"),    # Shenzhen
    (338, 118, PLUM, "5"),     # Rwanda
    (185, 52, OCHRE, "6"),     # Washington
    (314, 48, OCEAN, "7"),     # Geneva
    (452, 74, FOREST, "8"),    # Uttarakhand
    (332, 102, PLUM, "9"),     # Sudan
    (560, 44, FOREST, "10"),   # Tokyo
]


# ------------------------------------------------------------------ content
# Every fact below was reported on Tuesday 17 November 2026.
# Headlines are plain ASCII so the 6x8 font covers every character.

HEROES = [
    ("CRIMEA BRIDGE HIT AGAIN", CRIMSON, scene_bridge,
     "Kyiv strikes the Kerch crossing a second day running, collapsing "
     "a road span."),
    ("TANKERS HIT AT HORMUZ", CRIMSON, scene_hormuz,
     "Tankers struck by mines near the strait; fires aboard, crews safe."),
    ("TRUMP, XI, PUTIN MEET", FOREST, scene_summit,
     "First three-way summit in years: 19 Nov in Shenzhen, on the APEC "
     "sidelines."),
]

PANELS = [
    ("GENEVA: ROBOT WEAPONS TALKS", OCEAN, scene_geneva,
     "A treaty push to ban lethal autonomous weapons."),
    ("RWANDA: RETURN HUB PLAN", PLUM, scene_rwanda,
     "A joint facility for rejected asylum seekers."),
    ("PENTAGON AUDIT FAILS AGAIN", SLATE, scene_pentagon,
     "Disclaimer on more than $4.8 trillion in assets."),
    ("NVIDIA REVENUE DOUBLES", FOREST, scene_nvidia,
     "Up 103% year on year; Huang will not return."),
]

# (region name, colour, [(headline, summary), ...])
REGIONS = [
    ("EUROPE", OCEAN, [
        ("KYIV BRIDGES HIT",
         "Russia hits the North and South bridges over the Dnipro; heat, "
         "water and power cut."),
        ("1,441 DRONES DOWNED",
         "Russia claims it intercepted 1,441 Ukrainian drones overnight."),
        ("UK GIVES 240M POUNDS",
         "Britain pledges 240 million pounds for Ukraine's air defence."),
        ("DRONE OVER CHISINAU",
         "Moldova says a Russian drone flew over its capital; protest "
         "lodged."),
        ("GERMANY 5-0 DUTCH",
         "Wirtz scores twice as Germany win their Nations League group."),
        ("PRAGUE TRAINS COLLIDE",
         "Two passenger trains crash in Prague; passengers and both "
         "drivers hurt."),
        ("MIG-29 CRASH IN SERBIA",
         "A pilot is killed as a MiG-29 crashes near Stara Pazova."),
        ("372 CIVILIANS IN OCTOBER",
         "UN monitors say at least 372 civilians were killed in Ukraine "
         "in October."),
    ]),
    ("MIDDLE EAST", CRIMSON, [
        ("IRAN DRONES AT BAHRAIN",
         "Iran fires drones at a US radar base in Bahrain; all "
         "intercepted, no casualties."),
        ("DIRTY BOMB PLOT CLAIM",
         "US intelligence says Iran is developing plans to target senior "
         "Trump officials in Washington."),
        ("THIRD US CARRIER",
         "USS Theodore Roosevelt reaches the Middle East, joining the "
         "Bush and the Washington."),
        ("UK SANCTIONS 8 FIRMS",
         "Britain sanctions eight Israeli settlement firms and an "
         "aid-blocking group."),
        ("NETANYAHU CAMP ROW",
         "His camp is accused of giving police information that led to "
         "arrests of Arab party workers."),
        ("FOUR NATIONS: OPEN GAZA",
         "UK, Australia, Canada and Italy call on Israel to open Gaza "
         "crossings for aid."),
        ("HOUTHIS ADVANCE ON ADEN",
         "Yemen's government forces pull back from the Red Sea coast to "
         "defend Aden."),
        ("SETTLER KILLS WOMAN, 72",
         "Israeli settlers kill a 72-year-old Palestinian woman in "
         "Jericho, West Bank."),
    ]),
    ("ASIA-PACIFIC", FOREST, [
        ("JAPAN JETS SCRAMBLE",
         "Tokyo protests after two suspected Russian aircraft violate its "
         "airspace."),
        ("XI-CARNEY TARIFF CUT",
         "China and Canada agree further tariff cuts and deeper ties."),
        ("BUS INTO RAVINE",
         "Bus plunges into a ravine in Uttarakhand, India; six to eight "
         "dead, more than 20 hurt."),
        ("MONGOLIA PRESIDENT QUITS",
         "President Khurelsukh resigns amid embezzlement accusations."),
        ("SEOUL JETS DEPLOY",
         "South Korea sends jets after Russian aircraft enter its air "
         "defence zone."),
        ("CHINA'S 250-MILE E-PLANE",
         "China tests a 250-mile electric plane in a major aviation "
         "milestone."),
        ("MALAYSIA-FRANCE MINERALS",
         "Malaysia signs its first critical minerals pact, with France."),
        ("TRUMP LANDS IN MANILA",
         "The US president arrives for a state visit and the ASEAN-US "
         "summit."),
    ]),
    ("AMERICAS", OCHRE, [
        ("13 MEASLES BABIES",
         "Congenital measles cases in the US, 2025 to Sep 2026; "
         "infections at their highest since 1991."),
        ("US LOSES MEASLES STATUS",
         "The US loses its measles elimination status after 26 years; "
         "Mexico and Bolivia too."),
        ("WHITE HOUSE GAG ORDER",
         "Every federal agency must get White House approval before any "
         "employee testifies to Congress."),
        ("US CHIP CURBS",
         "Commerce moves to stop China renting US computing power; new "
         "SE Asia chip licences."),
        ("SPY SOLDIER IN CUSTODY",
         "An American soldier arrested in Britain on spying suspicion is "
         "taken into US military custody."),
        ("ZVEREV INTO ATP FINALS",
         "World No. 1 Zverev beats Shelton to reach the ATP Finals "
         "knockout stage."),
        ("ALCARAZ BEATS TIAFOE",
         "Carlos Alcaraz opens his ATP Finals campaign with a win over "
         "Frances Tiafoe."),
        ("WALES STUN NEW ZEALAND",
         "Wales beat New Zealand in Cardiff in a historic rugby win."),
    ]),
    ("AFRICA", PLUM, [
        ("SUDAN: 2,230 DEAD",
         "UN confirms more than 2,230 civilian deaths in Sudan, "
         "Jan-Oct 2026; most by drones."),
        ("TRACHOMA BEATEN",
         "WHO validates the elimination of trachoma, a blinding eye "
         "disease, in Eritrea."),
    ]),
    ("GLOBAL/TECH", SLATE, [
        ("SE ASIA CHIP LICENCES",
         "New US licensing for advanced processor sales to data centres "
         "in South-East Asia."),
        ("SINGAPORE SEEKS CHIPS",
         "Singapore seeks trusted access to advanced AI processors amid "
         "US export curbs."),
        ("CYBERCRIME $10.5T",
         "Global cybercrime damages are projected at $10.5 trillion."),
        ("NVIDIA'S DGX SPARK",
         "Nvidia unveils DGX Spark and Rubin HPC at the SC26 conference."),
        ("APPLE OUTAGES",
         "Outages hit iCloud, Apple Pay and the App Store on the same "
         "day."),
    ]),
]

# Three market lines shown as a box at the foot of Global / Tech.
MARKETS = [
    ("NASDAQ 100", "-2.7% AS NVIDIA SHAKEUP WEIGHS ON TECH"),
    ("OIL", "SLIDES ON EXPECTED GLOBAL SURPLUS"),
    ("EURO", "BELOW $1.10 FOR FIRST TIME SINCE APRIL 2025"),
]

# (big number, label) for the sidebar beside the map.
NUMBERS = [
    ("1,441", "UKRAINIAN DRONES RUSSIA SAYS IT DOWNED OVERNIGHT"),
    ("$115.8B", "NVIDIA REVENUE, UP 103% YEAR ON YEAR"),
    ("9TH", "YEAR IN A ROW THE PENTAGON FAILED ITS AUDIT"),
    ("$4.8T", "PENTAGON ASSETS UNDER AUDIT DISCLAIMER"),
    ("$10.5T", "PROJECTED GLOBAL CYBERCRIME DAMAGES"),
    ("128", "STATES MEETING IN GENEVA ON ROBOT WEAPONS"),
]

MAP_KEY_LINES = [
    "1 CRIMEA   2 HORMUZ   3 BAHRAIN   4 SHENZHEN",
    "5 RWANDA   6 WASHINGTON   7 GENEVA   8 UTTARAKHAND",
    "9 SUDAN   10 TOKYO",
]


# ------------------------------------------------------------------ layout
W, H = 1024, 1024
MARGIN = 24
CONTENT_W = W - 2 * MARGIN  # 976


def draw_masthead(sh):
    sh.write_mid(W // 2, 16, "THE WORLD IN ONE DAY", 6, INK, heavy=True)
    sh.write_mid(W // 2, 72,
                 "TUESDAY 17 NOVEMBER 2026  \u2022  49 STORIES  \u2022  "
                 "6 REGIONS  \u2022  ONE PAGE",
                 2, INK)
    sh.rule(MARGIN, 96, CONTENT_W, INK, 3)
    sh.rule(MARGIN, 102, CONTENT_W, INK, 1)


def draw_heroes(sh):
    y0, hh = 110, 174
    bw, gap = 320, 8
    for i, (head, color, scene, summ) in enumerate(HEROES):
        x = MARGIN + i * (bw + gap)
        sh.frame(x, y0, bw, hh, RULE, 1)
        sh.bar(x + 1, y0 + 1, bw - 2, 5, color)
        scene(sh, x + 1, y0 + 6, bw - 2, 64)
        hy = y0 + 76
        for ln in fold(head, 3, bw - 16)[:3]:
            sh.write(x + 8, hy, ln, 3, INK)
            hy += 27
        sh.block(x + 8, hy + 2, summ, 1, INK, bw - 16, 2, gap=9)


def draw_map_band(sh):
    y0, mh = 292, 178
    mx, mw = MARGIN, 520
    my, mhh = y0, mh - 30  # legend strip takes the bottom 30 px
    sh.bar(mx, y0, mw, mh, SEA)
    # faint graticule so the sea reads as a map, not a blank panel
    for gy in range(y0 + 24, y0 + mhh, 24):
        sh.rule(mx, gy, mw, (200, 216, 222), 1)
    for gx in range(mx + 52, mx + mw, 52):
        sh.bar(gx, y0, 1, mhh, (200, 216, 222))
    sx, sy = mw / 640.0, mhh / 182.0
    for _name, (lx, ly), pts in CONTINENTS:
        scaled = [(mx + int(px * sx), my + int(py * sy)) for px, py in pts]
        sh.poly(scaled, LAND)
    # a few shaded patches so the land is not one flat slab
    for ex, ey, erx, ery in ((300, 60, 26, 12), (470, 40, 34, 14),
                             (150, 140, 22, 16), (330, 118, 20, 14)):
        sh.ellipse(mx + int(ex * sx), my + int(ey * sy),
                   int(erx * sx), int(ery * sy), LAND2)
    for _name, (lx, ly), _pts in CONTINENTS:
        sh.write(mx + int(lx * sx) - 22, my + int(ly * sy) - 3,
                 _name, 1, (74, 82, 70))
    for hx, hy, color, num in SPOTS:
        cx = mx + int(hx * sx)
        cy = my + int(hy * sy)
        sh.ring(cx, cy, 8, WHITE, 2)
        sh.disc(cx, cy, 6, color)
        sh.write_mid(cx, cy - 3, num, 1, WHITE, heavy=True)
    sh.frame(mx, y0, mw, mh, INK, 1)
    ly = y0 + mh - 27
    for ln in MAP_KEY_LINES:
        sh.write_mid(mx + mw // 2, ly, ln, 1, INK)
        ly += 9

    # Sidebar: the day in numbers.
    sx, sw = 552, 448
    sh.frame(sx, y0, sw, mh, RULE, 1)
    sh.write_mid(sx + sw // 2, y0 + 8, "THE DAY IN NUMBERS", 2, CRIMSON,
                 heavy=True)
    sh.rule(sx + 10, y0 + 28, sw - 20, RULE, 1)
    sy = y0 + 36
    for num, label in NUMBERS:
        sh.write(sx + 10, sy, num, 2, INK, heavy=True)
        sh.block(sx + 118, sy + 2, label, 1, INK, sw - 128, 2, gap=9)
        sy += 24


def draw_panels(sh):
    y0, hh = 478, 78
    bw, gap = 238, 8
    for i, (head, color, scene, cap) in enumerate(PANELS):
        x = MARGIN + i * (bw + gap)
        sh.frame(x, y0, bw, hh, RULE, 1)
        sh.bar(x + 1, y0 + 1, bw - 2, 4, color)
        scene(sh, x + 1, y0 + 5, bw - 2, 42)
        sh.write(x + 6, y0 + 50, head, 1, INK, heavy=True)
        sh.block(x + 6, y0 + 61, cap, 1, INK, bw - 12, 2, gap=8)


def draw_region_column(sh, x, y0, name, color, stories, filler):
    col_w = 156
    sh.bar(x, y0, col_w, 24, color)
    sh.write_tight_mid(x + col_w // 2, y0 + 4, name, WHITE, heavy=True)
    sy = y0 + 30
    for head, summ in stories:
        hlines = fold(head, 1, col_w - 4)[:2]
        hy = sy
        for ln in hlines:
            sh.write(x + 2, hy, ln, 1, color, heavy=True)
            hy += 9
        sy = sh.block(x + 2, hy + 2, summ, 1, INK, col_w - 4, 3, gap=8)
        sy += 6
        sh.rule(x + 2, sy - 4, col_w - 4, RULE, 1)
    for kind in filler:
        if kind == "key":
            sy += 2
            sh.write(x + 2, sy, "MAP KEY", 1, INK, heavy=True)
            sy += 12
            for rname, rcolor, _ in REGIONS:
                sh.bar(x + 2, sy, 10, 10, rcolor)
                sh.write(x + 16, sy + 1, rname, 1, INK)
                sy += 14
            sy += 2
            sh.write(x + 2, sy, "SOURCES", 1, INK, heavy=True)
            sy += 12
            sy = sh.block(x + 2, sy,
                          "ALGENOM, JUST SECURITY, OPEN CHRONICLE, "
                          "FEEDCAST, ZARK NEWS, ONETURN, BBC, REUTERS, "
                          "AP, FOREIGN EXCHANGES.",
                          1, FAINT, col_w - 4, 4, gap=8)
        elif kind == "markets":
            sy += 4
            sh.write(x + 2, sy, "MARKETS", 1, INK, heavy=True)
            sy += 13
            for mname, mtext in MARKETS:
                sh.write(x + 2, sy, mname, 1, INK, heavy=True)
                sy = sh.block(x + 2, sy + 9, mtext, 1, INK, col_w - 4, 2,
                              gap=8)
                sy += 5
        elif kind == "spots":
            sy += 2
            sh.write(x + 2, sy, "HOTSPOTS ON THE MAP", 1, INK, heavy=True)
            sy += 12
            names = ["1 CRIMEA", "2 HORMUZ", "3 BAHRAIN", "4 SHENZHEN",
                     "5 RWANDA", "6 WASHINGTON", "7 GENEVA",
                     "8 UTTARAKHAND", "9 SUDAN", "10 TOKYO"]
            for nm in names:
                sh.write(x + 2, sy, nm, 1, INK)
                sy += 12
        elif kind == "note":
            sy += 4
            sy = sh.block(x + 2, sy,
                          "ALL STORIES AS REPORTED TUESDAY 17 NOVEMBER "
                          "2026. NEXT: THE SUMMIT IN SHENZHEN.",
                          1, FAINT, col_w - 4, 4, gap=8)
    sh.rule(x, 1000, col_w, color, 2)



def draw_regions(sh):
    y0 = 564
    col_w, gap = 156, 8
    fillers = {"AFRICA": ["key", "spots"],
               "GLOBAL/TECH": ["markets", "note"]}
    for i, (name, color, stories) in enumerate(REGIONS):
        x = MARGIN + i * (col_w + gap)
        draw_region_column(sh, x, y0, name, color, stories,
                           fillers.get(name, []))


def draw_footer(sh):
    sh.write_mid(W // 2, 1012,
                 "THE WORLD IN ONE DAY - TUESDAY 17 NOVEMBER 2026 - "
                 "ALL STORIES AS REPORTED THAT DAY",
                 1, FAINT)


def build():
    sh = Sheet(W, H, PAPER)
    sh.speckle(0, 0, W, H, (234, 229, 216), 2, 12345)
    sh.speckle(0, 0, W, H, (241, 236, 224), 2, 98765)
    sh.speckle(0, 0, W, H, (238, 233, 220), 3, 55555)
    draw_masthead(sh)
    draw_heroes(sh)
    draw_map_band(sh)
    draw_panels(sh)
    draw_regions(sh)
    draw_footer(sh)
    return sh


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    sheet = build()
    data = encode_png(sheet)
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    print("wrote %s (%d bytes, %dx%d)" % (path, len(data), sheet.w, sheet.h))


if __name__ == "__main__":
    main()
