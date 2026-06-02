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

def wrapped_text(c, x, y, text, width, size=9, color=None, font="Helvetica",
                 line_height=None, align="left"):
    if color is None:
        color = C_DARK
    if line_height is None:
        line_height = size * 1.45
    c.setFont(font, size)
    c.setFillColor(color)
    words = text.split()
    line, lines = [], []
    for w in words:
        test = " ".join(line + [w])
        if c.stringWidth(test, font, size) <= width:
            line.append(w)
        else:
            if line:
                lines.append(" ".join(line))
            line = [w]
    if line:
        lines.append(" ".join(line))
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

def fit_image(c, path, x, y, w, h, anchor="center"):
    """Letterbox — full image visible.
    anchor='top'    → image flush with box top, white space below.
    anchor='center' → image centered, white space split evenly.
    """
    if not os.path.exists(path):
        return
    try:
        pil = _pil_to_rgb(PILImage.open(path))
        iw, ih = pil.size
        if max(iw, ih) > MAX_IMG_PX:
            r = MAX_IMG_PX / max(iw, ih)
            pil = pil.resize((int(iw*r), int(ih*r)), PILImage.LANCZOS)
            iw, ih = pil.size
        scale = min(w / iw, h / ih)
        dw, dh = iw * scale, ih * scale
        buf = BytesIO(); pil.save(buf, format="JPEG", quality=72); buf.seek(0)
        ox = x + (w - dw) / 2
        oy = (y + h - dh) if anchor == "top" else (y + (h - dh) / 2)
        c.drawImage(ImageReader(buf), ox, oy, dw, dh)
    except Exception as e:
        print(f"  [fit_image skip] {path}: {e}")

# ── Shared chrome ──────────────────────────────────────────────────────────────
def draw_footer(c, page_num, total_pages):
    c.setFillColor(C_RULE)
    c.rect(CX, CY - 2, CW, 0.5, fill=1, stroke=0)
    draw_text(c, CX, CY - 11, "Chimwemwe Chinkuyu  |  Engineering Portfolio",
              size=9, color=C_MUTED)
    draw_text(c, CX + CW, CY - 11, f"{page_num} / {total_pages}",
              size=9, color=C_MUTED, align="right")

def draw_section_label(c, x, y, label):
    draw_text(c, x, y, label.upper(), size=10, color=C_MUTED, font="Helvetica-Bold")
    c.setStrokeColor(C_RULE)
    c.setLineWidth(0.5)
    c.line(x, y - 3, x + CW * 0.3, y - 3)

# ── Project page layout ────────────────────────────────────────────────────────
IMG_FRAC = 0.63
TXT_GAP  = 0.18 * inch

def img_col_w():  return CW * IMG_FRAC
def txt_col_x():  return CX + img_col_w() + TXT_GAP
def txt_col_w():  return CW - img_col_w() - TXT_GAP

def project_body_top():
    return PH - M

def draw_project_title_block(c, title, category, date):
    """Category / title / date at top of text column, no rule."""
    x = txt_col_x()
    w = txt_col_w()
    y = project_body_top()
    # Category label
    draw_text(c, x, y, category.upper(), size=11, color=C_MUTED, font="Helvetica-Bold")
    y -= 19
    # Title (wrapped, larger)
    y = wrapped_text(c, x, y, title, w, size=16, color=C_DARK,
                     font="Helvetica-Bold", line_height=19)
    y -= 10
    # Date
    draw_text(c, x, y, date, size=11, color=C_MUTED)
    y -= 26
    return y

def draw_text_column(c, bullets, start_y=None):
    x = txt_col_x()
    w = txt_col_w()
    y = start_y if start_y is not None else project_body_top()
    for label, text in bullets:
        if label:
            draw_section_label(c, x, y, label)
            y -= 15
        y = wrapped_text(c, x, y, text, w, size=12, color=C_MID, line_height=17)
        y -= 11
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

    draw_text(c, PAD, title_y, "ENGINEERING DESIGN PORTFOLIO",
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

    # Bio — 2 paragraphs
    bio_paras = [
        "I'm inspired by the possibility to turn ideas into smart, functional solutions at "
        "the intersection of hardware and software. My work spans mechanical design, fabrication, "
        "and software development — from building a load-bearing airfoil to writing autonomous "
        "vehicle controllers in Python and ROS.",
        "I'm eager to grow in innovation-focused environments and contribute to advanced devices, "
        "autonomous systems, and technologies that enhance human health and quality of life.",
    ]
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
    y -= 26

    # Contact links — linkedin + portfolio on row 1, email on row 2
    half_w    = CW / 2
    LABEL_W_L = 100   # shorter for LINKEDIN / EMAIL
    LABEL_W_R = 158   # wider for PORTFOLIO WEBSITE (longer label)

    draw_text(c, CX, y, "LINKEDIN", size=11, color=C_MUTED, font="Helvetica-Bold")
    draw_hyperlink(c, CX + LABEL_W_L, y, "linkedin.com/in/chimwemwe-chinkuyu",
                   "https://www.linkedin.com/in/chimwemwe-chinkuyu/", size=12)
    draw_text(c, CX + half_w, y, "PORTFOLIO WEBSITE", size=11, color=C_MUTED, font="Helvetica-Bold")
    draw_hyperlink(c, CX + half_w + LABEL_W_R, y, "ckcgithub16.github.io",
                   "https://ckcgithub16.github.io/CC_Portfolio/index.html", size=12)
    y -= 20

    draw_text(c, CX, y, "EMAIL", size=11, color=C_MUTED, font="Helvetica-Bold")
    draw_hyperlink(c, CX + LABEL_W_L, y, "cc9970@princeton.edu",
                   "mailto:cc9970@princeton.edu", size=12)

    draw_footer(c, 2, total_pages)
    c.showPage()

# ─────────────────────────────────────────────────────────────────────────────
# PROJECT 1 — SARR  (2 pages)
# ─────────────────────────────────────────────────────────────────────────────
def draw_sarr(c, page_start, total_pages):
    # ── Page 1 ────────────────────────────────────────────────────────────────
    c.setFillColor(C_BG); c.rect(0, 0, PW, PH, fill=1, stroke=0)

    top_y   = project_body_top()
    iw      = img_col_w()
    total   = top_y - CY
    main_h  = total * 0.62
    small_h = total - main_h - 6

    fit_image(c, os.path.join(BASE, "images/sarr/motherbot_on_ramp.JPG"),
              CX, CY + small_h + 6, iw, main_h, anchor="top")
    sw = (iw - 6) / 2
    fit_image(c, os.path.join(BASE, "images/sarr/motherbot_deploying_babybot.JPG"),
              CX, CY, sw, small_h)
    fit_image(c, os.path.join(BASE, "images/sarr/system_concept_diagram.png"),
              CX + sw + 6, CY, sw, small_h)

    title_y = draw_project_title_block(c,
        "Design & Manufacturing of a Search and Rescue Robot",
        "Mechanical Engineering", "Oct – Dec 2025")
    draw_text_column(c, [
        ("Outcome",
         "An 11-member team built a marsupial search-and-rescue robot in 8 weeks. "
         "The Motherbot autonomously navigated a ramp, chute, and 36-inch wall while "
         "carrying the Babybot. The Babybot was deployed over the wall, navigated to "
         "a target zone, and delivered a medkit payload — completing the full course "
         "at the final class demonstration."),
        ("My Contribution",
         "I designed the Motherbot's low-carbon steel (AISI 1018) chassis and a "
         "60:1 two-stage HTD belt drivetrain. Work included FEA for structural "
         "verification, manufacturing drawings in Creo Parametric, and hands-on "
         "fabrication: band saw cutting, knee mill coping, and MIG welding."),
        ("Skills Used",
         "Creo Parametric · FEA · GD&T · MIG Welding · CNC Milling · Lathe · "
         "Belt Drive Design · Embedded Control (Teensy/C++)"),
    ], start_y=title_y)

    draw_footer(c, page_start, total_pages)
    c.showPage()

    # ── Page 2 ────────────────────────────────────────────────────────────────
    c.setFillColor(C_BG); c.rect(0, 0, PW, PH, fill=1, stroke=0)

    top_y = project_body_top()
    iw    = img_col_w()
    GAP   = 8
    row_h = (top_y - CY - GAP) / 2

    fit_image(c, os.path.join(BASE, "images/sarr/motherbot_chassis_assembly_drawing.png"),
              CX, CY + row_h + GAP, iw, row_h, anchor="top")
    fit_image(c, os.path.join(BASE, "images/sarr/lifting_arm_deployment_sequence.png"),
              CX, CY, iw * 0.55, row_h)
    fit_image(c, os.path.join(BASE, "images/sarr/babybot_photo.jpeg"),
              CX + iw * 0.55 + 6, CY, iw * 0.45 - 6, row_h)

    title_y = draw_project_title_block(c,
        "Search and Rescue Robot — Subsystem Detail",
        "Mechanical Engineering", "Oct – Dec 2025")
    draw_text_column(c, [
        ("Chassis Design",
         "The welded steel chassis was optimized for rigidity at motor mount positions "
         "and the lifting arm pivot. FBD analysis confirmed tip-over stability during "
         "Babybot deployment. The weldment showed no deformation through all testing."),
        ("Drivetrain",
         "60:1 two-stage belt reduction over HTD pulleys and a jackshaft. Belt drives "
         "chosen for shock absorption and tolerance of minor shaft misalignment. "
         "Adjustment slots in motor mount brackets allowed precise pulley alignment."),
        ("Lifting Arm",
         "Rotating arm pivots from stowed horizontal to fully raised, clearing the wall. "
         "A spring-latch cradle keeps the Babybot level during lift and releases on "
         "contact with the far side. Torque requirements calculated analytically."),
        ("Controls",
         "State machine: proportional control (flat) → bang-bang (ramp) → PD (chute) "
         "→ open-loop arm sequence (wall). Ultrasonic sensors trigger state transitions; "
         "CdS phototransistors provide line-following error signals."),
    ], start_y=title_y)

    draw_footer(c, page_start + 1, total_pages)
    c.showPage()

# ─────────────────────────────────────────────────────────────────────────────
# PROJECT 2 — DIFFERENTIAL GEARBOX  (2 pages)
# ─────────────────────────────────────────────────────────────────────────────
def draw_gearbox(c, page_start, total_pages):
    # ── Page 1 ────────────────────────────────────────────────────────────────
    c.setFillColor(C_BG); c.rect(0, 0, PW, PH, fill=1, stroke=0)

    top_y   = project_body_top()
    iw      = img_col_w()
    total   = top_y - CY
    main_h  = total * 0.62
    small_h = total - main_h - 6

    fit_image(c, os.path.join(BASE, "images/gear_box/assembly_front_oblong_transluscent.png"),
              CX, CY + small_h + 6, iw, main_h, anchor="top")
    sw = (iw - 6) / 2
    fit_image(c, os.path.join(BASE, "images/gear_box/assembly_front.png"),
              CX, CY, sw, small_h)
    fit_image(c, os.path.join(BASE, "images/gear_box/assembly_side.png"),
              CX + sw + 6, CY, sw, small_h)

    title_y = draw_project_title_block(c,
        "Custom Differential Gearbox",
        "Mechanical Engineering  ·  CAD", "June 2025")
    draw_text_column(c, [
        ("Outcome",
         "A fully parametric bevel-gear axle differential designed entirely in "
         "Autodesk Fusion 360. The planetary differential configuration distributes "
         "drive torque between two output shafts while allowing independent rotation "
         "speeds, enabling smooth, skid-free turning."),
        ("Design Approach",
         "Gear geometry was determined using standard bevel gear formulas driven by "
         "linked Fusion 360 equations — module, pressure angle, tooth count, and pitch "
         "circle diameter update the full geometry automatically as inputs change."),
        ("Components Modeled",
         "Bevel ring gear · Spider gears · Output half-shafts · Hub flanges · Outer casing. "
         "All parts constrained in a fully assembled Fusion 360 model with exploded view animation."),
        ("Skills Used",
         "Autodesk Fusion 360 · Parametric Modeling · Bevel Gear Theory · "
         "Assembly Constraints · Engineering Visualization"),
    ], start_y=title_y)

    draw_footer(c, page_start, total_pages)
    c.showPage()

    # ── Page 2 ────────────────────────────────────────────────────────────────
    c.setFillColor(C_BG); c.rect(0, 0, PW, PH, fill=1, stroke=0)

    top_y = project_body_top()
    iw    = img_col_w()
    rows, cols = 2, 3
    gap   = 6
    rh_img = (top_y - CY - gap) / rows
    cw_img = (iw - gap * (cols - 1)) / cols

    comp_images = [
        ("images/gear_box/long_central_shaft_front.png",      "Long Drive Shaft"),
        ("images/gear_box/short_central_shaft_front.png",     "Short Drive Shaft"),
        ("images/gear_box/long_central_shaft_gear_front.png", "Bevel Gear"),
        ("images/gear_box/slotted_ring_front.png",            "Differential Ring"),
        ("images/gear_box/back_hub_front.png",                "Output Hub"),
        ("images/gear_box/outer_casing_bowl_front.png",       "Outer Casing"),
    ]
    for idx, (rel, lbl) in enumerate(comp_images):
        row = idx // cols; col = idx % cols
        bx = CX + col * (cw_img + gap)
        by = CY + (rows - 1 - row) * (rh_img + gap)
        fit_image(c, os.path.join(BASE, rel), bx, by + 12, cw_img, rh_img - 12,
                  anchor="top" if row == 0 else "center")
        draw_text(c, bx + cw_img / 2, by + 2, lbl, size=9.5, color=C_MUTED, align="center")

    title_y = draw_project_title_block(c,
        "Custom Differential Gearbox — Component Drawings",
        "Mechanical Engineering  ·  CAD", "June 2025")
    draw_text_column(c, [
        ("Parametric Design",
         "Every component dimension is driven by top-level gear parameters. "
         "Changing the module or tooth count propagates through the entire "
         "assembly without manual rework — a key advantage for iterative design."),
        ("Key Geometries",
         "Bevel gears use a 20° pressure angle standard. The differential ring "
         "constrains the spider gear orbits and transmits input torque to the "
         "output shafts via the crown gear mesh."),
        ("Visualization",
         "An exploded assembly animation was produced in Fusion 360 to communicate "
         "part relationships and assembly sequence clearly to non-engineering audiences."),
    ], start_y=title_y)

    draw_footer(c, page_start + 1, total_pages)
    c.showPage()

# ─────────────────────────────────────────────────────────────────────────────
# PROJECT 3 — SELF-DRIVING RC TRUCK  (1 page)
# ─────────────────────────────────────────────────────────────────────────────
def draw_car(c, page_start, total_pages):
    c.setFillColor(C_BG); c.rect(0, 0, PW, PH, fill=1, stroke=0)

    top_y = project_body_top()
    iw    = img_col_w()
    fit_image(c, os.path.join(BASE, "images/autonomous_car/autonomous_car_main.jpeg"),
              CX, CY, iw, top_y - CY, anchor="top")

    title_y = draw_project_title_block(c,
        "Self-Driving RC Truck with Obstacle Avoidance & Safety Filter",
        "Mechanical Engineering  ·  Software Development", "Mar – May 2025")
    draw_text_column(c, [
        ("Outcome",
         "A 1/10-scale RC truck programmed in Python + ROS to complete two "
         "autonomous driving tasks. Task 1: navigated 16 waypoints while avoiding "
         "up to 20 randomly placed obstacle cubes within 3:30. "
         "Result: 4th fastest of 14 teams. Task 2: ADAS safety filter overrode "
         "steering commands that would cause track departure."),
        ("Task 1 — Obstacle Avoidance",
         "Path planner dynamically resizes safety ellipse radii within a threshold "
         "distance of obstacles. Gaussian filtering (σ=2 physical, σ=5 sim) "
         "smoothed trajectories. Dual-planner cost calculation allowed simultaneous "
         "manual control until the last safe moment for full intervention."),
        ("Task 2 — Safety Filter",
         "Two-layer safety system using real sensor measurements and a simulator "
         "running at 1000 Hz for soft trajectory generation. Costs calculated over a "
         "varying time horizon; partial intervention applied as late as safely possible."),
        ("Key Lesson",
         "Bridging the simulation-to-hardware gap required substantial parameter "
         "tuning. A boolean flag bug causing incorrect behavior across multiple "
         "scenarios was caught through systematic per-subsystem isolation testing."),
        ("Skills Used",
         "Python · ROS · Path Planning · Control Theory · "
         "Obstacle Avoidance · Simulation-to-Hardware Transfer"),
    ], start_y=title_y)

    draw_footer(c, page_start, total_pages)
    c.showPage()

# ─────────────────────────────────────────────────────────────────────────────
# PROJECT 4 — HEAT TRANSFER SIMULATION  (2 pages)
# ─────────────────────────────────────────────────────────────────────────────
def draw_heat(c, page_start, total_pages):
    # ── Page 1 ────────────────────────────────────────────────────────────────
    c.setFillColor(C_BG); c.rect(0, 0, PW, PH, fill=1, stroke=0)

    top_y   = project_body_top()
    iw      = img_col_w()
    total   = top_y - CY
    main_h  = total * 0.58
    small_h = total - main_h - 6

    fit_image(c, os.path.join(BASE, "images/psi_omega_simulation/fin_main1_temp_only.png"),
              CX, CY + small_h + 6, iw, main_h, anchor="top")
    fit_image(c, os.path.join(BASE, "images/psi_omega_simulation/fin_main1.png"),
              CX, CY, iw, small_h)

    title_y = draw_project_title_block(c,
        "2D Unsteady Heat Transfer: Heated Cylinder & NACA 2412 Airfoil",
        "Mechanical Engineering  ·  Numerical Methods", "Apr – May 2025")
    draw_text_column(c, [
        ("Outcome",
         "A Psi-Omega (streamfunction-vorticity) finite difference numerical "
         "simulation built from scratch in MATLAB. Two geometries studied: "
         "a 400°C cylinder in 300°C flow (convective heat flux 7.6 kW/m²), and "
         "a NACA 2412 airfoil at 5° and 30° AoA "
         "(heat flux 1,002.6 vs 1,133.6 W/m²). Each run took 3–6 hours."),
        ("Technical Approach",
         "Three coupled PDEs solved at each time step: "
         "Streamfunction (Poisson) via Gauss-Seidel with over-relaxation; "
         "Vorticity (momentum) via forward Euler with upwind differencing; "
         "Temperature (energy) coupled to the velocity field."),
        ("Validation",
         "The 5° AoA result was validated against SimFlow CFD. The 30° AoA "
         "simulation exhibits vortex shedding with Strouhal number St = 0.62, "
         "consistent with separated flow theory."),
        ("Skills Used",
         "MATLAB · Finite Difference Methods · Fluid Dynamics · Heat Transfer · "
         "Numerical Stability · CFD Validation"),
    ], start_y=title_y)

    draw_footer(c, page_start, total_pages)
    c.showPage()

    # ── Page 2 ────────────────────────────────────────────────────────────────
    c.setFillColor(C_BG); c.rect(0, 0, PW, PH, fill=1, stroke=0)

    top_y = project_body_top()
    iw    = img_col_w()
    GAP   = 6
    row_h = (top_y - CY - GAP) / 2

    fit_image(c, os.path.join(BASE, "images/psi_omega_simulation/sim_part_b_main1.png"),
              CX, CY + row_h + GAP, iw, row_h, anchor="top")
    fit_image(c, os.path.join(BASE, "images/psi_omega_simulation/sim_part_b_main2.png"),
              CX, CY, iw, row_h)

    draw_text(c, CX + iw / 2, CY + row_h + 3,
              "NACA 2412 at 5° AoA — attached flow (validated against SimFlow)",
              size=9.5, color=C_MUTED, align="center")
    draw_text(c, CX + iw / 2, CY + 3,
              "NACA 2412 at 30° AoA — vortex shedding and stall (St = 0.62)",
              size=9.5, color=C_MUTED, align="center")

    title_y = draw_project_title_block(c,
        "Heat Transfer Simulation — Airfoil Results",
        "Mechanical Engineering  ·  Numerical Methods", "Apr – May 2025")
    draw_text_column(c, [
        ("5° Angle of Attack",
         "Flow remains attached. Temperature distribution is smooth and symmetric "
         "about the chord line. Validated within 5% of SimFlow commercial CFD results, "
         "confirming correct PDE discretization and boundary conditions."),
        ("30° Angle of Attack",
         "Flow separates at the leading edge, producing large unsteady vortices shed "
         "periodically into the wake. Higher stagnation temperatures and increased "
         "heat flux (13% above 5° case) result from thickened boundary layer."),
        ("Debugging Process",
         "10 iteration cycles for the cylinder, 5 for the airfoil. Primary instability "
         "sources: vorticity boundary conditions at the cylinder wall and incorrect "
         "vorticity extrapolation at sharp airfoil edges."),
    ], start_y=title_y)

    draw_footer(c, page_start + 1, total_pages)
    c.showPage()

# ─────────────────────────────────────────────────────────────────────────────
# PROJECT 5 — LOAD-BEARING AIRFOIL  (2 pages)
# ─────────────────────────────────────────────────────────────────────────────
def draw_airfoil(c, page_start, total_pages):
    # ── Page 1 ────────────────────────────────────────────────────────────────
    c.setFillColor(C_BG); c.rect(0, 0, PW, PH, fill=1, stroke=0)

    top_y   = project_body_top()
    iw      = img_col_w()
    total   = top_y - CY
    main_h  = total * 0.62
    small_h = total - main_h - 6

    fit_image(c, os.path.join(BASE, "images/airfoil/wing-assembly.jpg"),
              CX, CY + small_h + 6, iw, main_h, anchor="top")
    sw = (iw - 6) / 2
    fit_image(c, os.path.join(BASE, "images/airfoil/airfoil_deflecting_97.jpg"),
              CX, CY, sw, small_h)
    fit_image(c, os.path.join(BASE, "images/airfoil/assembly_fea.png"),
              CX + sw + 6, CY, sw, small_h)

    title_y = draw_project_title_block(c,
        "Design and Manufacturing of a Load-Bearing Airfoil",
        "Mechanical Engineering", "Mar – May 2023")
    draw_text_column(c, [
        ("Outcome",
         "A 9-member team designed and manufactured a 25.5-inch load-bearing "
         "airfoil that supported 97 lbf at 23.5 inches from the secured end "
         "with 3.75 in. tip deflection. Structure cost $180.75, weighed 18.3 oz. "
         "Failure at 120 lbs (beam web torsion) — above the 97 lbf design load."),
        ("Design",
         "Aluminum 7075-T651 I-beam (yield stress 73,000 psi) with circular "
         "lightening holes selected for best strength-to-weight ratio from four "
         "competing beam concepts. Nylon bulkheads with circular cutouts reduced "
         "weight; balsa wood skin formed the NACA profile."),
        ("FEA & Validation",
         "PTC Creo FEA validated deflection at 97 lbf. Failure mode — beam web "
         "torsion collapse at 120 lbs — was not captured in the planar FEA model, "
         "teaching the importance of 3D torsional load modeling."),
        ("Skills Used",
         "PTC Creo · FEA · CNC Milling (Haas VF-7/40) · Waterjet (ProtoMAX) · "
         "FDM & SLS 3D Printing · Structural Analysis · GD&T"),
    ], start_y=title_y)

    draw_footer(c, page_start, total_pages)
    c.showPage()

    # ── Page 2 ────────────────────────────────────────────────────────────────
    c.setFillColor(C_BG); c.rect(0, 0, PW, PH, fill=1, stroke=0)

    top_y = project_body_top()
    iw    = img_col_w()
    rows, cols = 2, 3
    gap   = 6
    rh_img = (top_y - CY - gap) / rows
    cw_img = (iw - gap * (cols - 1)) / cols

    mfg_images = [
        ("images/airfoil/circular_hole_I-beam.JPG",   "Circular-Hole I-Beam"),
        ("images/airfoil/beam_fea.png",                "I-Beam FEA"),
        ("images/airfoil/circle_bulkhead.png",         "Nylon Bulkhead Design"),
        ("images/airfoil/waterjetbh.png",              "Waterjetted Bulkhead"),
        ("images/airfoil/leadingedge.JPG",             "Leading Edge"),
        ("images/airfoil/airfoil_pre_test.jpg",        "Pre-Test Assembly"),
    ]
    for idx, (rel, lbl) in enumerate(mfg_images):
        row = idx // cols; col = idx % cols
        bx = CX + col * (cw_img + gap)
        by = CY + (rows - 1 - row) * (rh_img + gap)
        fit_image(c, os.path.join(BASE, rel), bx, by + 12, cw_img, rh_img - 12,
                  anchor="top" if row == 0 else "center")
        draw_text(c, bx + cw_img / 2, by + 2, lbl, size=9.5, color=C_MUTED, align="center")

    title_y = draw_project_title_block(c,
        "Load-Bearing Airfoil — Manufacturing & Testing",
        "Mechanical Engineering", "Mar – May 2023")
    draw_text_column(c, [
        ("Manufacturing",
         "I-beam CNC milled on Haas VF-7/40. Bulkheads waterjet-cut on ProtoMAX. "
         "Ribs printed on Ender 3 Pro (FDM) and structural parts on Formlabs SLS. "
         "Balsa skin cut on bandsaw and sanded to NACA profile."),
        ("Testing Results",
         "Passed 97 lbf design load at 3.75 in. deflection. Continued loading to "
         "failure at 120 lbs. All cost and weight targets met."),
        ("Lessons Learned",
         "Torsional loads must be explicitly modeled in 3D FEA. Physical load paths "
         "in complex assemblies differ from simplified beam theory predictions, "
         "especially near joints and web openings."),
    ], start_y=title_y)

    draw_footer(c, page_start + 1, total_pages)
    c.showPage()

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    TOTAL = 11

    c = canvas.Canvas(OUT, pagesize=landscape(letter))
    c.setTitle("Chimwemwe Chinkuyu — Engineering Portfolio")
    c.setAuthor("Chimwemwe Chinkuyu")

    draw_cover(c, TOTAL)
    draw_about(c, TOTAL)
    draw_sarr(c,    3, TOTAL)
    draw_gearbox(c, 5, TOTAL)
    draw_car(c,     7, TOTAL)
    draw_heat(c,    8, TOTAL)
    draw_airfoil(c, 10, TOTAL)

    c.save()
    print(f"Saved: {OUT}")
