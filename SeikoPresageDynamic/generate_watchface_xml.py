#!/usr/bin/env python3
"""Generates app/src/main/res/raw/watchface.xml (Watch Face Format v2).

Why generated: the four time-of-day themes are four copies of the same layer stack that
differ only by colours and by the alpha expression that cross-fades them, so a script
keeps them identical and makes colour tweaks a one-line change in config.py.

Cross-fade design (100 % schema-valid, no <Condition>, no tint expressions):
  * Each theme is a <Group> whose alpha is driven by [HOUR_0_23_MINUTE].
  * Stack order bottom->top: morning (always opaque), noon, evening, night.
  * noon    fades in at 11:00 (+-30 min) and stays on top of morning,
    evening fades in at 17:00,
    night   fades in at 20:00 and fades OUT at 06:00 revealing morning again.
  Because every upper layer is a fully opaque dial, two-layer blends are exact (no colour leak).
"""
import os
import sys
from xml.sax.saxutils import quoteattr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import *  # noqa: E402,F403

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "app", "src", "main", "res", "raw", "watchface.xml")

T = "[HOUR_0_23_MINUTE]"
H = FADE_HALF_HOURS
ST = {t["key"]: t["start"] for t in THEMES}


def ramp(start):
    """0 -> 1 across [start-H, start+H] (hours)."""
    return "clamp(%s-%s,0,1)" % (T, fmt(start - H))


def fmt(v):
    return ("%g" % v)


# alpha (0-255) of each group in the stack
ALPHA = {
    "morning": None,  # always opaque base
    "noon": "255*" + ramp(ST["noon"]),
    "evening": "255*" + ramp(ST["evening"]),
    # night: 1 before 05:30, fades to 0 over 06:00, fades back to 1 around 20:00
    "night": "255*(1-%s+%s)" % (ramp(ST["morning"]), ramp(ST["night"])),
}
# final visible weight of every theme (used for the single complication slot, which can't be duplicated)
_n = "(1-%s+%s)" % (ramp(ST["morning"]), ramp(ST["night"]))
_e = ramp(ST["evening"])
_o = ramp(ST["noon"])
WEIGHT = {
    "night": _n,
    "evening": "(1-%s)*%s" % (_n, _e),
    "noon": "(1-%s)*(1-%s)*%s" % (_n, _e, _o),
    "morning": "(1-%s)*(1-%s)*(1-%s)" % (_n, _e, _o),
}

W = SIZE
FULL = 'x="0" y="0" width="%d" height="%d"' % (W, W)


def a(name, val):
    return "%s=%s" % (name, quoteattr(str(val)))


def part_image(resource, tint=None, name=None, indent=""):
    t = ' tintColor="%s"' % tint if tint else ""
    n = ' name="%s"' % name if name else ""
    return '%s<PartImage %s%s%s>\n%s  <Image resource="%s"/>\n%s</PartImage>\n' % (indent, FULL, n, t, indent, resource, indent)


def text(x, y, w, h, template, expr, size, color, weight="NORMAL", indent="", name=None, extra="", spacing=None):
    n = ' name="%s"' % name if name else ""
    ls = ' letterSpacing="%s"' % spacing if spacing is not None else ""
    return (
        '{i}<PartText x="{x}" y="{y}" width="{w}" height="{h}"{n}{extra}>\n'
        '{i}  <Text align="CENTER">\n'
        '{i}    <Font family="SYNC_TO_DEVICE" size="{size}" color="{color}" weight="{weight}"{ls}>\n'
        '{i}      <Template>{tpl}<Parameter expression="{expr}"/></Template>\n'
        '{i}    </Font>\n'
        '{i}  </Text>\n'
        '{i}</PartText>\n'
    ).format(i=indent, x=x, y=y, w=w, h=h, n=n, extra=extra, size=size, color=color, weight=weight, ls=ls, tpl=template, expr=expr)


def arc(cx, cy, d, start, end, color, thickness, alpha=None, end_expr=None, indent=""):
    tr = '%s  <Transform target="endAngle" value="%s"/>\n' % (indent, end_expr) if end_expr else ""
    al = ""
    if alpha is not None:
        al = ""  # alpha is applied through the colour's alpha channel (#AARRGGBB)
    col = color if alpha is None else "#%02X%s" % (alpha, color.lstrip("#"))
    return (
        '{i}<Arc centerX="{cx}" centerY="{cy}" width="{d}" height="{d}" startAngle="{s}" endAngle="{e}" direction="CLOCKWISE">\n'
        '{i}  <Stroke color="{col}" thickness="{t}" cap="ROUND"/>\n'
        '{tr}{i}</Arc>\n'
    ).format(i=indent, cx=cx, cy=cy, d=d, s=start, e=end, col=col, t=thickness, tr=tr)


def draw(inner, name=None, indent=""):
    n = ' name="%s"' % name if name else ""
    return '%s<PartDraw %s%s>\n%s%s</PartDraw>\n' % (indent, FULL, n, inner, indent)


def analog_clock(hands_color, second_color, indent, second=True, name="clock"):
    s = ""
    s += '%s<AnalogClock %s>\n' % (indent, FULL)
    hand = '%s  <%s resource="%s" %s pivotX="0.5" pivotY="0.5" tintColor="%s"/>\n'
    s += hand % (indent, "HourHand", "hand_hour", FULL, hands_color)
    s += hand % (indent, "MinuteHand", "hand_minute", FULL, hands_color)
    if second:
        s += ('%s  <SecondHand resource="hand_second" %s pivotX="0.5" pivotY="0.5" tintColor="%s">\n'
              '%s    <Sweep frequency="15"/>\n%s  </SecondHand>\n') % (indent, FULL, second_color, indent, indent)
    s += '%s</AnalogClock>\n' % indent
    return s


def theme_group(th):
    k = th["key"]
    i = "      "
    j = i + "  "
    s = '%s<Group name="theme_%s" %s alpha="%d">\n' % (i, k, FULL, 255 if ALPHA[k] is None else 255)
    if ALPHA[k] is not None:
        s += '%s<Transform target="alpha" value="%s"/>\n' % (j, ALPHA[k])
    s += '%s<Variant mode="AMBIENT" target="alpha" value="0"/>\n' % j

    # 1. dial: flat base colour + sunburst overlay (white/black alpha texture, needs no tint)
    s += draw('%s  <Ellipse x="0" y="0" width="%d" height="%d">\n%s    <Fill color="%s"/>\n%s  </Ellipse>\n' % (j, W, W, j, th["base"], j),
              name="dial_base_%s" % k, indent=j)
    s += part_image("dial_sunburst", name="sunburst_%s" % k, indent=j)
    s += part_image("minute_track", tint=th["frame"], name="track_%s" % k, indent=j)
    # 2. indices: fill (facet shaded) under frame
    s += part_image("indices_fill", tint=th["fill"], name="idx_fill_%s" % k, indent=j)
    s += part_image("indices_frame", tint=th["frame"], name="idx_frame_%s" % k, indent=j)
    # 3. lettering
    s += part_image("logo", tint=th["hands"], name="logo_%s" % k, indent=j)

    # 4. date (3 o'clock)
    d = DATE_BOX
    s += part_image("date_frame", name="date_frame_%s" % k, indent=j)
    s += text(d["cx"] - d["w"] // 2 + 4, d["cy"] - d["h"] // 2 + 4, d["w"] - 8, d["h"] - 8, "%d", "[DAY]", 23, "#FF16161A",
              weight="MEDIUM", indent=j, name="date_text_%s" % k)

    # 5. battery half-moon (9 o'clock): track + progress (left half: 180 -> 360 deg)
    b = BATTERY
    inner = arc(b["cx"], b["cy"], b["d"], 180, 360, th["hands"], 2, alpha=0x46, indent=j + "  ")
    inner += arc(b["cx"], b["cy"], b["d"], 180, 180, th["hands"], 3, end_expr="180+1.8*[BATTERY_PERCENT]", indent=j + "  ")
    s += draw(inner, name="battery_arc_%s" % k, indent=j)
    s += text(b["cx"] - 22, b["cy"] - 9, 44, 18, "%d%%", "[BATTERY_PERCENT]", 11, th["hands"], indent=j, name="battery_text_%s" % k)

    # 6. steps ring (6 o'clock) + goal arc
    st = STEPS
    inner = arc(st["cx"], st["cy"], st["d"], 0, 359.9, th["hands"], 1.4, alpha=0x46, indent=j + "  ")
    inner += arc(st["cx"], st["cy"], st["d"], 0, 0, th["hands"], 3, end_expr="3.6*clamp([STEP_PERCENT],0,100)", indent=j + "  ")
    s += draw(inner, name="steps_arc_%s" % k, indent=j)
    s += text(st["cx"] - 22, st["cy"] - 8, 44, 16, "%d", "[STEP_COUNT]", 10.5, th["hands"], indent=j, name="steps_text_%s" % k)

    # 7. hands (second hand on top)
    s += analog_clock(th["hands"], th["second"], j, second=True, name="clock_%s" % k)
    s += '%s</Group>\n' % i
    return s


def ambient_group():
    i = "      "
    j = i + "  "
    s = '%s<Group name="ambient" %s alpha="0">\n' % (i, FULL)
    s += '%s<Variant mode="AMBIENT" target="alpha" value="255"/>\n' % j
    s += part_image("indices_frame", tint="#C8C8C8", name="ambient_indices", indent=j)
    s += analog_clock("#E6E6E6", "#E6E6E6", j, second=False, name="ambient_clock")
    s += '%s</Group>\n' % i
    return s


def temperature_slot():
    t = TEMP
    i = "      "
    j = i + "  "
    s = ('%s<ComplicationSlot slotId="0" name="temperature" displayName="Temperature" supportedTypes="SHORT_TEXT" '
         'isCustomizable="TRUE" x="%d" y="%d" width="%d" height="%d">\n') % (i, t["cx"] - t["w"] // 2, t["cy"] - t["h"] // 2, t["w"], t["h"])
    s += '%s<Variant mode="AMBIENT" target="alpha" value="0"/>\n' % j
    # No weather provider exists in the WFF v2 DefaultProviderPolicy list -> start empty,
    # the wearer picks the Weather complication once (see INSTALL.md).
    s += '%s<DefaultProviderPolicy defaultSystemProvider="EMPTY" defaultSystemProviderType="EMPTY"/>\n' % j
    s += '%s<BoundingBox x="0" y="0" width="%d" height="%d"/>\n' % (j, t["w"], t["h"])
    s += '%s<Complication type="SHORT_TEXT">\n' % j
    for th in THEMES:
        k = th["key"]
        s += '%s  <Group name="comp_%s" x="0" y="0" width="%d" height="%d" alpha="255">\n' % (j, k, t["w"], t["h"])
        s += '%s    <Transform target="alpha" value="255*(%s)"/>\n' % (j, WEIGHT[k])
        s += text(0, 0, t["w"], t["h"], "%s", "[COMPLICATION.TEXT]", 19, th["hands"], weight="MEDIUM", indent=j + "    ", name="temp_text_%s" % k)
        s += '%s  </Group>\n' % j
    s += '%s</Complication>\n' % j
    s += '%s</ComplicationSlot>\n' % i
    return s


def build():
    x = '<?xml version="1.0" encoding="utf-8"?>\n'
    x += '<!-- Generated by generate_watchface_xml.py - edit config.py and re-run, do not hand-edit. -->\n'
    x += '<WatchFace width="%d" height="%d" clipShape="CIRCLE">\n' % (W, W)
    x += '  <Metadata key="CLOCK_TYPE" value="ANALOG"/>\n'
    x += '  <Metadata key="PREVIEW_TIME" value="10:08:35"/>\n'
    x += '  <Metadata key="STEP_GOAL" value="%d"/>\n' % STEP_GOAL
    x += '  <Scene backgroundColor="#ff000000">\n'
    for th in THEMES:   # morning (base) -> noon -> evening -> night (top)
        x += theme_group(th)
    x += temperature_slot()
    x += ambient_group()
    x += '  </Scene>\n</WatchFace>\n'
    return x


if __name__ == "__main__":
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    xml = build()
    open(OUT, "w", encoding="utf-8").write(xml)
    print("wrote %s (%d bytes, %d lines)" % (os.path.relpath(OUT), len(xml), xml.count("\n")))
