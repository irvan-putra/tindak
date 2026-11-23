#!/usr/bin/env python3
# Derived from the shared family generator (kokok/tools/badge_icon.py, itself
# from bidik). Same pinned geometry; only the Tindak art, palette and version
# source differ. No repo writes: outputs go to an out/ dir for the custodian.
"""Tindak launcher icon generator: check-arrow glyph plus the family version badge.

Deterministic. Same version in, same PNGs out. Pillow and DejaVu Sans Bold are
hash-pinned; the script fails instead of falling back, because a different
rasterizer or font changes the pixels.
    pip install pillow==12.3.0   (the font is vendored next to this script)

Glyph: a bold check mark whose long arm extends into an arrowhead, pointing
up-right - a task being acted on, not just listed. Single flat accent colour
so it survives mdpi at 48px.

Badge: numbers only, a full-width strip across the bottom 24% of the icon.
Outputs match the com.vanipy family standard:
- legacy mipmap PNGs per density (rounded-square, strip)
- ic_launcher_round per density
- adaptive foreground + themed monochrome (432px), numbers cut out of the strip
- mipmap-anydpi-v26 XML and background colour
- webxdc 256px icon
"""
import hashlib, math, os, re, shutil, sys, tempfile
import PIL
from PIL import Image, ImageChops, ImageDraw, ImageFont

PILLOW_PIN = "12.3.0"
HERE = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(HERE, "assets", "fonts", "DejaVuSans-Bold.ttf")
FONT_SHA256 = "d1c3ff99f1e1ce1827a33efd4dad81f40babda06bff9e43bd7591c86662a287b"
DENSITIES = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}
S = 768
STRIP_TOP = 0.76      # strip covers 76%..100% of the icon height
TEXT_SIZE = 0.115     # numeral size, fraction of icon size
SAFE_R = 0.485        # picture and text must stay inside this radius (fraction)

if PIL.__version__ != PILLOW_PIN:
    sys.exit("Pillow %s required, found %s" % (PILLOW_PIN, PIL.__version__))


def font(px):
    if not os.path.exists(FONT_PATH):
        sys.exit("missing font " + FONT_PATH)
    if hashlib.sha256(open(FONT_PATH, "rb").read()).hexdigest() != FONT_SHA256:
        sys.exit("unexpected font file " + FONT_PATH)
    return ImageFont.truetype(FONT_PATH, px)


def circle_mask(size, r=SAFE_R):
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).ellipse([size * (.5 - r), size * (.5 - r), size * (.5 + r), size * (.5 + r)], fill=255)
    return m


def assert_inside_circle(layer, what, size=S, r=SAFE_R):
    alpha = layer.getchannel("A").point(lambda v: 255 if v > 8 else 0)
    outside = ImageChops.multiply(alpha, ImageChops.invert(circle_mask(size, r)))
    box = outside.getbbox()
    if box:
        sys.exit("%s leaves the round-mask safe circle at %s" % (what, box))


def new_layer(size=S):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def compose(bg, art, version, strip, text, rounded=None, size=S, circle_check=True):
    """Background, then the picture layer, then the badge strip."""
    if circle_check:
        assert_inside_circle(art, "picture", size)
    base = Image.new("RGBA", (size, size), bg) if bg else Image.new("RGBA", (size, size), (0, 0, 0, 0))
    base.alpha_composite(art)
    d = ImageDraw.Draw(base)
    y0 = int(size * STRIP_TOP)
    d.rectangle([0, y0, size, size], fill=strip)
    tl, td = new_layer(size)
    f = font(int(size * TEXT_SIZE))
    td.text((size / 2, (y0 + size) / 2), version, font=f, fill=text, anchor="mm")
    if circle_check:
        assert_inside_circle(tl, "version text", size)
    base.alpha_composite(tl)
    if rounded:
        m = Image.new("L", (size, size), 0)
        ImageDraw.Draw(m).rounded_rectangle([0, 0, size - 1, size - 1], radius=rounded * size, fill=255)
        base.putalpha(ImageChops.multiply(base.getchannel("A"), m))
    return base


def write_densities(img, res_dir, name="ic_launcher.png"):
    for dens, px in DENSITIES.items():
        out = os.path.join(res_dir, "mipmap-" + dens)
        os.makedirs(out, exist_ok=True)
        img.resize((px, px), Image.LANCZOS).save(os.path.join(out, name), optimize=True)


# Family palette (shared with intodo/kokok): dark navy face, darker strip.
TINDAK_BG = (16, 24, 40, 255)       # #101828
TINDAK_STRIP = (8, 12, 22, 255)     # #080C16
TINDAK_TEXT = (245, 248, 252, 255)
TINDAK_ACCENT = (245, 158, 11, 255) # family amber, carried over from intodo


def tindak_art():
    """Bold check mark; the long arm ends in an arrowhead pointing up-right."""
    art, d = new_layer()
    w = 74  # stroke width
    p0 = (246.0, 372.0)   # short-arm start
    p1 = (340.0, 466.0)   # vertex
    p2 = (596.0, 214.0)   # arm end (base of arrowhead)
    ux, uy = p2[0] - p1[0], p2[1] - p1[1]
    n = math.hypot(ux, uy)
    ux, uy = ux / n, uy / n          # arm direction
    px, py = -uy, ux                 # perpendicular
    # rounded caps at start and vertex
    d.ellipse([p0[0] - w / 2, p0[1] - w / 2, p0[0] + w / 2, p0[1] + w / 2], fill=TINDAK_ACCENT)
    d.ellipse([p1[0] - w / 2, p1[1] - w / 2, p1[0] + w / 2, p1[1] + w / 2], fill=TINDAK_ACCENT)
    d.line([p0, p1], fill=TINDAK_ACCENT, width=w)
    d.line([p1, p2], fill=TINDAK_ACCENT, width=w)
    # arrowhead: tip extended along the arm, base spread perpendicular
    tip = (p2[0] + ux * 66, p2[1] + uy * 66)
    back = (p2[0] - ux * 40, p2[1] - uy * 40)
    half = 62
    c1 = (back[0] + px * half, back[1] + py * half)
    c2 = (back[0] - px * half, back[1] - py * half)
    d.polygon([tip, c1, c2], fill=TINDAK_ACCENT)
    return art


def tindak(version):
    return compose(TINDAK_BG, tindak_art(), version, TINDAK_STRIP, TINDAK_TEXT, rounded=.2)


ADAPTIVE_XML = """<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/ic_launcher_background" />
    <foreground android:drawable="@drawable/ic_launcher_foreground" />
    <monochrome android:drawable="@drawable/ic_launcher_monochrome" />
</adaptive-icon>
"""

COLORS_XML = """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="ic_launcher_background">#101828</color>
</resources>
"""


def tindak_adaptive(version):
    """Foreground + monochrome layers with the family strip on the face.

    The 72dp face is 576px centred on the 108dp 864px layer (18dp overscan).
    Strip and text use the same 76%/88%/11.5% face geometry as the legacy
    icon, so masked and unmasked launchers show the same badge. The themed
    numbers are cut out of the strip for contrast.
    """
    T, F, I = 864, 576, 144
    art = tindak_art().resize((F, F), Image.LANCZOS)
    fg, d = new_layer(T)
    fg.alpha_composite(art, (I, I))
    y = I + int(F * STRIP_TOP)
    d.rectangle([0, y, T, T], fill=TINDAK_STRIP)
    text, td = new_layer(T)
    td.text((T / 2, I + F * .88), version, font=font(int(F * TEXT_SIZE)),
            fill=(255, 255, 255, 255), anchor="mm")
    fg.alpha_composite(text)
    alpha = Image.new("L", (T, T), 0)
    alpha.paste(art.getchannel("A"), (I, I))
    ImageDraw.Draw(alpha).rectangle([0, y, T, T], fill=255)
    alpha = ImageChops.subtract(alpha, text.getchannel("A"))
    mono = Image.new("RGBA", (T, T), (255, 255, 255, 255))
    mono.putalpha(alpha)
    return fg, mono


def write_all(version, res_dir):
    """Single launcher icon (family rule, Irvan 2026-11-23): one 192px full-color PNG at
    res/drawable/ic_launcher.png. No density ladder, no adaptive XML, no monochrome layer."""
    out = os.path.join(res_dir, "drawable")
    os.makedirs(out, exist_ok=True)
    tindak(version).resize((192, 192), Image.LANCZOS).save(os.path.join(out, "ic_launcher.png"), optimize=True)
    for stale in ("mipmap-mdpi", "mipmap-hdpi", "mipmap-xhdpi", "mipmap-xxhdpi", "mipmap-xxxhdpi",
                  "mipmap-anydpi-v26", "drawable-xxxhdpi"):
        shutil.rmtree(os.path.join(res_dir, stale), ignore_errors=True)


def main():
    root = os.path.dirname(HERE)
    gradle = open(os.path.join(root, 'app/build.gradle')).read()
    version = sys.argv[1] if len(sys.argv) > 1 else re.search(r"versionName '([^']+)'", gradle).group(1)
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        sys.exit('version must be X.Y.Z')
    write_all(version, os.path.join(root, 'app/src/main/res'))
    print('wrote native tindak icons for', version)


if __name__ == "__main__":
    main()
