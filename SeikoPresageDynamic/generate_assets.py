#!/usr/bin/env python3
"""Procedurally generates every PNG layer of the watch face + preview_4states.png.

    python3 generate_assets.py

All layers are 450x450 RGBA, centred on the dial centre (225,225). They are drawn
4x supersampled and downscaled with LANCZOS for clean anti-aliased edges.

Layers are authored as WHITE / GREY artwork so that WFF `tintColor` (which multiplies
the artwork colour) can recolour them per time of day:
    white  facet  -> exactly the tint colour
    grey   facet  -> a darker shade of the tint colour (the "shadow" facet)
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import *  # noqa: E402,F403

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "app", "src", "main", "res", "drawable-nodpi")
SS = 4                      # supersampling factor
BIG = SIZE * SS
C = CX * SS

LIGHT, SHADE = 255, 140     # facet brightness (multiplied by tint colour)


# ----------------------------------------------------------------------------- helpers
def pol(theta_deg, r, off=0.0):
    """Point at radius r (outward) and lateral offset off, on the ray theta (0 = 12 o'clock, clockwise)."""
    t = math.radians(theta_deg)
    x = CX + r * math.sin(t) + off * math.cos(t)
    y = CY - r * math.cos(t) + off * math.sin(t)
    return (x * SS, y * SS)


def canvas():
    img = Image.new("RGBA", (BIG, BIG), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def finish(img, name):
    out = img.resize((SIZE, SIZE), Image.LANCZOS)
    os.makedirs(OUT, exist_ok=True)
    out.save(os.path.join(OUT, name), optimize=True)
    return out


def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def tint(img, color):
    """Multiply-tint, same maths the preview assumes for WFF tintColor."""
    r, g, b = hex2rgb(color)
    a = np.asarray(img.convert("RGBA")).astype(np.float32)
    a[..., 0] *= r / 255.0
    a[..., 1] *= g / 255.0
    a[..., 2] *= b / 255.0
    return Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGBA")


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


# ----------------------------------------------------------------------------- layers
def dial_sunburst():
    """Fine radial brushed texture as a white/black alpha OVERLAY (sits on the coloured base disc)."""
    n = BIG                                        # computed 4x supersampled -> no moire
    y, x = np.mgrid[0:n, 0:n].astype(np.float32)
    x = (x + 0.5) / SS - CX
    y = (y + 0.5) / SS - CY
    r = np.hypot(x, y)
    th = np.arctan2(x, -y)                         # 0 at 12 o'clock, clockwise

    lines = 300
    saw = (th / (2 * math.pi) * lines) % 1.0
    tri = 1 - np.abs(2 * saw - 1) * 2              # triangle wave in [-1, 1]
    tri = np.sign(tri) * np.abs(tri) ** 0.7        # crisper, a bit more "engraved"

    amp = 0.55 * smoothstep(28, 120, r)            # lines converge softly, no moire at the centre
    # broad light catching sectors (two soft glints, like the reference photo)
    glint = 0.34 * np.cos(th - math.radians(-35)) ** 3 + 0.22 * np.cos(th - math.radians(150)) ** 3
    glint *= smoothstep(0, 90, r)
    L = 0.5 + 0.5 * amp * tri * 0.55 + glint * 0.30

    white_a = np.clip((L - 0.5) * 2, 0, 1) * 0.62
    black_a = np.clip((0.5 - L) * 2, 0, 1) * 0.50
    vig = smoothstep(140, 225, r) ** 1.4 * 0.30     # vignette towards the rim
    black_a = np.clip(black_a + vig, 0, 1)

    rgba = np.zeros((n, n, 4), np.float32)
    is_w = white_a >= black_a
    rgba[..., :3] = np.where(is_w[..., None], 255.0, 0.0)
    rgba[..., 3] = np.where(is_w, white_a, black_a) * 255
    rgba[..., 3] *= (r <= CX).astype(np.float32)
    img = Image.fromarray(rgba.clip(0, 255).astype(np.uint8), "RGBA")
    return finish(img, "dial_sunburst.png")


def minute_track():
    img, d = canvas()
    for m in range(60):
        th = m * 6
        if m % 5 == 0:
            a, b, w = pol(th, TRACK_R_OUT - 15), pol(th, TRACK_R_OUT), 2.6
        else:
            a, b, w = pol(th, TRACK_R_OUT - 8), pol(th, TRACK_R_OUT), 1.4
        d.line([a, b], fill=(255, 255, 255, 255), width=int(w * SS))
    return finish(img, "minute_track.png")


def _dagger(theta, off=0.0, hw=INDEX_HALF_W, scale_w=1.0):
    """Kite (dagger) outline split into (left facet, right facet, full outline)."""
    hw = hw * scale_w
    tip_in = pol(theta, INDEX_R_IN, off)
    sh_l = pol(theta, INDEX_R_SHOULDER, off - hw)
    sh_r = pol(theta, INDEX_R_SHOULDER, off + hw)
    tip_out = pol(theta, INDEX_R_OUT, off)
    return [tip_in, sh_l, tip_out], [tip_in, tip_out, sh_r], [tip_in, sh_l, tip_out, sh_r]


def _index_shapes():
    shapes = []
    for h in INDEX_HOURS:
        th = h * 30 % 360
        if h == 12:   # double / wide wedge at 12
            shapes.append(_dagger(th, off=-8.0, hw=5.2))
            shapes.append(_dagger(th, off=+8.0, hw=5.2))
        else:
            shapes.append(_dagger(th))
    return shapes


def indices_frame():
    img, d = canvas()
    for _, _, outline in _index_shapes():
        d.line(outline + [outline[0]], fill=(255, 255, 255, 255), width=int(1.7 * SS), joint="curve")
    return finish(img, "indices_frame.png"), _index_shapes()


def indices_fill():
    img, d = canvas()
    for left, right, _ in _index_shapes():
        d.polygon(left, fill=(LIGHT, LIGHT, LIGHT, 255))
        d.polygon(right, fill=(SHADE, SHADE, SHADE, 255))
    return finish(img, "indices_fill.png")


def _blade(tail, length, shoulder_r, half_w):
    """Dauphine blade in local (r, off) coords pointing up: returns (left facet, right facet)."""
    tail_w = half_w * 0.45
    left = [(-tail, 0), (-tail * 0.45, -tail_w), (shoulder_r, -half_w), (length, 0)]
    right = [(-tail, 0), (length, 0), (shoulder_r, half_w), (-tail * 0.45, tail_w)]
    return left, right


def _hand(name, tail, length, shoulder_r, half_w):
    img, d = canvas()
    left, right = _blade(tail, length, shoulder_r, half_w)
    # drop shadow (very soft, keeps the hand legible over the sunburst)
    sh = Image.new("RGBA", (BIG, BIG), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    for facet in (left, right):
        sd.polygon([pol(0, r, o + 1.3) for r, o in facet], fill=(0, 0, 0, 70))
    img.alpha_composite(sh)
    d.polygon([pol(0, r, o) for r, o in left], fill=(LIGHT, LIGHT, LIGHT, 255))
    d.polygon([pol(0, r, o) for r, o in right], fill=(SHADE, SHADE, SHADE, 255))
    return finish(img, name)


def hand_hour():
    return _hand("hand_hour.png", tail=24, length=116, shoulder_r=26, half_w=8.0)


def hand_minute():
    return _hand("hand_minute.png", tail=26, length=188, shoulder_r=34, half_w=6.0)


def hand_second():
    img, d = canvas()
    w = int(1.6 * SS)
    d.line([pol(0, -26), pol(0, 206)], fill=(255, 255, 255, 255), width=w)
    # diamond counterweight on the tail
    dia = [pol(0, -50), pol(0, -37, -5.5), pol(0, -24), pol(0, -37, 5.5)]
    d.polygon(dia, fill=(255, 255, 255, 255))
    # centre cap
    rr = 4.6 * SS
    d.ellipse([C - rr, C - rr, C + rr, C + rr], fill=(255, 255, 255, 255))
    hole = 1.7 * SS
    d.ellipse([C - hole, C - hole, C + hole, C + hole], fill=(40, 40, 40, 255))
    return finish(img, "hand_second.png")


def date_frame():
    img, d = canvas()
    cx, cy, w, h = DATE_BOX["cx"], DATE_BOX["cy"], DATE_BOX["w"], DATE_BOX["h"]
    x0, y0, x1, y1 = (cx - w / 2) * SS, (cy - h / 2) * SS, (cx + w / 2) * SS, (cy + h / 2) * SS
    # polished silver bezel with vertical gradient
    bez = Image.new("RGBA", (BIG, BIG), (0, 0, 0, 0))
    grad = np.zeros((BIG, BIG, 4), np.uint8)
    ys = np.linspace(0, 1, BIG)[:, None]
    shade = (232 - 120 * ys).repeat(BIG, axis=1)
    grad[..., :3] = shade[..., None].astype(np.uint8)
    grad[..., 3] = 255
    mask = Image.new("L", (BIG, BIG), 0)
    ImageDraw.Draw(mask).rectangle([x0, y0, x1, y1], fill=255)
    bez = Image.fromarray(grad, "RGBA")
    bez.putalpha(mask)
    img.alpha_composite(bez)
    # white date disc window
    inset = 3.2 * SS
    d.rectangle([x0 + inset, y0 + inset, x1 - inset, y1 - inset], fill=(244, 244, 240, 255))
    # inner top shadow
    d.rectangle([x0 + inset, y0 + inset, x1 - inset, y0 + inset + 2.4 * SS], fill=(190, 190, 186, 255))
    # fine dark outline
    d.rectangle([x0, y0, x1, y1], outline=(60, 60, 64, 255), width=int(0.9 * SS))
    return finish(img, "date_frame.png")


def _font(path, size):
    return ImageFont.truetype(path, int(size * SS))


def _spaced(draw, text, y, font, spacing, fill):
    widths = [draw.textlength(ch, font=font) for ch in text]
    total = sum(widths) + spacing * SS * (len(text) - 1)
    x = C - total / 2
    for ch, wd in zip(text, widths):
        draw.text((x, y * SS), ch, font=font, fill=fill, anchor="ls")
        x += wd + spacing * SS


def logo():
    """SEIKO / PRESAGE / AUTOMATIC lettering (white, tinted with the hands colour)."""
    img, d = canvas()
    serif = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
    sans = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
    _spaced(d, "SEIKO", LOGO_SEIKO_Y + 6, _font(serif, 19), 1.6, (255, 255, 255, 255))
    _spaced(d, "PRESAGE", LOGO_PRESAGE_Y + 4, _font(serif, 11.5), 1.1, (255, 255, 255, 255))
    _spaced(d, "AUTOMATIC", LOGO_AUTO_Y + 3, _font(sans, 7.4), 1.3, (255, 255, 255, 255))
    return finish(img, "logo.png")


# ----------------------------------------------------------------------------- preview
def _load(name):
    return Image.open(os.path.join(OUT, name)).convert("RGBA")


def rotate_about_center(img, deg):
    return img.rotate(-deg, resample=Image.BICUBIC, center=(CX, CY))


def draw_arc(img, cx, cy, d, a0, a1, color, width, alpha=255):
    """WFF-style arc: angles in degrees, 0 = 12 o'clock, clockwise."""
    layer = Image.new("RGBA", (BIG, BIG), (0, 0, 0, 0))
    dr = ImageDraw.Draw(layer)
    r = d / 2 * SS
    box = [cx * SS - r, cy * SS - r, cx * SS + r, cy * SS + r]
    # PIL angles: 0 = 3 o'clock, clockwise -> subtract 90
    dr.arc(box, a0 - 90, a1 - 90, fill=hex2rgb(color) + (alpha,), width=int(width * SS))
    img.alpha_composite(layer.resize((SIZE, SIZE), Image.LANCZOS))


def text_center(img, xy, s, size, color, bold=False):
    path = "/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf" % ("-Bold" if bold else "")
    f = ImageFont.truetype(path, size * 2)
    big = Image.new("RGBA", (SIZE * 2, SIZE * 2), (0, 0, 0, 0))
    ImageDraw.Draw(big).text((xy[0] * 2, xy[1] * 2), s, font=f, fill=hex2rgb(color) + (255,), anchor="mm")
    img.alpha_composite(big.resize((SIZE, SIZE), Image.LANCZOS))


def render_face(theme, layers, hh=10, mm=8, ss=35, day=17, batt=72, steps=5640, temp="21°", ambient=False):
    if ambient:
        img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 255))
        frame_c, hand_c = "#C8C8C8", "#E0E0E0"
        img.alpha_composite(tint(layers["indices_frame"], frame_c))
        h_ang = (hh % 12 + mm / 60) * 30
        img.alpha_composite(rotate_about_center(tint(layers["hand_hour"], hand_c), h_ang))
        img.alpha_composite(rotate_about_center(tint(layers["hand_minute"], hand_c), mm * 6))
        return img
    img = Image.new("RGBA", (SIZE, SIZE), hex2rgb(theme["base"]) + (255,))
    img.alpha_composite(layers["dial_sunburst"])
    img.alpha_composite(tint(layers["minute_track"], theme["frame"]))
    img.alpha_composite(tint(layers["indices_fill"], theme["fill"]))
    img.alpha_composite(tint(layers["indices_frame"], theme["frame"]))
    img.alpha_composite(tint(layers["logo"], theme["hands"]))
    img.alpha_composite(layers["date_frame"])
    text_center(img, (DATE_BOX["cx"], DATE_BOX["cy"] + 1), str(day), 22, "#16161A")
    # battery half-moon (left half of the sub-dial), progress along 180 -> 360
    b = BATTERY
    draw_arc(img, b["cx"], b["cy"], b["d"], 180, 360, theme["hands"], 2.0, 70)
    draw_arc(img, b["cx"], b["cy"], b["d"], 180, 180 + 1.8 * batt, theme["hands"], 3.0)
    text_center(img, (b["cx"], b["cy"]), "%d%%" % batt, 11, theme["hands"])
    # step ring
    s = STEPS
    draw_arc(img, s["cx"], s["cy"], s["d"], 0, 359.9, theme["hands"], 1.4, 70)
    draw_arc(img, s["cx"], s["cy"], s["d"], 0, 360 * min(steps / STEP_GOAL, 1), theme["hands"], 3.0)
    text_center(img, (s["cx"], s["cy"]), str(steps), 10.5, theme["hands"])
    text_center(img, (TEMP["cx"], TEMP["cy"]), temp, 18, theme["hands"])
    h_ang = (hh % 12 + mm / 60) * 30
    m_ang = (mm + ss / 60) * 6
    s_ang = ss * 6
    img.alpha_composite(rotate_about_center(tint(layers["hand_hour"], theme["hands"]), h_ang))
    img.alpha_composite(rotate_about_center(tint(layers["hand_minute"], theme["hands"]), m_ang))
    img.alpha_composite(rotate_about_center(tint(layers["hand_second"], theme["second"]), s_ang))
    return img


def circle_crop(img, bg=(16, 16, 20)):
    mask = Image.new("L", (SIZE * 4, SIZE * 4), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, SIZE * 4 - 1, SIZE * 4 - 1], fill=255)
    mask = mask.resize((SIZE, SIZE), Image.LANCZOS)
    out = Image.new("RGB", (SIZE, SIZE), bg)
    out.paste(img.convert("RGB"), (0, 0), mask)
    return out


def build_preview():
    names = ["dial_sunburst", "minute_track", "indices_frame", "indices_fill", "hand_hour",
             "hand_minute", "hand_second", "date_frame", "logo"]
    layers = {n: _load(n + ".png") for n in names}
    pad, head = 24, 34
    cell = SIZE
    sheet = Image.new("RGB", (pad * 3 + cell * 2, head + pad * 3 + cell * 2 + head), (16, 16, 20))
    d = ImageDraw.Draw(sheet)
    lab = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 17)
    for i, th in enumerate(THEMES):
        col, row = i % 2, i // 2
        x = pad + col * (cell + pad)
        y = head // 2 + pad + row * (cell + pad + head // 2)
        d.text((x + cell // 2, y - 2), "%s  (%s)" % (th["label"], th["base"]), font=lab, fill=(235, 235, 235), anchor="mb")
        sheet.paste(circle_crop(render_face(th, layers)), (x, y))
    sheet.save(os.path.join(HERE, "preview_4states.png"), optimize=True)
    # watch-face picker thumbnail (res/drawable-nodpi/preview.png, referenced by xml/watch_face_info.xml)
    thumb = circle_crop(render_face(THEMES[0], layers), bg=(0, 0, 0)).convert("RGBA")
    m = Image.new("L", (SIZE * 4, SIZE * 4), 0)
    ImageDraw.Draw(m).ellipse([0, 0, SIZE * 4 - 1, SIZE * 4 - 1], fill=255)
    thumb.putalpha(m.resize((SIZE, SIZE), Image.LANCZOS))
    thumb.save(os.path.join(OUT, "preview.png"), optimize=True)
    # always-on (ambient) preview
    amb = circle_crop(render_face(THEMES[0], layers, ambient=True))
    amb.save(os.path.join(HERE, "preview_ambient.png"), optimize=True)


def main():
    dial_sunburst()
    minute_track()
    indices_frame()
    indices_fill()
    hand_hour()
    hand_minute()
    hand_second()
    date_frame()
    logo()
    build_preview()
    for f in sorted(os.listdir(OUT)):
        im = Image.open(os.path.join(OUT, f))
        print("%-20s %s %s %6d B" % (f, im.size, im.mode, os.path.getsize(os.path.join(OUT, f))))
    print("preview_4states.png / preview_ambient.png written")


if __name__ == "__main__":
    main()
