"""Shared design constants for the Seiko Presage Cocktail Time inspired watch face.

Used by generate_assets.py (PNG layers + preview) and generate_watchface_xml.py
(res/raw/watchface.xml) so geometry and colours can never drift apart.
All coordinates are in the 450x450 WFF canvas, origin top-left, centre = (225, 225).
"""

SIZE = 450
CX = CY = 225

# --- Colour matrix (from the brief). Hands/text colour = "hands". -----------------
# `second` is not in the brief: it follows the blue second hand of the reference watch,
# lightened on dark dials so it stays readable.
THEMES = [
    dict(key="morning", label="Sabah 06-11",       start=6,  base="#B8C7D1", frame="#FFFFFF", fill="#92A4B0", hands="#2A3439", second="#1F4E9E"),
    dict(key="noon",    label="Ogle 11-17",        start=11, base="#D8C5A8", frame="#FFF3D6", fill="#B89B72", hands="#4A3520", second="#1F4E9E"),
    dict(key="evening", label="Aksamustu 17-20",   start=17, base="#8C7263", frame="#E8C39E", fill="#634C40", hands="#F2E4D5", second="#8FB8F2"),
    dict(key="night",   label="Gece 20-06",        start=20, base="#18222D", frame="#647A8F", fill="#263545", hands="#D0DCE5", second="#8FB8F2"),
]

# Half-width (hours) of each cross-fade. 0.5 -> every colour change takes 1 hour
# (e.g. 10:30 -> 11:30), centred on the boundary given in the brief.
FADE_HALF_HOURS = 0.5

# --- Dial geometry ----------------------------------------------------------------
TRACK_R_OUT = 220
INDEX_R_IN, INDEX_R_SHOULDER, INDEX_R_OUT = 138, 178, 198
INDEX_HALF_W = 6.5
# hour positions that get an index (3 is left empty for the date window)
INDEX_HOURS = [1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12]

# --- Complications ----------------------------------------------------------------
DATE_BOX = dict(cx=372, cy=225, w=56, h=38)            # 3 o'clock window
BATTERY = dict(cx=118, cy=225, d=60)                   # 9 o'clock half-moon (left half)
STEPS = dict(cx=225, cy=326, d=54)                     # 6 o'clock sub-dial ring
TEMP = dict(cx=225, cy=152, w=70, h=34)                # below 12
LOGO_SEIKO_Y = 113
LOGO_PRESAGE_Y = 262
LOGO_AUTO_Y = 277

STEP_GOAL = 8000
