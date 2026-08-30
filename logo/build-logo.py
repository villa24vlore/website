from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen

BOLD = "/System/Library/Fonts/Supplemental/Georgia Bold.ttf"
REG  = "/System/Library/Fonts/Supplemental/Georgia.ttf"

class Face:
    def __init__(self, path):
        self.f = TTFont(path)
        self.gs = self.f.getGlyphSet()
        self.cmap = self.f.getBestCmap()
        self.upm = self.f['head'].unitsPerEm
        os2 = self.f['OS/2']
        self.cap = getattr(os2, 'sCapHeight', None) or int(self.upm * 0.7)
        self.kern = {}
        if 'kern' in self.f:
            for st in self.f['kern'].kernTables:
                self.kern.update(st.kernTable)

    def glyph(self, ch):
        return self.cmap[ord(ch)]

    def adv(self, ch):
        return self.f['hmtx'][self.glyph(ch)][0]

    def path(self, ch):
        pen = SVGPathPen(self.gs)
        self.gs[self.glyph(ch)].draw(pen)
        return pen.getCommands()

    def kpair(self, a, b):
        return self.kern.get((self.glyph(a), self.glyph(b)), 0)

def runs_to_svg(face, runs, size, x0, baseline, tracking=0.0, word_gap=0.0):
    """runs = [(text, colour)]; word_gap is inserted BETWEEN runs (flex gap)."""
    s = size / face.upm
    out, x = [], x0
    flat = "".join(t for t, _ in runs)
    i = 0
    for ri, (text, colour) in enumerate(runs):
        if ri:
            x += word_gap
        for ch in text:
            d = face.path(ch)
            if d:
                out.append(
                    f'<path fill="{colour}" transform="translate({x:.3f} {baseline:.3f}) '
                    f'scale({s:.6f} {-s:.6f})" d="{d}"/>'
                )
            x += face.adv(ch) * s
            nxt = flat[i + 1] if i + 1 < len(flat) else None
            if nxt is not None:
                x += face.kpair(ch, nxt) * s
            x += tracking
            i += 1
    return "\n  ".join(out), x - x0

def measure(face, text, size, tracking=0.0):
    s = size / face.upm
    w = 0.0
    for i, ch in enumerate(text):
        w += face.adv(ch) * s
        if i + 1 < len(text):
            w += face.kpair(ch, text[i + 1]) * s
        w += tracking
    return w - (tracking if text else 0)

bold, reg = Face(BOLD), Face(REG)

# --- geometry taken 1:1 from the site's CSS -------------------------------
D        = 38.0          # .logo .mark  width/height
R        = D / 2
GAP      = 10.0          # .logo gap
WORD_SZ  = 21.6          # 1.35rem
MARK_SZ  = 13.6          # .85rem
TRACK    = 0.03 * MARK_SZ  # letter-spacing .03em

DEEP, GOLD, GOLD_INK, WHITE = "#23022e", "#aa78a6", "#8d648a", "#ffffff"

def badge(bg, fg, cx=R, cy=R):
    w = measure(bold, "V24", MARK_SZ, TRACK)
    base = cy + (bold.cap * MARK_SZ / bold.upm) / 2
    frag, _ = runs_to_svg(bold, [("V24", fg)], MARK_SZ, cx - w / 2, base, TRACK)
    return (f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="{bg}"/>\n  ' + frag), w

def lockup(path, face, villa_col, num_col, bg_circle, bg_text, bg=None, size=WORD_SZ):
    base = R + (face.cap * size / face.upm) / 2
    mark, _ = badge(bg_circle, bg_text)
    word, wadv = runs_to_svg(face, [("Villa", villa_col), ("24", num_col)], size, D + GAP, base, word_gap=GAP)
    w = D + GAP + wadv
    rect = f'<rect width="{w:.2f}" height="{D}" fill="{bg}"/>\n  ' if bg else ""
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.2f} {D}" '
           f'width="{w:.2f}" height="{D}" role="img" aria-label="Villa 24">\n  '
           f'<title>Villa 24</title>\n  {rect}{mark}\n  {word}\n</svg>\n')
    open(path, "w").write(svg)
    return w

def markonly(path, bg, fg, pad=0.0):
    frag, _ = badge(bg, fg, R + pad, R + pad)
    side = D + pad * 2
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {side} {side}" '
           f'width="{side}" height="{side}" role="img" aria-label="Villa 24">\n  '
           f'<title>Villa 24</title>\n  {frag}\n</svg>\n')
    open(path, "w").write(svg)

def wordonly(path, face, villa_col, num_col, size=WORD_SZ, runs=None, wgap=GAP):
    asc = face.f['hhea'].ascent * size / face.upm
    desc = abs(face.f['hhea'].descent) * size / face.upm
    frag, w = runs_to_svg(face, runs or [("Villa", villa_col), ("24", num_col)], size, 0, asc, word_gap=wgap)
    h = asc + desc
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.2f} {h:.2f}" '
           f'width="{w:.2f}" height="{h:.2f}" role="img" aria-label="Villa 24">\n  '
           f'<title>Villa 24</title>\n  {frag}\n</svg>\n')
    open(path, "w").write(svg)

import sys
out = sys.argv[1]
w1 = lockup(f"{out}/villa24-logo.svg",      bold, DEEP,  GOLD_INK, DEEP, GOLD)
w2 = lockup(f"{out}/villa24-logo-dark.svg", bold, WHITE, GOLD,     WHITE, DEEP)
markonly(f"{out}/villa24-mark.svg",      DEEP, GOLD)
markonly(f"{out}/villa24-mark-dark.svg", WHITE, DEEP)
markonly(f"{out}/favicon.svg",           DEEP, GOLD, pad=3.0)
wordonly(f"{out}/villa24-wordmark.svg",      bold, DEEP,  GOLD_INK)
wordonly(f"{out}/villa24-wordmark-dark.svg", reg, WHITE, GOLD, size=22.4,
         runs=[("Villa ", WHITE), ("24", GOLD)], wgap=0.0)
print(f"lockup chiaro: {w1:.1f}x{D}  ·  lockup scuro: {w2:.1f}x{D}")
print(f"capHeight bold={bold.cap} reg={reg.cap} upm={bold.upm}  kern pairs: {len(bold.kern)}")

# ---- lockup quadrato (profili: Booking.com, Instagram, Google Business) ----
def square(path, side, villa_col, num_col, circ_bg, circ_fg, bg=None, face=bold):
    d    = side * 0.344                 # diametro badge
    r    = d / 2
    wsz  = side * 0.1484                # corpo wordmark
    msz  = d * 0.3579                   # testo badge, stessa proporzione del sito
    trk  = 0.03 * msz
    cap  = face.cap * wsz / face.upm
    gap  = side * 0.078
    top  = (side - (d + gap + cap)) / 2
    cy   = top + r
    base = top + d + gap + cap

    mw = measure(bold, "V24", msz, trk)
    mbase = cy + (bold.cap * msz / bold.upm) / 2
    mark, _ = runs_to_svg(bold, [("V24", circ_fg)], msz, side/2 - mw/2, mbase, trk)

    ww = measure(face, "Villa", wsz) + gap*0.55 + measure(face, "24", wsz)
    word, _ = runs_to_svg(face, [("Villa", villa_col), ("24", num_col)], wsz,
                          side/2 - ww/2, base, word_gap=gap*0.55)

    rect = f'<rect width="{side}" height="{side}" fill="{bg}"/>\n  ' if bg else ""
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {side} {side}" '
           f'width="{side}" height="{side}" role="img" aria-label="Villa 24">\n  '
           f'<title>Villa 24</title>\n  {rect}'
           f'<circle cx="{side/2}" cy="{cy:.2f}" r="{r:.2f}" fill="{circ_bg}"/>\n  '
           f'{mark}\n  {word}\n</svg>\n')
    open(path, "w").write(svg)

square(f"{out}/villa24-square-light.svg", 512, DEEP,  GOLD_INK, DEEP,  GOLD, bg="#ffffff")
square(f"{out}/villa24-square-dark.svg",  512, WHITE, GOLD,     WHITE, DEEP, bg=DEEP)
print("quadrati 512x512 generati")
