"""
Generate Chimwemwe Chinkuyu's engineering portfolio PDF.
Landscape letter (11 x 8.5 in), white background, dark typography.
"""

import os
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from PIL import Image as PILImage

BASE = r"C:\Users\ckc15\Downloads\CC_Portfolio"
OUT  = os.path.join(BASE, "downloads", "Chimwemwe_Chinkuyu_Portfolio.pdf")

PW, PH = landscape(letter)   # 792 × 612 pt
M  = 0.42 * inch
CX = M
CW = PW - 2 * M
CY = M
CH = PH - 2 * M

C_DARK   = colors.HexColor("#111111")
C_MID    = colors.HexColor("#3a3a3a")
C_MUTED  = colors.HexColor("#666666")
C_RULE   = colors.HexColor("#cccccc")
C_WHITE  = colors.white
C_BG     = colors.white

# ── Typography helpers ────────────────────────────────────────────────────────
def draw_text(c, x, y, text, size=10, color=None, font="Helvetica", align="left"):
    if color is None:
        color = C_DARK
    c.setFont(font, size)
    c.setFillColor(color)
    if align == "center":
        c.drawCentredString(x, y, text)
    elif align == "right":
        c.drawRightString(x, y, text)
    else:
        c.drawString(x, y, text)

def _wrap_lines(c, text, width, font, size):
    """Greedy word-wrap; returns the list of lines that fit within `width`."""
    words = text.split()
    line, lines = [], []
    for w in words:
        test = " ".join(line + [w])
        if c.stringWidth(test, font, size) <= width or not line:
            line.append(w)
        else:
            lines.append(" ".join(line))
            line = [w]
    if line:
        lines.append(" ".join(line))
    return lines

def wrapped_text(c, x, y, text, width, size=9, color=None, font="Helvetica",
                 line_height=None, align="left"):
    if color is None:
        color = C_DARK
    if line_height is None:
        line_height = size * 1.45
    c.setFont(font, size)
    c.setFillColor(color)
    lines = _wrap_lines(c, text, width, font, size)
    for ln in lines:
        if align == "center":
            c.drawCentredString(x + width / 2, y, ln)
        else:
            c.drawString(x, y, ln)
        y -= line_height
    return y

def draw_hyperlink(c, x, y, display_text, url, size=9.5, color=None, align="left"):
    if color is None:
        color = colors.HexColor("#1a5fb4")
    draw_text(c, x, y, display_text, size=size, color=color, font="Helvetica", align=align)
    text_w = c.stringWidth(display_text, "Helvetica", size)
    if align == "right":
        x0 = x - text_w
    elif align == "center":
        x0 = x - text_w / 2
    else:
        x0 = x
    c.setStrokeColor(color)
    c.setLineWidth(0.4)
    c.line(x0, y - 1.5, x0 + text_w, y - 1.5)
    c.linkURL(url, (x0, y - 3, x0 + text_w, y + size), relative=0)

# ── Image helpers ─────────────────────────────────────────────────────────────
MAX_IMG_PX = 1200

def _pil_to_rgb(pil):
    if pil.mode in ("RGBA", "P", "LA"):
        bg = PILImage.new("RGB", pil.size, (255, 255, 255))
        if pil.mode == "P":
            pil = pil.convert("RGBA")
        bg.paste(pil, mask=pil.split()[-1] if pil.mode in ("RGBA", "LA") else None)
        return bg
    elif pil.mode != "RGB":
        return pil.convert("RGB")
    return pil

def fill_image(c, path, x, y, w, h):
    if not os.path.exists(path):
        return
    try:
        pil = _pil_to_rgb(PILImage.open(path))
        iw, ih = pil.size
        target_ratio = w / h
        image_ratio  = iw / ih
        if image_ratio > target_ratio:
            crop_h = ih; crop_w = int(ih * target_ratio + 0.5)
        else:
            crop_w = iw; crop_h = int(iw / target_ratio + 0.5)
        left = (iw - crop_w) // 2; top = (ih - crop_h) // 2
        pil  = pil.crop((left, top, left + crop_w, top + crop_h))
        if max(pil.size) > MAX_IMG_PX:
            r = MAX_IMG_PX / max(pil.size)
            pil = pil.resize((int(pil.size[0]*r), int(pil.size[1]*r)), PILImage.LANCZOS)
        buf = BytesIO(); pil.save(buf, format="JPEG", quality=75); buf.seek(0)
        c.drawImage(ImageReader(buf), x, y, w, h)
    except Exception as e:
        print(f"  [fill_image skip] {path}: {e}")

def _crop_white_sides(pil, thresh=245):
    """Trim near-white left/right margins, keeping the full height."""
    gray = pil.convert("L")
    mask = gray.point(lambda v: 0 if v >= thresh else 255)
    bbox = mask.getbbox()
    if bbox:
        return pil.crop((bbox[0], 0, bbox[2], pil.height))
    return pil

def fitted_dh(path, w, h, crop_sides=False, rotate=0):
    """Height the image will occupy when letterboxed into a w×h box (0 if missing)."""
    if not os.path.exists(path):
        return 0.0
    try:
        pil = PILImage.open(path)
        if rotate:
            pil = pil.rotate(rotate, expand=True)
        if crop_sides:
            pil = _crop_white_sides(pil)
        iw, ih = pil.size
        return ih * min(w / iw, h / ih)
    except Exception:
        return 0.0

def fit_image(c, path, x, y, w, h, anchor="center", crop_sides=False, rotate=0):
    """Letterbox — full image visible.
    anchor='top'    → image flush with box top, white space below.
    anchor='center' → image centered, white space split evenly.
    anchor='bottom' → image flush with box bottom, white space above.
    crop_sides      → strip near-white left/right margins first.
    rotate          → rotate the image this many degrees (CCW) before fitting.
    """
    if not os.path.exists(path):
        return
    try:
        pil = _pil_to_rgb(PILImage.open(path))
        if rotate:
            pil = pil.rotate(rotate, expand=True)
        if crop_sides:
            pil = _crop_white_sides(pil)
        iw, ih = pil.size
        if max(iw, ih) > MAX_IMG_PX:
            r = MAX_IMG_PX / max(iw, ih)
            pil = pil.resize((int(iw*r), int(ih*r)), PILImage.LANCZOS)
            iw, ih = pil.size
        scale = min(w / iw, h / ih)
        dw, dh = iw * scale, ih * scale
        buf = BytesIO(); pil.save(buf, format="JPEG", quality=72); buf.seek(0)
        ox = x + (w - dw) / 2
        if anchor == "top":
            oy = y + h - dh
        elif anchor == "bottom":
            oy = y
        else:
            oy = y + (h - dh) / 2
        c.drawImage(ImageReader(buf), ox, oy, dw, dh)
    except Exception as e:
        print(f"  [fit_image skip] {path}: {e}")

# ── Shared chrome ──────────────────────────────────────────────────────────────
def draw_footer(c, page_num, total_pages):
    c.setFillColor(C_RULE)
    rule_y = CY - 2
    c.rect(CX, rule_y, CW, 0.5, fill=1, stroke=0)
    # Vertically center the 9 pt text in the band between the rule and page bottom.
    foot_y = rule_y / 2 - 9 * 0.32
    draw_text(c, CX + CW / 2, foot_y, "Chimwemwe Chinkuyu  |  Engineering Project Portfolio",
              size=9, color=C_MUTED, align="center")
    draw_text(c, CX + CW, foot_y, f"{page_num} / {total_pages}",
              size=9, color=C_MUTED, align="right")

def draw_section_label(c, x, y, label, line_w=None):
    if line_w is None:
        line_w = CW * 0.3
    draw_text(c, x, y, label.upper(), size=10, color=C_MUTED, font="Helvetica-Bold")
    c.setStrokeColor(C_RULE)
    c.setLineWidth(0.5)
    c.line(x, y - 3, x + line_w, y - 3)

# ── Project page layout ────────────────────────────────────────────────────────
IMG_FRAC = 0.63
TXT_GAP  = 0.18 * inch

def img_col_w():  return CW * IMG_FRAC
def txt_col_x():  return CX + img_col_w() + TXT_GAP
def txt_col_w():  return CW - img_col_w() - TXT_GAP

def project_body_top():
    return PH - M

def draw_project_title_block(c, title, category, date):
    """Full-width category / title / date at the top of the page.
    Returns y where image/text content should begin."""
    x = CX
    w = CW
    y = project_body_top()
    # Category label
    draw_text(c, x, y, category.upper(), size=11, color=C_MUTED, font="Helvetica-Bold")
    y -= 19
    # Title — spans full content width
    y = wrapped_text(c, x, y, title, w, size=18, color=C_DARK,
                     font="Helvetica-Bold", line_height=22)
    y -= 8
    # Date
    draw_text(c, x, y, date, size=11, color=C_MUTED)
    y -= 16
    # Dividing rule
    c.setStrokeColor(C_RULE); c.setLineWidth(0.5)
    c.line(x, y, x + w, y)
    y -= 10
    return y

# Vertical drop applied to every project-page text column so the first section
# title lines up with the top edge of the top image (calibrated to SARR page 1).
TXT_TOP_DROP = 10.7

# Base text-column metrics (size 12). When a column's content would run past
# the footer, every metric is scaled down by the same factor until it fits.
TXT_SIZE   = 12.0
TXT_LH     = 17.0   # line height
LABEL_GAP  = 15.0   # below a section label
SEC_GAP    = 11.0   # between sections
BULLET_GAP = 4.0    # between bullets
TXT_FLOOR  = 9.0    # smallest body size we will shrink to

def draw_bullets(c, x, y, items, width, size, color=None, line_height=17,
                 gap=BULLET_GAP):
    """Render a list of strings as bullet points with a hanging indent."""
    if color is None:
        color = C_MID
    bullet = "•  "
    bw = c.stringWidth(bullet, "Helvetica", size)
    for i, item in enumerate(items):
        c.setFont("Helvetica", size)
        c.setFillColor(color)
        c.drawString(x, y, bullet)
        y = wrapped_text(c, x + bw, y, item, width - bw, size=size,
                         color=color, line_height=line_height)
        if i != len(items) - 1:
            y -= gap
    return y

def _measure_column(c, bullets, w, scale):
    """Total vertical height the column would occupy at a given scale factor."""
    size = TXT_SIZE * scale
    lh   = TXT_LH * scale
    bw   = c.stringWidth("•  ", "Helvetica", size)
    h = 0.0
    for label, text in bullets:
        if label:
            h += LABEL_GAP * scale
        if isinstance(text, (list, tuple)):
            for i, item in enumerate(text):
                h += len(_wrap_lines(c, item, w - bw, "Helvetica", size)) * lh
                if i != len(text) - 1:
                    h += BULLET_GAP * scale
        else:
            h += len(_wrap_lines(c, text, w, "Helvetica", size)) * lh
        h += SEC_GAP * scale
    return h

def draw_shelf_image(c, path, x, shelf, w, band, lbl, rotate=0, crop_sides=False):
    """Bottom-anchor an image on a shelf with its caption directly beneath it
    (the tight image/caption pairing used on the gearbox component page)."""
    fit_image(c, os.path.join(BASE, path), x, shelf, w, band,
              anchor="bottom", rotate=rotate, crop_sides=crop_sides)
    draw_text(c, x + w / 2, shelf - 11, lbl, size=9.5, color=C_MUTED,
              align="center")

def draw_labeled_block(c, x, y, w, label, text, size=11, line_height=15):
    """A single section label + wrapped paragraph at an arbitrary position."""
    draw_section_label(c, x, y, label)
    y -= 14
    return wrapped_text(c, x, y, text, w, size=size, color=C_MID,
                        line_height=line_height)

def draw_text_column(c, bullets, start_y=None, x=None, w=None):
    if x is None:
        x = txt_col_x()
    if w is None:
        w = txt_col_w()
    y0 = (start_y if start_y is not None else project_body_top()) - TXT_TOP_DROP
    avail = y0 - (CY + 2)

    # Shrink uniformly only if the content would otherwise cross the footer.
    scale = 1.0
    while scale > TXT_FLOOR / TXT_SIZE and _measure_column(c, bullets, w, scale) > avail:
        scale -= 0.5 / TXT_SIZE   # step body size down 0.5 pt at a time

    size = TXT_SIZE * scale
    lh   = TXT_LH * scale

    label_line_w = min(CW * 0.3, w)   # keep the underline within the column
    y = y0
    for label, text in bullets:
        if label:
            draw_section_label(c, x, y, label, line_w=label_line_w)
            y -= LABEL_GAP * scale
        if isinstance(text, (list, tuple)):
            y = draw_bullets(c, x, y, text, w, size=size, line_height=lh,
                             gap=BULLET_GAP * scale)
        else:
            y = wrapped_text(c, x, y, text, w, size=size, color=C_MID,
                             line_height=lh)
        y -= SEC_GAP * scale
    return y

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: COVER
# ─────────────────────────────────────────────────────────────────────────────
def draw_cover(c, total_pages):
    c.setFillColor(C_BG)
    c.rect(0, 0, PW, PH, fill=1, stroke=0)

    PAD = M
    title_y  = PH - PAD - 30
    name_y   = PAD + 28
    degree_y = PAD + 12

    ZONE_TOP = title_y - 8
    ZONE_BOT = name_y + 14
    GAP      = 10
    SIDE_PAD = 40

    img_y = ZONE_BOT + GAP
    img_h = (ZONE_TOP - GAP) - img_y

    fit_image(c,
              os.path.join(BASE, "images/gear_box/assembly_front_oblong_transluscent.png"),
              SIDE_PAD, img_y, PW - 2 * SIDE_PAD, img_h)

    draw_text(c, PAD, title_y, "ENGINEERING PROJECT PORTFOLIO",
              size=30, color=C_DARK, font="Helvetica-Bold")
    draw_text(c, PW - PAD, name_y, "CHIMWEMWE CHINKUYU",
              size=17, color=C_MID, font="Helvetica-Bold", align="right")
    draw_text(c, PW - PAD, degree_y,
              "B.S.E. Mechanical & Aerospace Engineering  ·  Minor in Computer Science  ·  Princeton University, Class of 2026",
              size=11, color=C_MUTED, align="right")

    c.showPage()

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: ABOUT ME
# ─────────────────────────────────────────────────────────────────────────────
def draw_about(c, total_pages):
    c.setFillColor(C_BG)
    c.rect(0, 0, PW, PH, fill=1, stroke=0)

    top_y   = project_body_top()
    left_w  = CW * 0.62
    gap     = 0.22 * inch
    right_w = CW - left_w - gap
    right_x = CX + left_w + gap

    # Headshot — anchor="top" so content starts on the same line as text
    fit_image(c, os.path.join(BASE, "images/Chimwemwe_headshot2.png"),
              right_x, CY, right_w, top_y - CY, anchor="top")

    y = top_y

    # Name
    draw_text(c, CX, y, "Chimwemwe Chinkuyu", size=22,
              color=C_DARK, font="Helvetica-Bold")
    y -= 40

    # Education section label + degree info
    draw_text(c, CX, y, "EDUCATION", size=10, color=C_MUTED, font="Helvetica-Bold")
    c.setStrokeColor(C_RULE); c.setLineWidth(0.5)
    c.line(CX, y - 3, CX + CW * 0.3, y - 3)
    y -= 16
    y = wrapped_text(c, CX, y,
                     "B.S.E. Mechanical & Aerospace Engineering  ·  Minor in Computer Science  ·  "
                     "Princeton University, Class of 2026",
                     left_w - 4, size=13, color=C_MID, line_height=18)
    y -= 20

    # Bio — 2 paragraphs, under a Motivation header
    bio_paras = [
        "I'm inspired by the possibility to turn ideas into smart, functional solutions at "
        "the intersection of hardware and software. My work spans mechanical design, fabrication, "
        "and software development.",
        "I'm eager to grow in innovation-focused environments and contribute to advanced devices, "
        "autonomous systems, and technologies that enhance human health and quality of life.",
    ]
    draw_section_label(c, CX, y, "Motivation")
    y -= 18
    for para in bio_paras:
        y = wrapped_text(c, CX, y, para, left_w - 4, size=13, color=C_MID, line_height=18)
        y -= 16

    y -= 6
    c.setStrokeColor(C_RULE); c.setLineWidth(0.5)
    c.line(CX, y, CX + left_w, y)
    y -= 28

    # Technical skills — spans full content width
    skills = {
        "CAD / CAM": [
            "PTC Creo (incl. FEA)", "Fusion 360", "Onshape", "AutoCAD",
        ],
        "Programming & Robotics": [
            "Python", "MATLAB", "Java", "C", "ROS",
            "COMPAS FAB", "UR-RTDE", "PID control",
        ],
        "Fabrication": [
            "3D Printing (FDM, SLA, SLS)", "Manual & CNC Machining",
            "Carpentry", "Robotic Fabrication", "Autonomous Assembly",
        ],
        "Software & Tools": [
            "Simulink", "Jupyter Notebook", "Docker", "Anaconda",
            "Grasshopper", "NVIDIA Jetson", "RadiAnt DICOM Viewer",
        ],
    }

    draw_text(c, CX, y, "TECHNICAL SKILLS", size=11, color=C_MUTED, font="Helvetica-Bold")
    y -= 26

    max_items = max(len(v) for v in skills.values())
    col_w = CW / len(skills)
    for ci, (category, items) in enumerate(skills.items()):
        sx = CX + ci * col_w
        sy = y
        draw_text(c, sx, sy, category, size=11, color=C_DARK, font="Helvetica-Bold")
        sy -= 14
        for item in items:
            draw_text(c, sx, sy, f"• {item}", size=10.5, color=C_MID)
            sy -= 14

    y -= 14 * (1 + max_items) + 24

    c.setStrokeColor(C_RULE); c.setLineWidth(0.5)
    c.line(CX, y, CX + CW, y)
    rule_y = y

    # Contact links — linkedin + portfolio, vertically centered in the space
    # between the rule above and the footer rule below.
    half_w    = CW / 2
    LABEL_W_L = 100   # shorter for LINKEDIN
    LABEL_W_R = 158   # wider for PORTFOLIO WEBSITE (longer label)

    link_y = (rule_y + (CY - 2)) / 2 - 11 * 0.35

    draw_text(c, CX, link_y, "LINKEDIN", size=11, color=C_MUTED, font="Helvetica-Bold")
    draw_hyperlink(c, CX + LABEL_W_L, link_y, "linkedin.com/in/chimwemwe-chinkuyu",
                   "https://www.linkedin.com/in/chimwemwe-chinkuyu/", size=12)
    draw_text(c, CX + half_w, link_y, "PORTFOLIO WEBSITE", size=11, color=C_MUTED, font="Helvetica-Bold")
    draw_hyperlink(c, CX + half_w + LABEL_W_R, link_y, "ckcgithub16.github.io/CC_Portfolio/",
                   "https://ckcgithub16.github.io/CC_Portfolio/index.html", size=12)

    draw_footer(c, 2, total_pages)
    c.showPage()

# ─────────────────────────────────────────────────────────────────────────────
# PROJECT 1 — SARR  (2 pages)
# ─────────────────────────────────────────────────────────────────────────────
def draw_sarr(c, page_start, total_pages):
    # ── Page 1 ────────────────────────────────────────────────────────────────
    c.setFillColor(C_BG); c.rect(0, 0, PW, PH, fill=1, stroke=0)

    content_top = draw_project_title_block(c,
        "Design & Manufacturing of a Search and Rescue Robot",
        "Mechanical Engineering", "Oct – Dec 2025")

    iw          = img_col_w()
    total       = content_top - CY
    CAP_H       = 14   # space allocated per caption row (text + padding above)
    ROW_GAP     = 10   # pure visual gap separating the two image rows
    BOT_MARGIN  = 6    # matches the 10 pt gap left below the title rule

    # All image height split between the two rows
    total_img_h = total - BOT_MARGIN - 2 * CAP_H - ROW_GAP
    main_h      = total_img_h * 0.60
    small_h     = total_img_h - main_h

    # y positions — every caption sits 12 pt below its image's bottom edge
    bot_cap_y  = CY + BOT_MARGIN + 2
    bot_img_y  = CY + BOT_MARGIN + CAP_H
    main_cap_y = CY + BOT_MARGIN + CAP_H + small_h + ROW_GAP + 2
    main_img_y = CY + BOT_MARGIN + CAP_H + small_h + ROW_GAP + CAP_H

    # Main image — fill_image crops to box, eliminating letterbox gap
    fill_image(c, os.path.join(BASE, "images/sarr/motherbot_on_ramp.JPG"),
               CX, main_img_y, iw, main_h)
    draw_text(c, CX + iw / 2, main_cap_y, "SARR traveling over the ramp",
              size=9, color=C_MUTED, align="center")

    # Bottom row: deploying image wider, babybot cropped via fill_image.
    # Horizontal gap matches the vertical gap below the images (image bottom at
    # CY+BOT_MARGIN+CAP_H, footer rule at CY-2) for a uniform spacing appearance.
    img_gap = BOT_MARGIN + CAP_H + 2
    w2 = iw * 0.40 - 6        # babybot keeps its original width
    w1 = iw - w2 - img_gap    # deploying image shrinks to absorb the wider gap
    fill_image(c, os.path.join(BASE, "images/sarr/motherbot_deploying_babybot.JPG"),
               CX, bot_img_y, w1, small_h)
    fill_image(c, os.path.join(BASE, "images/sarr/babybot_photo.jpeg"),
               CX + w1 + img_gap, bot_img_y, w2, small_h)
    draw_text(c, CX + w1 / 2, bot_cap_y,
              "Motherbot deploying Babybot over the wall",
              size=9, color=C_MUTED, align="center")
    draw_text(c, CX + w1 + img_gap + w2 / 2, bot_cap_y, "The Babybot",
              size=9, color=C_MUTED, align="center")

    draw_text_column(c, [
        ("Overview",
         "For a mechanical design course, I collaborated with 11 classmates to build a "
         "marsupial search and rescue robot that could navigate an obstacle course to "
         "deliver a med kit. The system pairs a large Motherbot that carries a smaller "
         "Babybot onboard. The Motherbot traversed a ramp, a chute, and a 36-inch wall. "
         "At the wall, a motorized lifting arm raised the Babybot over the top, deploying "
         "it on the far side. The Babybot then navigated independently to a target zone "
         "and delivered a med kit payload."),
        ("Sensing & Control", [
         "Both robots used C++ state machine controllers on Teensy microcontrollers.",
         "The Motherbot used CdS phototransistors for line-following — proportional "
         "on flat ground, bang-bang on the ramp, PD in the chute — and ultrasonic "
         "sensors to trigger state transitions.",
         "The arm deployment was open-loop.",
         "The Babybot used similar sensing for post-deployment navigation.",
        ]),
        ("Result", [
         "The Motherbot navigated the entire course, deployed the Babybot over the "
         "36-inch wall, and the Babybot delivered the med kit to the target zone at "
         "the class final.",
        ]),
    ], start_y=content_top)

    draw_footer(c, page_start, total_pages)
    c.showPage()

    # ── Page 2 ────────────────────────────────────────────────────────────────
    c.setFillColor(C_BG); c.rect(0, 0, PW, PH, fill=1, stroke=0)

    content_top = draw_project_title_block(c,
        "Search and Rescue Robot — Chassis Design & Manufacturing",
        "Mechanical Engineering", "Oct – Dec 2025")

    iw = img_col_w()

    fit_image(c, os.path.join(BASE, "images/sarr/motherbot_chassis_assembly_drawing.png"),
              CX, CY, iw, content_top - CY, anchor="top")

    draw_text_column(c, [
        ("My Contribution", [
         "Designed the low-carbon steel chassis, 60:1 two-stage HTD belt drivetrain, "
         "and engineering drawings in Creo Parametric.",
         "Led fabrication of the chassis and drivetrain.",
        ]),
        ("Chassis Design", [
         "AISI 1018 steel was chosen for weldability and stiffness.",
         "FBD analysis confirmed tip-over stability under full arm extension.",
         "FEA at motor mount positions and the lifting arm pivot verified structural "
         "margins.",
         "The two-stage belt drivetrain over a jackshaft provided torque for the ramp; "
         "slotted motor mount holes allowed precise belt tensioning.",
        ]),
        ("Manufacturing", [
         "Steel frame members were band-saw cut, cope-cut on a knee mill, and MIG "
         "welded.",
         "Motor mount brackets and the jackshaft were manually machined on the lathe "
         "and knee mill.",
         "Sensor mounts and the lifting arm cradle were FDM 3D printed for rapid "
         "iteration.",
         "Key drivetrain components were CNC machined for dimensional accuracy.",
        ]),
    ], start_y=content_top)

    draw_footer(c, page_start + 1, total_pages)
    c.showPage()

# ─────────────────────────────────────────────────────────────────────────────
# PROJECT 2 — DIFFERENTIAL GEARBOX  (2 pages)
# ─────────────────────────────────────────────────────────────────────────────
def draw_gearbox(c, page_start, total_pages):
    # ── Page 1 ────────────────────────────────────────────────────────────────
    c.setFillColor(C_BG); c.rect(0, 0, PW, PH, fill=1, stroke=0)

    content_top = draw_project_title_block(c,
        "Custom Differential Gearbox",
        "Mechanical Engineering  ·  CAD", "June 2025")

    iw      = img_col_w()
    total   = content_top - CY
    main_h  = total * 0.62
    small_h = total - main_h - 6

    fit_image(c, os.path.join(BASE, "images/gear_box/assembly_front_oblong_transluscent.png"),
              CX, CY + small_h + 6, iw, main_h, anchor="top")
    sw = (iw - 6) / 2
    fit_image(c, os.path.join(BASE, "images/gear_box/assembly_front.png"),
              CX, CY, sw, small_h)
    fit_image(c, os.path.join(BASE, "images/gear_box/assembly_side.png"),
              CX + sw + 6, CY, sw, small_h)

    draw_text_column(c, [
        ("Overview",
         "As a personal project to sharpen my CAD skills, I designed a fully "
         "parametric bevel-gear axle differential entirely in Autodesk Fusion 360. "
         "The planetary differential configuration distributes drive torque between "
         "two output shafts while allowing independent rotation speeds, enabling "
         "smooth, skid-free turning."),
        ("Design Approach", [
         "Gear geometry was determined using standard bevel gear formulas driven by "
         "linked Fusion 360 equations.",
         "Module, pressure angle, tooth count, and pitch circle diameter update the "
         "full geometry automatically as inputs change.",
        ]),
        ("Skills Used",
         "Autodesk Fusion 360 · Parametric Modeling · Bevel Gear Theory"),
    ], start_y=content_top)

    draw_footer(c, page_start, total_pages)
    c.showPage()

    # ── Page 2 ────────────────────────────────────────────────────────────────
    c.setFillColor(C_BG); c.rect(0, 0, PW, PH, fill=1, stroke=0)

    content_top = draw_project_title_block(c,
        "Custom Differential Gearbox — Component Drawings",
        "Mechanical Engineering  ·  CAD", "June 2025")

    iw    = CW       # component grid now spans the full content width
    rows, cols = 2, 3
    gap   = 6
    cw_img = (iw - gap * (cols - 1)) / cols

    IMG_BAND = 160   # vertical space available to each image row (width usually binds)
    CAP_DROP = 11    # caption baseline below the shelf (image bottom)
    ROW_GAP  = 16    # gap between a row's caption and the next row's images

    comp_images = [
        ("images/gear_box/long_central_shaft_front.png",      "Long Drive Shaft"),
        ("images/gear_box/short_central_shaft_front.png",     "Short Drive Shaft"),
        ("images/gear_box/long_central_shaft_gear_front.png", "Bevel Gear"),
        ("images/gear_box/slotted_ring_front.png",            "Differential Ring"),
        ("images/gear_box/back_hub_front.png",                "Output Hub"),
        ("images/gear_box/outer_casing_bowl_front.png",       "Outer Casing"),
    ]
    # Images are bottom-anchored on a shelf with the caption directly below.
    # Raise the upper shelf so the tallest upper-row image's top reaches
    # content_top (the height of the Parametric Design section title); the lower
    # shelf keeps the same offset, so the gap between the rows is unchanged.
    upper_dh_max = max(fitted_dh(os.path.join(BASE, rel), cw_img, IMG_BAND)
                       for rel, _ in comp_images[:cols])
    upper_shelf = content_top - upper_dh_max
    lower_shelf = upper_shelf - CAP_DROP - ROW_GAP - IMG_BAND
    shelves = [upper_shelf, lower_shelf]
    for idx, (rel, lbl) in enumerate(comp_images):
        row = idx // cols; col = idx % cols
        bx = CX + col * (cw_img + gap)
        shelf = shelves[row]
        fit_image(c, os.path.join(BASE, rel), bx, shelf, cw_img, IMG_BAND,
                  anchor="bottom")
        draw_text(c, bx + cw_img / 2, shelf - CAP_DROP, lbl,
                  size=9.5, color=C_MUTED, align="center")

    draw_footer(c, page_start + 1, total_pages)
    c.showPage()

# ─────────────────────────────────────────────────────────────────────────────
# PROJECT 3 — SELF-DRIVING RC TRUCK  (1 page)
# ─────────────────────────────────────────────────────────────────────────────
def draw_car(c, page_start, total_pages):
    c.setFillColor(C_BG); c.rect(0, 0, PW, PH, fill=1, stroke=0)

    content_top = draw_project_title_block(c,
        "Self-Driving RC Truck with Obstacle Avoidance & Safety Filter",
        "Mechanical Engineering  ·  Software Development", "Mar – May 2025")

    iw    = img_col_w()
    track = "images/autonomous_car/car_on_track2.png"

    # Full-width photo of the truck on the Task 1 course, with the run video linked
    # beneath it (the YouTube clip is the team's Task 1 run on this track).
    track_h = fitted_dh(os.path.join(BASE, track), iw, content_top - CY)
    track_shelf = content_top - track_h
    draw_shelf_image(c, track, CX, track_shelf, iw, track_h,
                     "Navigating the Task 1 obstacle course")
    # Center the run-video link vertically between the image bottom and footer rule.
    link_size = 15
    link_mid  = (track_shelf + (CY - 2)) / 2
    draw_hyperlink(c, CX + iw / 2, link_mid - link_size * 0.35,
                   "▶  Watch the team's Task 1 run on YouTube",
                   "https://youtu.be/9XfZ48AbwDY", size=link_size, align="center")

    draw_text_column(c, [
        ("Overview",
         "For an intelligent robotics course, I worked in a team of 4 to program an "
         "autonomous RC truck, powered by an NVIDIA Jetson, to complete two tasks: "
         "racing through an obstacle course, and running a real-time driver-assist "
         "safety filter."),
        ("My Contribution",
         "Algorithm development · Code implementation · "
         "Debugging of both software and hardware"),
        ("Task 1 — Obstacle Course Racing", [
         "Implemented an iLQR (iterative Linear Quadratic Regulator) controller with "
         "cost-prioritization to navigate 16 ordered waypoints in 3:30 while avoiding "
         "up to 20 obstacle cubes.",
         "Finished 4th fastest of 14 teams after time penalties.",
        ]),
        ("Task 2 — Safety Filter", [
         "Built an Advanced Driver Assistance System (ADAS) that uses iLQR to monitor "
         "manual driver inputs in real time.",
         "Overrides steering that would leave the track or cross lane boundaries while "
         "minimizing unnecessary interventions.",
        ]),
        ("Skills Used",
         "Python · ROS · Optimal Control · Path Planning · Obstacle Avoidance"),
    ], start_y=content_top)

    draw_footer(c, page_start, total_pages)
    c.showPage()

# ─────────────────────────────────────────────────────────────────────────────
# PROJECT 4 — HEAT TRANSFER SIMULATION  (3 pages)
# These pages drop the standard image/text split so each MATLAB figure — which
# carries small axis text — can be printed as large as the body margins allow.
# ─────────────────────────────────────────────────────────────────────────────
def _heat_result_page(c, page_num, total_pages, title, img_rel, label, text):
    """A single airfoil-result page: one large figure with a short caption below."""
    c.setFillColor(C_BG); c.rect(0, 0, PW, PH, fill=1, stroke=0)

    content_top = draw_project_title_block(c, title,
        "Mechanical Engineering  ·  Numerical Methods", "Apr – May 2025")

    TEXT_H   = 52   # bottom band reserved for the result paragraph
    CAP_GAP  = 14   # gap between the figure and the text band
    graph_floor = CY + TEXT_H + CAP_GAP
    fit_image(c, os.path.join(BASE, img_rel),
              CX, graph_floor, CW, content_top - graph_floor, anchor="bottom")

    draw_labeled_block(c, CX, CY + TEXT_H - 2, CW, label, text,
                       size=11, line_height=15)

    draw_footer(c, page_num, total_pages)
    c.showPage()

def draw_heat(c, page_start, total_pages):
    # ── Page 1 — heated cylinder figure + project text ─────────────────────────
    c.setFillColor(C_BG); c.rect(0, 0, PW, PH, fill=1, stroke=0)

    content_top = draw_project_title_block(c,
        "2D Unsteady Heat Transfer: Heated Cylinder & NACA 2412 Airfoil",
        "Mechanical Engineering  ·  Numerical Methods", "Apr – May 2025")

    # Figure on the left, text column on its right. The figure's white side
    # margins are cropped so its plots fill the width. Horizontal gap between
    # the two matches the autonomous-car page (TXT_GAP).
    col_gap = TXT_GAP
    txt_w   = 210 * 0.90
    img_w   = CW - txt_w - col_gap
    tx      = CX + img_w + col_gap

    cyl = "images/psi_omega_simulation/fin_main1.png"
    dh  = fitted_dh(os.path.join(BASE, cyl), img_w, content_top - CY,
                    crop_sides=True)
    fit_image(c, os.path.join(BASE, cyl), CX, CY, img_w, content_top - CY,
              anchor="top", crop_sides=True)
    draw_text(c, CX + img_w / 2, content_top - dh - 11,
              "Heated cylinder — vorticity, stream function, temperature, "
              "and convergence history",
              size=9, color=C_MUTED, align="center")

    draw_text_column(c, [
        ("Overview",
         "For a heat transfer course, I built a Psi-Omega (streamfunction-vorticity) "
         "finite-difference simulation from scratch in MATLAB to model 2D unsteady "
         "heat transfer over two geometries: a 400°C cylinder in 300°C flow "
         "(convective heat flux 7.6 kW/m²), and a NACA 2412 airfoil at 5° and 30° "
         "angles of attack (heat flux 1,002.6 vs 1,133.6 W/m²)."),
        ("Technical Approach", [
         "Three coupled PDEs solved at each time step:",
         "Streamfunction (Poisson) via Gauss-Seidel with over-relaxation",
         "Vorticity (momentum) via forward Euler with upwind differencing",
         "Temperature (energy) coupled to the velocity field",
        ]),
        ("Skills Used",
         "MATLAB · Finite Difference Methods · Fluid Dynamics · Heat Transfer · "
         "Numerical Stability · CFD Validation"),
    ], start_y=content_top, x=tx, w=txt_w)

    draw_footer(c, page_start, total_pages)
    c.showPage()

    # ── Page 2 — NACA 2412 at 5° AoA ───────────────────────────────────────────
    _heat_result_page(c, page_start + 1, total_pages,
        "Heat Transfer Simulation — NACA 2412 at 5° Angle of Attack",
        "images/psi_omega_simulation/sim_part_b_main1.png",
        "Attached Flow",
        "Flow remains attached and the temperature distribution is smooth and "
        "symmetric about the chord line. The result was validated against SimFlow "
        "CFD — within 5% of the commercial result — confirming correct PDE "
        "discretization and boundary conditions.")

    # ── Page 3 — NACA 2412 at 30° AoA ──────────────────────────────────────────
    _heat_result_page(c, page_start + 2, total_pages,
        "Heat Transfer Simulation — NACA 2412 at 30° Angle of Attack",
        "images/psi_omega_simulation/sim_part_b_main2.png",
        "Separated Flow & Vortex Shedding",
        "Flow separates at the leading edge, producing large unsteady vortices shed "
        "periodically into the wake, with Strouhal number St = 0.62 — consistent with "
        "separated-flow theory. Higher stagnation temperatures and increased heat flux "
        "(13% above the 5° case) result from the thickened boundary layer.")

# ─────────────────────────────────────────────────────────────────────────────
# PROJECT 5 — LOAD-BEARING AIRFOIL  (2 pages)
# ─────────────────────────────────────────────────────────────────────────────
def draw_airfoil(c, page_start, total_pages):
    # ── Page 1 ────────────────────────────────────────────────────────────────
    c.setFillColor(C_BG); c.rect(0, 0, PW, PH, fill=1, stroke=0)

    content_top = draw_project_title_block(c,
        "Design and Manufacturing of a Load-Bearing Airfoil",
        "Mechanical Engineering", "Mar – May 2023")

    iw = img_col_w()

    # Top: wide full-wing FEA banner.  Bottom: deflection-test photo (rotated
    # upright) beside the finished wing.  All bottom-anchored with tight captions.
    fea = "images/airfoil/assembly_fea.png"
    fea_h = fitted_dh(os.path.join(BASE, fea), iw, content_top - CY)
    top_shelf = content_top - fea_h
    draw_shelf_image(c, fea, CX, top_shelf, iw, fea_h,
                     "Full-wing FEA — von Mises stress at 97 lbf")

    ROW_GAP    = 20
    bottom_top = (top_shelf - 11) - ROW_GAP
    bot_shelf  = CY + 24
    band       = bottom_top - bot_shelf
    half       = (iw - 12) / 2
    draw_shelf_image(c, "images/airfoil/airfoil_deflecting_97.jpg",
                     CX, bot_shelf, half, band,
                     "Wing under 97 lbf test load", rotate=270)
    draw_shelf_image(c, "images/airfoil/wing-assembly.jpg",
                     CX + half + 12, bot_shelf, half, band,
                     "Completed wing assembly")

    draw_text_column(c, [
        ("Overview",
         "The goal was to design a wing that could carry a specified load while "
         "minimizing deflection, cost, and weight. The 9-member team's 25.5-inch "
         "airfoil supported 97 lbf at 23.5 in. from the secured end with 3.75 in. "
         "tip deflection, weighed 18.3 oz, and failed at 120 lbs (beam web torsion) "
         "— above the 97 lbf design load."),
        ("Design", [
         "Aluminum 7075-T651 I-beam (yield stress 73,000 psi) with circular "
         "lightening holes — selected for best strength-to-weight ratio from four "
         "competing beam concepts.",
         "Nylon bulkheads with circular cutouts reduced weight.",
         "Balsa wood skin formed the NACA profile.",
        ]),
        ("FEA & Validation", [
         "PTC Creo FEA validated deflection at 97 lbf.",
         "Failure mode — beam web torsion collapse at 120 lbs — was not captured in "
         "the planar FEA model, teaching the importance of 3D torsional load modeling.",
        ]),
        ("Skills Used",
         "PTC Creo · FEA · CNC Milling (Haas VF-7/40) · Waterjet (ProtoMAX) · "
         "FDM & SLS 3D Printing · Structural Analysis · GD&T"),
    ], start_y=content_top)

    draw_footer(c, page_start, total_pages)
    c.showPage()

    # ── Page 2 ────────────────────────────────────────────────────────────────
    c.setFillColor(C_BG); c.rect(0, 0, PW, PH, fill=1, stroke=0)

    content_top = draw_project_title_block(c,
        "Load-Bearing Airfoil — Manufacturing & Testing",
        "Mechanical Engineering", "Mar – May 2023")

    iw   = img_col_w()
    gap  = 12
    half = (iw - gap) / 2

    ibeam    = "images/airfoil/circular_hole_I-beam.JPG"
    beamfea  = "images/airfoil/beam_fea.png"
    nylon    = "images/airfoil/circle_bulkhead.png"
    waterjet = "images/airfoil/waterjetbh.png"

    h_ibeam = fitted_dh(os.path.join(BASE, ibeam),   iw,   content_top - CY)
    h_fea   = fitted_dh(os.path.join(BASE, beamfea), iw,   content_top - CY)
    h_bulk  = max(fitted_dh(os.path.join(BASE, nylon),    half, content_top - CY),
                  fitted_dh(os.path.join(BASE, waterjet), half, content_top - CY))

    ROW = 44
    shelf1 = content_top - h_ibeam
    draw_shelf_image(c, ibeam, CX, shelf1, iw, h_ibeam, "Circular-Hole I-Beam")
    shelf2 = (shelf1 - 11) - ROW - h_fea
    draw_shelf_image(c, beamfea, CX, shelf2, iw, h_fea, "I-Beam FEA")
    shelf3 = (shelf2 - 11) - ROW - h_bulk
    draw_shelf_image(c, nylon,    CX,              shelf3, half, h_bulk,
                     "Nylon Bulkhead Design")
    draw_shelf_image(c, waterjet, CX + half + gap, shelf3, half, h_bulk,
                     "Waterjetted Bulkhead")

    draw_text_column(c, [
        ("Manufacturing", [
         "I-beam CNC milled on Haas VF-7/40.",
         "Bulkheads waterjet-cut on ProtoMAX.",
         "Ribs printed on Ender 3 Pro (FDM) and structural parts on Formlabs SLS.",
         "Balsa skin cut on bandsaw and sanded to NACA profile.",
        ]),
        ("My Contribution",
         "Designed and performed FEA on the I-beam · Bulkhead material selection "
         "· Airfoil assembly"),
        ("Testing Results", [
         "Passed the 97 lbf design load at 3.75 in. deflection, then continued "
         "loading to failure at 120 lbs.",
         "All weight targets were met.",
        ]),
        ("Lessons Learned", [
         "Torsional loads must be explicitly modeled in 3D FEA.",
         "Physical load paths in complex assemblies differ from simplified beam "
         "theory predictions, especially near joints and web openings.",
        ]),
    ], start_y=content_top)

    draw_footer(c, page_start + 1, total_pages)
    c.showPage()

# ─────────────────────────────────────────────────────────────────────────────
# PROJECT 0 — SENIOR THESIS  (3 pages)
#   Page 1 — overview.  Page 2 — software pipeline.  Page 3 — mechanical
#   components & results.  Image-forward like the other project pages, with the
#   body text kept short enough per page to stay at the standard 12 pt size.
# ─────────────────────────────────────────────────────────────────────────────
THESIS_CAT  = "Mechanical Engineering  ·  Software Development"
THESIS_DATE = "Sep 2025 – Apr 2026"

def img_aspect(path):
    """Width / height of an image, or 1.0 if it can't be read."""
    try:
        with PILImage.open(path) as im:
            return im.size[0] / im.size[1]
    except Exception:
        return 1.0

def _equal_height_row(c, y_top, imgs, gap=12, cap_h=15):
    """Draw a row of images all at the SAME height (natural, differing widths),
    left-aligned and spanning the image column width, with captions beneath.
    `imgs` is a list of (path, caption) tuples.  Returns the y just below the
    caption band so callers can stack the next row underneath."""
    iw  = img_col_w()
    asp = [img_aspect(os.path.join(BASE, p)) for p, _ in imgs]
    h   = (iw - gap * (len(imgs) - 1)) / sum(asp)   # equal height, full width
    row_bot = y_top - h
    x = CX
    for (path, cap), a in zip(imgs, asp):
        w = h * a
        fit_image(c, os.path.join(BASE, path), x, row_bot, w, h, anchor="bottom")
        draw_text(c, x + w / 2, row_bot - 11, cap, size=9.5, color=C_MUTED,
                  align="center")
        x += w + gap
    return row_bot - cap_h

def _thesis_quad(c, content_top, imgs):
    """Thesis image column: a 2×2 block, top-anchored under the title.  Both
    images in a row share the same height (natural, differing widths) and the
    row spans the column width.  The vertical gap between the two rows is set to
    half the distance from the lower row's bottom to the footer in the previous
    (tight, 14 pt-gap) layout, lifting the lower row toward mid-page.  `imgs` is
    four (path, caption) tuples in reading order."""
    iw      = img_col_w()
    row_gap = 12          # horizontal gap within a row (matches _equal_height_row)
    cap_h   = 15
    asp = [img_aspect(os.path.join(BASE, p)) for p, _ in imgs]
    h1 = (iw - row_gap) / (asp[0] + asp[1])
    h2 = (iw - row_gap) / (asp[2] + asp[3])
    row1_bot = content_top - h1
    prev_row2_bot = (row1_bot - cap_h - 14) - h2      # old layout, 14 pt row gap
    new_gap = (prev_row2_bot - (CY - 2)) / 2          # footer rule is at CY - 2
    _equal_height_row(c, content_top, imgs[:2])
    _equal_height_row(c, row1_bot - new_gap, imgs[2:])

def draw_thesis(c, page_start, total_pages):
    # ── Page 1 — Overview ──────────────────────────────────────────────────────
    c.setFillColor(C_BG); c.rect(0, 0, PW, PH, fill=1, stroke=0)

    content_top = draw_project_title_block(c,
        "Autonomous Robotic Assembly of Multi-Layer Lincoln Log Structures",
        THESIS_CAT, THESIS_DATE)

    # Single hero photo of the robot, shown in full (letterboxed, not cropped).
    iw    = img_col_w()
    CAP_H = 16
    tile  = "images/thesis/thesis_tile.JPG"
    box_h = content_top - CY - CAP_H
    dh    = fitted_dh(os.path.join(BASE, tile), iw, box_h)
    fit_image(c, os.path.join(BASE, tile), CX, CY + CAP_H, iw, box_h, anchor="top")
    draw_text(c, CX + iw / 2, content_top - dh - 11,
              "UR3 arm assembling a Lincoln Log structure",
              size=9.5, color=C_MUTED, align="center")

    draw_text_column(c, [
        ("Overview",
         "My senior thesis asks a single question: how can an automated robotic system "
         "reliably assemble multi-layer Lincoln Log structures layer-by-layer with high "
         "precision? To answer it, I designed and built an autonomous system that uses a "
         "UR3 robotic arm to assemble these structures with no cameras, force sensors, "
         "or runtime feedback. It is the autonomous foundation for a longer-term goal of "
         "human-robot collaborative construction: before a robot can share the task with "
         "a person, it has to perform its own half reliably."),
        ("Four Subsystems",
         "The system integrates a parametric toolpath generator, a Cartesian motion "
         "planner, a synchronized execution controller, and a set of custom 3D-printed "
         "fixtures. The next two pages walk through the software pipeline and then the "
         "mechanical hardware and test results."),
        ("Skills Used",
         "Python · Grasshopper / GhPython · COMPAS FAB · ROS · MoveIt! · UR3 · "
         "Fusion 360 · 3D Printing · Robotic Fabrication"),
    ], start_y=content_top)

    draw_footer(c, page_start, total_pages)
    c.showPage()

    # ── Page 2 — Software Pipeline ─────────────────────────────────────────────
    c.setFillColor(C_BG); c.rect(0, 0, PW, PH, fill=1, stroke=0)

    content_top = draw_project_title_block(c,
        "Autonomous Lincoln Log Assembly — Software Pipeline",
        THESIS_CAT, THESIS_DATE)

    # Cropped software-pipeline diagram, flush under the title.
    iw   = img_col_w()
    pipe = "images/thesis/code-pipeline_cropped.png"
    ph   = fitted_dh(os.path.join(BASE, pipe), iw, content_top - CY)
    fit_image(c, os.path.join(BASE, pipe), CX, content_top - ph, iw, ph, anchor="top")
    draw_text(c, CX + iw / 2, content_top - ph - 11,
              "Software pipeline — three GhPython components",
              size=9.5, color=C_MUTED, align="center")
    # Two trajectory images below, at equal height. The vertical gap to the
    # pipeline is half the distance from the trajectory-row bottom to the footer
    # in the previous (tight) layout, lifting the row toward mid-page.
    traj = [("images/thesis/trajectory-waypoints.png", "Generated waypoint planes (Visualization in Rhino)"),
            ("images/thesis/trajectory-planned.png",   "Planned Cartesian trajectory (Visualization in Rhino)")]
    traj_h = (iw - 12) / sum(img_aspect(os.path.join(BASE, p)) for p, _ in traj)
    pipe_bottom  = content_top - ph
    prev_row_bot = (pipe_bottom - 15 - 10) - traj_h   # old layout, 10 pt gap
    new_gap = (prev_row_bot - (CY - 2)) / 2           # footer rule is at CY - 2
    _equal_height_row(c, pipe_bottom - new_gap, traj)

    draw_text_column(c, [
        ("Software Pipeline",
         "Three independent GhPython components in Grasshopper — linked through native "
         "DataTrees — generate geometry, plan motion, and drive the robot. Every log "
         "follows the same seven-waypoint path, so the gripper enters and exits along "
         "the z-axis."),
        ("Parametric Toolpath Generator",
         "Turns a few geometric inputs (pick and place planes, layer count) into the "
         "end-effector frames for every log, handling alternating 90° layers with "
         "strictly vertical approach and departure."),
        ("Cartesian Motion Planner",
         "Iterates over the waypoints and calls COMPAS FAB's plan_cartesian_motion for "
         "each segment, with MoveIt! collision checking. Cartesian planning keeps the "
         "gripper on a controlled arc that clears placed logs; every trajectory is "
         "previewed in Rhino first."),
        ("Execution Controller",
         "Streams the trajectories to the UR3 over one persistent RPC connection and "
         "fires the pneumatic gripper at exact segment boundaries — closing at the "
         "dispenser, opening at the notch, each with a 500 ms dwell."),
    ], start_y=content_top)

    draw_footer(c, page_start + 1, total_pages)
    c.showPage()

    # ── Page 3 — Mechanical Components & Results ───────────────────────────────
    c.setFillColor(C_BG); c.rect(0, 0, PW, PH, fill=1, stroke=0)

    content_top = draw_project_title_block(c,
        "Autonomous Lincoln Log Assembly — Mechanical Design & Results",
        THESIS_CAT, THESIS_DATE)

    _thesis_quad(c, content_top, [
        ("images/thesis/base-v2-cad_cropped.png",      "Calibrated structural base"),
        ("images/thesis/dispenser-final.jpg",          "Gravity-fed log dispenser"),
        ("images/thesis/gripper-covers-installed.jpg", "Gripper with custom covers"),
        ("images/thesis/final-structure.jpg",          "Completed two-layer assembly"),
    ])

    draw_text_column(c, [
        ("Mechanical Design",
         "Three custom 3D-printed fixtures (Fusion 360 / Rhino, PLA) replace runtime "
         "sensing, so the robot never has to find or measure anything."),
        ("Custom Fixtures", [
         "A gravity-fed dispenser presents every log at the same pose from a 15° "
         "inclined channel — chosen over a spring magazine that analysis ruled out.",
         "A calibrated base fixes the first layer on exact 76.3 mm centerlines, so the "
         "system skips first-layer calibration.",
         "Custom gripper covers close the finger gap to log diameter for a positive-stop "
         "grasp.",
        ]),
        ("Testing & Results", [
         "Single-, two-, and three-layer builds, five trials each: 100%, ~75%, and ~83% "
         "success.",
         "Pick success was 100% every trial, validating the dispenser; all failures were "
         "placements.",
         "Failures were systematic: an odd-layer gripper-cover offset and an RPC "
         "connection-pool exhaustion at the 6th log — both diagnosed and fixed.",
        ]),
    ], start_y=content_top)

    draw_footer(c, page_start + 2, total_pages)
    c.showPage()

# ─────────────────────────────────────────────────────────────────────────────
# HTML PREVIEW — render each PDF page to PNG and build a scrollable gallery so
# layout changes can be checked with a browser refresh instead of reopening the
# PDF.  Requires PyMuPDF (fitz); silently skips if it isn't installed.
# ─────────────────────────────────────────────────────────────────────────────
PREVIEW_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Portfolio PDF — Layout Preview</title>
<style>
  :root { color-scheme: light dark; }
  * { box-sizing: border-box; }
  body { margin:0; font-family:-apple-system,Segoe UI,Roboto,Helvetica,sans-serif;
         background:#2b2b2b; color:#eee; }
  header { position:sticky; top:0; z-index:10; background:#1b1b1b;
           border-bottom:1px solid #000; padding:12px 20px;
           display:flex; align-items:center; gap:16px; flex-wrap:wrap; }
  header h1 { font-size:15px; margin:0; font-weight:600; }
  header .meta { font-size:12px; color:#9a9a9a; }
  header .hint { margin-left:auto; font-size:12px; color:#9a9a9a; }
  main { padding:26px 16px 64px; display:flex; flex-direction:column;
         align-items:center; gap:26px; }
  .page { margin:0; width:100%; max-width:1120px; }
  .page img { width:100%; height:auto; display:block; border-radius:4px;
              box-shadow:0 6px 22px rgba(0,0,0,.55); background:#fff; }
  .page figcaption { text-align:center; font-size:12px; color:#9a9a9a; margin-top:8px; }
</style>
</head>
<body>
<header>
  <h1>Portfolio PDF — Layout Preview</h1>
  <span class="meta">__PAGESINFO__</span>
  <span class="hint">Re-run generate_portfolio.py, then refresh (Ctrl/Cmd + R)</span>
</header>
<main>
__CARDS__
</main>
</body>
</html>
"""

def build_preview(pdf_path, dpi=140, pages=None):
    """Render PDF pages to PNGs and write portfolio_preview.html.
    pages=None renders the whole document; pass a list of 1-based page numbers
    (e.g. [3, 4, 5]) to refresh only those pages and show just them."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        print("  [preview skipped] PyMuPDF (fitz) not installed")
        return
    import time
    prev_dir = os.path.join(BASE, "preview")
    os.makedirs(prev_dir, exist_ok=True)

    doc = fitz.open(pdf_path)
    n = doc.page_count
    idxs = [p - 1 for p in pages] if pages else list(range(n))

    if pages is None:                 # full rebuild — clear stale renders first
        for f in os.listdir(prev_dir):
            if f.startswith("page_") and f.endswith(".png"):
                os.remove(os.path.join(prev_dir, f))

    mat = fitz.Matrix(dpi / 72.0, dpi / 72.0)
    ver = int(time.time())            # cache-buster so refresh shows new renders
    cards = []
    for i in idxs:
        fn = f"page_{i + 1:02d}.png"
        doc[i].get_pixmap(matrix=mat).save(os.path.join(prev_dir, fn))
        cards.append(
            '<figure class="page">'
            f'<img src="preview/{fn}?v={ver}" alt="Page {i + 1}" loading="lazy">'
            f'<figcaption>Page {i + 1} / {n}</figcaption></figure>'
        )
    doc.close()

    if pages:
        info = f"pages {', '.join(str(p) for p in pages)} of {n}"
    else:
        info = f"{n} pages"
    info += " · generated " + time.strftime("%Y-%m-%d %H:%M:%S")

    html = (PREVIEW_TEMPLATE
            .replace("__CARDS__", "\n".join(cards))
            .replace("__PAGESINFO__", info))
    out_html = os.path.join(BASE, "portfolio_preview.html")
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Preview: {out_html}  ({len(idxs)} of {n} pages)")

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    TOTAL = 15

    c = canvas.Canvas(OUT, pagesize=landscape(letter))
    c.setTitle("Chimwemwe Chinkuyu — Engineering Portfolio")
    c.setAuthor("Chimwemwe Chinkuyu")

    draw_cover(c, TOTAL)              # 1
    draw_about(c, TOTAL)             # 2
    draw_thesis(c,   3, TOTAL)       # 3, 4, 5
    draw_sarr(c,     6, TOTAL)       # 6, 7
    draw_gearbox(c,  8, TOTAL)       # 8, 9
    draw_car(c,     10, TOTAL)       # 10
    draw_heat(c,    11, TOTAL)       # 11, 12, 13
    draw_airfoil(c, 14, TOTAL)       # 14, 15

    c.save()
    print(f"Saved: {OUT}")

    # Rebuild the full portfolio preview.  (Pass pages=[...] to refresh only a
    # subset while iterating on specific pages.)
    build_preview(OUT)
