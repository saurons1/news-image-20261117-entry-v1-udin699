#!/usr/bin/env python3
"""THE WORLD IN ONE DAY -- Tuesday 17 November 2026.

A one-page newspaper front page summing up the day's world news:
a masthead, three hero stories, a world map with the day's hotspots,
and 24 stories across 6 regions. Drawn entirely with the Python
standard library: hand-written PNG encoder (zlib + struct) and an
embedded 5x7 bitmap font, every pixel plotted by hand.

Writes entry.png to $MAKEFUN_OUTPUT_DIR (default /output).
Deterministic: the same bytes on every run.
"""

import os
import struct
import sys
import zlib

# ---------------------------------------------------------------- font
# 5x7 bitmap font. Each glyph is 7 rows of 5 bits, '1' = ink.
# All text on the page is rendered in capitals.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
}
BLANK = ("00000", "00000", "00000", "00000", "00000", "00000", "00000")

# ---------------------------------------------------------------- canvas
PAPER = (246, 241, 229)   # newsprint off-white
INK = (20, 20, 20)        # near-black ink
RED = (163, 22, 33)       # masthead / Middle East accent
BLUE = (29, 78, 137)      # Europe
GREEN = (14, 107, 74)     # Asia-Pacific
BROWN = (122, 74, 18)     # Americas
PURPLE = (107, 58, 122)   # Africa
DARK = (51, 51, 51)       # Global / Tech
GREY = (120, 120, 112)    # secondary text / rules
LAND = (154, 168, 143)    # map land
SEA = (223, 232, 234)     # map sea
WHITE = (255, 255, 255)


def text_width(s, scale):
    """Pixel width of s at the given scale (6 px advance per glyph)."""
    return len(s) * 6 * scale - scale if s else 0


def wrap_text(s, scale, max_w):
    """Greedy word wrap; returns a list of lines fitting max_w pixels."""
    words = s.split(" ")
    lines = []
    cur = ""
    for w in words:
        trial = w if not cur else cur + " " + w
        if text_width(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg) * (w * h)

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def fill_rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def rect(self, x, y, w, h, color, t=1):
        self.fill_rect(x, y, w, t, color)
        self.fill_rect(x, y + h - t, w, t, color)
        self.fill_rect(x, y, t, h, color)
        self.fill_rect(x + w - t, y, t, h, color)

    def hline(self, x, y, w, color, t=1):
        self.fill_rect(x, y, w, t, color)

    def dot(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set(xx, yy, color)

    def ring(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                if r * r - 2 * r <= d2 <= r * r:
                    self.set(xx, yy, color)

    def glyph(self, x, y, ch, scale, color, bold=False):
        rows = FONT.get(ch, BLANK)
        for r in range(7):
            bits = rows[r]
            for c in range(5):
                if bits[c] == "1":
                    self.fill_rect(x + c * scale, y + r * scale,
                                   scale, scale, color)
                    if bold:
                        self.fill_rect(x + c * scale + 1, y + r * scale,
                                       scale, scale, color)

    def text(self, x, y, s, scale, color, bold=False):
        s = s.upper()
        cx = x
        for ch in s:
            self.glyph(cx, y, ch, scale, color, bold)
            cx += 6 * scale
        return cx

    def text_center(self, cx, y, s, scale, color, bold=False):
        w = text_width(s.upper(), scale)
        return self.text(cx - w // 2, y, s, scale, color, bold)

    def para(self, x, y, s, scale, color, max_w, max_lines, bold=False,
             leading=None):
        """Wrapped paragraph; returns the y just below the last line."""
        lh = leading if leading is not None else 7 * scale + 2
        lines = wrap_text(s, scale, max_w)[:max_lines]
        for ln in lines:
            self.text(x, y, ln, scale, color, bold)
            y += lh
        return y

# ---------------------------------------------------------------- png
def png_chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def encode_png(cv):
    """Encode the canvas as a deterministic RGB PNG (no time chunks)."""
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)  # filter: none
        raw += cv.px[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + png_chunk(b"IHDR", ihdr)
            + png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + png_chunk(b"IEND", b""))


# ---------------------------------------------------------------- map
# Simplified world map, 64 columns x 24 rows ('#' = land). Authored from
# the rough shape of the continents at a ~2.7:1 aspect; recognisable at a
# glance: Americas left, Europe/Africa centre, Asia right, Australia low.
MAP = [
    "........##########......####..................##################",
    "..#####..############...###..##..............###################",
    "...#####.###############..#..###............####################",
    "........###############..#..###..#.........#####################",
    ".........##############..##########........####################.",
    "..........##########....#################...##############..#...",
    "..........##########....#########.########...###########..##....",
    "...........########.....#####.#####..#####....##########...#....",
    "............#####.......#########....####.....######.###........",
    ".............####.......##########...####.....######.##.........",
    "..............###.......###########..###......#####.##..........",
    "...............##.......######..####..##......######.####.......",
    "................##......############..#......###########........",
    "..................######.###########........########.##..###....",
    "..................######.#######............######....##.##.....",
    "..................######.######..#..........########............",
    "...................#####.#####..#...........#######.............",
    "....................####..###...............#######.............",
    "....................###...###...............########..#.........",
    "....................##.......................######..##.........",
    "....................##..........................................",
    "....................#...........................................",
    "................................................................",
    "................................................................",
]

# (map column, map row, region colour) hotspots for the day's big stories.
HOTSPOTS = [
    (38, 4, RED),     # Crimea / Kyiv
    (43, 7, RED),     # Strait of Hormuz
    (42, 8, RED),     # Bahrain
    (54, 7, GREEN),   # Shenzhen
    (39, 13, PURPLE),  # Rwanda
    (14, 6, BROWN),   # Washington
    (35, 5, BLUE),    # Geneva
    (46, 8, GREEN),   # Uttarakhand
]

# ---------------------------------------------------------------- content
# All facts as reported on Tuesday 17 November 2026 (see the news brief).
# Headlines are kept short so they wrap to at most 3 lines in a column.

HEROES = [
    ("UKRAINE HITS CRIMEA BRIDGE AGAIN", RED,
     "Kyiv strikes the Kerch crossing a second day running. Russia hits "
     "Kyiv's bridges in reply; Zelenskyy hails an 'unprecedented "
     "operation'."),
    ("MINES HIT TANKERS AT HORMUZ", RED,
     "Tankers struck by mines near the strait; fires aboard, crews safe. "
     "A third US carrier sails in as Iran fires drones at a US radar "
     "base in Bahrain."),
    ("TRUMP, XI, PUTIN TO MEET THURSDAY", GREEN,
     "First three-way summit in years: 19 Nov in Shenzhen, on the APEC "
     "sidelines. Nuclear risks, sanctions and Ukraine on the table."),
]

# (region name, colour, [(headline, summary), ...])
REGIONS = [
    ("EUROPE", BLUE, [
        ("CRIMEA BRIDGE HIT",
         "Ukraine strikes the Kerch crossing a second day running; part "
         "of the road bridge collapses."),
        ("KYIV BRIDGES UNDER FIRE",
         "Russia hits the North and South bridges over the Dnipro; heat, "
         "water and power cut."),
        ("1,441 DRONES DOWNED",
         "Russia claims it intercepted 1,441 Ukrainian drones overnight."),
        ("ROBOT WEAPON TALKS",
         "Delegates of 128 states meet in Geneva on a treaty to ban "
         "lethal autonomous weapons."),
    ]),
    ("MIDDLE EAST", RED, [
        ("TANKERS HIT BY MINES",
         "Tankers struck by mines near the Strait of Hormuz; fires "
         "aboard, crews reported safe."),
        ("IRAN DRONES HIT US RADAR",
         "Iran fires drones at a US radar base in Bahrain; all "
         "intercepted, no casualties."),
        ("'DIRTY BOMB' PLOT CLAIM",
         "US intelligence says Iran is developing plans to target senior "
         "Trump officials in Washington."),
        ("US CARRIER NO. 3",
         "USS Theodore Roosevelt reaches the Middle East, joining the "
         "Bush and the Washington."),
        ("UK SANCTIONS FIRMS",
         "Britain sanctions eight Israeli settlement firms and an "
         "aid-blocking group."),
        ("NETANYAHU CAMP ROW",
         "His camp is accused of giving police information that led to "
         "arrests of Arab party workers."),
    ]),
    ("ASIA-PACIFIC", GREEN, [
        ("TRILATERAL THURSDAY",
         "China confirms the first three-way meeting, 19 Nov in Shenzhen "
         "on the APEC sidelines."),
        ("JAPAN JETS SCRAMBLE",
         "Tokyo protests after two suspected Russian aircraft violate its "
         "airspace."),
        ("XI-CARNEY TARIFF CUT",
         "China and Canada agree further tariff cuts and deeper ties."),
        ("BUS FALLS INTO RAVINE",
         "Bus plunges into a ravine in Uttarakhand, India; six to eight "
         "dead, more than 20 hurt."),
    ]),
    ("AMERICAS", BROWN, [
        ("PENTAGON AUDIT FAILS",
         "Ninth failed financial audit in a row; a disclaimer on more "
         "than $4.8 trillion in assets."),
        ("13 MEASLES BABIES",
         "Congenital measles cases in the US, 2025 to Sep 2026; "
         "infections at their highest since 1991."),
        ("WHITE HOUSE GAG ORDER",
         "Every federal agency must get White House approval before any "
         "employee testifies to Congress."),
        ("US CHIP CURBS",
         "Commerce moves to stop China renting US computing power; new "
         "SE Asia chip licences."),
    ]),
    ("AFRICA", PURPLE, [
        ("RWANDA RETURN HUB",
         "Five European states announce a joint return facility in "
         "Rwanda for rejected asylum seekers."),
        ("TRACHOMA BEATEN",
         "WHO validates the elimination of trachoma, a blinding eye "
         "disease, in Eritrea."),
    ]),
    ("GLOBAL / TECH", DARK, [
        ("SE ASIA CHIP LICENCES",
         "New US licensing for advanced processor sales to data centres "
         "in South-East Asia."),
        ("SINGAPORE SEEKS CHIPS",
         "Singapore seeks trusted access to advanced AI processors amid "
         "US export curbs."),
        ("CYBERCRIME $10.5T",
         "Global cybercrime damages are projected at $10.5 trillion."),
        ("TRUMP FLIES TO ASIA",
         "The US president travels to Asia ahead of the Shenzhen "
         "three-way meeting."),
    ]),
]

# (big number, label) for the sidebar.
NUMBERS = [
    ("1,441", "UKRAINIAN DRONES RUSSIA SAYS IT DOWNED OVERNIGHT"),
    ("9TH", "YEAR IN A ROW THE PENTAGON FAILED ITS AUDIT"),
    ("$4.8T", "PENTAGON ASSETS UNDER AUDIT DISCLAIMER"),
    ("$10.5T", "PROJECTED GLOBAL CYBERCRIME DAMAGES"),
    ("128", "STATES MEETING IN GENEVA ON ROBOT WEAPONS"),
    ("13", "BABIES BORN WITH CONGENITAL MEASLES IN THE US"),
]

# ---------------------------------------------------------------- layout
W, H = 1024, 1024
MARGIN = 24
CONTENT_W = W - 2 * MARGIN  # 976


def draw_masthead(cv):
    cv.text_center(W // 2, 20, "THE WORLD IN ONE DAY", 6, INK, bold=True)
    cv.text_center(W // 2, 74,
                   "TUESDAY 17 NOVEMBER 2026 - 24 STORIES - 6 REGIONS - ONE PAGE",
                   2, INK)
    cv.hline(MARGIN, 100, CONTENT_W, INK, 3)
    cv.hline(MARGIN, 106, CONTENT_W, INK, 1)


def draw_heroes(cv):
    y0, hh = 120, 132
    bw, gap = 320, 8
    for i, (head, color, summ) in enumerate(HEROES):
        x = MARGIN + i * (bw + gap)
        cv.rect(x, y0, bw, hh, GREY, 1)
        cv.fill_rect(x + 1, y0 + 1, bw - 2, 6, color)
        lines = wrap_text(head, 3, bw - 16)
        hy = y0 + 16
        for ln in lines[:3]:
            cv.text(x + 8, hy, ln, 3, INK)
            hy += 27  # scale-3 glyphs are 21 px tall; 27 px step leaves
            # a 6 px clear gap so headline lines never touch
        cv.para(x + 8, hy + 4, summ, 1, INK, bw - 16, 3, leading=9)


def draw_map_band(cv):
    y0, mh = 260, 240
    mx, mw = MARGIN, 640
    cv.fill_rect(mx, y0, mw, mh, SEA)
    cw, ch = mw // 64, mh // 24  # 10 x 10 px cells
    for r, row in enumerate(MAP):
        for c, ch2 in enumerate(row):
            if ch2 == "#":
                cv.fill_rect(mx + c * cw, y0 + r * ch, cw, ch, LAND)
    cv.rect(mx, y0, mw, mh, INK, 1)
    for (c, r, color) in HOTSPOTS:
        cx = mx + c * cw + cw // 2
        cy = y0 + r * ch + ch // 2
        cv.ring(cx, cy, 8, WHITE)
        cv.dot(cx, cy, 6, color)
    cv.fill_rect(mx + 1, y0 + mh - 18, mw - 2, 17, PAPER)
    cv.text_center(mx + mw // 2, y0 + mh - 14,
                   "WHERE THE DAY HAPPENED - DOTS MARK THE BIG STORIES",
                   1, INK)

    # Sidebar: the day in numbers.
    sx, sw = 672, 328
    cv.rect(sx, y0, sw, mh, GREY, 1)
    cv.text_center(sx + sw // 2, y0 + 10, "THE DAY IN NUMBERS", 2, RED,
                   bold=True)
    cv.hline(sx + 10, y0 + 30, sw - 20, GREY, 1)
    sy = y0 + 42
    for num, label in NUMBERS:
        cv.text(sx + 10, sy, num, 2, INK, bold=True)
        cv.para(sx + 108, sy + 2, label, 1, INK, sw - 118, 2, leading=9)
        sy += 33


def draw_regions(cv):
    y0 = 508
    col_w, gap = 156, 8
    for i, (name, color, stories) in enumerate(REGIONS):
        x = MARGIN + i * (col_w + gap)
        cv.fill_rect(x, y0, col_w, 26, color)
        cv.text_center(x + col_w // 2, y0 + 6, name, 2, WHITE, bold=True)
        sy = y0 + 34
        for head, summ in stories:
            lines = wrap_text(head, 2, col_w - 4)
            hy = sy
            for ln in lines[:2]:
                cv.text(x + 2, hy, ln, 2, INK, bold=True)
                hy += 15
            cv.para(x + 2, sy + 32, summ, 1, INK, col_w - 4, 4, leading=8)
            sy += 67
            if stories.index((head, summ)) < len(stories) - 1:
                cv.hline(x + 2, sy - 4, col_w - 4, GREY, 1)
        if name == "AFRICA":
            # Short column: fill with the map key and the sources.
            ky = sy + 8
            cv.text(x + 2, ky, "MAP KEY", 1, INK, bold=True)
            ky += 14
            for rname, rcolor, _ in REGIONS:
                cv.fill_rect(x + 2, ky, 10, 10, rcolor)
                cv.text(x + 16, ky + 1, rname, 1, INK)
                ky += 16
            ky += 6
            cv.text(x + 2, ky, "SOURCES", 1, INK, bold=True)
            ky += 14
            cv.para(x + 2, ky,
                    "ALGENOM, JUST SECURITY, OPEN CHRONICLE, FEEDCAST, "
                    "ZARK NEWS, ONETURN.",
                    1, GREY, col_w - 4, 4, leading=8)
        cv.hline(x, 1000, col_w, color, 2)


def draw_footer(cv):
    cv.text_center(W // 2, 1012,
                   "THE WORLD IN ONE DAY - TUESDAY 17 NOVEMBER 2026 - "
                   "ALL STORIES AS REPORTED THAT DAY",
                   1, GREY)


def build():
    cv = Canvas(W, H, PAPER)
    draw_masthead(cv)
    draw_heroes(cv)
    draw_map_band(cv)
    draw_regions(cv)
    draw_footer(cv)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    cv = build()
    data = encode_png(cv)
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    print("wrote %s (%d bytes, %dx%d)" % (path, len(data), cv.w, cv.h))


if __name__ == "__main__":
    main()
