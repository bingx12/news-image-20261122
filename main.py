"""THE WORLD TODAY — Sunday 22 November 2026, drawn as a newspaper page.

Pure-stdlib Python 3.13. Renders 1024x1024 front page from bitmap glyphs
in font_data.py (DejaVu Sans Book + Bold, one 64px base size, scaled at
runtime) and writes a deterministic PNG to /output/entry.png. No network,
no clock, no randomness.
"""

import math
import os
import struct
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from font_data import GLYPHS

BASE = 64
W = 1024
H = 1024

PAPER = (253, 251, 244)
INK = (18, 18, 18)
RED = (172, 32, 28)
BLUE = (28, 62, 110)
DARKPANEL = (26, 54, 96)
GREY = (112, 110, 102)
LIGHT = (214, 210, 198)
WHITE = (255, 255, 255)
SKY = (214, 230, 240)


# ---------------------------------------------------------------- canvas

class Canvas:
    def __init__(self, w, h, colour):
        self.w = w
        self.h = h
        self.px = bytearray(colour * (w * h))

    def set(self, x, y, colour):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i] = colour[0]
            self.px[i + 1] = colour[1]
            self.px[i + 2] = colour[2]

    def rect(self, x, y, w, h, colour):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, colour)

    def border(self, x, y, w, h, colour, t=1):
        self.rect(x, y, w, t, colour)
        self.rect(x, y + h - t, w, t, colour)
        self.rect(x, y, t, h, colour)
        self.rect(x + w - t, y, t, h, colour)

    def hline(self, x, y, w, colour, t=1):
        self.rect(x, y, w, t, colour)

    def vline(self, x, y, h, colour, t=1):
        self.rect(x, y, t, h, colour)

    def line(self, x0, y0, x1, y1, colour, t=1):
        dx = x1 - x0
        dy = y1 - y0
        steps = max(abs(dx), abs(dy), 1)
        for i in range(steps + 1):
            x = x0 + round(dx * i / steps)
            y = y0 + round(dy * i / steps)
            for a in range(t):
                for b in range(t):
                    self.set(x + a - t // 2, y + b - t // 2, colour)

    def disc(self, cx, cy, r, colour):
        for yy in range(cy - r, cy + r + 1):
            half = int(math.sqrt(max(r * r - (yy - cy) ** 2, 0)))
            for xx in range(cx - half, cx + half + 1):
                self.set(xx, yy, colour)

    def ring(self, cx, cy, r, colour, t=2):
        for yy in range(cy - r - t, cy + r + t + 1):
            for xx in range(cx - r - t, cx + r + t + 1):
                d = math.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
                if r - t <= d <= r + t:
                    self.set(xx, yy, colour)

    def poly(self, pts, colour):
        # Even-odd scanline fill.
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                for x in range(int(math.ceil(xs[k])), int(xs[k + 1]) + 1):
                    self.set(x, y, colour)


# ---------------------------------------------------------------- text

def _glyph(ch, bold):
    return GLYPHS[(ord(ch), 1 if bold else 0)]


def _bits(g):
    adv, left, top, w, h, hx = g
    raw = bytes.fromhex(hx) if hx else b""
    return raw, w, h


def text_width(s, size, bold=False):
    total = 0
    for ch in s:
        g = _glyph(ch, bold)
        total += int(g[0] * size / BASE)
    return total


def draw_text(cv, x, y, s, size, colour, bold=False):
    """Draw s with its baseline at y; x is the left edge. Returns end x."""
    cx = x
    for ch in s:
        g = _glyph(ch, bold)
        adv, left, top, w, h, hx = g
        raw, bw, bh = _bits(g)
        if bw and bh:
            tw = -(-bw * size // BASE)
            th = -(-bh * size // BASE)
            ox = int(left * size / BASE)
            oy = int(top * size / BASE)
            for ty in range(th):
                sy = ty * BASE // size
                for tx in range(tw):
                    sx = tx * BASE // size
                    bit = (raw[(sy * bw + sx) >> 3] >> (7 - ((sy * bw + sx) & 7))) & 1
                    if bit:
                        cv.set(cx + ox + tx, y + oy + ty, colour)
        cx += int(adv * size / BASE)
    return cx


def draw_centred(cv, s, cx, y, size, colour, bold=False):
    draw_text(cv, cx - text_width(s, size, bold) // 2, y, s, size, colour, bold)


def wrap(s, size, maxw, bold=False):
    words = s.split(" ")
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, size, bold) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def para(cv, x, y, s, size, maxw, colour=INK, bold=False, leading=None):
    lead = leading if leading is not None else size + 5
    for ln in wrap(s, size, maxw, bold):
        draw_text(cv, x, y, ln, size, colour, bold)
        y += lead
    return y


# ---------------------------------------------------------------- png

def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(cv, path):
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)
        raw += cv.px[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    data = b"\x89PNG\r\n\x1a\n"
    data += _chunk(b"IHDR", ihdr)
    data += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    data += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(data)
    return len(data)


# ---------------------------------------------------------------- page

def kicker(cv, x, y, s, colour=RED):
    draw_text(cv, x, y, s, 13, colour, bold=True)
    return y + 20


def headline(cv, x, y, s, size, maxw):
    lines = wrap(s, size, maxw, bold=True)
    for ln in lines:
        draw_text(cv, x, y, ln, size, INK, bold=True)
        y += size + 6
    return y


def rule(cv, y, x0=28, x1=996, colour=INK, t=1):
    cv.hline(x0, y, x1 - x0, colour, t)


def draw_page():
    cv = Canvas(W, H, PAPER)

    # ---- top strip -------------------------------------------------
    draw_text(cv, 28, 30, "SUNDAY 22 NOVEMBER 2026", 15, INK, bold=True)
    right = "WORLD EDITION"
    draw_text(cv, 996 - text_width(right, 13), 30, right, 13, GREY)
    rule(cv, 38, t=2)

    # ---- masthead --------------------------------------------------
    draw_centred(cv, "THE WORLD TODAY", 512, 108, 74, INK, bold=True)
    draw_centred(
        cv, "THE DAY IN ONE PAGE  —  EVERY STORY REPORTED SUNDAY 22 NOVEMBER 2026",
        512, 132, 13, GREY)
    rule(cv, 142, t=3)
    rule(cv, 147, t=1)

    # ---- lead: COP31 ----------------------------------------------
    lx, lw = 28, 656
    y = kicker(cv, lx, 172, "CLIMATE  ·  ANTALYA, TURKIYE")
    y = headline(cv, lx, y + 6,
                 "COP31 puts its final deal to a vote — with no mention of fossil fuels",
                 29, lw)
    y = para(cv, lx, y + 4,
             "After two days in overtime, negotiators in Antalya put a final "
             "deal before nearly 200 governments in the early hours of "
             "Sunday. The text never names fossil fuels, oil, coal or a phase-out. "
             "It is the first COP deal to admit the world will pass the 1.5C "
             "limit, and it sets a goal of raising electricity to 35% of energy "
             "use by 2035, plus one billion tonnes of carbon capture.",
             14, lw, leading=20)

    # ---- lead motif: thermometer -----------------------------------
    px, py, pw, ph = 716, 158, 280, 196
    cv.border(px, py, pw, ph, INK, 2)
    cv.rect(px + 2, py + 2, pw - 4, 26, INK)
    draw_centred(cv, "THE 1.5C LIMIT", 856, py + 21, 13, WHITE, bold=True)
    draw_centred(cv, "1.5°C", 856, py + 80, 44, RED, bold=True)
    draw_text(cv, px + 18, py + 106, "THE WORLD IS SET TO PASS IT", 12, INK, bold=True)
    # thermometer
    tx, ty = 856, py + 124
    cv.rect(tx - 9, ty, 18, 40, WHITE)
    cv.border(tx - 9, ty, 18, 40, INK, 2)
    cv.rect(tx - 6, ty + 6, 12, 34, RED)
    cv.disc(tx, ty + 44, 14, RED)
    cv.disc(tx, ty + 44, 8, (255, 120, 110))
    cv.hline(tx + 12, ty + 6, 14, INK, 2)
    draw_text(cv, tx + 30, ty + 10, "OVERSHOOT", 11, INK, bold=True)
    draw_text(cv, tx + 30, ty + 26, "EXPECTED", 11, INK, bold=True)
    draw_text(cv, tx + 30, ty + 42, "WITHIN YEARS", 11, GREY)

    rule(cv, y + 8, t=2)

    # ---- three columns ---------------------------------------------
    # Measure every column's text first, then put all three panels on one
    # shared line below the longest body so nothing ever overlaps.
    colw = 304
    cols = [28, 360, 692]
    top = y + 24
    stories = [
        ("WAR IN UKRAINE  ·  KRYVYI RIH",
         "Missiles strike Zelensky's home city — rescuers hit next",
         "Two ballistic missiles hit the centre of Kryvyi Rih, President "
         "Zelensky's home city, on Friday night. A seven-year-old boy and a "
         "20-year-old paramedic were killed and about 60 people were wounded."),
        ("MEXICO  ·  SINALOA",
         "'El Chapo Isidro' seized in shoot-out",
         "Special forces arrested Fausto Isidro Meza Flores, known as "
         "'El Chapo Isidro', in Sinaloa on Saturday. The cartel boss was on "
         "the FBI's ten most wanted list. Eleven people were killed in the "
         "violence that followed the arrest."),
        ("MARKETS  ·  NEW YORK",
         "Stocks slide into correction as the AI rally cracks",
         "The S&P 500 has fallen 10% from its October high, entering "
         "correction territory as investors question AI valuations. The "
         "Nasdaq fell 5.28% on Friday. Bitcoin slid to about $55,300, its "
         "lowest since September 2024, before recovering past $60,000."),
    ]
    ends = []
    for (kick, head, body) in stories:
        n = 20 + 4 + len(wrap(head, 19, colw, bold=True)) * 25 + 2
        n += len(wrap(body, 13, colw)) * 18
        ends.append(top + n)
    panel_y = max(ends) + 10
    panel_h = 84

    for idx, (kick, head, body) in enumerate(stories):
        x = cols[idx]
        y = kicker(cv, x, top, kick)
        y = headline(cv, x, y + 4, head, 19, colw)
        para(cv, x, y + 2, body, 13, colw, leading=18)

    # column A panel — schematic map of Ukraine
    x = cols[0]
    mx, my, mw, mh = x, panel_y, colw, panel_h
    cv.rect(mx, my, mw, mh, DARKPANEL)
    shape = [(18, 50), (52, 18), (104, 10), (168, 20), (216, 12),
             (252, 32), (238, 58), (196, 72), (120, 78), (58, 72), (24, 64)]
    shape = [(mx + a, my + b) for a, b in shape]
    cv.poly(shape, (52, 96, 148))
    cv.disc(mx + 150, my + 28, 5, WHITE)
    cv.disc(mx + 150, my + 28, 2, RED)
    draw_text(cv, mx + 160, my + 24, "KYIV", 11, WHITE, bold=True)
    kx, ky = mx + 176, my + 56
    for ang in range(0, 360, 45):
        rad = math.radians(ang)
        cv.line(kx, ky, kx + int(11 * math.cos(rad)), ky + int(11 * math.sin(rad)),
                (255, 190, 60), 2)
    cv.disc(kx, ky, 4, (255, 190, 60))
    draw_text(cv, mx + 196, my + 52, "KRYVYI", 11, WHITE, bold=True)
    draw_text(cv, mx + 196, my + 66, "RIH", 11, WHITE, bold=True)
    draw_text(cv, mx + 10, my + 13, "UKRAINE — SCHEMATIC", 10, (170, 196, 224), bold=True)

    # column B panel — wanted poster
    x = cols[1]
    mx, my, mw, mh = x, panel_y, colw, panel_h
    cv.border(mx, my, mw, mh, INK, 2)
    cv.rect(mx + 2, my + 2, mw - 4, 22, RED)
    draw_centred(cv, "WANTED — CAPTURED", mx + mw // 2, my + 18, 12, WHITE, bold=True)
    draw_text(cv, mx + 12, my + 48, "FAUSTO ISIDRO", 15, INK, bold=True)
    draw_text(cv, mx + 12, my + 68, "MEZA FLORES", 15, INK, bold=True)
    draw_text(cv, mx + 12, my + 78, "FBI TEN MOST WANTED", 11, GREY, bold=True)
    cv.disc(mx + mw - 34, my + 54, 18, INK)
    cv.disc(mx + mw - 34, my + 54, 12, PAPER)
    draw_centred(cv, "11", mx + mw - 34, my + 60, 14, RED, bold=True)
    draw_text(cv, mx + mw - 60, my + 78, "KILLED", 10, GREY, bold=True)

    # column C panel — falling chart
    x = cols[2]
    mx, my, mw, mh = x, panel_y, colw, panel_h
    cv.border(mx, my, mw, mh, INK, 2)
    pts = [(12, 16), (52, 24), (92, 20), (132, 36), (172, 34),
           (212, 52), (252, 50), (282, 70)]
    pts = [(mx + a, my + b) for a, b in pts]
    for i in range(len(pts) - 1):
        cv.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], RED, 3)
    cv.disc(pts[0][0], pts[0][1], 4, INK)
    cv.disc(pts[-1][0], pts[-1][1], 4, RED)
    draw_text(cv, mx + 10, my + 12, "S&P 500  -10%", 12, RED, bold=True)
    draw_text(cv, mx + 168, my + 78, "OCT HIGH TO NOW", 10, GREY, bold=True)

    rule(cv, panel_y + panel_h + 12, t=2)

    # ---- bottom band: two stories ----------------------------------
    y = panel_y + panel_h + 28
    x = 28
    kicker(cv, x, y, "TRADE  ·  BRUSSELS — JAKARTA")
    hy = headline(cv, x, y + 24,
                  "EU and Indonesia sign trade deal after ten years of talks", 18, 460)
    para(cv, x, hy + 4,
         "After a decade of talks, the European Union and Indonesia signed a "
         "trade agreement on Sunday. The deal opens one of the world's largest "
         "markets to European exporters and cuts tariffs on Indonesian goods.",
         13, 460, leading=18)

    x = 524
    kicker(cv, x, y, "TECHNOLOGY  ·  UNITED NATIONS")
    hy = headline(cv, x, y + 24,
                  "UN talks end with no binding rules for AI weapons", 18, 460)
    para(cv, x, hy + 4,
         "UN-backed talks ended without binding rules for AI weapons. About 100 "
         "countries backed strict limits on machines that choose their own "
         "targets, but the biggest weapons producers resisted.",
         13, 460, leading=18)
    cv.vline(508, y, 130, LIGHT, 1)

    rule(cv, 856, t=1)

    # ---- sport strip ------------------------------------------------
    draw_text(cv, 28, 882, "SPORT", 13, RED, bold=True)
    draw_text(cv, 96, 882,
              "Verstappen wins an extraordinary Las Vegas Grand Prix as the Ferraris "
              "collide  |  Australia edge Wales 29-26 in Cardiff",
              13, INK)

    rule(cv, 898, t=1)

    # ---- also strip --------------------------------------------------
    draw_text(cv, 28, 924, "ALSO TODAY", 12, RED, bold=True)
    para(cv, 28, 944,
         "Myanmar calls ASEAN's decision 'unfair and imbalanced'  |  Australia "
         "hits back at the US budget office over AUKUS  |  Iran strikes an "
         "industrial site in Bahrain  |  Princess Kate says she is in remission",
         12, 968, leading=17)

    rule(cv, 970, t=1)
    draw_centred(cv,
                 "Sources: Reuters, AP, BBC, Al Jazeera, The Guardian — all stories "
                 "reported Sunday 22 November 2026.",
                 512, 992, 11, GREY)

    return cv


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(outdir, exist_ok=True)
    cv = draw_page()
    path = os.path.join(outdir, "entry.png")
    n = write_png(cv, path)
    print("wrote %s (%d bytes)" % (path, n))


if __name__ == "__main__":
    main()
