#!/usr/bin/env python3
"""Build docs/project-slice.pptx — 10 easy projector slides for Bazaar."""

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Emu, Inches, Pt

OUT = Path(__file__).resolve().parent / "project-slice.pptx"

BG = RGBColor(0xF4, 0xEE, 0xE4)
CARD = RGBColor(0xFF, 0xFC, 0xF7)
FOREST = RGBColor(0x24, 0x36, 0x2C)
MUTED = RGBColor(0x6B, 0x62, 0x58)
INK = RGBColor(0x17, 0x14, 0x11)
CLAY = RGBColor(0xB8, 0x57, 0x2A)
LINE = RGBColor(0xE2, 0xD8, 0xC8)
WHITE = RGBColor(0xF6, 0xEF, 0xE3)

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)


def set_run(run, *, size, bold=False, color=INK, name="Calibri"):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = name


def add_textbox(slide, left, top, width, height):
    return slide.shapes.add_textbox(left, top, width, height)


def paint_bg(slide):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_W, SLIDE_H)
    shape.fill.solid()
    shape.fill.fore_color.rgb = BG
    shape.line.fill.background()
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.12), SLIDE_H)
    bar.fill.solid()
    bar.fill.fore_color.rgb = FOREST
    bar.line.fill.background()


def add_kicker(slide, text, top=Inches(0.55)):
    box = add_textbox(slide, Inches(0.7), top, Inches(12), Inches(0.45))
    p = box.text_frame.paragraphs[0]
    run = p.add_run()
    run.text = text.upper()
    set_run(run, size=18, bold=True, color=CLAY)


def add_title(slide, text, top=Inches(1.0), size=44):
    box = add_textbox(slide, Inches(0.7), top, Inches(12), Inches(1.2))
    p = box.text_frame.paragraphs[0]
    run = p.add_run()
    run.text = text
    set_run(run, size=size, bold=True, color=FOREST, name="Georgia")


def add_lede(slide, text, top=Inches(2.15)):
    box = add_textbox(slide, Inches(0.7), top, Inches(11.5), Inches(0.7))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = text
    set_run(run, size=24, color=MUTED)


def add_card(slide, left, top, width, height, title, body, num=None):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = CARD
    shape.line.color.rgb = LINE
    shape.adjustments[0] = 0.1

    y = top + Inches(0.22)
    if num is not None:
        badge = slide.shapes.add_shape(
            MSO_SHAPE.OVAL, left + Inches(0.22), y, Inches(0.38), Inches(0.38)
        )
        badge.fill.solid()
        badge.fill.fore_color.rgb = FOREST
        badge.line.fill.background()
        tb = add_textbox(slide, left + Inches(0.22), y - Inches(0.02), Inches(0.38), Inches(0.38))
        p = tb.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        run = p.add_run()
        run.text = str(num)
        set_run(run, size=14, bold=True, color=WHITE)
        y += Inches(0.48)

    tbox = add_textbox(slide, left + Inches(0.22), y, width - Inches(0.4), Inches(0.45))
    p = tbox.text_frame.paragraphs[0]
    run = p.add_run()
    run.text = title
    set_run(run, size=26, bold=True, color=FOREST, name="Georgia")

    bbox = add_textbox(
        slide, left + Inches(0.22), y + Inches(0.45), width - Inches(0.4), height - (y - top) - Inches(0.6)
    )
    tf = bbox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = body
    set_run(run, size=18, color=MUTED)


def add_bullets(slide, items, top=Inches(2.9)):
    box = add_textbox(slide, Inches(0.7), top, Inches(11.8), Inches(4.2))
    tf = box.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(14)
        run = p.add_run()
        run.text = "•  " + item
        set_run(run, size=26, color=INK)


def add_process(slide, steps, top=Inches(2.95)):
    n = len(steps)
    gap = Inches(0.18)
    arrow_w = Inches(0.28)
    usable = Inches(12.0) - gap * (n - 1) - arrow_w * (n - 1)
    w = Emu(int(usable) // n)
    left = Inches(0.7)
    for i, label in enumerate(steps):
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, w, Inches(1.55))
        shape.fill.solid()
        shape.fill.fore_color.rgb = CARD
        shape.line.color.rgb = LINE
        shape.adjustments[0] = 0.12

        num = add_textbox(slide, left, top + Inches(0.22), w, Inches(0.55))
        p = num.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        run = p.add_run()
        run.text = str(i + 1)
        set_run(run, size=28, bold=True, color=CLAY, name="Georgia")

        lab = add_textbox(slide, left + Inches(0.08), top + Inches(0.8), w - Inches(0.16), Inches(0.6))
        tf = lab.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        run = p.add_run()
        run.text = label
        set_run(run, size=18, bold=True, color=FOREST)

        left = Emu(int(left) + int(w) + int(gap))
        if i < n - 1:
            ab = add_textbox(slide, left, top + Inches(0.55), arrow_w, Inches(0.5))
            p = ab.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER
            run = p.add_run()
            run.text = "→"
            set_run(run, size=22, bold=True, color=CLAY)
            left = Emu(int(left) + int(arrow_w) + int(gap))


def build():
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H
    blank = prs.slide_layouts[6]

    # 1 Title
    s = prs.slides.add_slide(blank)
    paint_bg(s)
    box = add_textbox(s, Inches(0.7), Inches(2.2), Inches(11.5), Inches(0.55))
    p = box.text_frame.paragraphs[0]
    run = p.add_run()
    run.text = "Bazaar"
    set_run(run, size=32, bold=True, color=CLAY, name="Georgia")
    add_title(s, "Multi-vendor marketplace", top=Inches(2.75), size=54)
    add_lede(
        s,
        "One website. Seller tools. Staff console. Clear maker-checker control.",
        top=Inches(4.15),
    )
    meta = add_textbox(s, Inches(0.7), Inches(5.2), Inches(11.5), Inches(1.2))
    tf = meta.text_frame
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = "Nhanh Kimson, Ly Fanu, Barang LeangHour"
    set_run(run, size=24, bold=True, color=FOREST)
    p2 = tf.add_paragraph()
    run = p2.add_run()
    run.text = "Room 206"
    set_run(run, size=22, color=INK)

    # 2 Surfaces
    s = prs.slides.add_slide(blank)
    paint_bg(s)
    add_kicker(s, "What it is")
    add_title(s, "Three surfaces, one platform")
    add_lede(s, "Buyers, sellers, and staff each get their own place — all talk to the same API.")
    cards = [
        ("Website", "Browse shops & products, cart, checkout, track orders."),
        ("Seller", "Manage catalogue, stock, ship orders, ask for payouts."),
        ("Admin", "Verify shops, publish products, disputes, payouts."),
    ]
    left = Inches(0.7)
    w = Inches(3.85)
    for i, (t, b) in enumerate(cards):
        add_card(s, left, Inches(3.0), w, Inches(3.2), t, b, num=i + 1)
        left += w + Inches(0.25)

    # 3 Roles
    s = prs.slides.add_slide(blank)
    paint_bg(s)
    add_kicker(s, "Who uses it")
    add_title(s, "Four jobs, one login")
    add_lede(s, "Each role has one main job. Staff share the Admin console.")
    roles = [
        ("Customer", "Buy and track. Home: /account"),
        ("Vendor", "Run a shop. Home: /seller"),
        ("Staff", "Check shops & listings. Home: /admin"),
        ("Owner", "Roles & control. Home: /admin"),
    ]
    left = Inches(0.7)
    w = Inches(2.9)
    for t, b in roles:
        add_card(s, left, Inches(3.0), w, Inches(3.0), t, b)
        left += w + Inches(0.2)

    # 4 Buy
    s = prs.slides.add_slide(blank)
    paint_bg(s)
    add_kicker(s, "Buy flow")
    add_title(s, "From browse to e-receipt")
    add_lede(s, "Guests can shop. Email OTP unlocks checkout. Payment sends an e-receipt.")
    add_process(s, ["Browse", "Cart", "OTP if needed", "Pay", "Track + receipt"])
    add_bullets(
        s,
        [
            "Many shops, one checkout — each shop ships its own part",
            "Test card 4242…4242 is approved",
        ],
        top=Inches(4.8),
    )

    # 5 Sell
    s = prs.slides.add_slide(blank)
    paint_bg(s)
    add_kicker(s, "Sell flow")
    add_title(s, "Open a shop in a few steps")
    add_lede(s, "Register with OTP, create the shop (with photo), then add products.")
    add_process(s, ["Register + OTP", "Shop + photo", "Add products", "Staff publish"])
    add_bullets(s, ["Start at /sell · then land on /seller/products"], top=Inches(4.8))

    # 6 Maker-checker
    s = prs.slides.add_slide(blank)
    paint_bg(s)
    add_kicker(s, "Control")
    add_title(s, "Maker-checker: two people")
    add_lede(s, "The person who submits cannot be the only one who approves.")
    checks = [
        ("Shop", "Vendor submits → staff verify → shop goes live."),
        ("Product", "Vendor sends for review → staff publish or reject."),
        ("Payout", "Vendor requests → two different staff must sign."),
    ]
    left = Inches(0.7)
    w = Inches(3.85)
    for i, (t, b) in enumerate(checks):
        add_card(s, left, Inches(3.0), w, Inches(3.2), t, b, num=i + 1)
        left += w + Inches(0.25)

    # 7 Doors
    s = prs.slides.add_slide(blank)
    paint_bg(s)
    add_kicker(s, "Navigation")
    add_title(s, "Login cards open the right door")
    add_lede(s, "Same login page. Role decides where you land.")
    add_bullets(
        s,
        [
            "Customer → /account",
            "Vendor → /seller",
            "Staff / Owner → /admin",
            "Demo password for every seed account: demo",
        ],
    )

    # 8 Tech
    s = prs.slides.add_slide(blank)
    paint_bg(s)
    add_kicker(s, "Tech (simple)")
    add_title(s, "Next.js → Flask → Postgres")
    add_lede(s, "Browser only talks to Next.js. API and media are proxied.")
    add_bullets(
        s,
        [
            "Next.js — website + dashboards",
            "Flask API — REST + docs at /api/docs",
            "PostgreSQL + RLS — each shop only sees its own data",
            "Money in integer cents — no float mistakes",
        ],
    )

    # 9 Demo
    s = prs.slides.add_slide(blank)
    paint_bg(s)
    add_kicker(s, "Demo")
    add_title(s, "Try it in minutes")
    add_lede(s, "Run ./dev.sh then open these.")
    add_bullets(
        s,
        [
            "Site — http://127.0.0.1:3000",
            "Login cards — Maya (buy), Jess (sell), Ava (admin)",
            "Password — demo · Card — 4242 4242 4242 4242",
            "OTP / e-receipts (local) — backend/private/mailbox/",
        ],
    )

    # 10 Takeaway
    s = prs.slides.add_slide(blank)
    paint_bg(s)
    add_kicker(s, "Takeaway")
    add_title(s, "What works today")
    add_bullets(
        s,
        [
            "Email OTP register and guest checkout",
            "Shop apply with photo + seller dashboards",
            "Maker-checker for shops, listings, payouts",
            "Pay → order track + e-receipt",
        ],
        top=Inches(2.4),
    )
    foot = add_textbox(s, Inches(0.7), Inches(6.5), Inches(12), Inches(0.5))
    p = foot.text_frame.paragraphs[0]
    run = p.add_run()
    run.text = "Bazaar · Room 206 · Nhanh Kimson, Ly Fanu, Barang LeangHour"
    set_run(run, size=18, color=MUTED)

    prs.save(OUT)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    build()
